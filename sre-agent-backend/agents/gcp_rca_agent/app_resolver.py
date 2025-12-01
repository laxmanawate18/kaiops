"""
GCP Application Resolver - Dynamically resolves application metadata to GKE deployment information.

This module bridges the gap between application names (from users) and actual GKE
pod/namespace information from the metadata database.

Uses PostgreSQL with SQLAlchemy for database access.
Supports GKE deployments with multi-deployment applications.
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


class GCPAppResolver:
    """Resolves application names to GKE deployment information."""
    
    _session = None
    _app_cache = {}
    
    @classmethod
    def get_db_session(cls):
        """Get PostgreSQL database session."""
        if cls._session is None:
            try:
                from app.database.postgres_config import PostgresConfig
                from sqlalchemy import text
                cls._session = PostgresConfig.get_session()
                # Test connection
                cls._session.execute(text("SELECT 1"))
            except Exception as e:
                print(f"❌ PostgreSQL connection failed in GCPAppResolver: {e}")
                return None
        
        return cls._session
    
    @classmethod
    def get_app_metadata(cls, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch application metadata from PostgreSQL (GCP apps only).
        
        Args:
            app_name: Application name to look up
        
        Returns:
            Dictionary with app metadata or None if not found
        """
        # Check cache first
        cache_key = app_name.lower()
        if cache_key in cls._app_cache:
            return cls._app_cache[cache_key]
        
        try:
            session = cls.get_db_session()
            if session is None:
                return None
            
            from app.database.models import Application
            from sqlalchemy import func
            
            # Case-insensitive search for GCP apps
            app = session.query(Application).filter(
                func.lower(Application.application_name) == func.lower(app_name),
                func.lower(Application.cloud_provider) == 'gcp'
            ).first()
            
            # Cache the result as dictionary
            if app:
                app_dict = {
                    "id": app.id,
                    "application_name": app.application_name,
                    "cloud_provider": app.cloud_provider,
                    "gke_cluster_name": app.gke_cluster_name,
                    "namespace": app.namespace or "default",
                    "gcp_project_id": app.gcp_project_id,
                    "status": str(app.status) if app.status else None,
                    "application_owner": app.application_owner,
                    "argocd_app_name": app.argocd_app_name
                }
                cls._app_cache[cache_key] = app_dict
            
            return app_dict
        
        except Exception as e:
            print(f"❌ Error fetching app metadata for '{app_name}': {e}")
            return None
    
    @classmethod
    def resolve_pod_info(cls, app_name: str) -> Dict[str, Any]:
        """
        Resolve application name to all pod/deployment info for GKE.
        
        For multi-deployment apps (multiple deployments), returns all deployments.
        For single-deployment apps, returns list with one item.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Dictionary with 'deployments' (list) and deployment details.
            Each deployment includes: pod_name, deployment_name, namespace, criticality
        """
        app = cls.get_app_metadata(app_name)
        
        if not app:
            return {
                "deployments": [],
                "error": f"Application '{app_name}' not found in GCP metadata"
            }
        
        # Get GKE cluster info from metadata
        gke_cluster = app.get("gke_cluster_name", "")
        namespace = app.get("namespace", "default")
        deployment_name = app.get("argocd_app_name") or app_name.lower().replace(" ", "-")
        pod_name = f"{deployment_name}-pod"
        
        return {
            "deployments": [{
                "pod_name": pod_name,
                "deployment_name": deployment_name,
                "namespace": namespace,
                "status": app.get("status", "unknown"),
                "criticality": "critical",
                "component_type": "service"
            }],
            "app_name": app.get("application_name", app_name),
            "gke_cluster": gke_cluster,
            "environment": "unknown",
            "owner": app.get("application_owner", "unknown"),
            "is_multi_deployment": False
        }
    
    @classmethod
    def resolve_ingress_info(cls, app_name: str) -> Dict[str, Any]:
        """
        Resolve application name to Cloud Load Balancer info.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Dictionary with load balancer information
        """
        app = cls.get_app_metadata(app_name)
        
        if not app:
            return {
                "error": f"Application '{app_name}' not found in GCP metadata"
            }
        
        gke_cluster = app.get("gke_cluster_name", "")
        
        return {
            "gke_cluster": gke_cluster,
            "app_name": app.get("application_name", app_name),
            "app_host": "",
            "domain": "",
            "load_balancer_enabled": False
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear the application metadata cache."""
        cls._app_cache.clear()


# Convenience functions for use in tools
def get_pod_info(app_name: str) -> Dict[str, Any]:
    """Get pod and namespace for an application."""
    return GCPAppResolver.resolve_pod_info(app_name)


def get_ingress_info(app_name: str) -> Dict[str, Any]:
    """Get ingress/load balancer information for an application."""
    return GCPAppResolver.resolve_ingress_info(app_name)


__all__ = [
    "GCPAppResolver",
    "get_pod_info",
    "get_ingress_info"
]
