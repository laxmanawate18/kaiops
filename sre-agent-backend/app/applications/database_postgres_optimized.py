"""
Optimized database operations for applications with JOIN queries and caching.
This module adds performance improvements without breaking existing functionality.
"""
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy import desc, or_, and_
from datetime import datetime
import logging
from app.database.postgres_config import PostgresConfig
from app.database.models import Application, User
from app.cache import get_cache_manager

logger = logging.getLogger(__name__)
cache_manager = get_cache_manager()

class OptimizedApplicationDatabase:
    """Optimized application database operations with JOIN and caching."""
    
    def list_applications_with_users(
        self,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        cluster: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict], int]:
        """
        List applications with user information in a single query (eliminates N+1).
        Uses JOIN to fetch creator and updater information efficiently.
        """
        try:
            # Build cache key
            cache_key = f"apps_list:{status}:{owner}:{cluster}:{skip}:{limit}"
            cached = cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            db = PostgresConfig.get_session()
            
            # Create aliases for creator and updater
            Creator = aliased(User)
            Updater = aliased(User)
            
            # Build query with LEFT JOINs to include user information
            query = db.query(
                Application,
                Creator.username.label('creator_username'),
                Updater.username.label('updater_username')
            ).outerjoin(
                Creator, Application.created_by == Creator.id
            ).outerjoin(
                Updater, Application.updated_by == Updater.id
            )
            
            # Apply filters
            if status:
                query = query.filter(Application.status == status)
            
            if owner:
                query = query.filter(Application.application_owner == owner)
            
            if cluster:
                # Support all cloud providers
                query = query.filter(
                    or_(
                        Application.gke_cluster_name == cluster,
                        Application.aks_cluster_name == cluster,
                        Application.eks_cluster_name == cluster
                    )
                )
            
            # Get total count before pagination
            total = query.count()
            
            # Apply pagination and ordering
            results = query.order_by(
                desc(Application.created_at)
            ).offset(skip).limit(limit).all()
            
            # Convert to dictionaries with user information
            apps_with_users = []
            for app, creator_username, updater_username in results:
                app_dict = self._convert_app_to_dict(app)
                # Add usernames directly from JOIN
                app_dict['created_by_username'] = creator_username or 'system'
                app_dict['updated_by_username'] = updater_username
                apps_with_users.append(app_dict)
            
            db.close()
            
            # Cache for 60 seconds
            result = (apps_with_users, total)
            cache_manager.set(cache_key, result, ttl=60)
            
            logger.info(f"✅ Fetched {len(apps_with_users)} applications with users in 1 query")
            return result
            
        except Exception as e:
            logger.error(f"Error listing applications with users: {e}")
            if 'db' in locals():
                db.close()
            return [], 0
    
    def get_application_with_users(self, app_id: str) -> Optional[Dict]:
        """
        Get single application with user information in one query.
        """
        try:
            # Check cache first
            cache_key = f"app:{app_id}"
            cached = cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for app {app_id}")
                return cached
            
            db = PostgresConfig.get_session()
            
            # Create aliases for creator and updater
            Creator = aliased(User)
            Updater = aliased(User)
            
            # Single query with JOINs
            result = db.query(
                Application,
                Creator.username.label('creator_username'),
                Updater.username.label('updater_username')
            ).outerjoin(
                Creator, Application.created_by == Creator.id
            ).outerjoin(
                Updater, Application.updated_by == Updater.id
            ).filter(
                Application.id == app_id
            ).first()
            
            if not result:
                db.close()
                return None
            
            app, creator_username, updater_username = result
            
            # Convert to dictionary
            app_dict = self._convert_app_to_dict(app)
            app_dict['created_by_username'] = creator_username or 'system'
            app_dict['updated_by_username'] = updater_username
            
            db.close()
            
            # Cache for 120 seconds
            cache_manager.set(cache_key, app_dict, ttl=120)
            
            return app_dict
            
        except Exception as e:
            logger.error(f"Error getting application {app_id}: {e}")
            if 'db' in locals():
                db.close()
            return None
    
    def search_applications_with_users(
        self, 
        query_text: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Search applications with user information in one query."""
        try:
            db = PostgresConfig.get_session()
            
            # Create aliases
            Creator = aliased(User)
            Updater = aliased(User)
            
            search_term = f"%{query_text}%"
            
            # Build search query with JOINs
            results = db.query(
                Application,
                Creator.username.label('creator_username'),
                Updater.username.label('updater_username')
            ).outerjoin(
                Creator, Application.created_by == Creator.id
            ).outerjoin(
                Updater, Application.updated_by == Updater.id
            ).filter(
                or_(
                    Application.application_name.ilike(search_term),
                    Application.description.ilike(search_term),
                    Application.github_repo.ilike(search_term),
                    Application.application_owner.ilike(search_term)
                )
            ).limit(limit).all()
            
            # Convert to dictionaries
            apps_with_users = []
            for app, creator_username, updater_username in results:
                app_dict = self._convert_app_to_dict(app)
                app_dict['created_by_username'] = creator_username or 'system'
                app_dict['updated_by_username'] = updater_username
                apps_with_users.append(app_dict)
            
            db.close()
            
            return apps_with_users
            
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            if 'db' in locals():
                db.close()
            return []
    
    def invalidate_cache(self, app_id: Optional[str] = None):
        """Invalidate application caches after updates."""
        if app_id:
            cache_manager.delete(f"app:{app_id}")
        
        # Invalidate list caches (simple approach - delete all list caches)
        # In production, you'd want more sophisticated cache invalidation
        cache_manager.clear()  # Clear all for now
        logger.info("✅ Application caches invalidated")
    
    def _convert_app_to_dict(self, app: Application) -> Dict:
        """Convert Application model to dictionary."""
        return {
            "id": app.id,
            "application_name": app.application_name,
            "description": app.description,
            "application_owner": app.application_owner,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "cloud_provider": app.cloud_provider,
            "gcp_project_id": app.gcp_project_id,
            "aws_account_id": app.aws_account_id,
            "azure_subscription_id": app.azure_subscription_id,
            "github_repo": app.github_repo,
            "gke_cluster_name": app.gke_cluster_name,
            "aks_cluster_name": app.aks_cluster_name,
            "eks_cluster_name": app.eks_cluster_name,
            "argocd_app_name": app.argocd_app_name,
            "grafana_dashboard": app.grafana_dashboard,
            "grafana_alert_name": app.grafana_alert_name,
            "namespace": app.namespace,
            "gcp_log_resource": app.gcp_log_resource,
            "deployment_name": app.deployment_name,
            "pod_name": app.pod_name,
            "azure_deployment_name": app.azure_deployment_name,
            "azure_pod_name": app.azure_pod_name,
            "azure_namespace": app.azure_namespace,
            "resource_group": app.resource_group,
            "workspace": app.workspace,
            "workspace_resource_group": app.workspace_resource_group,
            "ingress_name": app.ingress_name,
            "ingress_public_ip": app.ingress_public_ip,
            "ingress_namespace": app.ingress_namespace,
            "cloudwatch_log_group_path": app.cloudwatch_log_group_path,
            "aws_deployment_name": app.aws_deployment_name,
            "aws_pod_name": app.aws_pod_name,
            "aws_namespace": app.aws_namespace,
            "application_criticality": app.application_criticality,
            "custom_metadata": app.custom_metadata or [],
            "tags": app.tags or [],
            "created_by": app.created_by,
            "updated_by": app.updated_by,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }


# Global instance
optimized_application_db = OptimizedApplicationDatabase()
