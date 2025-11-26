"""
Centralized MCP Client

Handles communication with all MCP servers (ArgoCD, GitHub, Grafana).
Provides a unified interface for calling MCP tools from any agent.
"""

import json
import os
import sys
import subprocess
import threading
import queue
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# MCP Server configurations
MCP_SERVERS = {
    'argocd': {
        'path': 'argocd-mcp-server/argocd_mcp_server.py',
        'env': {
            'ARGOCD_URL': os.getenv('ARGOCD_URL', 'http://localhost:8080'),
            'ARGOCD_AUTH_TOKEN': os.getenv('ARGOCD_AUTH_TOKEN', ''),
        }
    },
    'github': {
        'path': 'github-mcp-server/github_mcp_server.py',
        'env': {
            'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN', ''),
        }
    },
    'grafana': {
        'path': 'grafana-mcp-server/grafana_mcp_server.py',
        'env': {
            'GRAFANA_URL': os.getenv('GRAFANA_URL', 'http://172.168.254.97'),
            'GRAFANA_SERVICE_ACCOUNT_TOKEN': os.getenv('GRAFANA_SERVICE_ACCOUNT_TOKEN', ''),
        }
    }
}

# Active MCP processes
_mcp_processes = {}
_mcp_response_queues = {}
_mcp_locks = {}


def _get_mcp_server_path(server_name: str) -> str:
    """Get the absolute path to an MCP server."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mcp_path = os.path.join(current_dir, MCP_SERVERS[server_name]['path'])
    return os.path.abspath(mcp_path)


def _initialize_server(server_name: str):
    """Send initialization handshake to MCP server."""
    process = _mcp_processes.get(server_name)
    if not process or not process.stdin:
        return

    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": f"{server_name}-client",
                "version": "1.0.0"
            }
        }
    }

    process.stdin.write(json.dumps(init_request) + '\n')
    process.stdin.flush()
    import time
    time.sleep(0.1)


def _read_mcp_responses(server_name: str):
    """Background thread to read responses from MCP server."""
    process = _mcp_processes.get(server_name)
    response_queue = _mcp_response_queues.get(server_name)
    
    if process and process.stdout and response_queue:
        for line in iter(process.stdout.readline, ''):
            try:
                response = json.loads(line.strip())
                response_queue.put(response)
            except json.JSONDecodeError:
                continue


def _start_mcp_server(server_name: str):
    """Start an MCP server process if not already running."""
    if server_name not in _mcp_locks:
        _mcp_locks[server_name] = threading.Lock()
    
    with _mcp_locks[server_name]:
        process = _mcp_processes.get(server_name)
        
        if process is None or process.poll() is not None:
            server_path = _get_mcp_server_path(server_name)
            
            if not os.path.exists(server_path):
                raise Exception(f"MCP server not found: {server_path}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(MCP_SERVERS[server_name]['env'])
            
            # Start process
            _mcp_processes[server_name] = subprocess.Popen(
                [sys.executable, server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            # Initialize response queue
            _mcp_response_queues[server_name] = queue.Queue()
            
            # Start background thread
            response_thread = threading.Thread(
                target=_read_mcp_responses,
                args=(server_name,),
                daemon=True
            )
            response_thread.start()
            
            # Send initialization
            _initialize_server(server_name)


async def call_mcp_tool(server_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call a tool on an MCP server.
    
    Args:
        server_name: Name of the server ('argocd', 'github', 'grafana')
        tool_name: Name of the tool to call
        **kwargs: Tool arguments
    
    Returns:
        Tool response as dictionary
    """
    # Start server if needed
    _start_mcp_server(server_name)
    
    # Generate unique request ID
    request_id = int(asyncio.get_event_loop().time() * 1000000)
    
    # Create JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": kwargs
        }
    }
    
    # Send request
    process = _mcp_processes.get(server_name)
    response_queue = _mcp_response_queues.get(server_name)
    
    if process and process.stdin:
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        
        # Wait for response with timeout
        timeout = 30.0
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                response = response_queue.get_nowait()
                if response.get('id') == request_id:
                    if 'result' in response:
                        return response['result']
                    elif 'error' in response:
                        raise Exception(f"MCP Error: {response['error']}")
                else:
                    # Put back non-matching responses
                    response_queue.put(response)
            except queue.Empty:
                await asyncio.sleep(0.1)
        
        raise Exception(f"Timeout waiting for {server_name} MCP response")
    
    raise Exception(f"{server_name} MCP server not available")


def parse_mcp_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse MCP response format and extract actual data."""
    import logging
    logger = logging.getLogger(__name__)
    
    if "error" in result:
        logger.warning(f"MCP returned error: {result}")
        return result
    
    # Debug log the raw result
    logger.debug(f"📥 MCP raw result: {json.dumps(result, indent=2)}")
    
    content = result.get("content", [])
    if content and len(content) > 0:
        text_content = content[0].get("text", "{}")
        logger.debug(f"📝 Extracted text content: {text_content[:500]}")
        try:
            parsed = json.loads(text_content)
            logger.debug(f"✅ Successfully parsed JSON from MCP response")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from MCP text: {e}")
            logger.error(f"   Raw text was: {text_content[:500]}")
            return {}
    
    logger.warning(f"⚠️ No content in MCP response")
    return {}
