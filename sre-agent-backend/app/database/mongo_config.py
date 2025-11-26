"""
MongoDB Configuration

Centralized MongoDB connection management for all SRE Agent data.
"""
import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MongoDBConfig:
    """MongoDB connection manager."""
    
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get MongoDB connection string from environment (Azure Cosmos DB)."""
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError(
                "MONGODB_URI environment variable not set. "
                "Please configure Azure Cosmos DB connection in .env file."
            )
        return uri
    
    @classmethod
    def get_database_name(cls) -> str:
        """Get database name from environment."""
        return os.getenv("MONGODB_DATABASE", "sre_agent_db")
    
    @classmethod
    def connect(cls) -> Database:
        """
        Connect to MongoDB and return database instance.
        Creates connection if it doesn't exist (singleton pattern).
        """
        if cls._db is not None:
            return cls._db
        
        try:
            connection_string = cls.get_connection_string()
            database_name = cls.get_database_name()
            
            cls._client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Test connection
            cls._client.server_info()
            
            cls._db = cls._client[database_name]
            logger.info(f"✅ Connected to MongoDB: {database_name}")
            
            return cls._db
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    @classmethod
    def get_database(cls) -> Optional[Database]:
        """Get database instance (returns None if not connected)."""
        if cls._db is None:
            try:
                return cls.connect()
            except Exception as e:
                logger.debug(f"Failed to get database: {e}")
                return None
        return cls._db
    
    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if MongoDB is connected."""
        try:
            if cls._client:
                cls._client.server_info()
                return True
        except Exception as e:
            logger.debug(f"MongoDB connection check failed: {e}")
        return False


# Global database instance getter
def get_db() -> Optional[Database]:
    """Get MongoDB database instance."""
    return MongoDBConfig.get_database()


# Collection names
class Collections:
    """MongoDB collection names."""
    APPLICATIONS = "applications"
    CHAT_SESSIONS = "chat_sessions"
    CHAT_MESSAGES = "chat_messages"
    FEEDBACK = "feedback"
    TRAINING_DATASET = "training_dataset"  # Training data collection
    EVALUATION_DATASET = "evaluation_dataset"  # Evaluation data collection
    USERS = "users"
    TEAMS = "teams"
