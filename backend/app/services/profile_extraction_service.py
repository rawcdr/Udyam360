"""Profile Extraction Service for Udyam360.

Extracts structured business profile attributes from natural language user dialogue
using Gemini structured JSON output with deterministic heuristic fallback.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from google.genai import types

from app.core.config import settings
from app.schemas.business_profile import BusinessProfile, normalize_segment_string
from app.schemas.advisor import ExtractedProfileData, ProfileExtractionResult
from app.services.llm_service import llm_service

logger = logging.getLogger("udyam360.profile_extraction")

# Known Indian city tier mapping for verified tier identification
KNOWN_TIER_1_CITIES = {
    "delhi", "new delhi", "mumbai", "bengaluru", "bangalore",
    "hyderabad", "chennai", "kolkata", "pune", "ahmedabad"
}
KNOWN_TIER_2_CITIES = {
    "jaipur", "lucknow", "indore", "chandigarh", "coimbatore",
    "nagpur", "bhopal", "patna", "vadodara", "surat", "kochi",
    "cochin", "kanpur", "agra", "varanasi", "visakhapatnam",
    "ludhiana", "nashik", "madurai", "meerut", "rajkot", "kota"
}


def resolve_city_tier(city: Optional[str]) -> Optional[int]:
    """Map city to tier if confidently known, else return None without guessing."""
    if not city:
        return None
    c = city.strip().lower()
    if c in KNOWN_TIER_1_CITIES:
        return 1
    if c in KNOWN_TIER_2_CITIES:
        return 2
    return None


EXTRACTION_SYSTEM_INSTRUCTION = """
You are an expert MSME profiling assistant for Airtel / Accel Business onboarding in India.
Your job is to extract structured business profile information from customer dialogue.

CRITICAL RULES:
1. Extract ONLY what the user explicitly stated or directly corrected.
2. DO NOT invent, assume, or hallucinate missing information.
3. If headcount is not mentioned, employee_count must be null.
4. If location is not mentioned, city and city_tier must be null.
5. If GSTIN or Udyam registration is not explicitly affirmed or denied, set has_gstin/has_udyam to null.
6. If the user corrects an earlier statement (e.g. 'Actually 3 employees, not 5'), return the corrected value.
7. If the user provides conflicting or ambiguous statements, flag clarification_required = true with a clear reason.
8. Set business_segment to 'micro' (retail, kirana, salon, pharmacy, shop) or 'prof' (clinic, CA, doctor, coaching, consultancy) if clear, otherwise null.
9. Return valid JSON adhering to the specified schema.
10. If the business name is stated (e.g. 'Neelgiri Physio Clinic', 'Apollo Pharmacy', 'Shri Kirana'), extract it into business_name.
"""


class ProfileExtractionService:
    """Extracts and updates customer profile fields from conversation turns."""

    def __init__(self, llm_svc=None):
        self.llm_service = llm_svc or llm_service

    def extract_profile(
        self, message: str, existing_profile: Optional[BusinessProfile] = None
    ) -> ProfileExtractionResult:
        """Parse natural language message and return extracted fields and confidence."""
        if not message or not message.strip():
            return ProfileExtractionResult(
                extracted_profile=ExtractedProfileData(),
                fields_updated=[],
                missing_fields=[],
            )

        # Check for obvious prompt injection or jailbreak attempts
        if self._is_adversarial_input(message):
            logger.warning("Adversarial or prompt injection attempt intercepted.")
            return ProfileExtractionResult(
                extracted_profile=ExtractedProfileData(),
                fields_updated=[],
                missing_fields=[],
                clarification_required=True,
                clarification_reason="The request appears off-topic or violates safety guidelines. Please describe your business needs.",
            )

        # Attempt Gemini structured extraction if enabled
        if settings.ADVISOR_ENABLED and self.llm_service.api_key:
            try:
                gemini_res = self._extract_with_gemini(message, existing_profile)
                if gemini_res:
                    return gemini_res
            except Exception as e:
                logger.warning("Gemini extraction failed (%s: %s). Falling back to deterministic extractor.", type(e).__name__, str(e))

        # Deterministic regex and keyword fallback
        return self._extract_with_fallback(message, existing_profile)

    def _extract_with_gemini(
        self, message: str, existing_profile: Optional[BusinessProfile]
    ) -> Optional[ProfileExtractionResult]:
        """Call Gemini Developer API requesting structured JSON output."""
        client = self.llm_service.get_client()

        existing_context = ""
        if existing_profile:
            existing_dict = existing_profile.model_dump(exclude_none=True)
            if existing_dict:
                existing_context = f"CURRENT CONFIRMED PROFILE STATE: {json.dumps(existing_dict)}\n"

        prompt = f"""
{existing_context}
USER MESSAGE:
\"\"\"{message}\"\"\"

