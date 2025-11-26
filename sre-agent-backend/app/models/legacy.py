"""
Legacy models for backward compatibility.
These are the original models from app/models.py
"""

from pydantic import BaseModel
from typing import List, Optional


class MessagePart(BaseModel):
    text: Optional[str] = None
    # Add other part types as needed


class Message(BaseModel):
    role: str
    parts: List[MessagePart]


class AgentRunRequest(BaseModel):
    app_name: str
    user_id: str
    session_id: str
    new_message: Message
    streaming: Optional[bool] = False


class CustomChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None


class CustomChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    success: bool
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str
    available_agents: List[str]
