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
from src.scrape.apify import (
    apify_available,
    apify_instagram_videos,
    apify_tiktok_videos,
)
from src.scrape.social import (
    cookies_status,
    expand_instagram_channel,
    expand_tiktok_channel,
    fetch_social_many,
    social_pseudo_transcript,
)
from src.scrape.swipe_file import filter_supported, parse_swipe_file
from src.scrape.youtube import expand_channel, fetch_many, YoutubeVideo
from src.settings import DATA_DIR, settings
from src.transcribe.auto_subs import parse_vtt

log = logging.getLogger(__name__)

MAX_CRITIC_ITERATIONS = 3
MIN_TRANSCRIPT_CHARS = 80  # ponizej tego transkrypt = za krotki, skip


async def _empty_sources() -> list[tuple[YoutubeVideo, str]]:
    return []


async def _fetch_and_transcribe_youtube(urls: list[str]) -> list[tuple[YoutubeVideo, str]]:
    """YT: sciaga metadata + auto-subs PL, parsuje VTT. Zwraca tylko te z subami."""
    videos = await fetch_many(urls, concurrency=3)
    out = []
    for v in videos:
        if v.error:
            log.warning("YT source %s failed: %s", v.url, v.error)
            continue
        if not v.transcript_path:
            log.warning("YT source %s has no transcript", v.url)
            continue
        text = parse_vtt(v.transcript_path)
        if len(text) < MIN_TRANSCRIPT_CHARS:
            log.warning("YT %s transcript too short (%d chars), skipping",
                        v.url, len(text))
            continue
        out.append((v, text))
    return out


