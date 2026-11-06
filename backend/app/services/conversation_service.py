"""Conversation Management Service for Udyam360.

Maintains multi-turn state, history truncation, profile merging, correction handling,
and strict session isolation in memory.
"""

import uuid
from typing import Dict, Optional, List, Tuple
from app.core.config import settings
from app.schemas.business_profile import BusinessProfile
from app.schemas.advisor import (
    ChatMessage,
    ConversationState,
    ExtractedProfileData,
    ProfileExtractionResult,
)


class ConversationService:
    """Manages active conversation sessions and profile state merging."""

    def __init__(self):
        # In-memory session store: mapping conversation_id -> ConversationState
        self._sessions: Dict[str, ConversationState] = {}
        # Track asked field names to prevent repeated questioning
        self._asked_fields: Dict[str, List[str]] = {}

    def create_conversation(self, conversation_id: Optional[str] = None) -> ConversationState:
        """Create and register a new isolated onboarding conversation session."""
        conv_id = conversation_id.strip() if conversation_id else f"conv_{uuid.uuid4().hex[:12]}"
        state = ConversationState(
            conversation_id=conv_id,
            profile=BusinessProfile(),
            history=[],
            missing_fields=[],
            turn_count=0,
            status="collecting",
        )
        self._sessions[conv_id] = state
        self._asked_fields[conv_id] = []
        return state

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation state by ID."""
        return self._sessions.get(conversation_id.strip())

    def reset_conversation(self, conversation_id: str) -> bool:
        """Reset conversation session to clean initial state."""
        conv_id = conversation_id.strip()
        if conv_id in self._sessions:
            self._sessions[conv_id] = ConversationState(
                conversation_id=conv_id,
                profile=BusinessProfile(),
                history=[],
                missing_fields=[],
                turn_count=0,
                status="collecting",
            )
            self._asked_fields[conv_id] = []
            return True
        return False

    def add_user_message(self, conversation_id: str, message: str) -> None:
        """Record user message in bounded history."""
        state = self.get_conversation(conversation_id)
        if not state:
            raise KeyError(f"Conversation session '{conversation_id}' not found.")

        state.history.append(ChatMessage(role="user", content=message.strip()))
        state.turn_count += 1
        self._truncate_history(state)

    def add_assistant_message(self, conversation_id: str, message: str) -> None:
        """Record assistant reply in bounded history."""
        state = self.get_conversation(conversation_id)
        if not state:
            raise KeyError(f"Conversation session '{conversation_id}' not found.")

        state.history.append(ChatMessage(role="assistant", content=message.strip()))
        self._truncate_history(state)

    def merge_extracted_profile(
        self, conversation_id: str, extraction: ProfileExtractionResult
    ) -> Tuple[BusinessProfile, List[str]]:
        """Safely merge newly extracted fields into existing profile.
        
        Returns:
            (updated_profile, list_of_fields_updated)
        """
        state = self.get_conversation(conversation_id)
        if not state:
            raise KeyError(f"Conversation session '{conversation_id}' not found.")

        cur = state.profile
        ext = extraction.extracted_profile
        updated = []

        # Scalar field updates (allows corrections)
        if getattr(ext, "business_name", None) is not None and ext.business_name != cur.business_name:
            cur.business_name = ext.business_name
            updated.append("business_name")

        if ext.business_type is not None and ext.business_type != cur.business_type:
            cur.business_type = ext.business_type
            updated.append("business_type")

        if ext.business_segment is not None and ext.business_segment != cur.business_segment:
            cur.business_segment = ext.business_segment
            updated.append("business_segment")

        if ext.employee_count is not None and ext.employee_count != cur.employee_count:
            cur.employee_count = ext.employee_count
            updated.append("employee_count")

        if ext.num_sites is not None and ext.num_sites != cur.num_sites:
            cur.num_sites = ext.num_sites
            updated.append("num_sites")

        if ext.city is not None and ext.city != cur.city:
            cur.city = ext.city
            updated.append("city")

        if ext.city_tier is not None and ext.city_tier != cur.city_tier:
            cur.city_tier = ext.city_tier
            updated.append("city_tier")

        if ext.has_gstin is not None and ext.has_gstin != cur.has_gstin:
            cur.has_gstin = ext.has_gstin
            updated.append("has_gstin")

        if ext.has_udyam is not None and ext.has_udyam != cur.has_udyam:
            cur.has_udyam = ext.has_udyam
            updated.append("has_udyam")

        if ext.monthly_budget_inr is not None and ext.monthly_budget_inr != cur.monthly_budget_inr:
            cur.monthly_budget_inr = ext.monthly_budget_inr
            updated.append("monthly_budget_inr")

        # Explicit quantity fields
        if ext.mobile_lines_required is not None and ext.mobile_lines_required != cur.num_lines:
            cur.num_lines = ext.mobile_lines_required
            updated.append("num_lines")

        if ext.number_of_counters is not None and ext.number_of_counters != cur.num_counters:
            cur.num_counters = ext.number_of_counters
            updated.append("num_counters")

        if ext.preferred_language is not None and ext.preferred_language != cur.preferred_language:
            cur.preferred_language = ext.preferred_language
            updated.append("preferred_language")

        # List fields (append new required services)
        if ext.required_services:
            existing_services = set(cur.required_services)
            for req in ext.required_services:
                if req not in existing_services:
                    cur.required_services.append(req)
                    if "required_services" not in updated:
                        updated.append("required_services")

        state.profile = cur
        return cur, updated

    def mark_field_asked(self, conversation_id: str, field_name: str) -> None:
        """Remember that a question about a field has already been posed."""
        if conversation_id in self._asked_fields:
            if field_name not in self._asked_fields[conversation_id]:
                self._asked_fields[conversation_id].append(field_name)

    def was_field_asked(self, conversation_id: str, field_name: str) -> bool:
        """Check if a field was previously asked."""
        return field_name in self._asked_fields.get(conversation_id, [])

    def _truncate_history(self, state: ConversationState) -> None:
        """Ensure conversation history does not exceed configured boundary."""
        max_h = settings.MAX_CONVERSATION_HISTORY
        if len(state.history) > max_h:
            state.history = state.history[-max_h:]


conversation_service = ConversationService()

