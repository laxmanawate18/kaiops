"""
Chat Session Database with MongoDB

Persistent storage for chat sessions and messages.
"""
from typing import Dict, Optional, List
from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from ..database import get_db, Collections
from .models import ChatSession, ChatMessage, MessageSender
import uuid
import logging

logger = logging.getLogger(__name__)


class ChatDatabase:
    """MongoDB-backed database for managing user-isolated chat sessions and messages."""
    
    def __init__(self):
        self.db = get_db()
        self.sessions_collection: Optional[Collection] = None
        self.messages_collection: Optional[Collection] = None
        
        if self.db is not None:
            self.sessions_collection = self.db[Collections.CHAT_SESSIONS]
            self.messages_collection = self.db[Collections.CHAT_MESSAGES]
            self._create_indexes()
        else:
            logger.warning("⚠️ MongoDB not available, using in-memory fallback for chat")
            # Fallback to in-memory
            self.sessions: Dict[str, Dict[str, Dict]] = {}
            self.messages: Dict[str, List[Dict]] = {}
        
        logger.info("Chat database initialized with user isolation")
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        if self.sessions_collection is None or self.messages_collection is None:
            return
        
        try:
            # Session indexes
            self.sessions_collection.create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="user_sessions"
            )
            self.sessions_collection.create_index(
                [("is_active", ASCENDING)],
                name="active_sessions"
            )
            
            # Message indexes
            self.messages_collection.create_index(
                [("session_id", ASCENDING), ("timestamp", ASCENDING)],
                name="session_messages"
            )
            self.messages_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_messages"
            )
            
            logger.info("✅ Chat database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    # ==================== Session Management ====================
    
    def create_session(self, user_id: str, session_name: Optional[str] = None) -> Dict:
        """Create a new chat session for a user."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        if not session_name:
            session_name = f"Chat {timestamp.strftime('%b %d, %I:%M %p')}"
        
        session = {
            "id": session_id,
            "user_id": user_id,
            "name": session_name,
            "created_at": timestamp,
            "last_modified": timestamp,
            "message_count": 0,
            "is_active": True,
            "metadata": {}
        }
        
        if self.sessions_collection is not None:
            self.sessions_collection.insert_one(session)
            logger.info(f"Created chat session: {session_id} for user: {user_id}")
            # Convert datetime for response
            session["created_at"] = timestamp.isoformat()
            session["last_modified"] = timestamp.isoformat()
            session.pop("_id", None)
        else:
            # In-memory fallback
            if user_id not in self.sessions:
                self.sessions[user_id] = {}
            session["created_at"] = timestamp.isoformat()
            session["last_modified"] = timestamp.isoformat()
            self.sessions[user_id][session_id] = session
            self.messages[session_id] = []
        
        return session
    
    def get_session(self, user_id: str, session_id: str) -> Optional[Dict]:
        """Get a specific session for a user."""
        if self.sessions_collection is not None:
            session = self.sessions_collection.find_one({
                "id": session_id,
                "user_id": user_id
            })
            if session:
                session.pop("_id", None)
                if isinstance(session.get("created_at"), datetime):
                    session["created_at"] = session["created_at"].isoformat()
                if isinstance(session.get("last_modified"), datetime):
                    session["last_modified"] = session["last_modified"].isoformat()
            return session
        else:
            if user_id in self.sessions and session_id in self.sessions[user_id]:
                return self.sessions[user_id][session_id]
            return None
    
    def get_user_sessions(self, user_id: str, include_inactive: bool = True) -> List[Dict]:
        """Get all sessions for a user."""
        if self.sessions_collection is not None:
            query = {"user_id": user_id}
            if not include_inactive:
                query["is_active"] = True
            
            cursor = self.sessions_collection.find(query).sort("last_modified", DESCENDING)
            sessions = []
            for session in cursor:
                session.pop("_id", None)
                if isinstance(session.get("created_at"), datetime):
                    session["created_at"] = session["created_at"].isoformat()
                if isinstance(session.get("last_modified"), datetime):
                    session["last_modified"] = session["last_modified"].isoformat()
                sessions.append(session)
            return sessions
        else:
            if user_id not in self.sessions:
                return []
            
            sessions = list(self.sessions[user_id].values())
            if not include_inactive:
                sessions = [s for s in sessions if s.get("is_active", True)]
            
            sessions.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
            return sessions
    
    def update_session(self, user_id: str, session_id: str, **updates) -> Optional[Dict]:
        """Update session details."""
        if self.sessions_collection is not None:
            updates["last_modified"] = datetime.now(timezone.utc)
            
            result = self.sessions_collection.find_one_and_update(
                {"id": session_id, "user_id": user_id},
                {"$set": updates},
                return_document=True
            )
            
            if result:
                result.pop("_id", None)
                if isinstance(result.get("created_at"), datetime):
                    result["created_at"] = result["created_at"].isoformat()
                if isinstance(result.get("last_modified"), datetime):
                    result["last_modified"] = result["last_modified"].isoformat()
            
            return result
        else:
            session = self.get_session(user_id, session_id)
            if not session:
                return None
            
            allowed_fields = ["name", "is_active", "metadata"]
            for field in allowed_fields:
                if field in updates and updates[field] is not None:
                    session[field] = updates[field]
            
            session["last_modified"] = datetime.now(timezone.utc).isoformat()
            return session
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a session and all its messages."""
        if self.sessions_collection is not None and self.messages_collection is not None:
            session_result = self.sessions_collection.delete_one({
                "id": session_id,
                "user_id": user_id
            })
            
            if session_result.deleted_count > 0:
                self.messages_collection.delete_many({"session_id": session_id})
                logger.info(f"Deleted session {session_id} and its messages")
                return True
            return False
        else:
            if user_id not in self.sessions or session_id not in self.sessions[user_id]:
                return False
            
            del self.sessions[user_id][session_id]
            if session_id in self.messages:
                del self.messages[session_id]
            
            return True
    
    def delete_all_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        if self.sessions_collection is not None and self.messages_collection is not None:
            # Get all session IDs
            sessions = list(self.sessions_collection.find({"user_id": user_id}, {"id": 1}))
            session_ids = [s["id"] for s in sessions]
            
            # Delete messages
            if session_ids:
                self.messages_collection.delete_many({"session_id": {"$in": session_ids}})
            
            # Delete sessions
            result = self.sessions_collection.delete_many({"user_id": user_id})
            count = result.deleted_count
            
            logger.info(f"Deleted {count} sessions for user {user_id}")
            return count
        else:
            if user_id not in self.sessions:
                return 0
            
            session_ids = list(self.sessions[user_id].keys())
            for session_id in session_ids:
                if session_id in self.messages:
                    del self.messages[session_id]
            
            count = len(self.sessions[user_id])
            del self.sessions[user_id]
            return count
    
    # ==================== Message Management ====================
    
    def add_message(
        self,
        user_id: str,
        session_id: str,
        sender: MessageSender,
        text: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Add a message to a session."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        message = {
            "id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "sender": sender.value if hasattr(sender, 'value') else sender,
            "text": text,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        if self.messages_collection is not None and self.sessions_collection is not None:
            self.messages_collection.insert_one(message)
            
            # Update session
            self.sessions_collection.update_one(
                {"id": session_id, "user_id": user_id},
                {
                    "$set": {"last_modified": timestamp},
                    "$inc": {"message_count": 1}
                }
            )
            
            # Convert for response
            message["timestamp"] = timestamp.isoformat()
            message.pop("_id", None)
        else:
            # In-memory fallback
            message["timestamp"] = timestamp.isoformat()
            
            if session_id not in self.messages:
                self.messages[session_id] = []
            
            self.messages[session_id].append(message)
            
            # Update session
            session = self.get_session(user_id, session_id)
            if session:
                session["last_modified"] = timestamp.isoformat()
                session["message_count"] = session.get("message_count", 0) + 1
        
        return message
    
    def get_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 100,
        before_timestamp: Optional[str] = None
    ) -> List[Dict]:
        """Get messages for a session."""
        if self.messages_collection is not None:
            query = {"session_id": session_id, "user_id": user_id}
            
            if before_timestamp:
                query["timestamp"] = {"$lt": datetime.fromisoformat(before_timestamp)}
            
            cursor = self.messages_collection.find(query).sort("timestamp", ASCENDING).limit(limit)
            messages = []
            for msg in cursor:
                msg.pop("_id", None)
                if isinstance(msg.get("timestamp"), datetime):
                    msg["timestamp"] = msg["timestamp"].isoformat()
                messages.append(msg)
            return messages
        else:
            if session_id not in self.messages:
                return []
            
            messages = self.messages[session_id]
            
            if before_timestamp:
                messages = [m for m in messages if m["timestamp"] < before_timestamp]
            
            return messages[-limit:]
    
    def get_message_count(self, user_id: str, session_id: str) -> int:
        """Get count of messages in a session."""
        if self.messages_collection is not None:
            return self.messages_collection.count_documents({
                "session_id": session_id,
                "user_id": user_id
            })
        else:
            return len(self.messages.get(session_id, []))
    
    def delete_messages(self, user_id: str, session_id: str) -> int:
        """Delete all messages in a session."""
        if self.messages_collection is not None and self.sessions_collection is not None:
            result = self.messages_collection.delete_many({
                "session_id": session_id,
                "user_id": user_id
            })
            
            # Update session message count
            self.sessions_collection.update_one(
                {"id": session_id, "user_id": user_id},
                {"$set": {"message_count": 0}}
            )
            
            return result.deleted_count
        else:
            if session_id in self.messages:
                count = len(self.messages[session_id])
                self.messages[session_id] = []
                return count
            return 0


# Global chat database instance
chat_db = ChatDatabase()
