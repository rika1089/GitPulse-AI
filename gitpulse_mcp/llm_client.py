"""
llm/client.py
-------------
Groq API wrapper (OpenAI-compatible endpoint).

Groq exposes an OpenAI-compatible /v1/chat/completions endpoint, so we
use the openai Python SDK pointed at Groq's base URL.
The rest of the code (schemas, services, prompts) is unchanged.

Supported Groq models (set GROQ_MODEL in .env):
  llama-3.3-70b-versatile    ← default, best quality
  llama-3.1-8b-instant       ← fastest, cheapest
  mixtral-8x7b-32768         ← good for long contexts
  gemma2-9b-it               ← lightweight alternative

Rate limits (free tier): 30 req/min, 6000 tokens/min, 14400 req/day
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from gitpulse_mcp.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


class LLMError(Exception):
    """Raised when the LLM returns unparseable output after retries."""


class LLMClient:
    """
    Async wrapper around the Groq API using the OpenAI-compatible endpoint.

    Usage:
        client = LLMClient()
        result = await client.generate(
            prompt_name="health_narrative",
            variables={"metrics_json": json.dumps(metrics)},
            response_model=HealthNarrativeResponse,
        )
    """

    def __init__(self) -> None:
        # Point the openai SDK at Groq's base URL with the Groq API key
        self._client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
        self._prompt_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt_name: str,
        variables: dict[str, str],
        response_model: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """
        Generate a structured LLM response and parse it into response_model.

        Args:
            prompt_name:    Filename (without .txt) in llm/prompts/
            variables:      Dict of {placeholder: value} to substitute
            response_model: Pydantic model to parse the JSON response into
            temperature:    0.0–1.0 (lower = more deterministic)
        """
        prompt = self._load_prompt(prompt_name, variables)
        raw_json = await self._call_with_retry(prompt, temperature)
        return self._parse_response(raw_json, response_model)

    async def generate_raw(
        self,
        prompt_name: str,
        variables: dict[str, str],
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Generate and return as raw dict."""
        prompt = self._load_prompt(prompt_name, variables)
        raw_json = await self._call_with_retry(prompt, temperature)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Groq returned invalid JSON: {exc}\nRaw: {raw_json[:500]}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_prompt(self, prompt_name: str, variables: dict[str, str]) -> str:
        if prompt_name not in self._prompt_cache:
            path = _PROMPTS_DIR / f"{prompt_name}.txt"
            if not path.exists():
                raise FileNotFoundError(
                    f"Prompt template not found: {path}. "
                    f"Available: {[p.stem for p in _PROMPTS_DIR.glob('*.txt')]}"
                )
            self._prompt_cache[prompt_name] = path.read_text(encoding="utf-8")

        template = self._prompt_cache[prompt_name]
        try:
            return template.format(**variables)
        except KeyError as exc:
            raise ValueError(
                f"Prompt '{prompt_name}' requires variable {exc} "
                f"which was not provided. Got: {list(variables.keys())}"
            ) from exc

    async def _call_with_retry(self, prompt: str, temperature: float) -> str:
        """
        Call Groq. On JSON parse failure, retry once with a correction message.

        Note: Groq's API does NOT support response_format={"type":"json_object"}
        on all models, so we instruct via system prompt instead and parse manually.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise JSON-generating assistant. "
                    "ALWAYS respond with a valid JSON object ONLY. "
                    "No markdown code fences (no ```json). "
                    "No explanations. No text before or after the JSON. "
                    "Start your response with { and end with }."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        raw = await self._call_api(messages, temperature)

        # Quick JSON validation
        try:
            json.loads(raw)
            return raw
        except json.JSONDecodeError:
            pass

        # Retry with explicit correction
        logger.warning("Groq returned non-JSON on first attempt — retrying.")
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                "Your response was not valid JSON. "
                "Reply with ONLY the JSON object. "
                "Start with { and end with }. No other text."
            ),
        })
        raw = await self._call_api(messages, temperature=0.0)
        return raw

    async def _call_api(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        """Raw Groq API call via OpenAI-compatible SDK."""
        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,   # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    @staticmethod
    def _parse_response(raw_json: str, model: Type[T]) -> T:
        cleaned = raw_json.strip()
        # Strip accidental markdown fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            return model.model_validate_json(cleaned)
        except Exception as exc:
            raise LLMError(
                f"Failed to parse Groq response into {model.__name__}: {exc}\n"
                f"Raw (first 500 chars): {cleaned[:500]}"
            ) from exc


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
