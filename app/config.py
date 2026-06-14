"""Centralised, environment-aware configuration.

Reads from environment variables (prefix ``QC_``) and an optional ``.env`` file.
Validates at import time and fails fast with a clear message if a value is
malformed. No secret is ever hardcoded here — the Anthropic key is read from the
environment and is optional (the app degrades to deterministic reasoning).
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="QC_", env_file=".env", extra="ignore"
    )

    # --- LLM -----------------------------------------------------------------
    # Secret. Optional: when absent the app uses deterministic explanations.
    anthropic_api_key: Optional[str] = None
    llm_model: str = "claude-sonnet-4-20250514"

    # --- Connectors ----------------------------------------------------------
    request_timeout_s: float = Field(default=4.0, gt=0)

    # --- Decision policy -----------------------------------------------------
    abstention_confidence_threshold: float = Field(default=0.55, ge=0, le=1)
    max_acceptable_eta_minutes: int = Field(default=45, gt=0)

    # --- Auth (demo-grade) ---------------------------------------------------
    # Secret used to sign session cookies. If unset, a random per-process secret
    # is generated (sessions then reset on restart). Set QC_SESSION_SECRET in
    # prod, sourced from a secrets manager — never hardcode it.
    session_secret: Optional[str] = None
    auth_db_path: str = "auth.db"
    session_ttl_seconds: int = Field(default=7 * 24 * 3600, gt=0)
    # DEMO ONLY: surface the generated OTP in the API/UI because there is no SMS/
    # email provider wired. MUST be False in production.
    expose_demo_otp: bool = True
    # Set True when served over HTTPS so the session cookie is marked Secure.
    cookie_secure: bool = False

    @property
    def llm_enabled(self) -> bool:
        """True when a non-empty API key is configured."""
        return bool(self.anthropic_api_key and self.anthropic_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Rotated secrets are picked up on restart."""
    return Settings()
