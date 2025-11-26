from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
import logging
from app.models import CustomChatRequest, CustomChatResponse, HealthResponse
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.auth.models import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo purposes
active_sessions: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(user_id: str, session_id: str = None) -> str:
    """Get or create a session for the user."""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    session_key = f"{user_id}:{session_id}"
    if session_key not in active_sessions:
        active_sessions[session_key] = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": "2024-01-01T00:00:00Z",
            "message_count": 0
        }
    
    return session_id

@router.post("/argocd/chat")
async def argocd_chat_endpoint(
    request: CustomChatRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user)
):
    """
    Dedicated ArgoCD chat endpoint that bypasses sre_agent.py corruption.
    """
    try:
        # Use authenticated user ID if available, otherwise use provided or default
        user_id = current_user.username if current_user else (request.user_id or "anonymous")
        
        # Use MCP client for ArgoCD operations
        from agents.mcp_client import call_mcp_tool, parse_mcp_response
        import asyncio

        # Simple ArgoCD intent-based routing
        message_lower = request.message.lower()
        
        if any(keyword in message_lower for keyword in ["list", "show", "applications"]):
            result = await call_mcp_tool("argocd", "list_applications")
            response_text = parse_mcp_response(result)
        elif "status" in message_lower or "health" in message_lower:
            # Extract app name if mentioned
            app_name = None
            words = request.message.split()
            for i, word in enumerate(words):
                if word.lower() in ["status", "health", "of", "for"] and i + 1 < len(words):
                    app_name = words[i + 1]
                    break
            if app_name:
                result = await call_mcp_tool("argocd", "get_application_status", app_name=app_name)
                response_text = parse_mcp_response(result)
            else:
                result = await call_mcp_tool("argocd", "list_applications")
                response_text = parse_mcp_response(result)
        elif "sync" in message_lower or "synchronize" in message_lower:
            # Extract app name if mentioned
            app_name = None
            words = request.message.split()
            for i, word in enumerate(words):
                if word.lower() in ["sync", "synchronize"] and i + 1 < len(words):
                    app_name = words[i + 1]
                    break
            if app_name:
                response_text = argocd_sync_application(app_name)
            else:
                response_text = "Please specify which application to sync. For example: 'sync my-app'"
        elif "history" in message_lower or "deployments" in message_lower:
            # Extract app name if mentioned
            app_name = None
            words = request.message.split()
            for i, word in enumerate(words):
                if word.lower() in ["history", "deployments", "of", "for"] and i + 1 < len(words):
                    app_name = words[i + 1]
                    break
            if app_name:
                response_text = argocd_get_deployment_history(app_name)
            else:
                response_text = "Please specify which application to get deployment history for. For example: 'deployment history of my-app'"
        elif "search" in message_lower or "find" in message_lower:
            # Extract search query
            query = request.message
            response_text = argocd_search_applications(query)
        else:
            response_text = argocd_list_applications()
        
        return CustomChatResponse(
            response=response_text,
            user_id=user_id,
            session_id=request.session_id or "argocd-session",
            success=True
        )
        
    except Exception as e:
        return CustomChatResponse(
            response="",
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            success=False,
            error_message=f"ArgoCD Error: {str(e)}"
        )

