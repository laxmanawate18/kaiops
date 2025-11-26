"""
AWS RCA Agent - CloudWatch Logging & Root Cause Analysis for EKS

This agent performs log investigation, troubleshooting, and automated RCA using AWS CloudWatch MCP tools.
It dynamically resolves application names to EKS deployment information from MongoDB metadata.
"""

from .agent import root_agent

__all__ = ["root_agent"]
