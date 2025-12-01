"""
PostgreSQL Configuration

Centralized PostgreSQL connection management using SQLAlchemy.
Replaces MongoDB for all SRE Agent data storage.
"""
import os
from urllib.parse import quote
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Optional, Generator
import logging

logger = logging.getLogger(__name__)


class PostgresConfig:
    """PostgreSQL connection manager using SQLAlchemy."""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get PostgreSQL connection string from environment."""
        postgres_user = os.getenv("POSTGRES_USER", "sre_user")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "Azure@123456")  # Default password
        postgres_host = os.getenv("POSTGRES_HOST", "34.9.74.83")  # Cloud SQL public IP
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("SRE_AGENT_DB", "sre_agent_db")  # NEW database for SRE data
        
        if not postgres_password:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable not set. "
                "Please configure PostgreSQL password in .env file."
            )
        
        # URL-encode password to handle special characters
        encoded_password = quote(postgres_password, safe='')
        
        # Connection format: postgresql://user:password@host:port/database
        connection_string = (
            f"postgresql://{postgres_user}:{encoded_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )
        return connection_string
    
    @classmethod
    def get_engine(cls):
        """Get or create SQLAlchemy engine (singleton)."""
        if cls._engine is None:
            try:
                connection_string = cls.get_connection_string()
                
                # Create engine with connection pooling
                cls._engine = create_engine(
                    connection_string,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    echo=False,  # Set True for SQL debugging
                    pool_pre_ping=True,  # Verify connections before using
                    connect_args={
                        "connect_timeout": 10,
                        "options": "-c statement_timeout=30000"  # 30 second timeout
                    }
                )
                
                # Test connection
                with cls._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("✅ PostgreSQL connection successful")
                
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                raise
        
        return cls._engine
    
    @classmethod
    def get_session_factory(cls):
        """Get or create SessionLocal (singleton)."""
        if cls._SessionLocal is None:
            engine = cls.get_engine()
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        return cls._SessionLocal
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session."""
        SessionLocal = cls.get_session_factory()
        return SessionLocal()
    
    @classmethod
    def create_all_tables(cls, Base):
        """Create all tables from Base metadata."""
        try:
            engine = cls.get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("✅ All PostgreSQL tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    @classmethod
    def drop_all_tables(cls, Base):
        """Drop all tables (use with caution - for testing only)."""
        try:
            engine = cls.get_engine()
            Base.metadata.drop_all(bind=engine)
            logger.warning("⚠️ All PostgreSQL tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    @classmethod
    def check_database_exists(cls) -> bool:
        """Check if database connection is working."""
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    @classmethod
    def close(cls):
        """Close all database connections."""
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            cls._SessionLocal = None
            logger.info("PostgreSQL connection closed")


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection."""
    db = PostgresConfig.get_session()
    try:
        yield db
    finally:
        db.close()


# Import for convenience
from sqlalchemy import text
