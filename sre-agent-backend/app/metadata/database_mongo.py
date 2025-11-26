"""
MongoDB operations for application metadata storage and retrieval.

Provides CRUD operations for managing application metadata with full integration configurations.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError, PyMongoError
from pymongo.collection import Collection

from app.database.mongo_config import MongoDBConfig
from app.metadata.models import ApplicationMetadata, GitHubMetadata, ArgoCDMetadata, GrafanaMetadata, CostMetadata

logger = logging.getLogger(__name__)


class MetadataDatabase:
    """MongoDB database operations for application metadata."""
    
    COLLECTION_NAME = "application_metadata"
    
    @classmethod
    def get_collection(cls) -> Collection:
        """Get the metadata collection."""
        db = MongoDBConfig.connect()
        return db[cls.COLLECTION_NAME]
    
    @classmethod
    def ensure_indexes(cls) -> None:
        """Create necessary indexes for the metadata collection."""
        collection = cls.get_collection()
        
        try:
            # Index on app_name (non-unique - Azure Cosmos DB limitation)
            # Uniqueness enforced at application level
            collection.create_index("app_name")
            logger.info("Created index on app_name")
            
            # Note: Text indexes not supported by Azure Cosmos DB
            # Use app_name index for searching instead
            
            # Index for environment and team queries
            collection.create_index([("environment", 1), ("team", 1)])
            logger.info("Created index on environment and team")
            
            # Index for enabled integrations (for filtering)
            collection.create_index([
                ("github.enabled", 1),
                ("argocd.enabled", 1),
                ("grafana.enabled", 1),
                ("cost.enabled", 1)
            ])
            logger.info("Created index on integration enabled flags")
            
        except PyMongoError as e:
            logger.warning(f"Index creation warning: {e}")
    
    @classmethod
    def create_metadata(cls, metadata: ApplicationMetadata) -> bool:
        """
        Create new application metadata.
        
        Args:
            metadata: ApplicationMetadata object
            
        Returns:
            True if successful, False otherwise
        """
        collection = cls.get_collection()
        
        try:
            # Convert to dict and add timestamp
            metadata_dict = metadata.dict()
            metadata_dict["created_at"] = metadata.created_at
            metadata_dict["updated_at"] = metadata.updated_at
            
            result = collection.insert_one(metadata_dict)
            logger.info(f"Created metadata for application: {metadata.app_name} (id: {result.inserted_id})")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Application metadata already exists: {metadata.app_name}")
            return False
        except PyMongoError as e:
            logger.error(f"Error creating metadata: {e}")
            return False
    
    @classmethod
    def get_metadata(cls, app_name: str) -> Optional[ApplicationMetadata]:
        """
        Retrieve metadata for a specific application.
        
        Args:
            app_name: Application name
            
        Returns:
            ApplicationMetadata object or None if not found
        """
        collection = cls.get_collection()
        
        try:
            result = collection.find_one({"app_name": app_name})
            
            if result:
                # Remove MongoDB's _id field
                result.pop("_id", None)
                return ApplicationMetadata(**result)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Error retrieving metadata for {app_name}: {e}")
            return None
    
    @classmethod
    def list_all_metadata(cls) -> List[ApplicationMetadata]:
        """
        Retrieve all application metadata.
        
        Returns:
            List of ApplicationMetadata objects
        """
        collection = cls.get_collection()
        
        try:
            results = collection.find({}).sort("app_name", 1)
            metadata_list = []
            
            for doc in results:
                doc.pop("_id", None)
                metadata_list.append(ApplicationMetadata(**doc))
            
            logger.info(f"Retrieved {len(metadata_list)} metadata records")
            return metadata_list
            
        except PyMongoError as e:
            logger.error(f"Error listing metadata: {e}")
            return []
    
    @classmethod
    def update_metadata(cls, app_name: str, updated_fields: Dict[str, Any], updated_by: Optional[str] = None) -> bool:
        """
        Update metadata for an application.
        
        Args:
            app_name: Application name
            updated_fields: Dictionary of fields to update
            updated_by: User who performed the update
            
        Returns:
            True if successful, False otherwise
        """
        collection = cls.get_collection()
        
        try:
            # Add update timestamp and user
            update_dict = {
                **updated_fields,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if updated_by:
                update_dict["updated_by"] = updated_by
            
            result = collection.update_one(
                {"app_name": app_name},
                {"$set": update_dict}
            )
            
            if result.matched_count == 0:
                logger.warning(f"No metadata found for application: {app_name}")
                return False
            
            logger.info(f"Updated metadata for application: {app_name}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Error updating metadata for {app_name}: {e}")
            return False
    
    @classmethod
    def delete_metadata(cls, app_name: str) -> bool:
        """
        Delete metadata for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            True if successful, False otherwise
        """
        collection = cls.get_collection()
        
        try:
            result = collection.delete_one({"app_name": app_name})
            
            if result.deleted_count == 0:
                logger.warning(f"No metadata found for application: {app_name}")
                return False
            
            logger.info(f"Deleted metadata for application: {app_name}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Error deleting metadata for {app_name}: {e}")
            return False
    
    @classmethod
    def search_metadata(cls, query: str) -> List[ApplicationMetadata]:
        """
        Search metadata using text search.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching ApplicationMetadata objects
        """
        collection = cls.get_collection()
        
        try:
            results = collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
            
            metadata_list = []
            for doc in results:
                doc.pop("_id", None)
                doc.pop("score", None)
                metadata_list.append(ApplicationMetadata(**doc))
            
            logger.info(f"Found {len(metadata_list)} results for search: {query}")
            return metadata_list
            
        except PyMongoError as e:
            logger.error(f"Error searching metadata: {e}")
            return []
    
    @classmethod
    def get_by_team(cls, team: str) -> List[ApplicationMetadata]:
        """
        Retrieve all metadata for a specific team.
        
        Args:
            team: Team name
            
        Returns:
            List of ApplicationMetadata objects
        """
        collection = cls.get_collection()
        
        try:
            results = collection.find({"team": team}).sort("app_name", 1)
            metadata_list = []
            
            for doc in results:
                doc.pop("_id", None)
                metadata_list.append(ApplicationMetadata(**doc))
            
            logger.info(f"Retrieved {len(metadata_list)} metadata records for team: {team}")
            return metadata_list
            
        except PyMongoError as e:
            logger.error(f"Error retrieving metadata for team {team}: {e}")
            return []
    
    @classmethod
    def get_by_environment(cls, environment: str) -> List[ApplicationMetadata]:
        """
        Retrieve all metadata for a specific environment.
        
        Args:
            environment: Environment name (production, staging, development)
            
        Returns:
            List of ApplicationMetadata objects
        """
        collection = cls.get_collection()
        
        try:
            results = collection.find({"environment": environment}).sort("app_name", 1)
            metadata_list = []
            
            for doc in results:
                doc.pop("_id", None)
                metadata_list.append(ApplicationMetadata(**doc))
            
            logger.info(f"Retrieved {len(metadata_list)} metadata records for environment: {environment}")
            return metadata_list
            
        except PyMongoError as e:
            logger.error(f"Error retrieving metadata for environment {environment}: {e}")
            return []
    
    @classmethod
    def get_configured_integrations(cls, app_name: str) -> Dict[str, bool]:
        """
        Get enabled integrations for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Dictionary of integration names and their enabled status
        """
        metadata = cls.get_metadata(app_name)
        
        if not metadata:
            return {}
        
        return {
            "github": metadata.github.enabled,
            "argocd": metadata.argocd.enabled,
            "grafana": metadata.grafana.enabled,
            "cost": metadata.cost.enabled
        }
    
    @classmethod
    def count_metadata(cls) -> int:
        """
        Get total count of metadata records.
        
        Returns:
            Number of metadata records
        """
        collection = cls.get_collection()
        
        try:
            count = collection.count_documents({})
            return count
        except PyMongoError as e:
            logger.error(f"Error counting metadata: {e}")
            return 0


# Initialize indexes on module load
try:
    MetadataDatabase.ensure_indexes()
except Exception as e:
    logger.warning(f"Could not initialize indexes on module load: {e}")
