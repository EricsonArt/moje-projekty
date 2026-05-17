"""Provider implementations - bezposrednie REST calls przez httpx.
Brak SDK zeby uniknac konfliktow wersji i utrzymac wszystko lekkie.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


class RateLimitError(ProviderError):
    pass


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class GeminiProvider:
    """Google AI Studio - Gemini 2.5 Flash. Free ~250-500 req/day."""

    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    model = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        self.api_key = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        timeout: float = 90.0,
    ) -> LLMResponse:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        gen_cfg = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": gen_cfg,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
        if r.status_code == 429:
            raise RateLimitError(f"Gemini 429: {r.text[:200]}")
        if r.status_code >= 400:
            raise ProviderError(f"Gemini {r.status_code}: {r.text[:300]}")

        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise ProviderError(f"Gemini empty candidates. Full response: {json.dumps(data)[:300]}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        usage = data.get("usageMetadata") or {}
        return LLMResponse(
            text=text,
            provider=self.name,
            model=self.model,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
        )


class GroqProvider:
    """Groq Cloud - Llama 3.3 70B Versatile. Free ~30 RPM / 14k TPM."""

    name = "groq"
    base_url = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY missing")
        self.api_key = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        timeout: float = 90.0,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(self.base_url, json=payload, headers=headers)
        if r.status_code == 429:
            raise RateLimitError(f"Groq 429: {r.text[:200]}")
        if r.status_code >= 400:
            raise ProviderError(f"Groq {r.status_code}: {r.text[:300]}")

        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(f"Groq empty choices: {json.dumps(data)[:300]}")
        text = (choices[0].get("message") or {}).get("content", "").strip()
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            provider=self.name,
            model=self.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
