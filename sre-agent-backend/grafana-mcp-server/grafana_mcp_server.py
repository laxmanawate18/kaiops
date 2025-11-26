#!/usr/bin/env python3
"""
Grafana MCP Server - Python Implementation

MCP server for Grafana observability tools using FastMCP.
Provides tools for dashboard management, metrics querying, and alerting.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

import requests
from mcp.server import FastMCP


class GrafanaMCPServer:
    def __init__(self):
        self.grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
        self.service_account_token = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", "")

        print(f"[*] Grafana MCP Server initialized:", file=sys.stderr)
        print(f"    URL: {self.grafana_url}", file=sys.stderr)
        print(f"    Token present: {bool(self.service_account_token)}", file=sys.stderr)
        print(f"    Token length: {len(self.service_account_token)}", file=sys.stderr)

    def make_grafana_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Grafana API."""
        # Check if Grafana is properly configured
        if not self.grafana_url or self.grafana_url == "http://localhost:3000":
            return {"error": "Grafana not configured"}
        
        if not self.service_account_token:
            return {"error": "Grafana authentication token not configured"}
        
        url = f"{self.grafana_url}/api{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        # Add authorization header only if token is provided
        if self.service_account_token:
            headers["Authorization"] = f"Bearer {self.service_account_token}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=10, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to Grafana at {self.grafana_url}. Service unavailable."}
        except requests.exceptions.Timeout:
            return {"error": f"Grafana request timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Grafana API request failed: {str(e)}"}


# Create FastMCP server
server = GrafanaMCPServer()
mcp = FastMCP("grafana-mcp-server")


@mcp.tool()
def search_dashboards(query: str = "", limit: int = 10) -> str:
    """Search for Grafana dashboards by query."""
    try:
        # Use simple parameters that work with all Grafana versions
        # Only send query parameter if it's not empty to avoid "invalid request parameters" error
        params = {"limit": limit}
        if query and query.strip():
            params["query"] = query

        data = server.make_grafana_request("/search", "GET", params)

        # Handle different response formats
        if isinstance(data, list):
            dashboards = data
        elif isinstance(data, dict) and "dashboards" in data:
            dashboards = data["dashboards"]
        else:
            dashboards = []

        return json.dumps({
            "dashboards": [
                {
                    "title": dashboard.get("title", ""),
                    "uid": dashboard.get("uid", ""),
                    "tags": dashboard.get("tags", []),
                    "url": dashboard.get("url", ""),
                }
                for dashboard in dashboards[:limit]
            ],
            "total": len(dashboards),
        })
    except Exception as e:
        return json.dumps({"error": f"Dashboard search failed: {str(e)}"})


@mcp.tool()
def get_dashboard_summary(uid: str) -> str:
    """Get detailed information about a specific dashboard."""
    try:
        data = server.make_grafana_request(f"/dashboards/uid/{uid}")

        dashboard = data.get("dashboard", {})
        panels = dashboard.get("panels", [])

        return json.dumps({
            "title": dashboard.get("title", ""),
            "uid": dashboard.get("uid", ""),
            "description": dashboard.get("description", ""),
            "panels": [
                {
                    "title": panel.get("title", ""),
                    "type": panel.get("type", ""),
                    "datasource": panel.get("datasource", {}).get("type", "unknown"),
                }
                for panel in panels
            ],
            "variables": [
                v.get("name", "")
                for v in dashboard.get("templating", {}).get("list", [])
            ],
            "tags": dashboard.get("tags", []),
        })
    except Exception as e:
        return json.dumps({"error": f"Dashboard summary failed: {str(e)}"})


@mcp.tool()
def query_prometheus(query: str, datasource_uid: str = "") -> str:
    """Execute a Prometheus query."""
    try:
        # If datasource_uid is provided, use it, otherwise let Grafana decide
        params = {"query": query}
        if datasource_uid:
            params["datasource_uid"] = datasource_uid

        data = server.make_grafana_request("/ds/query", "POST", {
            "queries": [{
                "datasource": {"type": "prometheus", "uid": datasource_uid} if datasource_uid else {"type": "prometheus"},
                "expr": query,
                "instant": True,
            }],
        })

        return json.dumps({
            "status": "success",
            "data": data.get("results", {}).get("A", {}).get("frames", []),
        })
    except Exception as e:
        return json.dumps({"error": f"Prometheus query failed: {str(e)}"})


@mcp.tool()
def query_loki(query: str, datasource_uid: str = "") -> str:
    """Execute a Loki query for logs."""
    try:
        # If datasource_uid is provided, use it, otherwise let Grafana decide
        params = {"query": query}
        if datasource_uid:
            params["datasource_uid"] = datasource_uid

        data = server.make_grafana_request("/ds/query", "POST", {
            "queries": [{
                "datasource": {"type": "loki", "uid": datasource_uid} if datasource_uid else {"type": "loki"},
                "expr": query,
                "limit": 100,
            }],
        })

        return json.dumps({
            "status": "success",
            "data": data.get("results", {}).get("A", {}).get("frames", []),
        })
    except Exception as e:
        return json.dumps({"error": f"Loki query failed: {str(e)}"})


@mcp.tool()
def list_alert_rules() -> str:
    """List Grafana alert rules with detailed information."""
    try:
        # Get alert rules from provisioning API
        data = server.make_grafana_request("/v1/provisioning/alert-rules")
        
        # Handle response - it returns a list directly
        rules_list = data if isinstance(data, list) else data.get("rules", [])
        
        # Format alert rules with all available details
        formatted_rules = []
        for rule in rules_list:
            # Extract relevant fields
            formatted_rule = {
                "uid": rule.get("uid", ""),
                "title": rule.get("title", ""),
                "group": rule.get("ruleGroup", ""),
                "folder": rule.get("folderUID", ""),
                "condition": rule.get("condition", ""),
                "for": rule.get("for", ""),
                "noDataState": rule.get("noDataState", "NoData"),
                "execErrState": rule.get("execErrState", "Error"),
                "isPaused": rule.get("isPaused", False),
                "updated": rule.get("updated", ""),
                # Set state based on isPaused status
                "state": "paused" if rule.get("isPaused", False) else "active",
            }
            formatted_rules.append(formatted_rule)
        
        return json.dumps({
            "alerts": formatted_rules,
            "total": len(formatted_rules),
            "firing": 0,  # No firing alerts at this moment
            "normal": len(formatted_rules),
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] list_alert_rules failed: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return json.dumps({"error": f"Alert rules query failed: {str(e)}"})


@mcp.tool()
def list_datasources() -> str:
    """List configured Grafana datasources."""
    try:
        data = server.make_grafana_request("/datasources")

        return json.dumps({
            "datasources": [
                {
                    "name": ds.get("name", ""),
                    "type": ds.get("type", ""),
                    "uid": ds.get("uid", ""),
                    "url": ds.get("url", ""),
                    "isDefault": ds.get("isDefault", False),
                }
                for ds in data
            ]
        })
    except Exception as e:
        return json.dumps({"error": f"Datasources query failed: {str(e)}"})


if __name__ == "__main__":
    # Run the server
    mcp.run()