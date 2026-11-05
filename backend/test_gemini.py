"""Gemini Developer API Connection Test for Udyam360.

Tests connectivity to Google Gemini API using the official google-genai SDK,
verifies environment configuration, prints model info, latency, and token usage,
and handles API exceptions without exposing secrets.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors


TEST_PROMPT = (
    "You are testing the Udyam360 AI development environment. "
    "Reply with exactly: Udyam360 Gemini API connection successful."
)
EXPECTED_REPLY = "Udyam360 Gemini API connection successful."


def load_env_safely() -> None:
    """Load .env from backend/.env or root .env."""
    candidates = [
        Path(".env"),
        Path("backend/.env"),
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(dotenv_path=candidate)
            return
    load_dotenv()


def test_gemini_connection() -> bool:
    """Execute minimal connectivity test against the configured Gemini model."""
    load_env_safely()

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    print("=== UDYAM360 GEMINI API CONNECTION TEST ===")

    if not api_key:
        print("[FAIL] Authentication Error: GEMINI_API_KEY is not set in environment or .env file.")
        print("Please configure your GEMINI_API_KEY in backend/.env before running tests.")
        return False

    if not model_name:
        print("[FAIL] Configuration Error: GEMINI_MODEL is not set in environment or .env file.")
        print("Please configure your GEMINI_MODEL (e.g. gemini-3.1-flash-lite) in backend/.env.")
        return False

    print(f"Selected Model: {model_name}")
    print("Initialising Google GenAI client...")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[FAIL] Client Initialisation Error: {type(e).__name__}: {str(e)}")
        return False

    print(f"Sending test prompt to {model_name}...")
    start_time = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=TEST_PROMPT,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        print(f"\n--- CONNECTION STATUS: SUCCESS ---")
        print(f"Response Latency: {latency_ms:.2f} ms")

        # Response text
        response_text = response.text.strip() if response.text else ""
        print(f"Response Text:\n{response_text}")

        # Match check
        if EXPECTED_REPLY in response_text or response_text == EXPECTED_REPLY:
            print("\n[MATCH] Response text matches expected output exactly.")
        else:
            print(f"\n[NOTE] Response received, though slightly varying from expected string.")

        # Token usage metadata
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            prompt_tokens = getattr(meta, "prompt_token_count", "N/A")
            candidates_tokens = getattr(meta, "candidates_token_count", "N/A")
            total_tokens = getattr(meta, "total_token_count", "N/A")
            print(f"Token Usage Metadata:")
            print(f"  - Prompt tokens: {prompt_tokens}")
            print(f"  - Candidate tokens: {candidates_tokens}")
            print(f"  - Total tokens: {total_tokens}")
        else:
            print("Token Usage Metadata: Not returned in response")

        return True

    except errors.ClientError as e:
        # 4xx errors: Auth, Permission, Invalid Model, Rate Limits / Quotas
        status_code = getattr(e, "code", None)
        message = getattr(e, "message", str(e))

        print(f"\n--- CONNECTION STATUS: FAILED (Client Error {status_code}) ---")

        if status_code == 400:
            print(f"[ERROR] Bad Request / Invalid Model: The model '{model_name}' may be invalid or parameters unsupported.")
            print(f"Details: {message}")
        elif status_code == 401:
            print("[ERROR] Authentication Failure: The provided GEMINI_API_KEY is invalid or expired.")
            print("Please verify your API key in Google AI Studio (https://aistudio.google.com).")
        elif status_code == 403:
            print(f"[ERROR] Permission Denied: The API key does not have permission to access model '{model_name}'.")
            print(f"Details: {message}")
        elif status_code == 404:
            print(f"[ERROR] Model Not Found (404): Model '{model_name}' does not exist or is not available for your project.")
            print("Run 'python backend/app/services/model_discovery.py' to list available models.")
        elif status_code == 429:
            print("[ERROR] Rate Limit Exceeded or Free-Tier Quota Exhausted (429):")
            print(
                "You have reached the free-tier requests per minute (RPM) or requests per day (RPD) limit.\n"
                "STOPPING: Aggressive retries are disabled. Do NOT activate paid billing.\n"
                "Please wait for your free-tier quota window to reset or verify limits in Google AI Studio."
            )
            print(f"Details: {message}")
        else:
            print(f"[ERROR] Client Error ({status_code}): {message}")

        return False

    except errors.ServerError as e:
        # 5xx errors: Server errors
        status_code = getattr(e, "code", None)
        message = getattr(e, "message", str(e))
        print(f"\n--- CONNECTION STATUS: FAILED (Server Error {status_code}) ---")
        print(f"Google Gemini service temporary error: {message}")
        return False

    except errors.APIError as e:
        print(f"\n--- CONNECTION STATUS: FAILED (API Error) ---")
        print(f"API Error ({e.code}): {e.message}")
        return False

    except Exception as e:
        print(f"\n--- CONNECTION STATUS: FAILED (Network or Unexpected Error) ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Details: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_gemini_connection()
    sys.exit(0 if success else 1)

