"""
User Database with MongoDB

Persistent storage for user authentication and profiles.
"""
from typing import Dict, Optional, List
from datetime import datetime
from pymongo.collection import Collection
from pymongo import ASCENDING
from ..database import get_db, Collections
from .models import UserRole, UserResponse
from .utils import get_password_hash
import uuid
import logging

logger = logging.getLogger(__name__)


class UserDatabase:
    """
    MongoDB-backed user database for authentication.
    """
    
    def __init__(self):
        self.db = get_db()
        self.users_collection: Optional[Collection] = None
        
        if self.db is not None:
            self.users_collection = self.db[Collections.USERS]
            self._create_indexes()
            self._create_default_users()
        else:
            logger.warning("⚠️ MongoDB not available, using in-memory fallback")
            self.users: Dict[str, Dict] = {}
            self.email_to_username: Dict[str, str] = {}
            self._create_default_users()
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        if self.users_collection is None:
            return
        
        try:
            # Note: Unique indexes on non-empty collections will fail with Azure Cosmos DB
            # Uniqueness is enforced at the application level (see create_user method)
            self.users_collection.create_index(
                [("username", ASCENDING)],
                name="username_index"
            )
            self.users_collection.create_index(
                [("email", ASCENDING)],
                name="email_index"
            )
            self.users_collection.create_index(
                [("role", ASCENDING)],
                name="role_index"
            )
            self.users_collection.create_index(
                [("is_active", ASCENDING)],
                name="is_active_index"
            )
            
            logger.info("✅ User database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
    
    def _create_default_users(self):
        """Create default admin and user accounts."""
        try:
            # Check if users already exist
            if self.users_collection is not None:
                if self.users_collection.count_documents({}) > 0:
                    return
            elif self.users:
                return
            
            logger.info("Creating default users...")
            
            # Default admin user
            admin_hash = get_password_hash("admin123")
            admin_user = {
                "id": "admin",  # Use username as ID
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": admin_hash,
                "full_name": "System Administrator",
                "role": UserRole.ADMIN,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            # Default regular user
            user_hash = get_password_hash("user123")
            regular_user = {
                "id": "user",  # Use username as ID
                "username": "user",
                "email": "user@example.com",
                "password_hash": user_hash,
                "full_name": "Demo User",
                "role": UserRole.USER,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            # Default team lead user
            teamlead_hash = get_password_hash("teamlead123")
            teamlead_user = {
                "id": str(uuid.uuid4()),
                "username": "teamlead",
                "email": "teamlead@example.com",
                "password_hash": teamlead_hash,
                "full_name": "Team Lead User",
                "role": UserRole.TEAM_LEAD,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            if self.users_collection is not None:
                self.users_collection.insert_many([admin_user, regular_user, teamlead_user])
            else:
                # In-memory fallback
                for user in [admin_user, regular_user, teamlead_user]:
                    user["created_at"] = user["created_at"].isoformat()
                    self.users[user["username"]] = user
                    self.email_to_username[user["email"]] = user["username"]
            
            logger.info("✅ Default users created successfully")
            logger.info("   Admin: username=admin, password=admin123")
            logger.info("   User:  username=user, password=user123")
            logger.info("   Team Lead: username=teamlead, password=teamlead123")
        except Exception as e:
            logger.error(f"❌ Error creating default users: {e}")
    
    # ==================== User Retrieval ====================
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        if self.users_collection is not None:
            user = self.users_collection.find_one({"username": username})
            if user:
                user.pop("_id", None)
                if isinstance(user.get("created_at"), datetime):
                    user["created_at"] = user["created_at"].isoformat()
            return user
        else:
            return self.users.get(username)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID (username is now the ID)."""
        return self.get_user(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        if self.users_collection is not None:
            user = self.users_collection.find_one({"email": email})
            if user:
                user.pop("_id", None)
                if isinstance(user.get("created_at"), datetime):
                    user["created_at"] = user["created_at"].isoformat()
            return user
        else:
            username = self.email_to_username.get(email)
            if username:
                return self.users.get(username)
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)."""
        if self.users_collection is not None:
            users = []
            for user in self.users_collection.find():
                user.pop("_id", None)
                if isinstance(user.get("created_at"), datetime):
                    user["created_at"] = user["created_at"].isoformat()
                users.append(user)
            return users
        else:
            return list(self.users.values())
    
    def get_users_by_role(self, role: UserRole) -> List[Dict]:
        """Get all users with a specific role."""
        if self.users_collection is not None:
            users = []
            for user in self.users_collection.find({"role": role}):
                user.pop("_id", None)
                if isinstance(user.get("created_at"), datetime):
                    user["created_at"] = user["created_at"].isoformat()
                users.append(user)
            return users
        else:
            return [user for user in self.users.values() if user["role"] == role]
    
    # ==================== User Management ====================
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> Dict:
        """Create a new user."""
        # Check if username already exists
        if self.get_user(username):
            raise ValueError("Username already exists")
        
        # Check if email already exists
        if self.get_user_by_email(email):
            raise ValueError("Email already exists")
        
        # Validate password length
        if len(password) > 128:
            raise ValueError("Password cannot be longer than 128 characters")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        try:
            password_hash = get_password_hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise ValueError("Password processing failed")
        
        user_data = {
            "id": username,  # Use username as ID
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        if self.users_collection is not None:
            self.users_collection.insert_one(user_data.copy())
            user_data["created_at"] = user_data["created_at"].isoformat()
        else:
            user_data["created_at"] = user_data["created_at"].isoformat()
            self.users[username] = user_data
            self.email_to_username[email] = username
        
        return user_data
    
    def update_user(self, username: str, updates: Dict) -> Optional[Dict]:
        """Update user data."""
        user = self.get_user(username)
        if not user:
            return None
        
        # Handle password update separately
        if "password" in updates:
            password = updates.pop("password")
            if len(password) > 128:
                raise ValueError("Password cannot be longer than 128 characters")
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            
            try:
                updates["password_hash"] = get_password_hash(password)
            except Exception as e:
                logger.error(f"Error hashing password: {e}")
                raise ValueError("Password processing failed")
        
        # Remove id from updates
        updates.pop("id", None)
        
        if self.users_collection is not None:
            result = self.users_collection.find_one_and_update(
                {"username": username},
                {"$set": updates},
                return_document=True
            )
            if result:
                result.pop("_id", None)
                if isinstance(result.get("created_at"), datetime):
                    result["created_at"] = result["created_at"].isoformat()
            return result
        else:
            user.update(updates)
            return user
    
    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        user = self.get_user(username)
        if not user:
            return False
        
        if self.users_collection is not None:
            result = self.users_collection.delete_one({"username": username})
            return result.deleted_count > 0
        else:
            email = user["email"]
            del self.users[username]
            del self.email_to_username[email]
            return True
    
    def search_users(self, query: str, limit: int = 10) -> List[Dict]:
        """Search users by username, email, or full name."""
        query_lower = query.lower()
        
        if self.users_collection is not None:
            # Use regex search in MongoDB
            cursor = self.users_collection.find({
                "$or": [
                    {"username": {"$regex": query_lower, "$options": "i"}},
                    {"email": {"$regex": query_lower, "$options": "i"}},
                    {"full_name": {"$regex": query_lower, "$options": "i"}}
                ]
            }).limit(limit)
            
            results = []
            for user in cursor:
                user.pop("_id", None)
                if isinstance(user.get("created_at"), datetime):
                    user["created_at"] = user["created_at"].isoformat()
                results.append(user)
            return results
        else:
            results = []
            for user in self.users.values():
                if (query_lower in user["username"].lower() or
                    query_lower in user["email"].lower() or
                    (user.get("full_name") and query_lower in user["full_name"].lower())):
                    results.append(user)
                    if len(results) >= limit:
                        break
            return results


# Global database instance
user_db = UserDatabase()
