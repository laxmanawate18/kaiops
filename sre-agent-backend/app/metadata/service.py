"""
Service layer for application metadata management.

Provides business logic with caching, validation, and error handling for metadata operations.
Sits between API routes and database layer.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.metadata.models import ApplicationMetadata
from app.metadata.database_mongo import MetadataDatabase
from app.metadata.cache import metadata_cache
from app.metadata.validation import MetadataValidator, ValidationError

logger = logging.getLogger(__name__)


class MetadataService:
    """Service layer for metadata operations with caching and validation."""
    
    @staticmethod
    def get_metadata(app_name: str, use_cache: bool = True) -> Optional[ApplicationMetadata]:
        """
        Get metadata for an application with caching.
        
        Args:
            app_name: Application name
            use_cache: Whether to use cache (default: True)
            
        Returns:
            ApplicationMetadata object or None if not found
        """
        cache_key = f"metadata:{app_name}"
        
        # Try cache first
        if use_cache:
            cached_data = metadata_cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Cache hit for metadata: {app_name}")
                return cached_data
        
        # Fetch from database
        metadata = MetadataDatabase.get_metadata(app_name)
        
        # Store in cache
        if metadata and use_cache:
            metadata_cache.set(cache_key, metadata)
            logger.info(f"Cached metadata for: {app_name}")
        
        return metadata
    
    @staticmethod
    def list_all_metadata(use_cache: bool = True) -> List[ApplicationMetadata]:
        """
        List all application metadata with caching.
        
        Args:
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of ApplicationMetadata objects
        """
        cache_key = "metadata:all"
        
        # Try cache first
        if use_cache:
            cached_data = metadata_cache.get(cache_key)
            if cached_data is not None:
                logger.info("Cache hit for all metadata")
                return cached_data
        
        # Fetch from database
        metadata_list = MetadataDatabase.list_all_metadata()
        
        # Store in cache
        if use_cache:
            metadata_cache.set(cache_key, metadata_list)
            logger.info(f"Cached {len(metadata_list)} metadata records")
        
        return metadata_list
    
    @staticmethod
    def add_metadata(
        app_name: str,
        description: Optional[str] = None,
        environment: Optional[str] = None,
        team: Optional[str] = None,
        github: Optional[Dict[str, Any]] = None,
        argocd: Optional[Dict[str, Any]] = None,
        grafana: Optional[Dict[str, Any]] = None,
        cost: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Add new application metadata with validation.
        
        Args:
            app_name: Application name
            description: Application description
            environment: Environment (production, staging, development)
            team: Team name
            github: GitHub metadata dict
            argocd: ArgoCD metadata dict
            grafana: Grafana metadata dict
            cost: Cost metadata dict
            tags: List of tags
            created_by: User who created this
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Validate required fields
            MetadataValidator.validate_app_name(app_name)
            
            if environment:
                MetadataValidator.validate_environment(environment)
            
            if team:
                MetadataValidator.validate_team(team)
            
            # Build metadata object
            from app.metadata.models import (
                GitHubMetadata, ArgoCDMetadata, GrafanaMetadata, CostMetadata
            )
            
            github_meta = GitHubMetadata(**github) if github else GitHubMetadata()
            argocd_meta = ArgoCDMetadata(**argocd) if argocd else ArgoCDMetadata()
            grafana_meta = GrafanaMetadata(**grafana) if grafana else GrafanaMetadata()
            cost_meta = CostMetadata(**cost) if cost else CostMetadata()
            
            # Validate integration metadata
            if github:
                MetadataValidator.validate_github_metadata(github_meta.enabled, github)
            
            if argocd:
                MetadataValidator.validate_argocd_metadata(argocd_meta.enabled, argocd)
            
            if grafana:
                MetadataValidator.validate_grafana_metadata(grafana_meta.enabled, grafana)
            
            if cost:
                MetadataValidator.validate_cost_metadata(cost_meta.enabled, cost)
            
            # Create metadata object
            metadata = ApplicationMetadata(
                app_name=app_name,
                description=description,
                environment=environment,
                team=team,
                github=github_meta,
                argocd=argocd_meta,
                grafana=grafana_meta,
                cost=cost_meta,
                created_by=created_by,
                updated_by=created_by,
                tags=tags
            )
            
            # Save to database
            success = MetadataDatabase.create_metadata(metadata)
            
            if success:
                # Invalidate list cache
                metadata_cache.delete("metadata:all")
                logger.info(f"Added metadata for: {app_name}")
                return (True, None)
            else:
                return (False, f"Metadata for '{app_name}' already exists")
        
        except ValidationError as e:
            error_msg = f"Validation error: {str(e)}"
            logger.warning(error_msg)
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Error adding metadata: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    @staticmethod
    def update_metadata(
        app_name: str,
        description: Optional[str] = None,
        environment: Optional[str] = None,
        team: Optional[str] = None,
        github: Optional[Dict[str, Any]] = None,
        argocd: Optional[Dict[str, Any]] = None,
        grafana: Optional[Dict[str, Any]] = None,
        cost: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        updated_by: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Update existing metadata with validation.
        
        Args:
            app_name: Application name
            description: Updated description
            environment: Updated environment
            team: Updated team
            github: Updated GitHub metadata
            argocd: Updated ArgoCD metadata
            grafana: Updated Grafana metadata
            cost: Updated Cost metadata
            tags: Updated tags
            updated_by: User who performed update
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Check if metadata exists
            existing = MetadataDatabase.get_metadata(app_name)
            if not existing:
                error_msg = f"Metadata for '{app_name}' not found"
                logger.warning(error_msg)
                return (False, error_msg)
            
            # Validate updates
            if environment:
                MetadataValidator.validate_environment(environment)
            
            if team:
                MetadataValidator.validate_team(team)
            
            # Build update dict
            update_dict = {}
            
            if description is not None:
                update_dict["description"] = description
            
            if environment is not None:
                update_dict["environment"] = environment
            
            if team is not None:
                update_dict["team"] = team
            
            if tags is not None:
                update_dict["tags"] = tags
            
            # Handle integration updates
            if github is not None:
                from app.metadata.models import GitHubMetadata
                MetadataValidator.validate_github_metadata(
                    github.get("enabled", False), github
                )
                update_dict["github"] = GitHubMetadata(**github).dict()
            
            if argocd is not None:
                from app.metadata.models import ArgoCDMetadata
                MetadataValidator.validate_argocd_metadata(
                    argocd.get("enabled", False), argocd
                )
                update_dict["argocd"] = ArgoCDMetadata(**argocd).dict()
            
            if grafana is not None:
                from app.metadata.models import GrafanaMetadata
                MetadataValidator.validate_grafana_metadata(
                    grafana.get("enabled", False), grafana
                )
                update_dict["grafana"] = GrafanaMetadata(**grafana).dict()
            
            if cost is not None:
                from app.metadata.models import CostMetadata
                MetadataValidator.validate_cost_metadata(
                    cost.get("enabled", False), cost
                )
                update_dict["cost"] = CostMetadata(**cost).dict()
            
            # Update in database
            success = MetadataDatabase.update_metadata(
                app_name, update_dict, updated_by
            )
            
            if success:
                # Invalidate caches
                metadata_cache.delete(f"metadata:{app_name}")
                metadata_cache.delete("metadata:all")
                logger.info(f"Updated metadata for: {app_name}")
                return (True, None)
            else:
                return (False, f"Failed to update metadata for '{app_name}'")
        
        except ValidationError as e:
            error_msg = f"Validation error: {str(e)}"
            logger.warning(error_msg)
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Error updating metadata: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    @staticmethod
    def delete_metadata(app_name: str) -> tuple[bool, Optional[str]]:
        """
        Delete metadata for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Delete from database
            success = MetadataDatabase.delete_metadata(app_name)
            
            if success:
                # Invalidate caches
                metadata_cache.delete(f"metadata:{app_name}")
                metadata_cache.delete("metadata:all")
                logger.info(f"Deleted metadata for: {app_name}")
                return (True, None)
            else:
                return (False, f"Metadata for '{app_name}' not found")
        
        except Exception as e:
            error_msg = f"Error deleting metadata: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    @staticmethod
    def search_metadata(query: str, use_cache: bool = False) -> List[ApplicationMetadata]:
        """
        Search metadata by query (not cached as results are dynamic).
        
        Args:
            query: Search query
            use_cache: Not used for search (always fresh results)
            
        Returns:
            List of matching ApplicationMetadata objects
        """
        try:
            results = MetadataDatabase.search_metadata(query)
            logger.info(f"Search results for '{query}': {len(results)} matches")
            return results
        except Exception as e:
            logger.error(f"Error searching metadata: {e}")
            return []
    
    @staticmethod
    def get_configured_integrations(app_name: str) -> Dict[str, bool]:
        """
        Get enabled integrations for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Dictionary of integration names and enabled status
        """
        try:
            # Try to get from cache first
            metadata = MetadataService.get_metadata(app_name, use_cache=True)
            
            if not metadata:
                logger.warning(f"Metadata not found for: {app_name}")
                return {}
            
            integrations = {
                "github": metadata.github.enabled,
                "argocd": metadata.argocd.enabled,
                "grafana": metadata.grafana.enabled,
                "cost": metadata.cost.enabled
            }
            
            logger.info(f"Retrieved integrations for {app_name}: {integrations}")
            return integrations
        
        except Exception as e:
            logger.error(f"Error getting integrations for {app_name}: {e}")
            return {}
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        return metadata_cache.get_stats()
    
    @staticmethod
    def clear_cache(pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match (supports * wildcard). If None, clears all.
            
        Returns:
            Number of entries cleared
        """
        if pattern:
            count = metadata_cache.invalidate_pattern(pattern)
        else:
            metadata_cache.clear()
            count = metadata_cache.get_stats()["total_entries"]
        
        logger.info(f"Cache cleared: {count} entries")
        return count
