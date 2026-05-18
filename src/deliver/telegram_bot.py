"""Telegram delivery - 1 wiadomosc per skrypt + summary.
Telegram limit: 4096 chars per msg. Skrypt typowo ~1500 chars, mieści się.
"""
from __future__ import annotations

import asyncio
import html
import logging
from typing import Any

import httpx

from src.settings import settings

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


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


async def _send(client: httpx.AsyncClient, text: str) -> dict:
    url = f"{API_BASE}/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text[:4090],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = await client.post(url, json=payload)
    if r.status_code >= 400:
        log.error("Telegram error %s: %s", r.status_code, r.text[:300])
    return r.json() if r.content else {}


async def deliver_scripts(scripts: list[dict], today: str) -> bool:
    """Wysyla 1 wiadomosc per skrypt + 1 summary. True jezeli wszystko OK."""
    if not settings.has_telegram():
        log.warning("Telegram not configured - skipping delivery")
        return False

    total = len(scripts)
    async with httpx.AsyncClient(timeout=30.0) as client:
        # summary first - widzisz od razu listę hooks
        await _send(client, _format_summary(scripts, today))
        for i, script in enumerate(scripts, 1):
            text = _format_script_html(i, total, script, today)
            await _send(client, text)
            await asyncio.sleep(0.3)  # Telegram rate limit gentle pacing
    log.info("Delivered %d scripts to Telegram chat %s", total, settings.telegram_chat_id)
    return True
