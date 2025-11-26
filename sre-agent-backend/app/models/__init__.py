"""
Data models and schemas for the application.
"""

from .responses import (
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse,
    CursorPaginatedResponse,
    PaginationMeta,
    CursorPaginationMeta,
    PaginationParams,
    CursorPaginationParams,
    BulkOperationResponse,
    AsyncOperationResponse,
    HealthCheckResponse
)

# Import legacy models for backward compatibility
from .legacy import (
    MessagePart,
    Message,
    AgentRunRequest,
    CustomChatRequest,
    CustomChatResponse,
    HealthResponse
)

__all__ = [
    # Response models
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "CursorPaginatedResponse",
    "PaginationMeta",
    "CursorPaginationMeta",
    "PaginationParams",
    "CursorPaginationParams",
    "BulkOperationResponse",
    "AsyncOperationResponse",
    "HealthCheckResponse",
    # Legacy models
    "MessagePart",
    "Message",
    "AgentRunRequest",
    "CustomChatRequest",
    "CustomChatResponse",
    "HealthResponse",
]
