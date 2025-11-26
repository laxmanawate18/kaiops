import os
import sys
import asyncio
import warnings
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.cli.fast_api import get_fast_api_app
from app.routers import custom_routes
from app.auth.routes import router as auth_router
from app.auth.team_routes import router as team_router
from app.feedback.routes import router as feedback_router
from app.chat.routes import router as chat_router
from app.applications.routes import router as applications_router
from app.metadata.routes import router as metadata_router

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import new middleware and utilities (non-breaking additions)
from app.middleware import RequestContextMiddleware
from app.cache import get_cache_manager
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings for async generator cleanup during shutdown
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*async.*generator.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, message=".*EXPERIMENTAL.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*non-text parts in the response.*")

# Configuration
AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents"))
SESSION_DB_URL = "sqlite:///./adk_sessions.db"

# CORS allowed origins - restrict wildcard in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:5173",    # Vite default port
    "http://localhost:3000",    # React default port
    "http://localhost:3001", 
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
# Note: Remove wildcard "*" in production for security

# Global variables to store app state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    
    # Startup
    logger.info("=" * 70)
    logger.info("Starting ADK FastAPI application...")
    logger.info("=" * 70)
    
    # Initialize Azure Cosmos DB connection (required)
    from app.database import MongoDBConfig
    try:
        db = MongoDBConfig.connect()
        logger.info(f"✅ Azure Cosmos DB connected: {MongoDBConfig.get_database_name()}")
        app_state["mongodb_connected"] = True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Azure Cosmos DB: {e}")
        logger.error("Cannot start without database connection. Exiting.")
        raise
    
    # Log new features
    logger.info("✅ Features enabled:")
    logger.info("  • Custom exception hierarchy with error context")
    logger.info("  • Request correlation IDs for tracing")
    logger.info("  • Multi-layer caching (Redis + in-memory)")
    logger.info("  • Integration health checks")
    logger.info("  • Audit logging for operations")
    logger.info("  • Structured response models")
    logger.info("  • Timeout management for operations")
    
    app_state["agents_loaded"] = True
    logger.info(f"Agent directory: {AGENT_DIR}")
    logger.info(f"Session database: {SESSION_DB_URL}")
    logger.info("Default credentials:")
    logger.info("   Admin: username=admin, password=admin123")
    logger.info("   Team Lead: username=teamlead, password=teamlead123")
    logger.info("   User: username=user, password=user123")
    logger.info("Default teams: SRE Team, DevOps Team, Security Team")
    logger.info("✅ All systems initialized")
    logger.info("=" * 70)
    
    yield
    
    # Shutdown  
    logger.info("Shutting down ADK FastAPI application...")
    try:
        MongoDBConfig.close()
        app_state.clear()
        logger.info("✅ Shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create ADK FastAPI app
    adk_app = get_fast_api_app(
        agents_dir=AGENT_DIR,
        session_service_uri=SESSION_DB_URL,
        allow_origins=ALLOWED_ORIGINS,
        web=False,  # Disable ADK web interface to avoid conflicts - we use custom routes instead
        lifespan=lifespan
    )
    
    # Add request context middleware (for correlation IDs and request tracking)
    adk_app.add_middleware(RequestContextMiddleware)
    
    # Add CORS middleware
    adk_app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize cache manager
    try:
        cache_manager = get_cache_manager()
        logger.info(f"✅ Cache manager initialized: {cache_manager.get_stats()}")
    except Exception as e:
        logger.warning(f"⚠️ Cache manager initialization failed: {e}, continuing with defaults")
    
    # Include authentication routes
    adk_app.include_router(
        auth_router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )
    
    # Include team management routes
    adk_app.include_router(
        team_router,
        prefix="/api/v1/teams",
        tags=["Team Management"]
    )
    
    # Include feedback routes - FIXED PREFIX
    adk_app.include_router(
        feedback_router,
        prefix="/api/v1/feedback",
        tags=["Feedback System"]
    )
    
    # Include chat session routes
    adk_app.include_router(
        chat_router,
        prefix="/api/v1/chat",
        tags=["Chat Sessions"]
    )
    
    # Include application registration routes
    adk_app.include_router(
        applications_router,
        prefix="/api/v1/applications",
        tags=["Application Registration"]
    )
    
    # Include metadata management routes
    adk_app.include_router(
        metadata_router,
        tags=["Metadata Management"]
    )
    
    # Include custom routers
    adk_app.include_router(
        custom_routes.router, 
        prefix="/api/v1", 
        tags=["Custom Endpoints"]
    )
    
    # Add a root endpoint
    @adk_app.get("/")
    async def root():
        return {
            "message": "ADK FastAPI Application with Team Management, Feedback System & Authentication",
            "version": "1.0.0", 
            "docs_url": "/docs",
            "authentication": {
                "login": "/api/v1/auth/login",
                "register": "/api/v1/auth/register",
                "me": "/api/v1/auth/me"
            },
            "team_management": {
                "teams": "/api/v1/teams/teams",
                "permissions": "/api/v1/teams/permissions",
                "stats": "/api/v1/teams/stats"
            },
            "feedback_system": {
                "create_feedback": "/api/v1/feedback/",
                "my_feedback": "/api/v1/feedback/my",
                "review_pending": "/api/v1/feedback/pending",
                "stats": "/api/v1/feedback/stats",
                "datasets": "/api/v1/feedback/datasets/entries"
            },
            "chat_sessions": {
                "create_session": "/api/v1/chat/sessions",
                "get_sessions": "/api/v1/chat/sessions",
                "send_message": "/api/v1/chat/messages",
                "get_messages": "/api/v1/chat/sessions/{session_id}/messages",
                "stats": "/api/v1/chat/stats"
            },
            "applications": {
                "list": "/api/v1/applications/",
                "create": "/api/v1/applications/",
                "get": "/api/v1/applications/{app_id}",
                "update": "/api/v1/applications/{app_id}",
                "delete": "/api/v1/applications/{app_id}",
                "toggle_status": "/api/v1/applications/{app_id}/toggle",
                "search": "/api/v1/applications/search/query",
                "stats": "/api/v1/applications/stats/summary"
            },
            "adk_endpoints": {
                "list_agents": "/list-apps",
                "run_agent": "/run", 
                "run_agent_streaming": "/run_sse"
            },
            "custom_endpoints": {
                "health": "/api/v1/health",
                "chat": "/api/v1/chat",
                "stats": "/api/v1/stats"
            }
        }
    
    # Add health check endpoint
    @adk_app.get("/api/v1/health")
    async def health_check():
        """Health check endpoint for the entire API."""
        return {
            "status": "healthy",
            "service": "sre_agent_api",
            "message": "API is running and connected to Azure Cosmos DB",
            "database": "sre_agent_db"
        }
    
    return adk_app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped gracefully")
        sys.exit(0)
    except Exception as e:
        print(f"\nServer error: {e}")
        sys.exit(1)
