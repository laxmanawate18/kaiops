"""
GCP RCA Agent - Cloud Logging & Root Cause Analysis for GKE

This agent performs log investigation, troubleshooting, and automated RCA using 
Google Cloud Logging and Cloud Monitoring APIs directly (no MCP server needed).
It dynamically resolves application names to GKE deployment information from MongoDB metadata.
"""

from .agent import root_agent

__all__ = ["root_agent"]
