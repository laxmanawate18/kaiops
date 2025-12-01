"""
Chat Session Database with PostgreSQL

Persistent storage for chat sessions and messages.
"""
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database.postgres_config import PostgresConfig
from ..database.models import ChatSession, ChatMessage, MessageSenderEnum
from .models import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel, MessageSender
import uuid
import logging

logger = logging.getLogger(__name__)


class ChatDatabase:
    """PostgreSQL-backed database for managing user-isolated chat sessions and messages."""
    
    def __init__(self):
        """Initialize chat database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ Chat database initialized with PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to initialize chat database: {e}")
            raise
    
    # ==================== SESSION MANAGEMENT ====================
    
    def create_session(self, user_id: str, session_name: Optional[str] = None) -> Dict:
        """Create a new chat session for a user."""
        try:
            db = PostgresConfig.get_session()
            
            session_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            if not session_name:
                session_name = f"Chat {timestamp.strftime('%b %d, %I:%M %p')}"
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                name=session_name,
                is_active=True,
                message_count=0,
                created_at=timestamp,
                last_modified=timestamp,
                metadata={}
            )
            
            db.add(session)
            db.commit()
            
            result = self._convert_session_to_dict(session)
            db.close()
            
            logger.info(f"✅ Created chat session: {session_id} for user: {user_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating chat session: {e}")
            db.close()
            raise
    
    def get_session(self, user_id: str, session_id: str) -> Optional[Dict]:
        """Get a specific session for a user."""
        try:
            db = PostgresConfig.get_session()
            
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            result = self._convert_session_to_dict(session) if session else None
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting chat session {session_id}: {e}")
            db.close()
            return None
    
    def get_user_sessions(self, user_id: str, include_inactive: bool = True) -> List[Dict]:
        """Get all sessions for a user."""
        try:
            db = PostgresConfig.get_session()
            
            query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
            
            if not include_inactive:
                query = query.filter(ChatSession.is_active == True)
            
            sessions = query.order_by(desc(ChatSession.last_modified)).all()
            result = [self._convert_session_to_dict(s) for s in sessions]
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            db.close()
            return []
    
    def update_session(self, user_id: str, session_id: str, **updates) -> Optional[Dict]:
        """Update session details."""
        try:
            db = PostgresConfig.get_session()
            
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                db.close()
                return None
            
            allowed_fields = ['name', 'is_active', 'metadata']
            for key, value in updates.items():
                if key in allowed_fields and hasattr(session, key):
                    setattr(session, key, value)
            
            session.last_modified = datetime.now()
            db.commit()
            
            result = self._convert_session_to_dict(session)
            db.close()
            
            logger.info(f"✅ Updated session: {session_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating session: {e}")
            db.close()
            raise
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            db = PostgresConfig.get_session()
            
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                db.close()
                return False
            
            # Delete all messages in the session (cascade handled by model)
            db.delete(session)
            db.commit()
            
            logger.info(f"✅ Deleted session: {session_id}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting session: {e}")
            db.close()
            return False
    
    def delete_all_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        try:
            db = PostgresConfig.get_session()
            
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            count = len(sessions)
            
            for session in sessions:
                db.delete(session)
            
            db.commit()
            
            logger.info(f"✅ Deleted {count} sessions for user: {user_id}")
            db.close()
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting user sessions: {e}")
            db.close()
            return 0
    
    # ==================== MESSAGE MANAGEMENT ====================
    
    def add_message(
        self,
        user_id: str,
        session_id: str,
        sender: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Add a message to a session."""
        try:
            db = PostgresConfig.get_session()
            
            timestamp = datetime.now()
            message_id = str(uuid.uuid4())
            
            # Convert sender to uppercase enum if it's a string or lowercase enum
            if hasattr(sender, 'value'):
                sender_val = sender.value
            else:
                sender_val = str(sender)
            
            try:
                # Try to map to uppercase enum (USER, ASSISTANT, SYSTEM)
                db_sender = MessageSenderEnum[sender_val.upper()]
            except KeyError:
                # Fallback to original if not found (though likely to fail if DB enforces enum)
                logger.warning(f"⚠️ Could not map sender '{sender}' to MessageSenderEnum. Using as is.")
                db_sender = sender

            message = ChatMessage(
                id=message_id,
                session_id=session_id,
                user_id=user_id,
                sender=db_sender,
                text=text,
                timestamp=timestamp,
                metadata=metadata or {}
            )
            
            db.add(message)
            
            # Update session message count and last modified
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if session:
                session.message_count += 1
                session.last_modified = timestamp
            
            db.commit()
            
            result = self._convert_message_to_dict(message)
            db.close()
            
            logger.info(f"✅ Added message to session: {session_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error adding message: {e}")
            db.close()
            raise
    
    def get_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get messages for a session with pagination."""
        try:
            db = PostgresConfig.get_session()
            
            query = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id
            )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            if limit is None:
                limit = 100
                
            messages = query.order_by(ChatMessage.timestamp.asc()).offset(offset).limit(limit).all()
            
            result = [self._convert_message_to_dict(m) for m in messages]
            db.close()
            
            return result, total
            
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            db.close()
            return [], 0
    
    def get_message_count(self, user_id: str, session_id: str) -> int:
        """Get count of messages in a session."""
        try:
            db = PostgresConfig.get_session()
            
            count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id
            ).count()
            
            db.close()
            return count
            
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            db.close()
            return 0
    
    def delete_messages(self, user_id: str, session_id: str) -> int:
        """Delete all messages in a session."""
        try:
            db = PostgresConfig.get_session()
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id
            ).all()
            
            count = len(messages)
            for message in messages:
                db.delete(message)
            
            # Reset message count
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if session:
                session.message_count = 0
            
            db.commit()
            
            logger.info(f"✅ Deleted {count} messages from session: {session_id}")
            db.close()
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting messages: {e}")
            db.close()
            return 0
    
    # ==================== STATISTICS ====================
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get chat statistics for a specific user."""
        try:
            db = PostgresConfig.get_session()
            
            # Get all user sessions
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).all()
            
            total_sessions = len(sessions)
            active_sessions = sum(1 for s in sessions if s.is_active)
            
            # Get total message count
            total_messages = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id
            ).count()
            
            # Get sessions created today
            from datetime import datetime, timedelta
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            sessions_today = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= today_start
            ).count()
            
            db.close()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "sessions_created_today": sessions_today
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            if 'db' in locals():
                db.close()
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "total_messages": 0,
                "sessions_created_today": 0
            }
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_session_to_dict(session: ChatSession) -> Dict:
        """Convert ChatSession model to dictionary."""
        if not session:
            return None
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "name": session.name,
            "is_active": session.is_active,
            "message_count": session.message_count,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_modified": session.last_modified.isoformat() if session.last_modified else None,
            "metadata": session.metadata_json or {}
        }
    
    @staticmethod
    def _convert_message_to_dict(message: ChatMessage) -> Dict:
        """Convert ChatMessage model to dictionary."""
        if not message:
            return None
        
        # Convert SQLAlchemy enum to string value (lowercase for Pydantic compatibility)
        sender_val = message.sender
        if hasattr(sender_val, 'value'):
            sender_val = sender_val.value
        
        # Ensure lowercase for Pydantic model compatibility
        if isinstance(sender_val, str):
            sender_val = sender_val.lower()
            
        return {
            "id": message.id,
            "session_id": message.session_id,
            "user_id": message.user_id,
            "sender": sender_val,
            "text": message.text,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "metadata": message.metadata_json or {}
        }


# Global chat database instance
chat_db = ChatDatabase()
