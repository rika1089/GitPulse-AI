"""
llm/client.py
-------------
OpenAI API wrapper with structured JSON output, retry logic, and prompt loading.

Design decisions:
  - All prompts are loaded from .txt template files — easy to edit without
    touching Python code.
  - We always request JSON-only responses and parse with pydantic's
    model_validate_json. On parse failure we retry once with an explicit
    correction message before raising.
  - The client is provider-agnostic at the interface level — swap the
    underlying call in _call_api() to use Anthropic, Gemini, etc.
  - Temperature is 0.2 for health/triage (deterministic scoring) and
    0.4 for reviews (allows more varied feedback language).
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

# Directory containing .txt prompt templates
_PROMPTS_DIR = Path(__file__).parent / "prompts"


class LLMError(Exception):
    """Raised when the LLM returns unparseable output after retries."""


class LLMClient:
    """
    Async wrapper around OpenAI's chat completions API.

    Usage:
        client = LLMClient()
        result = await client.generate(
            prompt_name="health_narrative",
            variables={"metrics_json": json.dumps(metrics)},
            response_model=HealthNarrativeResponse,
        )
    """

    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
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
        Generate a structured LLM response and parse it into `response_model`.

        Args:
            prompt_name:    Filename (without .txt) in llm/prompts/
            variables:      Dict of {placeholder: value} to substitute into prompt
            response_model: Pydantic model to parse the JSON response into
            temperature:    0.0–1.0 (lower = more deterministic)

        Returns:
            Parsed instance of response_model.

        Raises:
            LLMError: If parsing fails after 1 retry.
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
        """
        Generate an LLM response and return it as a raw dict.
        Used when the response schema varies (e.g. per-file reviews).
        """
        prompt = self._load_prompt(prompt_name, variables)
        raw_json = await self._call_with_retry(prompt, temperature)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM returned invalid JSON: {exc}\nRaw: {raw_json[:500]}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_prompt(self, prompt_name: str, variables: dict[str, str]) -> str:
        """Load and interpolate a prompt template from the prompts directory."""
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
                f"Prompt '{prompt_name}' requires variable {exc} which was not provided. "
                f"Provided variables: {list(variables.keys())}"
            ) from exc

    async def _call_with_retry(self, prompt: str, temperature: float) -> str:
        """
        Call the LLM API. On JSON parse failure, retry once with correction.
        Returns raw text content from the model.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise JSON-generating assistant. "
                    "Always respond with valid JSON only. "
                    "No markdown code fences. No explanations outside the JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        raw = await self._call_api(messages, temperature)

        # Quick validation — if it parses as JSON we're done
        try:
            json.loads(raw)
            return raw
        except json.JSONDecodeError:
            pass

        # Retry with correction message
        logger.warning("LLM returned invalid JSON on first attempt. Retrying with correction.")
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                "Your response was not valid JSON. "
                "Please respond with ONLY the JSON object, no other text, "
                "no markdown, no code fences."
            ),
        })

        raw = await self._call_api(messages, temperature=0.0)  # zero temp for correction
        return raw

    async def _call_api(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        """Raw OpenAI API call. Swap this method to change providers."""
        response = await self._openai.chat.completions.create(
            model=settings.openai_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=2000,
            response_format={"type": "json_object"},  # GPT-4o feature for guaranteed JSON
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    @staticmethod
    def _parse_response(raw_json: str, model: Type[T]) -> T:
        """Parse raw JSON string into the given Pydantic model."""
        # Strip json fences in case the model ignored our instructions
        cleaned = raw_json.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        try:
            return model.model_validate_json(cleaned)
        except Exception as exc:
            raise LLMError(
                f"Failed to parse LLM response into {model.__name__}: {exc}\n"
                f"Raw JSON (first 500 chars): {cleaned[:500]}"
            ) from exc


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Return the shared LLMClient singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
