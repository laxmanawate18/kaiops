"""
Metadata Agent Tools

PostgreSQL tools for application metadata and configuration management.
Replaced MongoDB with SQLAlchemy-based PostgreSQL backend.
"""

import json
import os
import sys
from typing import Optional
from google.adk.tools import ToolContext
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

# Global cache for database queries (TTL: 2 minutes)
_query_cache = TTLCache(maxsize=50, ttl=120)

# Global database session
_session = None


def get_session():
    """Get or create SQLAlchemy database session."""
    global _session
    if _session is None:
        try:
            from app.database.postgres_config import PostgresConfig
            from sqlalchemy import text
            _session = PostgresConfig.get_session()
            # Test connection
            _session.execute(text("SELECT 1"))
            print("✅ PostgreSQL session initialized successfully")
        except Exception as e:
            print(f"❌ PostgreSQL session init failed: {e}")
            return None

    return _session


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
        session = get_session()
        if session is None:
            return "❌ **PostgreSQL Connection Failed**\nDatabase is unavailable. Please try again later."

        from app.database.models import Application
        from sqlalchemy import func

        # Case-insensitive search
        app = session.query(Application).filter(
            func.lower(Application.application_name) == func.lower(app_name)
        ).first()

        if not app:
            # Fallback: list available apps
            all_apps = session.query(Application.application_name).all()
            
            if not all_apps:
                return f"❌ **Application Not Found**\nNo application named '{app_name}' exists. Database is empty."
            
            app_names = "\n".join([f"• {a[0]}" for a in all_apps])
            return f"❌ **Application Not Found**\nNo application named '{app_name}' in database.\n\n📋 **Available Applications:**\n{app_names}"

        # Format response with emoji
        response = f"📱 **Application: {app.application_name}**\n\n"
        response += f"🔗 **Repository**: `{app.github_repo or 'N/A'}`\n"
        response += f"👤 **Owner**: `{app.application_owner or 'N/A'}`\n"
        response += f"🌐 **Cluster**: `{app.gke_cluster_name or 'N/A'}`\n"
        response += f"📦 **Namespace**: `{app.namespace or 'N/A'}`\n"
        response += f"🚀 **ArgoCD App**: `{app.argocd_app_name or 'N/A'}`\n"
        response += f"📊 **Grafana Dashboard**: `{app.grafana_dashboard or 'N/A'}`\n"
        response += f"☁️ **Cloud Provider**: `{app.cloud_provider or 'N/A'}`\n"
        response += f"📝 **Description**: {app.description or 'N/A'}\n"
        response += f"✅ **Status**: {app.status or 'N/A'}\n"
        
        return response

    except Exception as e:
        print(f"❌ Error in search_application_by_name: {str(e)}")
        return f"❌ **Error Searching Application**: {str(e)}"


async def list_all_applications(tool_context: Optional[ToolContext] = None) -> str:
    """Return all applications as structured JSON for frontend rendering."""
    try:
        session = get_session()
        if session is None:
            return json.dumps({
                "error": True,
                "message": "PostgreSQL Connection Failed",
                "description": "Database is unavailable. Please try again later.",
                "applications": []
            })

        from app.database.models import Application

        apps = session.query(Application).all()

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
            status = (str(app.status) if app.status else "unknown").lower()
            if status == "active":
                active_count += 1
            elif status == "inactive":
                inactive_count += 1
            elif status == "pending":
                pending_count += 1

            formatted_apps.append({
                "application_name": app.application_name,
                "application_owner": app.application_owner or "N/A",
                "gke_cluster_name": app.gke_cluster_name or "N/A",
                "status": str(app.status) if app.status else "Unknown",
                "github_repo": app.github_repo or "N/A",
                "argocd_app_name": app.argocd_app_name or "N/A",
                "grafana_dashboard": app.grafana_dashboard or "N/A",
                "cloud_provider": app.cloud_provider or "N/A"
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
    Execute a custom PostgreSQL query based on filter criteria.
    
    DEPRECATED: This function has been replaced by PostgreSQL backend.
    Kept for backward compatibility - defaults to listing all applications.
    
    Args:
        filter: Query filter dictionary (for compatibility, may not fully support MongoDB syntax)
        collection_name: Optional collection name (ignored, PostgreSQL uses tables)
    
    Returns:
        JSON-formatted query results
    """
    try:
        cache_key = f"applications:{json.dumps(filter, sort_keys=True, default=str)}"

        if cache_key in _query_cache:
            return _query_cache[cache_key]

        session = get_session()
        if session is None:
            return "❌ PostgreSQL not available. Please check database connection."

        from app.database.models import Application
        from sqlalchemy import func

        # For backward compatibility, treat filter as basic query
        # If filter is empty, return all applications
        if not filter:
            apps = session.query(Application).all()
        else:
            # Try to match by application_name if provided
            if "application_name" in filter:
                app_name = filter["application_name"]
                if isinstance(app_name, dict) and "$regex" in app_name:
                    # MongoDB regex pattern
                    pattern = app_name["$regex"]
                    apps = session.query(Application).filter(
                        func.lower(Application.application_name).ilike(f"%{pattern}%")
                    ).all()
                else:
                    # Exact match
                    apps = session.query(Application).filter(
                        func.lower(Application.application_name) == func.lower(str(app_name))
                    ).all()
            else:
                apps = session.query(Application).all()

        # Convert to list of dicts
        docs = []
        for app in apps:
            docs.append({
                "id": app.id,
                "application_name": app.application_name,
                "description": app.description,
                "application_owner": app.application_owner,
                "status": str(app.status) if app.status else None,
                "cloud_provider": app.cloud_provider,
                "github_repo": app.github_repo,
                "gke_cluster_name": app.gke_cluster_name,
                "argocd_app_name": app.argocd_app_name,
                "grafana_dashboard": app.grafana_dashboard,
                "namespace": app.namespace
            })

        result = json.dumps(docs, indent=2, default=str) if docs else "No matching documents found."

        _query_cache[cache_key] = result
        return result

    except Exception as e:
        return f"❌ PostgreSQL query error: {str(e)}"


__all__ = [
    "search_application_by_name",
    "list_all_applications",
    "query_mongodb"
]
