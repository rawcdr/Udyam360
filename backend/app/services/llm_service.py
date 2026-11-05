"""LLM Service wrapper for Google Gemini Developer API.

Provides client lifecycle management, configurable model selection,
minimal text generation, safe logging without secret leakage, and
health verification without making unrequested API calls.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import errors


# Configure safe logger
logger = logging.getLogger("udyam360.llm_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class GeminiLLMService:
    """Manages Gemini API client lifecycle and text generation interactions."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._load_environment()
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self._client: Optional[genai.Client] = None

    @staticmethod
    def _load_environment() -> None:
        """Find and load environment variables safely from .env candidate paths."""
        candidates = [
            Path(".env"),
            Path("backend/.env"),
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
        ]
        for p in candidates:
            if p.exists():
                load_dotenv(dotenv_path=p)
                return
        load_dotenv()

    def get_client(self) -> genai.Client:
        """Lazily initialize and return the official Google GenAI client."""
        if self._client is None:
            if not self.api_key:
                logger.error("Attempted to initialize Gemini client without GEMINI_API_KEY")
                raise ValueError("GEMINI_API_KEY is not set. Please configure backend/.env.")
            
            logger.info("Initializing Google GenAI client for model: %s", self.model_name)
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def check_health(self) -> Dict[str, Any]:
        """Health check that validates configuration and client initialization readiness.
        
        Does NOT execute an API call during routine checks to preserve quota and avoid costs.
        """
        has_key = bool(self.api_key)
        return {
            "status": "HEALTHY" if has_key else "DEGRADED",
            "api_key_configured": has_key,
            "configured_model": self.model_name,
            "provider": "google-gemini",
        }

    def generate_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text from the Gemini model with robust exception handling.
        
        Only called when explicitly requested.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt content cannot be empty.")

        client = self.get_client()
        logger.info("Sending text generation request to model: %s", self.model_name)

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            response_text = response.text.strip() if response.text else ""
            meta = getattr(response, "usage_metadata", None)

            token_usage = {
                "prompt_tokens": getattr(meta, "prompt_token_count", None) if meta else None,
                "candidates_tokens": getattr(meta, "candidates_token_count", None) if meta else None,
                "total_tokens": getattr(meta, "total_token_count", None) if meta else None,
            }

            return {
                "success": True,
                "text": response_text,
                "model": self.model_name,
                "token_usage": token_usage,
            }

        except errors.ClientError as e:
            status_code = getattr(e, "code", None)
            message = getattr(e, "message", str(e))
            logger.error("Gemini API Client Error (%s): %s", status_code, message)

            if status_code == 429:
                return {
                    "success": False,
                    "error_type": "RateLimitOrQuotaExhausted",
                    "status_code": 429,
                    "message": "Free-tier quota limit reached or rate limit exceeded. Retry later.",
                }

            return {
                "success": False,
                "error_type": "ClientError",
                "status_code": status_code,
                "message": message,
            }

        except errors.ServerError as e:
            status_code = getattr(e, "code", None)
            message = getattr(e, "message", str(e))
            logger.error("Gemini API Server Error (%s): %s", status_code, message)
            return {
                "success": False,
                "error_type": "ServerError",
                "status_code": status_code,
                "message": message,
            }

        except Exception as e:
            logger.error("Unexpected error in LLM service: %s: %s", type(e).__name__, str(e))
            return {
                "success": False,
                "error_type": type(e).__name__,
                "message": str(e),
            }


# Singleton service helper
llm_service = GeminiLLMService()
