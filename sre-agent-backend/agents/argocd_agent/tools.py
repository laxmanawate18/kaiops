"""
ArgoCD Agent Tools

MCP tool wrappers for deployment management via ArgoCD.
All tools communicate with argocd-mcp-server.
"""

import sys
import os
from typing import Dict, Any

# Add parent to path for mcp_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.mcp_client import call_mcp_tool, parse_mcp_response


async def get_application_status(app_name: str) -> str:
    """
    Get comprehensive sync and health status of an ArgoCD application.
    
    Args:
        app_name: ArgoCD application name (should be extracted from metadata)
    
    Returns:
        Formatted deployment status with emojis, links, and comprehensive details
    """
    try:
        if not app_name or app_name.lower() == "n/a":
            return "⚠️ **No ArgoCD Configuration**\nThis application is not deployed via ArgoCD."
        
        result = await call_mcp_tool("argocd", "get_application_status", app_name=app_name)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **ArgoCD Error**: {data['error']}"

        sync_status = data.get("sync_status", "Unknown")
        health_status = data.get("health_status", "Unknown")
        revision = data.get("target_revision", "Unknown")
        last_sync = data.get("last_sync_time", "Never")
        
        # Extract additional details
        namespace = data.get("namespace", "default")
        cluster = data.get("cluster", "Unknown")
        replicas_current = data.get("replicas_current", "N/A")
        replicas_desired = data.get("replicas_desired", "N/A")
        resources_synced = data.get("resources_synced", "N/A")
        resources_total = data.get("resources_total", "N/A")
        
        # Determine emoji based on status
        sync_emoji = "✅" if sync_status == "Synced" else ("❌" if sync_status == "OutOfSync" else "⏳")
        health_emoji = "🟢" if health_status == "Healthy" else ("🟡" if health_status == "Progressing" else "🔴")
        
        # Create ArgoCD URL from environment
        import os
        argocd_base = os.getenv("ARGOCD_URL", "https://argocd.example.com").rstrip("/")
        argocd_url = f"{argocd_base}/applications/{app_name}"
        
        output = f"🚀 **ArgoCD Deployment Status**\n\n"
        output += f"**📍 Application Information**:\n"
        output += f"• **Name**: {app_name}\n"
        output += f"• **Namespace**: `{namespace}`\n"
        output += f"• **Cluster**: {cluster}\n\n"
        
        output += f"**⚡ Sync Status**:\n"
        output += f"• Status: {sync_emoji} **{sync_status}**\n"
        if sync_status == "OutOfSync":
            output += f"  ⚠️ Git state differs from live state - sync required\n"
        output += f"• Last Synced: {last_sync}\n"
        output += f"• Target Revision: `{revision}`\n\n"
        
        output += f"**💚 Health Status**:\n"
        output += f"• Status: {health_emoji} **{health_status}**\n"
        if health_status == "Degraded":
            output += f"  ⚠️ Some resources are unhealthy - check pod status\n"
        output += f"• Replicas: {replicas_current}/{replicas_desired}\n"
        output += f"• Resources Synced: {resources_synced}/{resources_total}\n\n"
        
        output += f"**🔗 Quick Links**:\n"
        output += f"• [View in ArgoCD]({argocd_url})\n"
        output += f"• [Application Logs]({argocd_url}/pod-logs)\n"
        output += f"• [Resource Tree]({argocd_url}/resource-tree)\n\n"
        
        # Recommendations
        output += f"**💡 Recommendations**:\n"
        if sync_status == "OutOfSync":
            output += f"• 🔄 Run sync to align Git and live state\n"
        if health_status != "Healthy":
            output += f"• 🔍 Check pod logs and events for errors\n"
        else:
            output += f"• ✅ Application is healthy and synced\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def sync_application(app_name: str, force: bool = False, prune: bool = False) -> str:
    """
    Trigger manual synchronization of an ArgoCD application.
    
    Args:
        app_name: ArgoCD application name
        force: Force sync even if already synced
        prune: Remove resources not in Git
    
    Returns:
        Sync initiation confirmation
    """
    try:
        result = await call_mcp_tool("argocd", "sync_application", app_name=app_name, force=force, prune=prune)
        data = parse_mcp_response(result)
        
        if "error" in data:
            return f"❌ **Sync Failed**: {data['error']}"
        
        return f"✅ **Synchronization Initiated**\n\n**Application**: {app_name}\n**Status**: Syncing in progress..."
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def get_deployment_history(app_name: str, limit: int = 10) -> str:
    """
    Get deployment history and recent sync operations.
    
    Args:
        app_name: ArgoCD application name
        limit: Number of recent deployments to show
    
    Returns:
        Formatted deployment timeline
    """
    try:
        result = await call_mcp_tool("argocd", "get_deployment_history", app_name=app_name, limit=limit)
        data = parse_mcp_response(result)
        
        if "error" in data:
            return f"❌ **History Fetch Failed**: {data['error']}"
        
        syncs = data.get("recent_syncs", [])
        if not syncs:
            return f"⚠️ **No Deployment History**\nNo recent deployments found for {app_name}"
        
        output = f"📊 **Deployment History**: {app_name}\n\n"
        for i, sync in enumerate(syncs[:10], 1):
            rev = sync.get('revision', 'Unknown')[:8]
            status = sync.get('status', 'Unknown')
            timestamp = sync.get('timestamp', 'Unknown')
            message = sync.get('message', '')
            
            status_emoji = "✅" if status == "Synced" else ("⏳" if status == "Syncing" else "❌")
            output += f"{i}. {status_emoji} `{rev}` - {status}\n"
            output += f"   • Time: {timestamp}\n"
            if message:
                output += f"   • Message: {message}\n"
            output += "\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def search_applications(query: str, limit: int = 20) -> str:
    """
    Search ArgoCD applications by query string.
    
    Args:
        query: Search query
        limit: Maximum results to return
    
    Returns:
        Formatted list of matching applications
    """
    try:
        result = await call_mcp_tool("argocd", "search_applications", query=query, limit=limit)
        data = parse_mcp_response(result)
        
        if "error" in data:
            return f"❌ **Search Failed**: {data['error']}"
        
        apps = data.get("applications", [])
        if not apps:
            return f"⚠️ **No Applications Found**\nNo applications matching '{query}' in ArgoCD"
        
        output = f"🔍 **Search Results**: Found {len(apps)} applications\n\n"
        for app in apps[:limit]:
            name = app.get('name', 'Unknown')
            sync = app.get('sync_status', 'Unknown')
            health = app.get('health_status', 'Unknown')
            
            sync_emoji = "✅" if sync == "Synced" else "❌"
            health_emoji = "🟢" if health == "Healthy" else "🔴"
            
            output += f"• **{name}**: {sync_emoji} {sync} | {health_emoji} {health}\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def list_repositories() -> str:
    """
    List all Git repositories configured in ArgoCD.
    
    Returns:
        Formatted list of repository URLs
    """
    try:
        result = await call_mcp_tool("argocd", "list_repositories")
        data = parse_mcp_response(result)
        
        if "error" in data:
            return f"❌ **Error Fetching Repositories**: {data['error']}"
        
        repos = data.get("repositories", [])
        if not repos:
            return "⚠️ **No Repositories Found**\nNo Git repositories configured in ArgoCD"
        
        output = f"📁 **ArgoCD Repositories**: {len(repos)} configured\n\n"
        for repo in repos:
            url = repo.get('url', 'Unknown')
            repo_type = repo.get('type', 'Unknown')
            output += f"• `{url}` ({repo_type})\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def list_projects() -> str:
    """
    List all ArgoCD projects.
    
    Returns:
        Formatted list of projects
    """
    try:
        result = await call_mcp_tool("argocd", "list_projects")
        data = parse_mcp_response(result)
        
        if "error" in data:
            return f"❌ **Error Fetching Projects**: {data['error']}"
        
        projects = data.get("projects", [])
        if not projects:
            return "⚠️ **No Projects Found**\nNo ArgoCD projects available"
        
        output = f"📂 **ArgoCD Projects**: {len(projects)} available\n\n"
        for proj in projects:
            name = proj.get('name', 'Unknown')
            desc = proj.get('description', '')
            output += f"• **{name}**"
            if desc:
                output += f": {desc}"
            output += "\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


__all__ = [
    "get_application_status",
    "sync_application",
    "get_deployment_history",
    "search_applications",
    "list_repositories",
    "list_projects"
]
