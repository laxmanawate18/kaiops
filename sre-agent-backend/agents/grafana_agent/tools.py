"""
Grafana Agent Tools

MCP tool wrappers for observability and monitoring via Grafana.
All tools communicate with grafana-mcp-server.
"""

import sys
import os
from typing import Dict, Any

# Add parent to path for mcp_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.mcp_client import call_mcp_tool, parse_mcp_response


async def search_dashboards(query: str, limit: int = 10) -> str:
    """
    Search for Grafana dashboards by query with comprehensive details.
    
    Args:
        query: Dashboard name or search term (from metadata)
        limit: Maximum results to return
    
    Returns:
        Formatted list of dashboards with links and detailed information
    """
    try:
        if not query or query.lower() == "n/a":
            return "⚠️ **No Grafana Configuration**\nNo Grafana dashboard configured for this application."
        
        result = await call_mcp_tool("grafana", "search_dashboards", query=query, limit=limit)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Search Error**: {data['error']}"

        dashboards = data.get("dashboards", [])
        if not dashboards:
            return f"⚠️ **No Dashboards Found**\nNo dashboards matching '{query}'"

        import os
        grafana_base = os.getenv("GRAFANA_URL", "http://172.168.254.97").rstrip("/")
        
        output = f"📊 **Grafana Dashboards**: {query}\n\n"
        for i, dash in enumerate(dashboards[:limit], 1):
            title = dash.get("title", "Unknown")
            uid = dash.get("uid", "")
            tags = dash.get("tags", [])
            description = dash.get("description", "")
            panel_count = dash.get("panels", 0)
            
            # Create actual clickable dashboard link
            dashboard_url = f"{grafana_base}/d/{uid}/" if uid else grafana_base
            
            output += f"**{i}. {title}**\n"
            if description:
                output += f"   📝 Description: {description}\n"
            output += f"   🆔 UID: `{uid}`\n"
            if panel_count:
                output += f"   📈 Panels: {panel_count}\n"
            if tags:
                output += f"   🏷️ Tags: {', '.join(tags)}\n"
            output += f"   🔗 [🌐 Open Dashboard]({dashboard_url})\n"
            output += "\n"

        output += f"\n**💡 Tip**: Click on 'Open Dashboard' to view real-time metrics, panels, and health information.\n"
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def get_dashboard_summary(uid: str) -> str:
    """
    Get detailed summary of a Grafana dashboard.
    
    Args:
        uid: Dashboard UID
    
    Returns:
        Formatted dashboard details and metrics overview
    """
    try:
        if not uid:
            return "⚠️ **Invalid Dashboard UID**"
        
        result = await call_mcp_tool("grafana", "get_dashboard_summary", uid=uid)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Error Fetching Dashboard**: {data['error']}"

        title = data.get("title", "Unknown")
        description = data.get("description", "")
        panels = data.get("panels", [])
        tags = data.get("tags", [])
        
        output = f"📊 **Dashboard Summary**\n\n"
        output += f"**Title**: {title}\n"
        output += f"**UID**: `{uid}`\n"
        if description:
            output += f"**Description**: {description}\n"
        if tags:
            output += f"**Tags**: {', '.join(tags)}\n"
        output += f"**Panels**: {len(panels)}\n\n"
        
        if panels:
            output += "**Panel Overview**:\n"
            for i, panel in enumerate(panels[:10], 1):
                name = panel.get("title", "Panel")
                ptype = panel.get("type", "unknown")
                output += f"{i}. **{name}** ({ptype})\n"

        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def list_alert_rules(limit: int = 20) -> str:
    """
    List alert rules in Grafana with comprehensive details.
    
    Returns:
        Formatted list of alert rules with status and configuration information
    """
    try:
        result = await call_mcp_tool("grafana", "list_alert_rules")
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Error Fetching Alerts**: {data['error']}"

        alerts = data.get("alerts", [])
        
        # Handle case where alerts is not a list
        if not isinstance(alerts, list):
            alerts = []
        
        if not alerts:
            return "✅ **No Alert Rules Configured**\nNo alert rules are currently defined in Grafana"

        import os
        grafana_base = os.getenv("GRAFANA_URL", "http://172.168.254.97").rstrip("/")
        alerts_url = f"{grafana_base}/alerting/list"
        
        output = f"🚨 **Grafana Alert Rules**\n\n"
        
        # Separate by state
        active_alerts = [a for a in alerts if isinstance(a, dict) and a.get("state") == "active"]
        paused_alerts = [a for a in alerts if isinstance(a, dict) and a.get("state") == "paused"]
        
        output += f"**📊 Summary**:\n"
        output += f"• 🟢 **Active Rules**: {len(active_alerts)} rule(s) monitoring\n"
        output += f"• ⏸️ **Paused Rules**: {len(paused_alerts)} rule(s) disabled\n"
        output += f"• 📋 **Total**: {len(alerts)} alert rule(s)\n"
        output += f"• 🔗 [Manage Alerts]({alerts_url})\n\n"
        
        # Show active alerts
        if active_alerts:
            output += "**🟢 ACTIVE ALERT RULES** (Currently Monitoring):\n"
            for i, alert in enumerate(active_alerts[:limit], 1):
                title = alert.get("title", "Unknown")
                group = alert.get("group", "default")
                for_duration = alert.get("for", "1m")
                uid = alert.get("uid", "")
                condition = alert.get("condition", "")
                no_data_state = alert.get("noDataState", "NoData")
                
                output += f"\n{i}. **{title}** 🟢\n"
                output += f"   📍 Group: `{group}`\n"
                output += f"   ⏱️ For: `{for_duration}`\n"
                if condition:
                    output += f"   📊 Condition: `{condition}`\n"
                output += f"   🚫 No Data: {no_data_state}\n"
                output += f"   🆔 UID: `{uid}`\n"
            output += "\n"

        # Show paused alerts
        if paused_alerts:
            output += f"**⏸️ PAUSED ALERT RULES**: {len(paused_alerts)} disabled\n"
            for i, alert in enumerate(paused_alerts[:5], 1):
                title = alert.get("title", "Unknown")
                output += f"{i}. {title}\n"
            output += "\n"
        
        output += f"**💡 Quick Links**:\n"
        output += f"• 🔗 [View All Alert Rules]({alerts_url})\n"
        output += f"• ⚙️ [Configure Alerts]({grafana_base}/alerting/routes)\n"
        output += f"• 📊 [Alert History]({grafana_base}/alerting/history)\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


__all__ = [
    "search_dashboards",
    "get_dashboard_summary",
    "list_alert_rules"
]
