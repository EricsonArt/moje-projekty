"""Trending hooks - codzienna analiza scrape'owanych filmow z swipe-file.
Wyciaga top N viralowych hookow z ostatnich 24-48h (lub od ostatniego runa)
i wysyla na Telegram jako oddzielna wiadomosc rano.

Mechanika:
1. Pobierz top filmy z kanalow (Apify TT/IG + yt-dlp YT) - po views
2. Wyciagnij ich opis/title
3. LLM extrahuje pattern hooka (typ: kontrarian/liczba/curiosity_gap/...)
4. Posortuj po views malejaco
5. Wyslij top N na Telegram z linkami do orgynalow
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict

from src.llm.router import LLMRouter
from src.scrape.youtube import YoutubeVideo

log = logging.getLogger(__name__)


@dataclass
class TrendingHook:
    source_url: str
    source_title: str
    source_views: int
    hook_text: str          # ekstraktowany pierwsze 2 zdania
    pattern_type: str       # "kontrarian" | "liczba" | "curiosity_gap" | ...
    platform: str


def _extract_hook_from_text(text: str, max_chars: int = 180) -> str:
    """Najprostsze: pierwsze zdanie do '. ' lub max_chars znakow."""
    if not text:
        return ""
    snippet = text.strip().replace("\n", " ")
    # Spróbuj wyciągnąć pierwsze zdanie
    for sep in (". ", "! ", "? ", ".\n"):
        if sep in snippet[:200]:
            return snippet.split(sep)[0][:max_chars]
    return snippet[:max_chars]


async def classify_hooks_with_llm(
    router: LLMRouter,
    candidates: list[YoutubeVideo],
    top_n: int = 5,
) -> list[TrendingHook]:
    """LLM ekstrahuje pattern hooka z opisu video. Zwroc top N po views."""
    if not candidates:
        return []

    sorted_videos = sorted(candidates, key=lambda v: v.view_count, reverse=True)[: top_n * 2]
    items_text = "\n".join(
        f"{i+1}. [{v.platform} views={v.view_count}] {v.title}\nOpis: {(v.description or '')[:300]}"
        for i, v in enumerate(sorted_videos)
    )

    prompt = f"""Mam {len(sorted_videos)} viralowych krótkich filmów. Wyciagnij z kazdego:
1. Hook (pierwsze 1-2 zdania - to co przyciaga uwage)
2. Typ patternu: jeden z [kontrarian, liczba, transformation, curiosity_gap, hot_take, founder_line, story, list]

FILMY:
{items_text}

ZWROC JSON z tablica obiektow (jeden per film, kolejnosc taka sama jak input):
[{{"hook": "...", "pattern_type": "kontrarian|liczba|..."}}]

ZASADY:
- hook max 180 znakow
- pattern_type musi byc jednym z listy wyzej
"""
    parsed, _ = await router.call_json(prompt, temperature=0.3, max_tokens=2000)

    if not isinstance(parsed, list):
        log.warning("Trending hooks LLM nie zwrocilo listy: %s", str(parsed)[:200])
        return []

    out: list[TrendingHook] = []
    for v, item in zip(sorted_videos, parsed):
        if not isinstance(item, dict):
            continue
        out.append(TrendingHook(
            source_url=v.url,
            source_title=v.title,
            source_views=v.view_count,
            hook_text=str(item.get("hook", _extract_hook_from_text(v.description or v.title))),
            pattern_type=str(item.get("pattern_type", "story")),
            platform=v.platform,
        ))
        if len(out) >= top_n:
            break
    return out


def format_trending_for_telegram(hooks: list[TrendingHook]) -> str:
    """HTML message dla Telegrama z top trending hooks."""
    if not hooks:
        return "<b>TRENDING HOOKS</b>\nBrak danych - swipe-file pusty lub scrape padl."

    lines = ["<b>🔥 TRENDING HOOKS dzisiaj</b>\n"]
    for i, h in enumerate(hooks, 1):
        plat = {"tiktok": "🎵 TT", "instagram": "📷 IG", "youtube": "▶️ YT"}.get(h.platform, "·")
        lines.append(
            f"<b>{i}. [{plat} · {h.pattern_type}]</b>\n"
            f"<i>{h.source_views:,} views</i>\n"
            f"💬 <b>{h.hook_text}</b>\n"
            f"<a href=\"{h.source_url}\">→ oryginal</a>\n"
        )
    return "\n".join(lines)
