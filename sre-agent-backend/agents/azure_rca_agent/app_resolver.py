"""
Application Resolver - Dynamically resolves application metadata to Kubernetes pod information.

This module bridges the gap between application names (from users) and actual Kubernetes
pod/namespace information from the metadata database.

It replaces hardcoded pod names and namespaces with dynamic resolution.
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


class AppResolver:
    """Resolves application names to Kubernetes pod information."""
    
    _mongo_client = None
    _db = None
    _app_cache = {}
    
    @classmethod
    def get_mongo_db(cls):
        """Get MongoDB connection."""
        if cls._db is None:
            try:
                from pymongo import MongoClient
                from app.database import MongoDBConfig
                
                connection_string = MongoDBConfig.get_connection_string()
                db_name = MongoDBConfig.get_database_name()
                
                cls._mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
                cls._db = cls._mongo_client[db_name]
                cls._mongo_client.admin.command('ping')
            except Exception as e:
                print(f"❌ MongoDB connection failed in AppResolver: {e}")
                return None
        
        return cls._db
    
    @classmethod
    def get_app_metadata(cls, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch application metadata from MongoDB.
        
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
            db = cls.get_mongo_db()
            if db is None:
                return None
            
            from app.database import Collections
            collection = db[Collections.APPLICATIONS]
            
            # Case-insensitive search
            app = collection.find_one({
                "application_name": {
                    "$regex": f"^{app_name}$",
                    "$options": "i"
                }
            }, {"_id": 0})
            
            # Cache the result
            if app:
                cls._app_cache[cache_key] = app
            
            return app
        
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
        
        # Check if app has multiple deployments defined
        deployments_data = app.get("deployments", [])
        
        if deployments_data and isinstance(deployments_data, list) and len(deployments_data) > 0:
            # Multi-deployment app - return all deployments
            deployments = []
            for deploy in deployments_data:
                deployments.append({
                    "pod_name": deploy.get("pod_name", f"{deploy.get('deployment_name', 'unknown')}-pod"),
                    "deployment_name": deploy.get("deployment_name", "unknown"),
                    "namespace": deploy.get("namespace", namespace),
                    "status": deploy.get("status", "unknown"),
                    "criticality": deploy.get("criticality", "medium"),
                    "component_type": deploy.get("component_type", "service")
                })
            
            return {
                "deployments": deployments,
                "app_name": app.get("application_name", app_name),
                "namespace": namespace,
                "cluster": cluster,
                "environment": app.get("environment", "unknown"),
                "owner": app.get("application_owner", "unknown"),
                "is_multi_deployment": True
            }
        else:
            # Single deployment app - construct pod info from legacy format
            pod_name = app.get("pod_name")
            if not pod_name:
                # Try to construct pod name from common Kubernetes naming patterns
                app_name_normalized = app.get("application_name", app_name).lower().replace(" ", "-")
                pod_name = f"{app_name_normalized}-deployment-pod"  # Fallback pattern
            
            deployment_name = app.get("deployment_name", pod_name.split("-pod")[0] if "-pod" in pod_name else pod_name)
            
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
                "environment": app.get("environment", "unknown"),
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
        ingress_namespace = app.get("ingress_namespace", "app-routing-system")
        cluster = app.get("gke_cluster_name", "")
        
        return {
            "namespace": ingress_namespace,
            "cluster": cluster,
            "app_name": app.get("application_name", app_name),
            "app_host": app.get("app_host", ""),
            "domain": app.get("domain", "")
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
        
        # Return just the deployment prefix (e.g., "todo-backend-app-deploy")
        pod_name = info.get("pod_name", "")
        if pod_name:
            # Extract the deployment prefix (everything before the unique pod suffix)
            parts = pod_name.split("-")
            if len(parts) > 2:
                return "-".join(parts[:-2])  # Remove the unique pod identifier
        
        return app_name.lower().replace(" ", "-")


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
