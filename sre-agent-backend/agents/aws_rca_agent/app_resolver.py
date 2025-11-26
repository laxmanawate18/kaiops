"""
AWS Application Resolver - Dynamically resolves application metadata to EKS deployment information.

This module bridges the gap between application names (from users) and actual EKS
pod/namespace information from the metadata database.

Supports EKS deployments (same Kubernetes structure as Azure agent).
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


class AWSAppResolver:
    """Resolves application names to EKS deployment information."""
    
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
                print(f"❌ MongoDB connection failed in AWSAppResolver: {e}")
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
            
            # Case-insensitive search for AWS apps
            app = collection.find_one({
                "application_name": {
                    "$regex": f"^{app_name}$",
                    "$options": "i"
                },
                "cloud_provider": {"$in": ["aws", "AWS", None]}  # AWS or unspecified (backward compat)
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
        Resolve application name to all pod/deployment info for EKS.
        
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
                "error": f"Application '{app_name}' not found in AWS metadata"
            }
        
        namespace = app.get("namespace", "default")
        cluster = app.get("aws_cluster_name", "")
        
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
                    "component_type": deploy.get("component_type", "service"),
                    "cloudwatch_log_group": deploy.get("cloudwatch_log_group", app.get("cloudwatch_log_group", ""))
                })
            
            return {
                "deployments": deployments,
                "app_name": app.get("application_name", app_name),
                "namespace": namespace,
                "cluster": cluster,
                "environment": app.get("environment", "unknown"),
                "owner": app.get("application_owner", "unknown"),
                "is_multi_deployment": True,
                "cloudwatch_log_group": app.get("cloudwatch_log_group", "")
            }
        else:
            # Single deployment app - construct pod info from metadata
            pod_name = app.get("pod_name")
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
                    "component_type": "service",
                    "cloudwatch_log_group": app.get("cloudwatch_log_group", "")
                }],
                "app_name": app.get("application_name", app_name),
                "namespace": namespace,
                "cluster": cluster,
                "environment": app.get("environment", "unknown"),
                "owner": app.get("application_owner", "unknown"),
                "is_multi_deployment": False,
                "cloudwatch_log_group": app.get("cloudwatch_log_group", "")
            }
    
    @classmethod
    def resolve_ingress_info(cls, app_name: str) -> Dict[str, str]:
        """
        Resolve application name to ALB log group.
        
        Args:
            app_name: Application name from user
        
        Returns:
            Dictionary with 'log_group' and related ingress info
        """
        app = cls.get_app_metadata(app_name)
        
        if not app:
            return {
                "log_group": None,
                "error": f"Application '{app_name}' not found in metadata"
            }
        
        # Get ALB log group from app metadata or use default
        from agents.aws_rca_agent.config import AWSConfig
        alb_log_group = app.get("alb_log_group", AWSConfig.AWS_ALB_LOG_GROUP)
        cluster = app.get("aws_cluster_name", "")
        
        return {
            "log_group": alb_log_group,
            "cluster": cluster,
            "app_name": app.get("application_name", app_name),
            "app_host": app.get("app_host", ""),
            "domain": app.get("domain", "")
        }


# Convenience functions for use in tools
def get_pod_info(app_name: str) -> Dict[str, str]:
    """Get pod and namespace for an application."""
    return AWSAppResolver.resolve_pod_info(app_name)


def get_ingress_info(app_name: str) -> Dict[str, str]:
    """Get ingress information for an application."""
    return AWSAppResolver.resolve_ingress_info(app_name)


__all__ = [
    "AWSAppResolver",
    "get_pod_info",
    "get_ingress_info"
]
