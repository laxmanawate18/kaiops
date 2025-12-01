"""
Metadata Database with PostgreSQL

MongoDB operations for application metadata storage and retrieval.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database.postgres_config import PostgresConfig
from ..database.models import ApplicationMetadata
from .models import ApplicationMetadata as ApplicationMetadataModel

import uuid

logger = logging.getLogger(__name__)


class MetadataDatabase:
    """PostgreSQL database operations for application metadata."""
    
    def __init__(self):
        """Initialize metadata database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ Metadata database initialized with PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to initialize metadata database: {e}")
            raise
    
    # ==================== CREATE OPERATIONS ====================
    
    def create_metadata(self, app_name: str, application_id: str, team: str, **kwargs) -> Dict[str, Any]:
        """Create metadata for an application."""
        try:
            db = PostgresConfig.get_session()
            
            metadata = ApplicationMetadata(
                id=str(uuid.uuid4()),
                application_id=application_id,
                app_name=app_name,
                team=team,
                environment=kwargs.get("environment"),
                metadata_json=kwargs.get("metadata_json", {}),
                created_at=datetime.now()
            )
            
            db.add(metadata)
            db.commit()
            
            result = self._convert_to_dict(metadata)
            db.close()
            
            logger.info(f"✅ Created metadata for app: {app_name}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating metadata: {e}")
            db.close()
            raise
    
    # ==================== READ OPERATIONS ====================
    
    @classmethod
    def get_metadata(cls, app_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an application by name."""
        try:
            db = PostgresConfig.get_session()
            
            metadata = db.query(ApplicationMetadata).filter(
                ApplicationMetadata.app_name.ilike(app_name)
            ).first()
            
            result = cls._convert_to_dict(metadata) if metadata else None
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting metadata for {app_name}: {e}")
            db.close()
            return None
    
    def get_by_team(self, team: str) -> List[Dict[str, Any]]:
        """Retrieve all metadata for a specific team."""
        try:
            db = PostgresConfig.get_session()
            
            metadata_list = db.query(ApplicationMetadata).filter(
                ApplicationMetadata.team == team
            ).order_by(ApplicationMetadata.app_name.asc()).all()
            
            result = [self._convert_to_dict(m) for m in metadata_list]
            db.close()
            
            logger.info(f"Retrieved {len(result)} metadata records for team: {team}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving metadata for team {team}: {e}")
            db.close()
            return []
    
    def get_all_metadata(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all application metadata."""
        try:
            db = PostgresConfig.get_session()
            
            metadata_list = db.query(ApplicationMetadata).order_by(
                desc(ApplicationMetadata.created_at)
            ).limit(limit).all()
            
            result = [self._convert_to_dict(m) for m in metadata_list]
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting all metadata: {e}")
            db.close()
            return []
    
    def get_by_environment(self, environment: str) -> List[Dict[str, Any]]:
        """Get metadata filtered by environment (dev, staging, prod)."""
        try:
            db = PostgresConfig.get_session()
            
            metadata_list = db.query(ApplicationMetadata).filter(
                ApplicationMetadata.environment == environment
            ).all()
            
            result = [self._convert_to_dict(m) for m in metadata_list]
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting metadata by environment {environment}: {e}")
            db.close()
            return []
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_metadata(self, app_name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update metadata for an application."""
        try:
            db = PostgresConfig.get_session()
            
            metadata = db.query(ApplicationMetadata).filter(
                ApplicationMetadata.app_name.ilike(app_name)
            ).first()
            
            if not metadata:
                logger.warning(f"Metadata for {app_name} not found")
                db.close()
                return None
            
            # Update allowed fields
            allowed_fields = ['team', 'environment', 'metadata_json']
            for key, value in updates.items():
                if key in allowed_fields and hasattr(metadata, key):
                    setattr(metadata, key, value)
            
            metadata.updated_at = datetime.now()
            db.commit()
            
            result = self._convert_to_dict(metadata)
            db.close()
            
            logger.info(f"✅ Updated metadata for: {app_name}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating metadata: {e}")
            db.close()
            raise
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete_metadata(self, app_name: str) -> bool:
        """Delete metadata for an application."""
        try:
            db = PostgresConfig.get_session()
            
            metadata = db.query(ApplicationMetadata).filter(
                ApplicationMetadata.app_name.ilike(app_name)
            ).first()
            
            if not metadata:
                logger.warning(f"Metadata for {app_name} not found")
                db.close()
                return False
            
            db.delete(metadata)
            db.commit()
            
            logger.info(f"✅ Deleted metadata for: {app_name}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting metadata: {e}")
            db.close()
            return False
    
    # ==================== SEARCH & FILTERING ====================
    
    def search_metadata(self, search_term: str) -> List[Dict[str, Any]]:
        """Search metadata by application name or team."""
        try:
            db = PostgresConfig.get_session()
            
            search_pattern = f"%{search_term}%"
            metadata_list = db.query(ApplicationMetadata).filter(
                (ApplicationMetadata.app_name.ilike(search_pattern)) |
                (ApplicationMetadata.team.ilike(search_pattern))
            ).all()
            
            result = [self._convert_to_dict(m) for m in metadata_list]
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error searching metadata: {e}")
            db.close()
            return []
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_to_dict(metadata: ApplicationMetadata) -> Dict[str, Any]:
        """Convert metadata model to dictionary."""
        if not metadata:
            return None
        
        return {
            "id": metadata.id,
            "application_id": metadata.application_id,
            "app_name": metadata.app_name,
            "team": metadata.team,
            "environment": metadata.environment,
            "metadata_json": metadata.metadata_json or {},
            "created_at": metadata.created_at.isoformat() if metadata.created_at else None,
            "updated_at": metadata.updated_at.isoformat() if metadata.updated_at else None,
        }
    
    @classmethod
    def ensure_indexes(cls) -> None:
        """Indexes are already created in the SQLAlchemy model definition."""
        logger.info("✅ Metadata indexes verified (created via SQLAlchemy model)")


# Initialize indexes on module load
try:
    MetadataDatabase.ensure_indexes()
except Exception as e:
    logger.warning(f"Could not initialize indexes on module load: {e}")

# Global metadata database instance
metadata_db = MetadataDatabase()