Extract updated fields and output JSON.
"""
        config = types.GenerateContentConfig(
            system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ExtractedProfileData,
            temperature=0.0,
        )

        response = client.models.generate_content(
            model=self.llm_service.model_name,
            contents=prompt,
            config=config,
        )

        if not response.text:
            return None

        data = json.loads(response.text)
        extracted = ExtractedProfileData(**data)

        # Automatically resolve city_tier if city was provided but tier left null
        if extracted.city and extracted.city_tier is None:
            extracted.city_tier = resolve_city_tier(extracted.city)

        # Track which fields were extracted in this turn
        updated_fields: List[str] = []
        confidences: Dict[str, float] = {}

        for field_name, value in extracted.model_dump(exclude_none=True).items():
            if value is not None and (not isinstance(value, list) or len(value) > 0):
                updated_fields.append(field_name)
                confidences[field_name] = 0.95

        return ProfileExtractionResult(
            extracted_profile=extracted,
            fields_updated=updated_fields,
            missing_fields=[],
            confidence_by_field=confidences,
            clarification_required=False,
            clarification_reason=None,
        )

    def _extract_with_fallback(
        self, message: str, existing_profile: Optional[BusinessProfile]
    ) -> ProfileExtractionResult:
        """Deterministic regex and keyword extractor for zero-LLM / fallback scenarios."""
        text = message.lower()
        extracted = ExtractedProfileData()
        updated_fields = []
        confidences = {}

        # 0. Business Name: e.g. "I run Neelgiri Physio Clinic in Delhi", "I have a clinic called Apollo Care Pharmacy"
        name_match = re.search(
            r"\b(?:i run|we run|run|shop is|clinic is|firm is|called|named|business is|my business is)\s+([A-Z0-9][A-Za-z0-9\s&'\.\-]+?)(?:\s+(?:in|at|with|near|for|\.|\,|$|\n))",
            message,
            re.IGNORECASE,
        )
        if name_match:
            candidate_name = name_match.group(1).strip()
            if 2 <= len(candidate_name.split()) <= 6 and not candidate_name.lower().startswith(("a ", "an ", "the ")):
                extracted.business_name = candidate_name.title()
                updated_fields.append("business_name")
                confidences["business_name"] = 0.90

        # 1. Employee Count: e.g. "3 employees", "five staff", "team of five", "team of 5", "headcount of 4"
        num_word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        emp_match = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(employees|staff|workers|people|members)", text)
        if not emp_match:
            emp_match = re.search(r"\b(?:team of|headcount of|having)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", text)
        if emp_match:
            raw_val = emp_match.group(1)
            emp_cnt = int(raw_val) if raw_val.isdigit() else num_word_map.get(raw_val, 1)
            extracted.employee_count = emp_cnt
            updated_fields.append("employee_count")
            confidences["employee_count"] = 0.90

        # 2. Number of Sites / Premises: e.g. "1 shop", "2 branches", "single store"
        if re.search(r"\b(single shop|one store|one shop|1 shop|1 location|1 branch|single branch)\b", text):
            extracted.num_sites = 1
            updated_fields.append("num_sites")
            confidences["num_sites"] = 0.90
        else:
            site_match = re.search(r"(\d+)\s*(shops|stores|branches|sites|locations)", text)
            if site_match:
                extracted.num_sites = int(site_match.group(1))
                updated_fields.append("num_sites")
                confidences["num_sites"] = 0.90

        # 3. Monthly Budget: e.g. "budget is ₹5,000", "₹3,000", "budget 3000", "5000 per month"
        budget_match = re.search(r"(?:budget\s*(?:is|of|around)?\s*)?(?:rs\.?|inr|₹)\s*([\d,]+)", text)
        if not budget_match:
            budget_match = re.search(r"(?:budget|spend|pay)\s*(?:is|of|around)?\s*([\d,]+)", text)
        if budget_match:
            try:
                clean_num = float(budget_match.group(1).replace(",", ""))
                if 200 <= clean_num <= 500000:
                    extracted.monthly_budget_inr = clean_num
                    updated_fields.append("monthly_budget_inr")
                    confidences["monthly_budget_inr"] = 0.90
            except ValueError:
                pass

        # 4. Business Type & Segment
        if any(w in text for w in ["pharmacy", "chemist", "medical store"]):
            extracted.business_type = "Pharmacy"
            extracted.business_segment = "micro"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95
        elif any(w in text for w in ["kirana", "grocery", "provision", "general store"]):
            extracted.business_type = "Kirana Store"
            extracted.business_segment = "micro"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95
        elif any(w in text for w in ["salon", "spa", "parlour", "beauty"]):
            extracted.business_type = "Salon"
            extracted.business_segment = "micro"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95
        elif any(w in text for w in ["clinic", "hospital", "doctor", "dentist", "dental"]):
            extracted.business_type = "Clinic"
            extracted.business_segment = "prof"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95
        elif any(w in text for w in ["ca practice", "ca firm", "chartered accountant", "tax advisory", "accounting"]):
            extracted.business_type = "CA Practice"
            extracted.business_segment = "prof"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95
        elif any(w in text for w in ["coaching", "tuition", "institute", "academy"]):
            extracted.business_type = "Coaching Centre"
            extracted.business_segment = "prof"
            updated_fields.extend(["business_type", "business_segment"])
            confidences["business_type"] = 0.95

        # 5. City & Tier
        all_cities = list(KNOWN_TIER_1_CITIES) + list(KNOWN_TIER_2_CITIES)
        for city_name in all_cities:
            if re.search(r"\b" + re.escape(city_name) + r"\b", text):
                extracted.city = city_name.capitalize()
                extracted.city_tier = resolve_city_tier(city_name)
                updated_fields.extend(["city", "city_tier"])
                confidences["city"] = 0.95
                break

        # 6. GSTIN status - check negative declarations FIRST
        if re.search(r"\b(no gst|without gst|not registered for gst|don't have gst|dont have gst|no gstin|do not have gst)\b", text):
            extracted.has_gstin = False
            updated_fields.append("has_gstin")
            confidences["has_gstin"] = 0.90
        elif re.search(r"\b(have gst|have gstin|gst registered|gst active|registered under gst|with gst)\b", text):
            extracted.has_gstin = True
            updated_fields.append("has_gstin")
            confidences["has_gstin"] = 0.90

        # 7. Required Services & Keywords
        services = []
        if re.search(r"\b(pos|billing|cash counter)\b", text):
            services.append("pos")
        if re.search(r"\b(cctv|camera|surveillance)\b", text):
            services.append("cctv")
        if re.search(r"\b(internet|broadband|wifi|wi-fi|fibre|fiber)\b", text):
            services.append("broadband")
        if re.search(r"\b(backup|cloud backup|data backup)\b", text):
            services.append("backup")
        if re.search(r"\b(email|office suite|custom domain|m365|google workspace)\b", text):
            services.append("email")
        if re.search(r"\b(security|antivirus|endpoint|firewall)\b", text):
            services.append("security")
        if re.search(r"\b(whatsapp|sms|marketing)\b", text):
            services.append("whatsapp")

        if services:
            extracted.required_services = services
            updated_fields.append("required_services")
            confidences["required_services"] = 0.85

        return ProfileExtractionResult(
            extracted_profile=extracted,
            fields_updated=list(set(updated_fields)),
            missing_fields=[],
            confidence_by_field=confidences,
            clarification_required=False,
            clarification_reason=None,
        )

    def _is_adversarial_input(self, message: str) -> bool:
        """Detect prompt injection and malicious boundary probes."""
        text = message.lower()
        patterns = [
            r"ignore (all )?previous instructions",
            r"reveal (your )?system prompt",
            r"give me all customer records",
            r"dump (the )?database",
            r"system:\s*override",
            r"<script>",
            r"exec\(",
            r"eval\(",
        ]
        return any(re.search(p, text) for p in patterns)


profile_extraction_service = ProfileExtractionService()
