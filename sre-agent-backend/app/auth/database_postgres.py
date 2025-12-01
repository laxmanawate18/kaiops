"""
User Database with PostgreSQL

Persistent storage for user authentication and profiles.
"""
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from ..database.postgres_config import PostgresConfig
from ..database.models import User
from .models import UserRole, UserResponse
from .utils import get_password_hash
import uuid
import logging

logger = logging.getLogger(__name__)


class UserDatabase:
    """PostgreSQL-backed user database for authentication."""
    
    def __init__(self):
        """Initialize user database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ User database initialized with PostgreSQL")
            self._create_default_users()
        except Exception as e:
            logger.error(f"Failed to initialize user database: {e}")
            raise
    
    def _create_default_users(self):
        """Create default admin and user accounts."""
        try:
            db = PostgresConfig.get_session()
            
            # Check if users already exist
            if db.query(User).count() > 0:
                logger.info("Default users already exist")
                db.close()
                return
            
            logger.info("Creating default users...")
            
            # Default admin user
            admin_hash = get_password_hash("admin123")
            admin_user = User(
                id="admin",
                username="admin",
                email="admin@example.com",
                password_hash=admin_hash,
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.now()
            )
            
            # Default regular user
            user_hash = get_password_hash("user123")
            regular_user = User(
                id="user",
                username="user",
                email="user@example.com",
                password_hash=user_hash,
                full_name="Demo User",
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.now()
            )
            
            # Default team lead user
            teamlead_hash = get_password_hash("teamlead123")
            teamlead_user = User(
                id=str(uuid.uuid4()),
                username="teamlead",
                email="teamlead@example.com",
                password_hash=teamlead_hash,
                full_name="Team Lead User",
                role=UserRole.TEAM_LEAD,
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add_all([admin_user, regular_user, teamlead_user])
            db.commit()
            
            logger.info("✅ Default users created successfully")
            logger.info("   Admin: username=admin, password=admin123")
            logger.info("   User:  username=user, password=user123")
            logger.info("   Team Lead: username=teamlead, password=teamlead123")
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating default users: {e}")
            db.rollback()
            db.close()
    
    # ==================== CREATE OPERATIONS ====================
    
    def create_user(self, username: str, email: str, password: str, full_name: Optional[str] = None, role: str = "user") -> Dict:
        """Create a new user."""
        try:
            db = PostgresConfig.get_session()
            
            # Check if user already exists
            if db.query(User).filter(User.username == username).first():
                logger.warning(f"User {username} already exists")
                db.close()
                raise ValueError(f"User {username} already exists")
            
            if db.query(User).filter(User.email == email).first():
                logger.warning(f"Email {email} already in use")
                db.close()
                raise ValueError(f"Email {email} already in use")
            
            user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                full_name=full_name,
                role=role,
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(user)
            db.commit()
            
            result = self._convert_to_dict(user)
            db.close()
            
            logger.info(f"✅ Created user: {username}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating user: {e}")
            db.close()
            raise
    
    # ==================== READ OPERATIONS ====================
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            db = PostgresConfig.get_session()
            user = db.query(User).filter(User.username == username).first()
            result = self._convert_to_dict(user) if user else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            db.close()
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        try:
            db = PostgresConfig.get_session()
            user = db.query(User).filter(User.id == user_id).first()
            result = self._convert_to_dict(user) if user else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            db.close()
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        try:
            db = PostgresConfig.get_session()
            user = db.query(User).filter(User.email == email).first()
            result = self._convert_to_dict(user) if user else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            db.close()
            return None
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all users with pagination."""
        try:
            db = PostgresConfig.get_session()
            users = db.query(User).offset(skip).limit(limit).all()
            result = [self._convert_to_dict(user) for user in users]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            db.close()
            return []
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        """Get all users with a specific role."""
        try:
            db = PostgresConfig.get_session()
            users = db.query(User).filter(User.role == role).all()
            result = [self._convert_to_dict(user) for user in users]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            db.close()
            return []
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_user(self, username: str, updates: Dict) -> Optional[Dict]:
        """Update user details."""
        try:
            db = PostgresConfig.get_session()
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User {username} not found")
                db.close()
                return None
            
            # Update allowed fields
            allowed_fields = ['full_name', 'email', 'role', 'is_active']
            for key, value in updates.items():
                if key in allowed_fields and hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.now()
            db.commit()
            
            result = self._convert_to_dict(user)
            db.close()
            
            logger.info(f"✅ Updated user: {username}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating user {username}: {e}")
            db.close()
            raise
    
    def change_password(self, username: str, new_password: str) -> bool:
        """Change user password."""
        try:
            db = PostgresConfig.get_session()
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User {username} not found")
                db.close()
                return False
            
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"✅ Changed password for user: {username}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error changing password for user {username}: {e}")
            db.close()
            return False
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        try:
            db = PostgresConfig.get_session()
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User {username} not found")
                db.close()
                return False
            
            db.delete(user)
            db.commit()
            
            logger.info(f"✅ Deleted user: {username}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting user {username}: {e}")
            db.close()
            return False
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_to_dict(user: User) -> Dict:
        """Convert SQLAlchemy model to dictionary."""
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "password_hash": user.password_hash,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }


# Global database instance
user_db = UserDatabase()
