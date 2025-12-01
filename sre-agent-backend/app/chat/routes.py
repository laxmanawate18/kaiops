"""
Chat Session Routes

RESTful API endpoints for managing user-isolated chat sessions and messages.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any
from app.auth.dependencies import get_current_user
from app.auth.models import UserResponse, UserRole
from .models import (
    CreateSessionRequest, CreateSessionResponse,
    SendMessageRequest, SendMessageResponse,
    GetMessagesResponse, GetSessionsResponse,
    UpdateSessionRequest, DeleteSessionResponse,
    ChatStatsResponse, ChatSession, ChatMessage, MessageSender
)
from .database_postgres import chat_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Session Management ====================

@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new chat session for the authenticated user.
    
    - **name**: Optional session name (auto-generated if not provided)
    """
    try:
        session = chat_db.create_session(
            user_id=current_user.id,
            session_name=request.name
        )
        
        return CreateSessionResponse(
            session=ChatSession(**session),
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions", response_model=GetSessionsResponse)
async def get_sessions(
    include_inactive: bool = Query(True, description="Include inactive sessions"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all chat sessions for the authenticated user.
    
    - **include_inactive**: Include inactive/archived sessions (default: true)
    """
    try:
        sessions = chat_db.get_user_sessions(
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        return GetSessionsResponse(
            sessions=[ChatSession(**s) for s in sessions],
            total=len(sessions)
        )
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific chat session by ID.
    
    Users can only access their own sessions.
    """
    session = chat_db.get_session(current_user.id, session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or access denied"
        )
    
    return ChatSession(**session)


@router.patch("/sessions/{session_id}", response_model=ChatSession)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update session details (name, active status, metadata).
    
    Users can only update their own sessions.
    """
    session = chat_db.update_session(
        user_id=current_user.id,
        session_id=session_id,
        **request.dict(exclude_none=True)
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or access denied"
        )
    
    return ChatSession(**session)


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages.
    
    Users can only delete their own sessions.
    """
    success = chat_db.delete_session(current_user.id, session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or access denied"
        )
    
    return DeleteSessionResponse(
        session_id=session_id,
        message="Session deleted successfully"
    )


@router.delete("/sessions", response_model=dict)
async def delete_all_sessions(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete all chat sessions for the authenticated user.
    
    ⚠️ This action cannot be undone!
    """
    count = chat_db.delete_all_user_sessions(current_user.id)
    
    return {
        "message": f"Deleted {count} sessions",
        "deleted_count": count
    }


# ==================== Message Management ====================

@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Send a message to a chat session.
    
    This endpoint:
    1. Adds the user message to the session
    2. Processes the message (mock response for now)
    3. Adds the agent response to the session
    4. Returns both messages
    """
    try:
        # Add user message
        user_message = chat_db.add_message(
            user_id=current_user.id,
            session_id=request.session_id,
            sender=MessageSender.USER,
            text=request.message,
            metadata=request.metadata
        )
        
        if not user_message:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found or access denied"
            )
        
        # Process message through AI agent
        from app.chat.agent_service import process_message
        agent_result = await process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        agent_response_text = agent_result["response"]
        agent_metadata = agent_result.get("metadata", {})
        
        # Add agent response
        agent_message = chat_db.add_message(
            user_id=current_user.id,
            session_id=request.session_id,
            sender=MessageSender.ASSISTANT,
            text=agent_response_text,
            metadata=agent_metadata
        )
        
        return SendMessageResponse(
            user_message=ChatMessage(**user_message),
            agent_message=ChatMessage(**agent_message) if agent_message else None,
            session_id=request.session_id,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return SendMessageResponse(
            user_message=None,
            agent_message=None,
            session_id=request.session_id,
            success=False,
            error_message=f"Failed to send message: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessage, status_code=201)
async def add_message_to_session(
    session_id: str,
    request: Dict[str, Any] = Body(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Add a message to a specific chat session.
    
    This is a simpler endpoint for direct message addition.
    For AI chat, use the /messages endpoint instead.
    
    Request body:
    {
        "text": "message text",
        "sender": "user" | "agent" | "system",
        "metadata": {} (optional)
    }
    """
    try:
        text = request.get("text")
        sender_str = request.get("sender", "user")
        metadata = request.get("metadata")
        
        if not text:
            raise HTTPException(status_code=400, detail="Message text is required")
        
        # Convert sender string to enum
        try:
            sender = MessageSender(sender_str)
        except ValueError:
            sender = MessageSender.USER
        
        message = chat_db.add_message(
            user_id=current_user.id,
            session_id=session_id,
            sender=sender,
            text=text,
            metadata=metadata
        )
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or access denied"
            )
        
        return ChatMessage(**message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=GetMessagesResponse)
async def get_messages(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get messages for a specific chat session.
    
    - **limit**: Maximum number of messages to return
    - **offset**: Number of messages to skip (for pagination)
    
    Users can only access their own session messages.
    """
    messages, total = chat_db.get_messages(
        user_id=current_user.id,
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    if messages is None and total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or access denied"
        )
    
    return GetMessagesResponse(
        session_id=session_id,
        messages=[ChatMessage(**m) for m in messages],
        total=total
    )


@router.delete("/sessions/{session_id}/messages", response_model=dict)
async def clear_messages(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Clear all messages from a chat session.
    
    The session itself is preserved, but all messages are deleted.
    """
    success = chat_db.clear_session_messages(current_user.id, session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or access denied"
        )
    
    return {
        "message": "Messages cleared successfully",
        "session_id": session_id
    }


# ==================== Statistics ====================

@router.get("/stats", response_model=ChatStatsResponse)
async def get_user_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get chat statistics for the authenticated user.
    
    Returns:
    - Total number of sessions
    - Active sessions count
    - Total messages sent
    - Sessions created today
    """
    stats = chat_db.get_user_stats(current_user.id)
    stats["user_id"] = current_user.id
    return ChatStatsResponse(**stats)


@router.get("/admin/stats", response_model=dict)
async def get_admin_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get global chat statistics (admin only).
    
    Returns platform-wide statistics.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return chat_db.get_all_stats()


# ==================== Health Check ====================

@router.get("/health")
async def chat_health_check():
    """
    Health check endpoint for chat service.
    """
    return {
        "status": "healthy",
        "service": "chat_sessions",
        "message": "Chat session service is running with user isolation"
    }
