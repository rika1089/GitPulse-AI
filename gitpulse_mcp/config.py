"""
config.py
---------
Single source of truth for all runtime settings.

Changes from original:
  - OpenAI replaced with Groq (GROQ_API_KEY, GROQ_MODEL)
  - .env file is searched from the project root upward so uvicorn
    launched from any subdirectory still finds it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    """
    Walk up from this file's location until we find a .env file.
    Handles running uvicorn from gitpulse_mcp/ OR from GitPulseAI/.
    """
    current = Path(__file__).resolve().parent
    for _ in range(4):                        # search up to 4 levels up
        candidate = current / ".env"
        if candidate.exists():
            return str(candidate)
        current = current.parent
    # Fallback — pydantic-settings will raise a clear error if still missing
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- GitHub ---
    github_token: str = Field(..., description="GitHub Personal Access Token")
    github_api_version: str = Field(default="2022-11-28")
    github_base_url: str = Field(default="https://api.github.com")

    # --- Groq (replaces OpenAI) ---
    groq_api_key: str = Field(..., description="Groq API key (https://console.groq.com)")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model. Fast options: llama-3.1-8b-instant, mixtral-8x7b-32768",
    )
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")

    # --- Health scoring weights (must sum to 1.0) ---
    weight_commit_freq: float = Field(default=0.30, ge=0.0, le=1.0)
    weight_pr_merge_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_issue_close_rate: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_contributor_activity: float = Field(default=0.20, ge=0.0, le=1.0)

    # --- Metric lookback ---
    activity_lookback_days: int = Field(default=30, ge=1)

    # --- Cache ---
    cache_ttl_seconds: int = Field(default=300, ge=0)

    # --- HTTP timeouts ---
    github_timeout_seconds: float = Field(default=30.0, ge=1.0)
    github_max_retries: int = Field(default=3, ge=0)

    @field_validator("weight_commit_freq")
    @classmethod
    def _check_weight(cls, v: float) -> float:
        return v

    def model_post_init(self, __context) -> None:  # noqa: ANN001
        total = (
            self.weight_commit_freq
            + self.weight_pr_merge_ratio
            + self.weight_issue_close_rate
            + self.weight_contributor_activity
        )
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Health scoring weights must sum to 1.0, got {total:.4f}. "
                "Check WEIGHT_* variables in your .env file."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
