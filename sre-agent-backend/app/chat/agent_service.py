"""
Agent service for handling AI agent calls in chat.
This service integrates with the KaiOPS SRE Agent using the correct ADK invocation pattern.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.runners import Runner, InMemorySessionService
from google.genai.types import Content, Part
from genai_retry_wrapper import with_genai_retry

logger = logging.getLogger(__name__)

# Global services
_session_service: Optional[InMemorySessionService] = None
_runner: Optional[Runner] = None
AGENT_AVAILABLE = False

try:
    from agents import root_agent
    
    # Initialize ADK services
    _session_service = InMemorySessionService()
    _runner = Runner(
        agent=root_agent, 
        app_name="kaiops", 
        session_service=_session_service
    )
    AGENT_AVAILABLE = True
    logger.info("✅ ADK Agent Runner initialized successfully with root_agent")
    logger.info(f"   Root agent name: {root_agent.name}")
    logger.info(f"   Tools available: {len(root_agent.tools)}")
except Exception as e:
    logger.error(f"❌ Failed to load root agent or initialize runner: {e}")
    AGENT_AVAILABLE = False


@with_genai_retry
async def _run_agent_session(runner: Runner, user_id: str, session_id: str, user_content: Content) -> str:
    """
    Execute the agent session with retry logic for GenAI overload errors.
    Wraps the async generator consumption to allow retrying the entire generation process.
    """
    response_parts = []
    async for event in runner.run_async(
        user_id=user_id, 
        session_id=session_id, 
        new_message=user_content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_parts.append(part.text)
    return "".join(response_parts)


async def process_message(message: str, session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Process a user message through the SRE agent using ADK's runner pattern.
    
    Args:
        message: The user's input message
        session_id: The chat session ID
        user_id: The user's ID
        
    Returns:
        Dictionary with agent response and metadata
    """
    try:
        if not AGENT_AVAILABLE or _runner is None or _session_service is None:
            logger.error("❌ Agent service not available")
            return {
                "response": "Agent service is not available. Please try again later.",
                "success": False,
                "metadata": {"error": "agent_unavailable"}
            }
        
        logger.info(f"📨 Processing message for session {session_id}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"💬 Message: {message}")
        
        # Ensure session exists in ADK memory
        session = await _session_service.get_session(
            app_name="kaiops", 
            user_id=user_id, 
            session_id=session_id
        )
        
        if not session:
            logger.info(f"🆕 Creating new ADK session for {session_id}")
            await _session_service.create_session(
                app_name="kaiops", 
                user_id=user_id, 
                session_id=session_id
            )
        
        # Create Content object for the message
        user_content = Content(role="user", parts=[Part(text=message)])
        
        logger.info(f"🚀 Invoking root agent...")
        # Run the agent and collect responses
        response_text = await _run_agent_session(_runner, user_id, session_id, user_content)
        
        if not response_text:
            logger.warning("⚠️ Agent returned empty response")
            response_text = "No response generated. Please try your query again."
        
        logger.info(f"✅ Agent response received: {len(response_text)} characters")
        logger.info(f"📝 Response preview: {response_text[:200]}...")
        
        # Preserve formatting - DO NOT strip emojis or markdown
        return {
            "response": response_text,
            "success": True,
            "metadata": {"agent": "root_agent", "response_length": len(response_text)}
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}", exc_info=True)
        return {
            "response": f"An error occurred while processing your request: {str(e)}",
            "success": False,
            "metadata": {"error": str(e)}
        }
