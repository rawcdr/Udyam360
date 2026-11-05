"""Gemini Model Discovery Service for Udyam360.

Discovers available Gemini models via Google GenAI SDK, checks for content generation
support, verifies the availability of the preferred model (gemini-3.1-flash-lite),
and reports free-tier validation requirements.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import errors


PREFERRED_MODEL_KEYWORD = "gemini-3.1-flash-lite"


def load_environment() -> None:
    """Find and load environment variables from .env files."""
    candidates = [
        Path(".env"),
        Path("backend/.env"),
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    loaded = False
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p)
            loaded = True
            break
    if not loaded:
        load_dotenv()


def get_genai_client() -> genai.Client:
    """Initialize and return the Google GenAI client using GEMINI_API_KEY."""
    load_environment()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing or empty. Please check your .env file.")
    return genai.Client(api_key=api_key)


def discover_models() -> Dict[str, Any]:
    """Discover available models and verify support for content generation."""
    client = get_genai_client()
    configured_model = os.getenv("GEMINI_MODEL", PREFERRED_MODEL_KEYWORD)

    print("=== GEMINI MODEL DISCOVERY ===")
    print(f"Configured Model in .env: {configured_model}")
    print(f"Preferred Model target: {PREFERRED_MODEL_KEYWORD}")

    try:
        models_pager = client.models.list()
        all_models = list(models_pager)
    except errors.APIError as e:
        print(f"[ERROR] API Error during model listing: {e.message} (code: {e.code})")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error listing models: {type(e).__name__}: {str(e)}")
        raise

    generation_models: List[Dict[str, Any]] = []
    preferred_model_found = False
    preferred_model_info = None

    for model in all_models:
        name = getattr(model, "name", "")
        # Model names often look like "models/gemini-2.5-flash" or "gemini-2.5-flash"
        display_name = getattr(model, "display_name", name)
        supported_actions = getattr(model, "supported_generation_methods", [])
        
        # Check if content generation is supported
        supports_content_generation = True
        if supported_actions:
            supports_content_generation = any("generateContent" in action for action in supported_actions)

        # In google-genai SDK 2.x, some models have supported_actions or description
        description = getattr(model, "description", "")

        model_entry = {
            "name": name,
            "display_name": display_name,
            "supports_generation": supports_content_generation,
            "description": description,
        }

        if supports_content_generation:
            generation_models.append(model_entry)

        # Check match against preferred model or configured model
        clean_name = name.split("/")[-1] if "/" in name else name
        if clean_name.lower() == PREFERRED_MODEL_KEYWORD.lower():
            preferred_model_found = True
            preferred_model_info = model_entry
        elif not preferred_model_found and PREFERRED_MODEL_KEYWORD.lower() in clean_name.lower():
            preferred_model_found = True
            preferred_model_info = model_entry
        elif configured_model.lower() == clean_name.lower():
            configured_match = model_entry

    print(f"\nTotal models retrieved: {len(all_models)}")
    print(f"Models supporting content generation: {len(generation_models)}")

    print(f"\nChecking availability for '{PREFERRED_MODEL_KEYWORD}':")
    if preferred_model_found:
        print(f"  [SUCCESS] Preferred model '{PREFERRED_MODEL_KEYWORD}' is available!")
        if preferred_model_info:
            print(f"  Model identifier: {preferred_model_info['name']}")
    else:
        print(f"  [WARNING] Preferred model '{PREFERRED_MODEL_KEYWORD}' was not found in the models list.")
        print("  Available candidate models supporting content generation:")
        for m in generation_models:
            clean = m["name"].split("/")[-1] if "/" in m["name"] else m["name"]
            if "gemini" in clean.lower():
                print(f"    - {clean} ({m['display_name']})")

    # Free tier eligibility note
    print("\n[NOTE ON FREE TIER ELIGIBILITY]")
    print(
        "Google GenAI SDK model listing exposes model capabilities and limits, but does NOT expose account-level "
        "billing tier or real-time free-tier quota entitlement in the API metadata.\n"
        "Free-tier availability must be confirmed directly in Google AI Studio "
        "(https://aistudio.google.com) under Billing & Rate Limits."
    )

    return {
        "configured_model": configured_model,
        "preferred_model": PREFERRED_MODEL_KEYWORD,
        "preferred_available": preferred_model_found,
        "total_models": len(all_models),
        "generation_models": generation_models,
        "preferred_model_info": preferred_model_info,
    }


if __name__ == "__main__":
    discover_models()