@router.post("/chat", response_model=CustomChatResponse)
async def custom_chat_endpoint(
    request: CustomChatRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user)
):
    """
    Enhanced chat endpoint using the root_agent via proper ADK Runner.
    Routes requests to the appropriate agent based on content analysis.
    """
    try:
        # Use authenticated user ID if available, otherwise use provided or default
        user_id = current_user.username if current_user else (request.user_id or "anonymous")
        
        session_id = get_or_create_session(user_id, request.session_id)

        logger.info(f"Processing chat message from {user_id}: {request.message}")
        
        # Use the agent service to properly invoke the agent
        from app.chat.agent_service import process_message
        
        agent_result = await process_message(
            message=request.message,
            session_id=session_id,
            user_id=user_id
        )
        
        response_text = agent_result.get("response", "No response generated")
        
        # Update session
        session_key = f"{user_id}:{session_id}"
        if session_key in active_sessions:
            active_sessions[session_key]["message_count"] += 1
        
        logger.info(f"Successfully processed chat message for {user_id}")
        
        return CustomChatResponse(
            response=response_text,
            user_id=user_id,
            session_id=session_id,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {type(e).__name__}: {str(e)}", exc_info=True)
        return CustomChatResponse(
            response="",
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            success=False,
            error_message=f"Error processing request: {str(e)}"
        )


@router.post("/agent/chat", response_model=CustomChatResponse)
async def agent_chat_endpoint(
    request: CustomChatRequest,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user)
):
    """
    Agent-based chat endpoint that uses the root_agent with tool invocation.
    The agent will automatically decide which tool to use based on the user's message.
    """
    try:
        from agents.sre_agent import root_agent
        
        # Use authenticated user ID if available, otherwise use provided or default
        user_id = current_user.username if current_user else (request.user_id or "anonymous")
        session_id = get_or_create_session(user_id, request.session_id)
        
        # Prepare the message for the agent
        user_message = request.message
        
        try:
            # Invoke the agent using run_async
            # run_async returns an async generator, so we need to iterate through it
            response_parts = []
            async for response in root_agent.run_async(user_message):
                if hasattr(response, 'text'):
                    response_parts.append(response.text)
                else:
                    response_parts.append(str(response))
            
            response_text = "\n".join(response_parts) if response_parts else "No response generated"
            
        except Exception as agent_error:
            response_text = f"Agent invocation error: {type(agent_error).__name__}: {str(agent_error)}"
        
        # Update session
        session_key = f"{user_id}:{session_id}"
        if session_key in active_sessions:
            active_sessions[session_key]["message_count"] += 1
        
        return CustomChatResponse(
            response=response_text,
            user_id=user_id,
            session_id=session_id,
            success=True
        )
        
    except Exception as e:
        return CustomChatResponse(
            response="",
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            success=False,
            error_message=f"Error processing agent request: {str(e)}"
        )

@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all sessions for a specific user (authenticated only)."""
    # Users can only access their own sessions, admins can access any
    if current_user.role != "admin" and current_user.username != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user_sessions = []
    for session_key, session_data in active_sessions.items():
        if session_data["user_id"] == user_id:
            user_sessions.append(session_data)
    
    return {
        "user_id": user_id,
        "sessions": user_sessions,
        "total_sessions": len(user_sessions)
    }

@router.delete("/sessions/{user_id}/{session_id}")
async def delete_session(
    user_id: str,
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a specific session (authenticated only)."""
    # Users can only delete their own sessions, admins can delete any
    if current_user.role != "admin" and current_user.username != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_key = f"{user_id}:{session_id}"
    if session_key in active_sessions:
        del active_sessions[session_key]
        return {"message": f"Session {session_id} deleted for user {user_id}"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@router.get("/stats")
async def get_stats(current_user: Optional[UserResponse] = Depends(get_optional_current_user)):
    """Get basic statistics about the service."""
    total_sessions = len(active_sessions)
    active_users = len(set(session["user_id"] for session in active_sessions.values()))
    
    # Return different stats based on authentication
    base_stats = {
        "agent_info": {
            "name": "weather_time_assistant",
            "capabilities": ["weather_lookup", "time_lookup"],
            "supported_cities": ["New York", "London", "Tokyo", "Paris", "Los Angeles", "Sydney"]
        }
    }
    
    if current_user:
        # Authenticated users get more detailed stats
        base_stats.update({
            "total_sessions": total_sessions,
            "active_users": active_users,
            "user_info": {
                "username": current_user.username,
                "role": current_user.role,
                "authenticated": True
            }
        })
    else:
        # Anonymous users get limited stats
        base_stats.update({
            "user_info": {
                "authenticated": False
            }
        })
    
    return base_stats
