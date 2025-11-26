"""
AWS MCP Client Helper - Execute queries via CloudWatch MCP Server

Provides functions to call the MCP server for CloudWatch log retrieval, 
pod analysis, metrics, and ALB log queries.

Uses stdio connection to CloudWatch MCP server.
"""

import subprocess
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class CloudWatchMCPClient:
    """CloudWatch MCP client for querying logs, events, and metrics"""
    
    def __init__(self):
        self.mcp_server_path = os.getenv(
            "AWS_MCP_SERVER_PATH",
            "awslabs.cloudwatch-mcp-server@latest"
        )
        self.region = os.getenv("AWS_REGION", "ap-southeast-2")
    
    def call_mcp_tool(self, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """
        Call a CloudWatch MCP tool via stdio.
        
        Args:
            tool_name: Name of the MCP tool (describe_log_groups, analyze_log_group, etc)
            arguments: Tool arguments
        
        Returns:
            Dictionary with tool results or error
        """
        try:
            # For now, return mock responses (MCP server integration to be implemented)
            # In production, this would connect via stdio to the actual CloudWatch MCP server
            
            if tool_name == "get_log_events":
                return self._mock_get_log_events(arguments)
            elif tool_name == "execute_log_insights_query":
                return self._mock_execute_log_insights_query(arguments)
            elif tool_name == "get_cloudwatch_metrics":
                return self._mock_get_cloudwatch_metrics(arguments)
            elif tool_name == "get_alb_logs":
                return self._mock_get_alb_logs(arguments)
            else:
                return {"error": f"Unknown CloudWatch tool: {tool_name}"}
        
        except Exception as e:
            return {"error": f"Error calling CloudWatch MCP tool: {str(e)}"}
    
    def _mock_get_log_events(self, arguments: dict) -> Dict[str, Any]:
        """Mock CloudWatch log events retrieval."""
        log_group = arguments.get("log_group", "unknown")
        log_stream = arguments.get("log_stream", "unknown")
        lines = arguments.get("lines", 100)
        
        # Return different logs based on component type (for testing)
        if "backend" in log_stream.lower() or "api" in log_stream.lower():
            # API component - could have errors
            mock_logs = [
                {"timestamp": "2024-11-24T10:15:23Z", "message": "[INFO] Starting API pod"},
                {"timestamp": "2024-11-24T10:15:24Z", "message": "[INFO] Database connection established"},
                {"timestamp": "2024-11-24T10:15:25Z", "message": "[INFO] Server listening on port 5000"},
                {"timestamp": "2024-11-24T10:15:26Z", "message": "[ERROR] Failed to load configuration from ConfigMap"},
                {"timestamp": "2024-11-24T10:15:27Z", "message": "[ERROR] java.lang.NullPointerException: Config is null"},
                {"timestamp": "2024-11-24T10:15:28Z", "message": "[ERROR] Stack trace: at com.app.config.ConfigLoader.load()"},
                {"timestamp": "2024-11-24T10:15:29Z", "message": "[ERROR] Application startup failed"},
                {"timestamp": "2024-11-24T10:15:30Z", "message": "[FATAL] Exiting due to configuration error"},
            ]
        elif "frontend" in log_stream.lower() or "web" in log_stream.lower():
            # Frontend component - healthy
            mock_logs = [
                {"timestamp": "2024-11-24T10:15:23Z", "message": "[INFO] Starting frontend pod"},
                {"timestamp": "2024-11-24T10:15:24Z", "message": "[INFO] Loading environment: production"},
                {"timestamp": "2024-11-24T10:15:25Z", "message": "[INFO] Webpack compilation complete"},
                {"timestamp": "2024-11-24T10:15:26Z", "message": "[INFO] Development server listening on port 3000"},
                {"timestamp": "2024-11-24T10:15:27Z", "message": "[INFO] Ready to accept requests"},
                {"timestamp": "2024-11-24T10:16:00Z", "message": "[INFO] GET /api/health 200"},
                {"timestamp": "2024-11-24T10:16:05Z", "message": "[INFO] POST /api/login 200"},
                {"timestamp": "2024-11-24T10:16:10Z", "message": "[INFO] GET /api/todos 200"},
            ]
        else:
            # Generic healthy pod
            mock_logs = [
                {"timestamp": "2024-11-24T10:15:23Z", "message": "[INFO] Starting pod"},
                {"timestamp": "2024-11-24T10:15:24Z", "message": "[INFO] Database connection established"},
                {"timestamp": "2024-11-24T10:15:25Z", "message": "[INFO] Server listening on port 5000"},
                {"timestamp": "2024-11-24T10:15:26Z", "message": "[INFO] Ready to accept connections"},
                {"timestamp": "2024-11-24T10:16:00Z", "message": "[INFO] Received request: GET /api/todos"},
                {"timestamp": "2024-11-24T10:16:01Z", "message": "[INFO] Processing request..."},
                {"timestamp": "2024-11-24T10:16:02Z", "message": "[INFO] Request completed successfully"},
            ]
        
        return {
            "status": "success",
            "log_group": log_group,
            "log_stream": log_stream,
            "events_count": len(mock_logs),
            "events": mock_logs[:lines],
            "timestamp": "2024-11-24T10:16:02Z"
        }
    
    def _mock_execute_log_insights_query(self, arguments: dict) -> Dict[str, Any]:
        """Mock CloudWatch Logs Insights query execution."""
        log_group = arguments.get("log_group", "")
        query = arguments.get("query", "")
        
        return {
            "status": "success",
            "log_group": log_group,
            "query": query[:100] + "..." if len(query) > 100 else query,
            "query_status": "Complete",
            "results_count": 0,
            "results": []
        }
    
    def _mock_get_cloudwatch_metrics(self, arguments: dict) -> Dict[str, Any]:
        """Mock CloudWatch metrics retrieval."""
        namespace = arguments.get("namespace", "ContainerInsights")
        metric_name = arguments.get("metric_name", "")
        dimensions = arguments.get("dimensions", {})
        
        # Return mock metrics based on component type
        component = dimensions.get("PodName", "unknown")
        
        if "backend" in component.lower() or "api" in component.lower():
            # API component - high CPU/memory
            metrics = [
                {"timestamp": "2024-11-24T10:15:00Z", "cpu_utilization": 75, "memory_utilization": 82},
                {"timestamp": "2024-11-24T10:16:00Z", "cpu_utilization": 88, "memory_utilization": 95},
                {"timestamp": "2024-11-24T10:17:00Z", "cpu_utilization": 92, "memory_utilization": 98},
            ]
        else:
            # Frontend/healthy component - normal metrics
            metrics = [
                {"timestamp": "2024-11-24T10:15:00Z", "cpu_utilization": 20, "memory_utilization": 35},
                {"timestamp": "2024-11-24T10:16:00Z", "cpu_utilization": 25, "memory_utilization": 40},
                {"timestamp": "2024-11-24T10:17:00Z", "cpu_utilization": 22, "memory_utilization": 38},
            ]
        
        return {
            "status": "success",
            "namespace": namespace,
            "metric_name": metric_name,
            "dimensions": dimensions,
            "datapoints_count": len(metrics),
            "datapoints": metrics
        }
    
    def _mock_get_alb_logs(self, arguments: dict) -> Dict[str, Any]:
        """Mock ALB logs retrieval."""
        log_group = arguments.get("log_group", "")
        lines = arguments.get("lines", 50)
        
        mock_alb_logs = [
            {
                "timestamp": "2024-11-24T10:16:00Z",
                "method": "GET",
                "path": "/api/todos",
                "status_code": "200",
                "response_time_ms": "45",
                "upstream": "10.0.1.15:5000"
            },
            {
                "timestamp": "2024-11-24T10:16:05Z",
                "method": "POST",
                "path": "/api/todos",
                "status_code": "201",
                "response_time_ms": "82",
                "upstream": "10.0.1.15:5000"
            },
            {
                "timestamp": "2024-11-24T10:16:10Z",
                "method": "GET",
                "path": "/api/todos/123",
                "status_code": "200",
                "response_time_ms": "38",
                "upstream": "10.0.1.15:5000"
            },
            {
                "timestamp": "2024-11-24T10:16:15Z",
                "method": "DELETE",
                "path": "/api/todos/456",
                "status_code": "500",
                "response_time_ms": "5000",
                "upstream": "10.0.1.15:5000"
            },
        ]
        
        return {
            "status": "success",
            "log_group": log_group,
            "logs_count": len(mock_alb_logs),
            "logs": mock_alb_logs[:lines],
            "timestamp": "2024-11-24T10:16:02Z"
        }


# Global client instance
_client = CloudWatchMCPClient()


def get_log_events(log_group: str, log_stream: str, lines: int = 100) -> List[Dict[str, str]]:
    """Get CloudWatch log events and return as list of dicts."""
    result = _client.call_mcp_tool("get_log_events", {
        "log_group": log_group,
        "log_stream": log_stream,
        "lines": lines
    })
    
    if result.get("status") == "success":
        return result.get("events", [])
    else:
        return [{"timestamp": datetime.now().isoformat(), "message": f"Error: {result.get('error', 'Unknown error')}"}]


def execute_log_insights_query(log_group: str, query: str, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
    """Execute CloudWatch Logs Insights query."""
    if not start_time:
        start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    if not end_time:
        end_time = int(datetime.now().timestamp() * 1000)
    
    result = _client.call_mcp_tool("execute_log_insights_query", {
        "log_group": log_group,
        "query": query,
        "start_time": start_time,
        "end_time": end_time
    })
    
    return result


def get_cloudwatch_metrics(namespace: str, metric_name: str, dimensions: dict, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
    """Get CloudWatch metrics."""
    if not start_time:
        start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    if not end_time:
        end_time = int(datetime.now().timestamp() * 1000)
    
    result = _client.call_mcp_tool("get_cloudwatch_metrics", {
        "namespace": namespace,
        "metric_name": metric_name,
        "dimensions": dimensions,
        "start_time": start_time,
        "end_time": end_time
    })
    
    return result


def get_alb_logs(log_group: str, lines: int = 50) -> List[Dict[str, str]]:
    """Get ALB logs and return as list of dicts."""
    result = _client.call_mcp_tool("get_alb_logs", {
        "log_group": log_group,
        "lines": lines
    })
    
    if result.get("status") == "success":
        return result.get("logs", [])
    else:
        return []


__all__ = [
    "CloudWatchMCPClient",
    "get_log_events",
    "execute_log_insights_query",
    "get_cloudwatch_metrics",
    "get_alb_logs"
]
