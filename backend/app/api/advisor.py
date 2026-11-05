"""FastAPI router for Conversational GenAI Business Advisor endpoints."""

from fastapi import APIRouter, HTTPException, Path
from app.core.config import settings
from app.schemas.advisor import (
    AdvisorStartResponse,
    AdvisorMessageRequest,
    AdvisorMessageResponse,
    ConversationState,
)
from app.services.advisor_orchestrator import advisor_orchestrator
from app.services.conversation_service import conversation_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/advisor", tags=["GenAI Business Advisor"])


@router.post("/start", response_model=AdvisorStartResponse, summary="Start a new onboarding conversation")
def start_conversation():
    """Initializes a new isolated onboarding conversation session and returns a welcome greeting."""
    return advisor_orchestrator.start_conversation()


@router.post("/message", response_model=AdvisorMessageResponse, summary="Send message to the advisor")
def send_message(request: AdvisorMessageRequest):
    """Processes user dialogue turn, updates profile, and generates follow-ups or grounded recommendations."""
    return advisor_orchestrator.process_message(request)


@router.get("/conversation/{conversation_id}", response_model=ConversationState, summary="Get conversation state")
def get_conversation(conversation_id: str = Path(..., description="Active conversation identifier")):
    """Retrieves the current structured business profile and message history for a session."""
    state = conversation_service.get_conversation(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Conversation session '{conversation_id}' not found.")
    return state


@router.post("/reset/{conversation_id}", summary="Reset conversation session")
def reset_conversation(conversation_id: str = Path(..., description="Active conversation identifier")):
    """Resets the conversation state and history back to a clean initial profile."""
    success = conversation_service.reset_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation session '{conversation_id}' not found.")
    return {
        "status": "RESET_SUCCESSFUL",
        "conversation_id": conversation_id,
        "message": "Conversation history and business profile have been reset to initial state.",
    }


@router.get("/health", summary="Advisor service health check")
def advisor_health():
    """Returns advisor operational status, LLM provider, and active model without exposing secrets."""
    llm_health = llm_service.check_health()
    return {
        "advisor_enabled": settings.ADVISOR_ENABLED,
        "llm_provider": settings.LLM_PROVIDER,
        "configured_model": settings.GEMINI_MODEL,
        "api_key_configured": llm_health["api_key_configured"],
        "max_history_turns": settings.MAX_CONVERSATION_HISTORY,
        "status": "HEALTHY" if llm_health["api_key_configured"] else "DEGRADED",
    }

