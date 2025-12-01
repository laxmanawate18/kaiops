"""
Application Resolver - Dynamically resolves application metadata to Kubernetes pod information.

This module bridges the gap between application names (from users) and actual Kubernetes
pod/namespace information from the metadata database.

It replaces hardcoded pod names and namespaces with dynamic resolution.
Uses PostgreSQL with SQLAlchemy for database access.
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


class AppResolver:
    """Resolves application names to Kubernetes pod information."""
    
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
                print(f"❌ PostgreSQL connection failed in AppResolver: {e}")
                return None
        
        return cls._session
    
    @classmethod
    def get_app_metadata(cls, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch application metadata from PostgreSQL.
        
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
            
            # Case-insensitive search
            app = session.query(Application).filter(
                func.lower(Application.application_name) == func.lower(app_name)
            ).first()
            
            # Cache the result as dictionary
            if app:
                app_dict = {
                    "id": app.id,
                    "application_name": app.application_name,
                    "description": app.description,
                    "application_owner": app.application_owner,
                    "status": str(app.status) if app.status else None,
                    "cloud_provider": app.cloud_provider,
                    "gke_cluster_name": app.gke_cluster_name,
                    "namespace": app.namespace or "kaiops-ns",
                    "pod_name": None,  # Not stored in model, derived from app name
                    "deployment_name": app.argocd_app_name,  # Use ArgoCD app name as deployment
                    "github_repo": app.github_repo,
                    "argocd_app_name": app.argocd_app_name,
                    "grafana_dashboard": app.grafana_dashboard
                }
                cls._app_cache[cache_key] = app_dict
            
            return app_dict
        
        except Exception as e:
            print(f"❌ Error fetching app metadata for '{app_name}': {e}")
            return None
    
    @classmethod
    def resolve_pod_info(cls, app_name: str) -> Dict[str, Any]:
        """
        Resolve application name to all pod/deployment info for the app.
        
        For multi-deployment apps (e.g., todo-backend + todo-frontend), returns all deployments.
        For single-deployment apps, returns list with one item.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Dictionary with 'deployments' (list) and 'app_name', 'namespace', 'cluster' keys.
            Each deployment includes: pod_name, deployment_name, status, namespace
        """
        app = cls.get_app_metadata(app_name)
        
        if not app:
            return {
                "deployments": [],
                "error": f"Application '{app_name}' not found in database"
            }
        
        namespace = app.get("namespace", "kaiops-ns")
        cluster = app.get("gke_cluster_name", "")
        deployment_name = app.get("deployment_name") or app.get("argocd_app_name") or app_name.lower().replace(" ", "-")
        
        # Construct pod name from deployment name
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
            "namespace": namespace,
            "cluster": cluster,
            "environment": "unknown",
            "owner": app.get("application_owner", "unknown"),
            "is_multi_deployment": False
        }
    
    @classmethod
    def resolve_ingress_info(cls, app_name: str) -> Dict[str, str]:
        """
        Resolve application name to ingress/load balancer namespace.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Dictionary with 'namespace' and related ingress info
        """
        app = cls.get_app_metadata(app_name)
        
        if not app:
            return {
                "namespace": None,
                "error": f"Application '{app_name}' not found in database"
            }
        
        # Get ingress namespace from app metadata
        # Default to standard NGINX ingress namespace
        ingress_namespace = "app-routing-system"
        cluster = app.get("gke_cluster_name", "")
        
        return {
            "namespace": ingress_namespace,
            "cluster": cluster,
            "app_name": app.get("application_name", app_name),
            "app_host": "",
            "domain": ""
        }
    
    @classmethod
    def get_pod_pattern(cls, app_name: str) -> str:
        """
        Get the pod name pattern for grep/filter operations.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Pod name pattern for matching multiple pods
        """
        info = cls.resolve_pod_info(app_name)
        if info.get("error"):
            return app_name.lower().replace(" ", "-")
        
        # Return the deployment prefix for pod matching
        deployment_name = info.get("deployments", [{}])[0].get("deployment_name", app_name.lower().replace(" ", "-"))
        return deployment_name


# Convenience functions for use in tools
def get_pod_info(app_name: str) -> Dict[str, str]:
    """Get pod and namespace for an application."""
    return AppResolver.resolve_pod_info(app_name)


def get_ingress_info(app_name: str) -> Dict[str, str]:
    """Get ingress information for an application."""
    return AppResolver.resolve_ingress_info(app_name)


def get_pod_pattern(app_name: str) -> str:
    """Get pod name pattern for an application."""
    return AppResolver.get_pod_pattern(app_name)


__all__ = [
    "AppResolver",
    "get_pod_info",
    "get_ingress_info",
    "get_pod_pattern"
]
