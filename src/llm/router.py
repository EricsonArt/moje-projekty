"""Router LLM - tries providers in order, fallbacks on rate limit / error.

W Fazie 1: Gemini -> Groq fallback. W Fazie 2 dolaczamy Cerebras + OpenRouter.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from src.llm.providers import (
    GeminiProvider,
    GroqProvider,
    LLMResponse,
    ProviderError,
    RateLimitError,
)
from src.settings import settings

log = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self.providers = []
        if settings.gemini_api_key:
            self.providers.append(GeminiProvider(settings.gemini_api_key))
        if settings.groq_api_key:
            self.providers.append(GroqProvider(settings.groq_api_key))
        if not self.providers:
            raise RuntimeError(
                "No LLM providers configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env"
            )

    async def call_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        last_err: Optional[Exception] = None
        for prov in self.providers:
            try:
                resp = await prov.call(prompt, temperature=temperature, max_tokens=max_tokens)
                log.info(
                    "LLM ok provider=%s tokens=%d/%d",
                    resp.provider, resp.prompt_tokens, resp.completion_tokens,
                )
                return resp
            except RateLimitError as e:
                log.warning("Provider %s rate-limited, trying next: %s", prov.name, e)
                last_err = e
            except ProviderError as e:
                log.warning("Provider %s failed: %s", prov.name, e)
                last_err = e
        raise RuntimeError(f"All providers failed. Last error: {last_err}")

    async def call_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> tuple[dict | list, LLMResponse]:
        """Wywoluje LLM z proba uzyskania JSON. Parsuje z fallback do tolerancyjnego extraction."""
        last_err: Optional[Exception] = None
        for prov in self.providers:
            try:
                resp = await prov.call(
                    prompt, temperature=temperature, max_tokens=max_tokens, json_mode=True
                )
                parsed = _extract_json(resp.text)
                log.info(
                    "LLM-json ok provider=%s tokens=%d/%d",
                    resp.provider, resp.prompt_tokens, resp.completion_tokens,
                )
                return parsed, resp
            except RateLimitError as e:
                log.warning("Provider %s rate-limited, trying next: %s", prov.name, e)
                last_err = e
            except (ProviderError, json.JSONDecodeError, ValueError) as e:
                log.warning("Provider %s failed (json mode): %s", prov.name, e)
                last_err = e
        raise RuntimeError(f"All providers failed (json mode). Last error: {last_err}")


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json(text: str) -> dict | list:
    """LLM moze owinac JSON w markdown code fence albo dorzucic preface text.
    Probuje znalezc i sparsowac."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try first {...} or [...] block
    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract JSON from text: {text[:200]}")
