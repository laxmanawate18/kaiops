"""
GCP Application Resolver - Dynamically resolves application metadata to GKE deployment information.

This module bridges the gap between application names (from users) and actual GKE
pod/namespace information from the metadata database (Azure Cosmos DB / MongoDB).

Supports GKE deployments with multi-deployment applications.
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


class GCPAppResolver:
    """Resolves application names to GKE deployment information."""
    
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
                print(f"❌ MongoDB connection failed in GCPAppResolver: {e}")
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
            
            # Case-insensitive search for GCP apps
            app = collection.find_one({
                "application_name": {
                    "$regex": f"^{app_name}$",
                    "$options": "i"
                },
                "cloud_provider": {"$in": ["gcp", "GCP"]}
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
        gke_cluster = app.get("gke_cluster", "")
        gcp_log_resource = app.get("gcp_log_resource", "k8s_container")
        
        # Check if app has multiple deployments defined
        deployments_data = app.get("deployments", [])
        
        if deployments_data and isinstance(deployments_data, list) and len(deployments_data) > 0:
            # Multi-deployment app - return all deployments
            deployments = []
            for deploy in deployments_data:
                deployments.append({
                    "pod_name": deploy.get("pod_name", f"{deploy.get('deployment_name', 'unknown')}-pod"),
                    "deployment_name": deploy.get("deployment_name", "unknown"),
                    "namespace": deploy.get("namespace", "default"),
                    "status": deploy.get("status", "unknown"),
                    "criticality": deploy.get("criticality", "medium"),
                    "component_type": deploy.get("component_type", "service")
                })
            
            return {
                "deployments": deployments,
                "app_name": app.get("application_name", app_name),
                "gke_cluster": gke_cluster,
                "gcp_log_resource": gcp_log_resource,
                "environment": app.get("environment", "unknown"),
                "owner": app.get("application_owner", "unknown"),
                "is_multi_deployment": len(deployments) > 1
            }
        else:
            # Single deployment app - construct pod info from metadata
            pod_name = app.get("pod_name")
            namespace = app.get("namespace", "default")
            
            if not pod_name:
                # Try to construct pod name from common Kubernetes naming patterns
                app_name_normalized = app.get("application_name", app_name).lower().replace(" ", "-")
                pod_name = f"{app_name_normalized}-deployment-pod"
            
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
                "gke_cluster": gke_cluster,
                "gcp_log_resource": gcp_log_resource,
                "environment": app.get("environment", "unknown"),
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
        
        gke_cluster = app.get("gke_cluster", "")
        
        return {
            "gke_cluster": gke_cluster,
            "app_name": app.get("application_name", app_name),
            "app_host": app.get("app_host", ""),
            "domain": app.get("domain", ""),
            "load_balancer_enabled": app.get("load_balancer_enabled", False)
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
