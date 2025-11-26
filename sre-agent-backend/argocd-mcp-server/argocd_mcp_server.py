#!/usr/bin/env python3
"""
ArgoCD MCP Server - Python Implementation

MCP server for ArgoCD deployment management using FastMCP.
Provides tools for application management, synchronization, and monitoring.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

import requests
from mcp.server import FastMCP

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


class ArgocdMCPServer:
    def __init__(self):
        self.argocd_url = os.getenv("ARGOCD_URL", "http://localhost:8080")
        self.argocd_token = os.getenv("ARGOCD_AUTH_TOKEN", "")

        print(f"[*] ArgoCD MCP Server initialized:", file=sys.stderr)
        print(f"    URL: {self.argocd_url}", file=sys.stderr)
        print(f"    Token present: {bool(self.argocd_token)}", file=sys.stderr)

    def make_argocd_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the ArgoCD API."""
        url = f"{self.argocd_url}/api/v1{endpoint}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Add authorization header only if token is provided
        if self.argocd_token:
            headers["Authorization"] = f"Bearer {self.argocd_token}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=10, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"ArgoCD API request failed: {str(e)}")


# Create FastMCP server
server = ArgocdMCPServer()
mcp = FastMCP("argocd-mcp-server")


@mcp.tool()
def list_applications(project: str = "", limit: int = 50) -> str:
    """List all ArgoCD applications."""
    try:
        params = {"limit": limit}
        if project:
            params["projects"] = project

        data = server.make_argocd_request("/applications", "GET", params)

        applications = data.get("items", []) if isinstance(data, dict) else data

        result = {
            "total": len(applications),
            "applications": [
                {
                    "name": app.get("metadata", {}).get("name", ""),
                    "namespace": app.get("metadata", {}).get("namespace", ""),
                    "project": app.get("spec", {}).get("project", ""),
                    "sync_status": app.get("status", {}).get("sync", {}).get("status", "Unknown"),
                    "health_status": app.get("status", {}).get("health", {}).get("status", "Unknown"),
                    "repo_url": app.get("spec", {}).get("source", {}).get("repoURL", ""),
                    "target_revision": app.get("spec", {}).get("source", {}).get("targetRevision", "")
                }
                for app in applications
            ]
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to list applications: {str(e)}"})


@mcp.tool()
def get_application_details(app_name: str) -> str:
    """Get detailed information about a specific ArgoCD application."""
    try:
        data = server.make_argocd_request(f"/applications/{app_name}", "GET")

        result = {
            "name": data.get("metadata", {}).get("name", ""),
            "namespace": data.get("metadata", {}).get("namespace", ""),
            "project": data.get("spec", {}).get("project", ""),
            "sync_status": data.get("status", {}).get("sync", {}).get("status", "Unknown"),
            "health_status": data.get("status", {}).get("health", {}).get("status", "Unknown"),
            "source": {
                "repo_url": data.get("spec", {}).get("source", {}).get("repoURL", ""),
                "path": data.get("spec", {}).get("source", {}).get("path", ""),
                "target_revision": data.get("spec", {}).get("source", {}).get("targetRevision", "")
            },
            "destination": {
                "server": data.get("spec", {}).get("destination", {}).get("server", ""),
                "namespace": data.get("spec", {}).get("destination", {}).get("namespace", "")
            },
            "last_sync_time": data.get("status", {}).get("operationState", {}).get("finishedAt", ""),
            "last_sync_result": data.get("status", {}).get("operationState", {}).get("phase", "")
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to get application details: {str(e)}"})


@mcp.tool()
def get_application_status(app_name: str) -> str:
    """Get sync and health status of an ArgoCD application."""
    try:
        data = server.make_argocd_request(f"/applications/{app_name}", "GET")

        result = {
            "app_name": app_name,
            "sync_status": data.get("status", {}).get("sync", {}).get("status", "Unknown"),
            "health_status": data.get("status", {}).get("health", {}).get("status", "Unknown"),
            "sync_message": data.get("status", {}).get("sync", {}).get("comparedTo", {}).get("source", ""),
            "last_sync_time": data.get("status", {}).get("operationState", {}).get("finishedAt", ""),
            "last_sync_result": data.get("status", {}).get("operationState", {}).get("phase", ""),
            "resources": {
                "total": len(data.get("status", {}).get("resources", [])),
                "healthy": sum(1 for r in data.get("status", {}).get("resources", []) if r.get("health", {}).get("status") == "Healthy")
            }
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to get application status: {str(e)}"})


@mcp.tool()
def sync_application(app_name: str, force: bool = False, prune: bool = False) -> str:
    """Trigger a manual sync of an ArgoCD application."""
    try:
        params = {
            "name": app_name,
            "appNamespace": "argocd"
        }

        # For sync, we typically POST with sync preferences in body
        sync_params = {
            "dryRun": False,
            "prune": prune,
            "force": force
        }

        data = server.make_argocd_request(f"/applications/{app_name}/sync", "POST", sync_params)

        result = {
            "app_name": app_name,
            "status": "Sync initiated",
            "operation_id": data.get("metadata", {}).get("uid", ""),
            "sync_phase": data.get("status", {}).get("operationState", {}).get("phase", "Pending")
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to sync application: {str(e)}"})


@mcp.tool()
def get_deployment_history(app_name: str, limit: int = 10) -> str:
    """Get deployment/sync history of an ArgoCD application."""
    try:
        data = server.make_argocd_request(f"/applications/{app_name}", "GET")

        history = data.get("status", {}).get("history", [])

        result = {
            "app_name": app_name,
            "total_syncs": len(history),
            "recent_syncs": [
                {
                    "revision": sync.get("revision", ""),
                    "deployed_at": sync.get("deployedAt", ""),
                    "status": sync.get("result", {}).get("phase", "Unknown"),
                    "message": sync.get("result", {}).get("message", "")
                }
                for sync in history[:limit]
            ]
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to get deployment history: {str(e)}"})


@mcp.tool()
def search_applications(query: str, limit: int = 20) -> str:
    """Search for ArgoCD applications by name or label."""
    try:
        data = server.make_argocd_request("/applications", "GET", {"limit": 100})

        applications = data.get("items", []) if isinstance(data, dict) else data
        query_lower = query.lower()

        filtered = [
            app for app in applications
            if query_lower in app.get("metadata", {}).get("name", "").lower()
            or query_lower in app.get("spec", {}).get("project", "").lower()
        ][:limit]

        result = {
            "query": query,
            "results_count": len(filtered),
            "applications": [
                {
                    "name": app.get("metadata", {}).get("name", ""),
                    "project": app.get("spec", {}).get("project", ""),
                    "sync_status": app.get("status", {}).get("sync", {}).get("status", "Unknown"),
                    "health_status": app.get("status", {}).get("health", {}).get("status", "Unknown")
                }
                for app in filtered
            ]
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to search applications: {str(e)}"})


@mcp.tool()
def list_repositories() -> str:
    """List all configured Git repositories in ArgoCD."""
    try:
        data = server.make_argocd_request("/repositories", "GET")

        repositories = data.get("items", []) if isinstance(data, dict) else data

        result = {
            "total": len(repositories),
            "repositories": [
                {
                    "url": repo.get("repo", ""),
                    "connection_status": repo.get("connectionState", {}).get("status", "Unknown"),
                    "last_checked": repo.get("connectionState", {}).get("attemptedAt", ""),
                    "insecure": repo.get("insecure", False)
                }
                for repo in repositories
            ]
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to list repositories: {str(e)}"})


@mcp.tool()
def list_projects() -> str:
    """List all ArgoCD projects."""
    try:
        data = server.make_argocd_request("/projects", "GET")

        projects = data.get("items", []) if isinstance(data, dict) else data

        result = {
            "total": len(projects),
            "projects": [
                {
                    "name": proj.get("metadata", {}).get("name", ""),
                    "description": proj.get("spec", {}).get("description", ""),
                    "destinations": len(proj.get("spec", {}).get("destinations", [])),
                    "source_repos": len(proj.get("spec", {}).get("sourceRepos", []))
                }
                for proj in projects
            ]
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to list projects: {str(e)}"})


@mcp.tool()
def get_server_info() -> str:
    """Get ArgoCD server version and information."""
    try:
        data = server.make_argocd_request("/version", "GET")

        result = {
            "version": data.get("Version", ""),
            "build_date": data.get("BuildDate", ""),
            "git_commit": data.get("GitCommit", ""),
            "git_branch": data.get("GitBranch", "")
        }

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to get server info: {str(e)}"})


if __name__ == "__main__":
    print("Starting ArgoCD MCP Server...", file=sys.stderr)
    mcp.run()
