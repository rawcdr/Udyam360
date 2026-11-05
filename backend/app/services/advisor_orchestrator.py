"""Advisor Orchestrator Service for Udyam360.

Coordinates multi-turn dialogue, profile extraction, dependency validation,
recommendation engine invocation, and grounded response delivery.
"""

import logging
from typing import Optional, Dict, Any
from app.schemas.business_profile import BusinessProfile
from app.schemas.advisor import (
    AdvisorStartResponse,
    AdvisorMessageRequest,
    AdvisorMessageResponse,
    ConversationState,
)
from app.services.conversation_service import conversation_service
from app.services.profile_extraction_service import profile_extraction_service
from app.services.advisor_dialogue_service import advisor_dialogue_service
from app.services.recommendation_engine import recommendation_engine
from app.services.advisor_response_service import advisor_response_service

logger = logging.getLogger("udyam360.advisor_orchestrator")


class AdvisorOrchestrator:
    """End-to-end coordinator for conversational onboarding interactions."""

    def __init__(
        self,
        conv_svc=None,
        extract_svc=None,
        dialogue_svc=None,
        rec_eng=None,
        resp_svc=None,
    ):
        self.conversation_service = conv_svc or conversation_service
        self.profile_extraction_service = extract_svc or profile_extraction_service
        self.advisor_dialogue_service = dialogue_svc or advisor_dialogue_service
        self.recommendation_engine = rec_eng or recommendation_engine
        self.response_service = resp_svc or advisor_response_service

    def start_conversation(self) -> AdvisorStartResponse:
        """Initialize a new onboarding session with welcome message."""
        state = self.conversation_service.create_conversation()

        welcome_text = (
            "Namaste! Welcome to Udyam360, your AI Business Advisor for Airtel digital onboarding.\n\n"
            "I'm here to recommend the best telecom, high-speed broadband, cloud billing, and security "
            "solutions tailored to your business.\n\n"
            "To get started, what kind of business do you run, and which city are you located in?"
        )
        self.conversation_service.add_assistant_message(state.conversation_id, welcome_text)

        suggested = [
            "I run a pharmacy in Chennai with 3 staff and need POS & CCTV.",
            "I manage a CA practice in Delhi and need secure fibre & cloud email.",
            "I own a Kirana store in Jaipur looking for affordable internet.",
        ]

        return AdvisorStartResponse(
            conversation_id=state.conversation_id,
            welcome_message=welcome_text,
            suggested_prompts=suggested,
        )

    def process_message(self, request: AdvisorMessageRequest) -> AdvisorMessageResponse:
        """Process user message through extraction, validation, and recommendation flow."""
        conv_id = request.conversation_id.strip()
        state = self.conversation_service.get_conversation(conv_id)
        if not state:
            return AdvisorMessageResponse(
                conversation_id=conv_id,
                assistant_message="Session expired or not found. Please start a new conversation.",
                processing_status="ERROR",
                error_detail="Invalid conversation_id",
            )

        user_text = request.message.strip()
        self.conversation_service.add_user_message(conv_id, user_text)

        # 1. Extract Profile Attributes
        extraction_res = self.profile_extraction_service.extract_profile(
            message=user_text,
            existing_profile=state.profile,
        )

        # Handle clarification / adversarial flags
        if extraction_res.clarification_required:
            clarify_reply = self.response_service.generate_clarification_reply(
                extraction_res.clarification_reason
            )
            self.conversation_service.add_assistant_message(conv_id, clarify_reply)
            return AdvisorMessageResponse(
                conversation_id=conv_id,
                assistant_message=clarify_reply,
                extracted_profile=state.profile,
                missing_fields=state.missing_fields,
                clarification_required=True,
                recommendations_available=state.recommendations_available,
                recommendations=state.last_recommendations,
                processing_status="SUCCESS",
            )

        # 2. Merge extracted fields into persistent session profile
        updated_profile, fields_updated = self.conversation_service.merge_extracted_profile(
            conv_id, extraction_res
        )

        # 3. Assess missing fields & readiness
        missing_fields = self.advisor_dialogue_service.identify_missing_fields(updated_profile)
        state.missing_fields = missing_fields
        is_ready = self.advisor_dialogue_service.is_profile_ready_for_recommendations(updated_profile)

        # 4. Generate recommendations or ask follow-up
        if is_ready:
            try:
                recommendations = self.recommendation_engine.generate_recommendations(updated_profile)
                state.recommendations_available = True
                state.last_recommendations = recommendations
                state.status = "recommended"

                assistant_reply = self.response_service.generate_recommendation_reply(
                    profile=updated_profile,
                    recommendations=recommendations,
                    missing_fields=missing_fields,
                    user_message=user_text,
                )
                self.conversation_service.add_assistant_message(conv_id, assistant_reply)

                return AdvisorMessageResponse(
                    conversation_id=conv_id,
                    assistant_message=assistant_reply,
                    extracted_profile=updated_profile,
                    missing_fields=missing_fields,
                    clarification_required=False,
                    recommendations_available=True,
                    recommendations=recommendations,
                    processing_status="SUCCESS",
                )
            except Exception as e:
                logger.error("Recommendation failure: %s", str(e), exc_info=True)
                # Controlled graceful fallback
                fallback_reply = (
                    "I have updated your profile, but encountered a temporary calculation issue. "
                    "Please verify your location and headcount so we can re-evaluate packages."
                )
                self.conversation_service.add_assistant_message(conv_id, fallback_reply)
                return AdvisorMessageResponse(
                    conversation_id=conv_id,
                    assistant_message=fallback_reply,
                    extracted_profile=updated_profile,
                    missing_fields=missing_fields,
                    processing_status="FALLBACK",
                    error_detail=str(e),
                )

        else:
            # Need more details: select next unasked follow-up
            follow_up = self.advisor_dialogue_service.get_focused_follow_up(
                updated_profile, missing_fields
            )
            if follow_up:
                field_name, question_text = follow_up
                self.conversation_service.mark_field_asked(conv_id, field_name)
                assistant_reply = self.response_service.generate_follow_up_reply(
                    profile=updated_profile,
                    question_text=question_text,
                    user_message=user_text,
                )
            else:
                assistant_reply = "Could you tell me more about your business type and requirements?"

            self.conversation_service.add_assistant_message(conv_id, assistant_reply)
            return AdvisorMessageResponse(
                conversation_id=conv_id,
                assistant_message=assistant_reply,
                extracted_profile=updated_profile,
                missing_fields=missing_fields,
                clarification_required=False,
                recommendations_available=False,
                recommendations=None,
                processing_status="SUCCESS",
            )


advisor_orchestrator = AdvisorOrchestrator()

