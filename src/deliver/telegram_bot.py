"""Telegram delivery - 1 wiadomosc per skrypt + summary.
Telegram limit: 4096 chars per msg. Skrypt typowo ~1500 chars, mieści się.

Buttony inline: 👍/👎 (rating callback) + Edytuj (link do Vercel panelu).
Wymaga env vars:
- PANEL_URL = base URL panelu (np. https://skala-viral.vercel.app)
- RATING_TOKEN = ten sam token co w panelu (POST /api/ratings)
Jak nie ustawione - bot wysyla wiadomosci BEZ buttonow (legacy mode).
"""
from __future__ import annotations

import asyncio
import html
import logging
import os
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from src.settings import settings

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


def _panel_url() -> Optional[str]:
    u = os.environ.get("PANEL_URL", "").strip().rstrip("/")
    return u or None


def _rating_token() -> Optional[str]:
    t = os.environ.get("RATING_TOKEN", "").strip()
    return t or None


def _build_inline_keyboard(script_id: str) -> Optional[dict]:
    """Zwroc inline_keyboard z 👍/👎 + Edytuj. None jak brak PANEL_URL."""
    panel = _panel_url()
    if not panel:
        return None
    token = _rating_token()
    # URL buttons (nie callback_data) - dziala bez webhook bota.
    # User klika -> Vercel /api/ratings?id=X&rating=1&token=Y -> zwroci HTML "Zapisano".
    up_qs = urlencode({"id": script_id, "rating": "1", "token": token or ""})
    down_qs = urlencode({"id": script_id, "rating": "-1", "token": token or ""})
    return {
        "inline_keyboard": [
            [
                {"text": "👍 Świetne", "url": f"{panel}/api/ratings/click?{up_qs}"},
                {"text": "👎 Słabe", "url": f"{panel}/api/ratings/click?{down_qs}"},
            ],
            [
                {"text": "⚙️ Edytuj preferencje", "url": panel},
            ],
        ]
    }


def _build_summary_keyboard() -> Optional[dict]:
    panel = _panel_url()
    if not panel:
        return None
    return {
        "inline_keyboard": [
            [
                {"text": "🚀 Wygeneruj kolejne", "url": f"{panel}/?action=regen"},
                {"text": "⚙️ Suwaki", "url": panel},
            ],
        ]
    }


def _format_script_html(idx: int, total: int, script: dict, today: str) -> str:
    """Sklada jedna wiadomosc HTML z calym skryptem do Telegrama."""
    hook = html.escape(script.get("hook", ""))
    full = html.escape(script.get("full_script", ""))
    wc = script.get("word_count", "?")
    sec = script.get("estimated_seconds", "?")
    hook_type = html.escape(str(script.get("hook_type", "")))
    persona = html.escape(str(script.get("persona", "")))
    usp = html.escape(str(script.get("usp", "")))
    pkg = script.get("package_id", "?")
    source_url = html.escape(str(script.get("source_url", "")))
    source_title = html.escape(str(script.get("source_title", "")))

    scores = script.get("critic_scores") or {}
    score_line = " | ".join(f"{k}: {v}" for k, v in scores.items()) if scores else "—"
    iterations = script.get("iterations", 1)

    hashtags = script.get("hashtags") or []
    hashtags_str = html.escape(" ".join(hashtags[:20]))

    b_roll = script.get("b_roll_suggestions") or []
    b_roll_lines = []
    for b in b_roll[:6]:
        try:
            b_roll_lines.append(f"<code>{b.get('second', '?')}s</code> - {html.escape(str(b.get('shot', '')))}")
        except AttributeError:
            continue
    b_roll_str = "\n".join(b_roll_lines) if b_roll_lines else "(brak)"

    return (
        f"<b>SKRYPT {idx}/{total}</b> · {today}\n"
        f"<i>persona:</i> {persona} · <i>USP:</i> {usp} · <i>pakiet:</i> {pkg}\n"
        f"<i>hook type:</i> {hook_type} · <i>{wc} slow / ~{sec}s</i> · iter: {iterations}\n"
        f"<i>critic:</i> {score_line}\n"
        f"\n"
        f"<b>HOOK</b>\n{hook}\n\n"
        f"<b>PEŁNY SKRYPT (do nagrania)</b>\n{full}\n\n"
        f"<b>B-ROLL</b>\n{b_roll_str}\n\n"
        f"<b>HASHTAGI</b>\n<code>{hashtags_str}</code>\n\n"
        f"<b>ZRODLO INSPIRACJI</b>\n{source_title}\n{source_url}"
    )


def _format_summary(scripts: list[dict], today: str) -> str:
    lines = [f"<b>SKRYPTY {today}</b> ({len(scripts)} szt.)\n"]
    for i, s in enumerate(scripts, 1):
        hook = html.escape(s.get("hook", ""))
        lines.append(f"{i}. <i>{html.escape(str(s.get('hook_type', '')))}</i>: {hook}")
    return "\n".join(lines)


async def _send(client: httpx.AsyncClient, text: str, reply_markup: Optional[dict] = None) -> dict:
    url = f"{API_BASE}/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": settings.telegram_chat_id,
        "text": text[:4090],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    r = await client.post(url, json=payload)
    if r.status_code >= 400:
        log.error("Telegram error %s: %s", r.status_code, r.text[:300])
    return r.json() if r.content else {}


def _script_id(today: str, idx: int, script: dict) -> str:
    """Unique ID dla skryptu - matchuje filename w scripts/YYYY-MM-DD/."""
    hook_type = script.get("hook_type", "unknown")
    return f"{today}/{idx:02d}-{hook_type}"


async def deliver_scripts(scripts: list[dict], today: str) -> bool:
    """Wysyla 1 wiadomosc per skrypt + 1 summary z buttonami inline."""
    if not settings.has_telegram():
        log.warning("Telegram not configured - skipping delivery")
        return False

    total = len(scripts)
    has_panel = _panel_url() is not None
    if has_panel:
        log.info("Telegram delivery z inline buttons (panel=%s)", _panel_url())
    else:
        log.info("Telegram delivery bez buttonow (PANEL_URL nie ustawione)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        await _send(client, _format_summary(scripts, today), _build_summary_keyboard())
        for i, script in enumerate(scripts, 1):
            text = _format_script_html(i, total, script, today)
            sid = _script_id(today, i, script)
            await _send(client, text, _build_inline_keyboard(sid))
            await asyncio.sleep(0.3)
    log.info("Delivered %d scripts to Telegram chat %s", total, settings.telegram_chat_id)
    return True