async def _fetch_social(
    tiktok_urls: list[str], instagram_urls: list[str],
) -> list[tuple[YoutubeVideo, str]]:
    """TT/IG: sciaga metadata przez yt-dlp+cookies. Pseudo-transkrypt = tytul+opis."""
    items: list[tuple[str, str]] = []
    items.extend((u, "tiktok") for u in tiktok_urls)
    items.extend((u, "instagram") for u in instagram_urls)
    if not items:
        return []
    videos = await fetch_social_many(items, concurrency=2)
    out = []
    for v in videos:
        if v.error:
            log.warning("%s source %s failed: %s", v.platform, v.url, v.error)
            continue
        text = social_pseudo_transcript(v)
        if len(text) < MIN_TRANSCRIPT_CHARS:
            log.warning("%s %s pseudo-transcript too short (%d chars), skipping",
                        v.platform, v.url, len(text))
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
    supported = filter_supported(links)
    if not supported:
        log.error(
            "No supported links in %s. Wklejaj YT/TT/IG kanaly lub filmy.",
            swipe_file,
        )
        return []

    yt_channels = [l for l in supported if l.kind == "yt_channel"]
    yt_videos = [l for l in supported if l.kind == "yt_video"]
    tt_channels = [l for l in supported if l.kind == "tt_channel"]
    tt_videos = [l for l in supported if l.kind == "tt_video"]
    ig_channels = [l for l in supported if l.kind == "ig_channel"]
    ig_videos = [l for l in supported if l.kind == "ig_video"]
    log.info(
        "Inputs: YT=%dch+%dv | TT=%dch+%dv | IG=%dch+%dv",
        len(yt_channels), len(yt_videos),
        len(tt_channels), len(tt_videos),
        len(ig_channels), len(ig_videos),
    )

    # 1a. Tryb scraping TT/IG: APIFY ma priorytet, fallback = yt-dlp+cookies
    use_apify = apify_available()
    cookies = await cookies_status()
    if use_apify:
        log.info("APIFY_TOKEN ustawione - TT/IG przez Apify (chmurowy tryb).")
    else:
        if (tt_channels or tt_videos) and not cookies["tiktok"]:
            log.warning(
                "TT linki w swipe-file ale brak cookies i brak APIFY_TOKEN - TT pominiety."
            )
        if (ig_channels or ig_videos) and not cookies["instagram"]:
            log.warning(
                "IG linki w swipe-file ale brak cookies i brak APIFY_TOKEN - IG pominiety."
            )

    # 1b. Expand channels per platform
    yt_urls: list[str] = [l.url for l in yt_videos]
    tt_urls: list[str] = [l.url for l in tt_videos]
    ig_urls: list[str] = [l.url for l in ig_videos]
    # Apify zwraca od razu YoutubeVideo - omijamy fetch_social
    apify_tt_sources: list[tuple[YoutubeVideo, str]] = []
    apify_ig_sources: list[tuple[YoutubeVideo, str]] = []

    if yt_channels:
        yt_expansions = await asyncio.gather(*(
            expand_channel(
                ch.url,
                min_views=settings.channel_min_views,
                max_per_channel=settings.channel_max_shorts_per_channel,
                scan_depth=settings.channel_scan_depth,
            )
            for ch in yt_channels
        ))
        for ch, urls in zip(yt_channels, yt_expansions):
            if not urls:
                log.warning("YT channel %s yielded 0 viral shorts", ch.url)
            yt_urls.extend(urls)

    # TikTok: Apify > cookies > skip
    if tt_channels:
        if use_apify:
            try:
                tt_results = await asyncio.gather(*(
                    apify_tiktok_videos(ch.url, max_videos=settings.channel_max_shorts_per_channel)
                    for ch in tt_channels
                ), return_exceptions=True)
                for ch, vids in zip(tt_channels, tt_results):
                    if isinstance(vids, Exception):
                        log.error("Apify TT %s failed: %s", ch.url, vids)
                        continue
                    for v in vids:
                        text = f"Tytul: {v.title}\nOpis: {v.description}".strip()
                        if len(text) >= MIN_TRANSCRIPT_CHARS:
                            apify_tt_sources.append((v, text))
            except Exception as e:
                log.error("Apify TT global error: %s", e)
        elif cookies["tiktok"]:
            tt_expansions = await asyncio.gather(*(
                expand_tiktok_channel(
                    ch.url,
                    max_per_channel=settings.channel_max_shorts_per_channel,
                    scan_depth=settings.channel_scan_depth,
                )
                for ch in tt_channels
            ))
            for ch, urls in zip(tt_channels, tt_expansions):
                if not urls:
                    log.warning("TT channel %s yielded 0 videos", ch.url)
                tt_urls.extend(urls)

    # Instagram: Apify > cookies > skip
    if ig_channels:
        if use_apify:
            try:
                ig_results = await asyncio.gather(*(
                    apify_instagram_videos(ch.url, max_videos=settings.channel_max_shorts_per_channel)
                    for ch in ig_channels
                ), return_exceptions=True)
                for ch, vids in zip(ig_channels, ig_results):
                    if isinstance(vids, Exception):
                        log.error("Apify IG %s failed: %s", ch.url, vids)
                        continue
                    for v in vids:
                        text = f"Tytul: {v.title}\nOpis: {v.description}".strip()
                        if len(text) >= MIN_TRANSCRIPT_CHARS:
                            apify_ig_sources.append((v, text))
            except Exception as e:
                log.error("Apify IG global error: %s", e)
        elif cookies["instagram"]:
            ig_expansions = await asyncio.gather(*(
                expand_instagram_channel(
                    ch.url,
                    max_per_channel=settings.channel_max_shorts_per_channel,
                    scan_depth=settings.channel_scan_depth,
                )
                for ch in ig_channels
            ))
            for ch, urls in zip(ig_channels, ig_expansions):
                if not urls:
                    log.warning("IG channel %s yielded 0 videos", ch.url)
                ig_urls.extend(urls)

    # Dedup per platform
    def _dedup(urls: list[str]) -> list[str]:
        seen: set[str] = set()
        out = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    yt_urls = _dedup(yt_urls)
    tt_urls = _dedup(tt_urls)
    ig_urls = _dedup(ig_urls)
    log.info(
        "Po dedup: YT=%d, TT(cookies)=%d, IG(cookies)=%d, TT(apify)=%d, IG(apify)=%d",
        len(yt_urls), len(tt_urls), len(ig_urls),
        len(apify_tt_sources), len(apify_ig_sources),
    )

    have_any = bool(yt_urls or tt_urls or ig_urls or apify_tt_sources or apify_ig_sources)
    if not have_any:
        log.error(
            "No videos collected. Sprawdz kanaly w %s, cookies, APIFY_TOKEN, lub CHANNEL_MIN_VIEWS (now=%d).",
            swipe_file, settings.channel_min_views,
        )
        return []

    # 2. Fetch + transcribe per platform (rownolegle)
    yt_sources_task = _fetch_and_transcribe_youtube(yt_urls) if yt_urls else _empty_sources()
    social_sources_task = _fetch_social(tt_urls, ig_urls) if (tt_urls or ig_urls) else _empty_sources()
    yt_sources, social_sources = await asyncio.gather(yt_sources_task, social_sources_task)
    sources = yt_sources + social_sources + apify_tt_sources + apify_ig_sources
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
