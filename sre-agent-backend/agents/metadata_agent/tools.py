"""
Metadata Agent Tools

Direct MongoDB tools for application metadata and configuration management.
No MCP required - direct database access as the authoritative context source.
"""

import json
from bson.json_util import dumps
import os
import sys
from typing import Optional
from google.adk.tools import ToolContext
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

# Global cache for MongoDB queries (TTL: 2 minutes)
_mongo_cache = TTLCache(maxsize=50, ttl=120)

# Global MongoDB client
_mongo_client = None
_db = None


def get_mongo_client():
    """Get or create synchronous MongoDB client."""
    global _mongo_client, _db
    if _mongo_client is None:
        try:
            from pymongo import MongoClient
            from app.database import MongoDBConfig

            connection_string = MongoDBConfig.get_connection_string()
            db_name = MongoDBConfig.get_database_name()

            _mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            _db = _mongo_client[db_name]
            _mongo_client.admin.command('ping')
            print("✅ MongoDB client initialized successfully")
        except Exception as e:
            print(f"❌ MongoDB client init failed: {e}")
            return None, None

    return _mongo_client, _db


async def search_application_by_name(app_name: str, tool_context: Optional[ToolContext] = None) -> str:
    """
    Search for an application by name (case-insensitive).
    
    CRITICAL: Call this FIRST for any application-specific query.
    Returns complete metadata: github_repo, argocd_app_name, grafana_dashboard, owner, cluster, namespace.
    
    Args:
        app_name: Application name to search for
    
    Returns:
        Formatted application details with all metadata fields
    """
    try:
        client, db = get_mongo_client()
        if db is None:
            return "❌ **MongoDB Connection Failed**\nDatabase is unavailable. Please try again later."

        from app.database import Collections
        collection = db[Collections.APPLICATIONS]

        # Case-insensitive search
        app = collection.find_one({
            "application_name": {
                "$regex": f"^{app_name}$",
                "$options": "i"
            }
        }, {"_id": 0})

        if not app:
            # Fallback: list available apps
            all_apps = list(collection.find({}, {"application_name": 1, "_id": 0}))
            
            if not all_apps:
                return f"❌ **Application Not Found**\nNo application named '{app_name}' exists. Database is empty."
            
            app_names = "\n".join([f"• {a.get('application_name', 'Unknown')}" for a in all_apps])
            return f"❌ **Application Not Found**\nNo application named '{app_name}' in database.\n\n📋 **Available Applications:**\n{app_names}"

        # Format response with emoji
        response = f"📱 **Application: {app.get('application_name', 'Unknown')}**\n\n"
        response += f"🔗 **Repository**: `{app.get('github_repo', 'N/A')}`\n"
        response += f"👤 **Owner**: `{app.get('application_owner', 'N/A')}`\n"
        response += f"🌐 **Cluster**: `{app.get('gke_cluster_name', 'N/A')}`\n"
        response += f"📦 **Namespace**: `{app.get('namespace', 'N/A')}`\n"
        response += f"🚀 **ArgoCD App**: `{app.get('argocd_app_name', 'N/A')}`\n"
        response += f"📊 **Grafana Dashboard**: `{app.get('grafana_dashboard', 'N/A')}`\n"
        response += f"⚙️ **Environment**: `{app.get('environment', 'N/A')}`\n"
        response += f"📝 **Description**: {app.get('description', 'N/A')}\n"
        response += f"✅ **Status**: {app.get('status', 'N/A')}\n"
        
        return response

    except Exception as e:
        print(f"❌ Error in search_application_by_name: {str(e)}")
        return f"❌ **Error Searching Application**: {str(e)}"


async def list_all_applications(tool_context: Optional[ToolContext] = None) -> str:
    """Return all applications as structured JSON for frontend rendering."""
    try:
        client, db = get_mongo_client()
        if db is None:
            return json.dumps({
                "error": True,
                "message": "MongoDB Connection Failed",
                "description": "Database is unavailable. Please try again later.",
                "applications": []
            })

        from app.database import Collections
        collection = db[Collections.APPLICATIONS]

        apps = list(collection.find({}, {"_id": 0}))

        if not apps:
            return json.dumps({
                "error": False,
                "message": "No applications registered",
                "data_type": "applications_table",
                "total": 0,
                "applications": []
            })

        formatted_apps = []
        active_count = 0
        inactive_count = 0
        pending_count = 0

        for app in apps:
            status = (app.get("status") or "unknown").lower()
            if status == "active":
                active_count += 1
            elif status == "inactive":
                inactive_count += 1
            elif status == "pending":
                pending_count += 1

            formatted_apps.append({
                "application_name": app.get("application_name", "Unknown"),
                "application_owner": app.get("application_owner", "N/A"),
                "gke_cluster_name": app.get("gke_cluster_name", "N/A"),
                "status": app.get("status", "Unknown"),
                "github_repo": app.get("github_repo", "N/A"),
                "argocd_app_name": app.get("argocd_app_name", "N/A"),
                "grafana_dashboard": app.get("grafana_dashboard", "N/A"),
                "cloud_provider": app.get("cloud_provider", "N/A")
            })

        return json.dumps({
            "error": False,
            "message": "Registered Applications",
            "data_type": "applications_table",
            "total": len(formatted_apps),
            "stats": {
                "active": active_count,
                "inactive": inactive_count,
                "pending": pending_count
            },
            "applications": formatted_apps
        })

    except Exception as e:
        print(f"❌ Error in list_all_applications: {str(e)}")
        return json.dumps({
            "error": True,
            "message": "Error Listing Applications",
            "description": str(e),
            "applications": []
        })


async def query_mongodb(filter: dict, collection_name: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> str:
    """
    Execute a custom MongoDB query with a filter.
    
    Args:
        filter: MongoDB filter dictionary
        collection_name: Optional collection name (defaults to applications)
    
    Returns:
        JSON-formatted query results
    """
    try:
        cache_key = f"{collection_name or 'applications'}:{json.dumps(filter, sort_keys=True)}"

        if cache_key in _mongo_cache:
            return _mongo_cache[cache_key]

        client, db = get_mongo_client()
        if db is None:
            return "❌ MongoDB not available. Please check database connection."

        from app.database import Collections
        target_collection_name = collection_name or Collections.APPLICATIONS
        collection = db[target_collection_name]

        docs = list(collection.find(filter, {"_id": 0}))
        result = dumps(docs, indent=2) if docs else "No matching documents found."

        _mongo_cache[cache_key] = result
        return result

    except Exception as e:
        return f"❌ MongoDB query error: {str(e)}"


__all__ = [
    "search_application_by_name",
    "list_all_applications",
    "query_mongodb"
]
