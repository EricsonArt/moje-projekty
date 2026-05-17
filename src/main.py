"""Pelen pipeline MVP - uruchamiany przez `python -m src.main`.

Flow:
1. Load configs
2. Read data/swipe-file.txt - lista linkow YT
3. yt-dlp fetch metadata + auto-subs
4. Parse VTT do plain text
5. Topic Picker - dzien tygodnia -> persona/USP/pakiet
6. Per skrypt:
   - Pick random source viral (z dostepnych)
   - Pick hook_variant (rozny per skrypt)
   - Generate -> Critic loop (max 3 iteracji)
7. Telegram delivery + zapis do scripts/YYYY-MM-DD/
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import logging
import random
import sys
from pathlib import Path

from src.critic.pipeline import critique
from src.deliver.git_commit import save_scripts_to_disk
from src.deliver.telegram_bot import deliver_scripts
from src.generate.pipeline import (
    HOOK_VARIANTS,
    generate_one_script,
    load_configs,
    pick_topic_for_today,
)
from src.llm.router import LLMRouter
from src.scrape.swipe_file import filter_supported, parse_swipe_file
from src.scrape.youtube import fetch_many, YoutubeVideo
from src.settings import DATA_DIR, settings
from src.transcribe.auto_subs import parse_vtt

log = logging.getLogger(__name__)

MAX_CRITIC_ITERATIONS = 3
MIN_TRANSCRIPT_CHARS = 80  # ponizej tego transkrypt = za krotki, skip


async def _fetch_and_transcribe(urls: list[str]) -> list[tuple[YoutubeVideo, str]]:
    """Sciaga metadata + auto-subs PL, parsuje VTT do tekstu. Zwraca tylko te
    co maja sensowny transkrypt."""
    videos = await fetch_many(urls, concurrency=3)
    out = []
    for v in videos:
        if v.error:
            log.warning("Source video %s failed: %s", v.url, v.error)
            continue
        if not v.transcript_path:
            log.warning("Source video %s has no transcript", v.url)
            continue
        text = parse_vtt(v.transcript_path)
        if len(text) < MIN_TRANSCRIPT_CHARS:
            log.warning(
                "Source video %s transcript too short (%d chars), skipping",
                v.url, len(text),
            )
            continue
        out.append((v, text))
    return out


async def _generate_one_with_critic(
    router: LLMRouter,
    configs: dict,
    topic,
    source: YoutubeVideo,
    source_transcript: str,
    hook_variant: dict,
    script_idx: int,
) -> dict | None:
    """Generuje skrypt, krytykuje, regeneruje max MAX_CRITIC_ITERATIONS razy."""
    banned = configs["user_voice"]["banned_phrases"]
    persona_name = topic.persona_data["name"]

    best_script: dict | None = None
    best_verdict = None

    for iteration in range(1, MAX_CRITIC_ITERATIONS + 1):
        # Pierwsza próba - normalna; kolejne - wyższa temperatura, fresh hook
        temp = 0.85 if iteration == 1 else 0.95
        try:
            script = await generate_one_script(
                router, configs, topic, source, source_transcript, hook_variant, temperature=temp,
            )
        except Exception as e:
            log.error("Script %d iter %d generation failed: %s", script_idx, iteration, e)
            continue

        if not script.get("full_script") or not script.get("hook"):
            log.warning("Script %d iter %d: missing hook/full_script in LLM output", script_idx, iteration)
            continue

        try:
            verdict = await critique(
                router, script, source.title, persona_name, banned,
            )
        except Exception as e:
            log.error("Script %d iter %d critique failed: %s", script_idx, iteration, e)
            # Bez critic - zapisujemy ostatni, wypisujemy w summary
            best_script = script
            best_verdict = None
            break

        log.info(
            "Script %d iter %d verdict=%s scores=%s fails=%s",
            script_idx, iteration, verdict.verdict, verdict.scores, verdict.auto_fails,
        )

        # Track best so far po srednim score
        if best_verdict is None or verdict.total > best_verdict.total:
            best_script = script
            best_verdict = verdict

        if verdict.passed:
            best_script["critic_scores"] = verdict.scores
            best_script["iterations"] = iteration
            return best_script

    # Wszystkie iteracje wyczerpane - graceful degradation
    if best_script:
        best_script["critic_scores"] = best_verdict.scores if best_verdict else {}
        best_script["iterations"] = MAX_CRITIC_ITERATIONS
        best_script["critic_warning"] = (
            best_verdict.specific_fix if best_verdict else "Critic failed - manual review needed"
        )
        log.warning(
            "Script %d: max iterations reached, returning best with avg_score=%.1f",
            script_idx, best_verdict.total if best_verdict else 0.0,
        )
        return best_script

    log.error("Script %d: all iterations failed, dropping", script_idx)
    return None


async def run_pipeline(swipe_file: Path, scripts_per_day: int, today: dt.date) -> list[dict]:
    configs = load_configs()
    log.info("Configs loaded: product, icp, user_voice, niche_keywords")

    # 1. Read swipe file
    links = parse_swipe_file(swipe_file)
    log.info("Swipe file: %d links found", len(links))
    yt_links = filter_supported(links)
    log.info("YouTube links to process: %d", len(yt_links))
    if not yt_links:
        log.error(
            "No YouTube links in swipe file. Edit %s with viral Shorts URLs.",
            swipe_file,
        )
        return []

    # 2. Fetch + transcribe
    urls = [l.url for l in yt_links]
    sources = await _fetch_and_transcribe(urls)
    log.info("Usable sources after transcription: %d", len(sources))
    if not sources:
        log.error("No source videos with usable transcripts - aborting")
        return []

    # 3. Topic picker
    topic = pick_topic_for_today(configs, today)
    log.info(
        "Topic for %s: persona=%s usp=%s package=%s severity=%s angle=%s",
        today, topic.persona_id, topic.usp_id, topic.package_id, topic.cta_severity, topic.angle,
    )

    # 4. Generate N scripts (jeden hook variant per skrypt)
    router = LLMRouter()
    variants = random.sample(HOOK_VARIANTS, k=min(scripts_per_day, len(HOOK_VARIANTS)))

    tasks = []
    for i, variant in enumerate(variants, 1):
        source, transcript = random.choice(sources)
        tasks.append(
            _generate_one_with_critic(router, configs, topic, source, transcript, variant, i)
        )
    results = await asyncio.gather(*tasks, return_exceptions=True)

    scripts: list[dict] = []
    for i, r in enumerate(results, 1):
        if isinstance(r, Exception):
            log.error("Script %d failed: %s", i, r)
            continue
        if r is None:
            continue
        # Wzbogac metadata
        source_used = None
        for src, _t in sources:
            if src.title in r.get("full_script", "") or True:  # match doesn't matter, take first
                source_used = src
                break
        if not source_used:
            source_used = sources[0][0]
        r["persona"] = topic.persona_id
        r["usp"] = topic.usp_id
        r["package_id"] = topic.package_id
        r["source_url"] = source_used.url
        r["source_title"] = source_used.title
        scripts.append(r)

    log.info("Generated %d scripts (out of %d requested)", len(scripts), scripts_per_day)
    return scripts


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description="Viral Content Engine - dzienny run")
    parser.add_argument("--swipe-file", type=Path, default=DATA_DIR / "swipe-file.txt")
    parser.add_argument("--scripts", type=int, default=settings.scripts_per_day)
    parser.add_argument("--date", type=str, default=None, help="Override today's date YYYY-MM-DD")
    parser.add_argument("--no-telegram", action="store_true", help="Skip Telegram delivery")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    _setup_logging(args.debug or settings.debug)

    today = (
        dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    )

    if not settings.has_llm():
        log.error("No LLM API keys set. Add GEMINI_API_KEY or GROQ_API_KEY to .env")
        sys.exit(2)

    log.info(
        "Run: date=%s scripts=%d telegram=%s",
        today, args.scripts, settings.has_telegram() and not args.no_telegram,
    )

    scripts = asyncio.run(run_pipeline(args.swipe_file, args.scripts, today))

    if not scripts:
        log.error("Pipeline returned 0 scripts - check logs above")
        sys.exit(1)

    today_str = today.isoformat()

    # Save to disk (workflow commitnie potem)
    save_scripts_to_disk(scripts, today_str)

    # Send to Telegram unless disabled
    if not args.no_telegram and settings.has_telegram():
        asyncio.run(deliver_scripts(scripts, today_str))
    elif args.no_telegram:
        log.info("--no-telegram flag set, skipping delivery")
    else:
        log.warning("Telegram not configured - scripts saved only to disk")

    log.info("Done. Output: scripts/%s/", today_str)


if __name__ == "__main__":
    main()
