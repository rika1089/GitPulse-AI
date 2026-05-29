"""
config.py
---------
Single source of truth for all runtime settings.
Loaded once at import time; all modules reference `settings`.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- GitHub ---
    github_token: str = Field(..., description="GitHub Personal Access Token")
    github_api_version: str = Field(
        default="2022-11-28", description="GitHub API version header"
    )
    github_base_url: str = Field(
        default="https://api.github.com", description="GitHub REST API base URL"
    )

    # --- OpenAI ---
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(
        default="gpt-4o-mini", description="LLM model for report generation"
    )

    # --- Health scoring weights (must sum to 1.0) ---
    weight_commit_freq: float = Field(default=0.30, ge=0.0, le=1.0)
    weight_pr_merge_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_issue_close_rate: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_contributor_activity: float = Field(default=0.20, ge=0.0, le=1.0)

    # --- Metric lookback ---
    activity_lookback_days: int = Field(
        default=30, ge=1, description="Days to look back for commit/activity metrics"
    )

    # --- Cache ---
    cache_ttl_seconds: int = Field(
        default=300, ge=0, description="Session cache TTL in seconds (0 = disable)"
    )

    # --- HTTP timeouts ---
    github_timeout_seconds: float = Field(default=30.0, ge=1.0)
    github_max_retries: int = Field(default=3, ge=0)

    @field_validator("weight_commit_freq")
    @classmethod
    def weights_sum_to_one(cls, v: float, info) -> float:  # noqa: ANN001
        """
        Deferred validation: runs only when all weight fields are available.
        Actual sum check is done in __post_init__ below because pydantic
        validators run per-field, not across all fields simultaneously.
        We keep the per-field range checks here and do the sum check on the
        model itself.
        """
        return v

    def model_post_init(self, __context) -> None:  # noqa: ANN001
        total = (
            self.weight_commit_freq
            + self.weight_pr_merge_ratio
            + self.weight_issue_close_rate
            + self.weight_contributor_activity
        )
        if not (0.99 <= total <= 1.01):  # allow float rounding tolerance
            raise ValueError(
                f"Health scoring weights must sum to 1.0, got {total:.4f}. "
                "Check WEIGHT_* variables in your .env file."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.
    Use this everywhere instead of instantiating Settings() directly.

    Example:
        from gitpulse_mcp.config import get_settings
        settings = get_settings()
        print(settings.openai_model)
    """
    return Settings()  # type: ignore[call-arg]


# Convenience alias — import `settings` directly for brevity
settings = get_settings()
