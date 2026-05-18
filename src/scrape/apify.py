"""Apify-based scraper dla TikTok i Instagram. Backup gdy yt-dlp+cookies nie dziala.

Aktywuje sie automatycznie gdy ustawiony jest env var APIFY_TOKEN.
Apify free tier: $5 kredytow/mc, wystarcza dla ~10k filmow/mc.

Endpointy uzywanych aktorow:
- TikTok Scraper:     clockworks/tiktok-scraper
- Instagram Scraper:  apify/instagram-scraper

API doc: https://docs.apify.com/api/v2
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

from src.scrape.youtube import YoutubeVideo

log = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
APIFY_TIMEOUT = 180.0


def apify_available() -> bool:
    return bool(os.environ.get("APIFY_TOKEN", "").strip())


def _token() -> str:
    return os.environ["APIFY_TOKEN"].strip()


@dataclass
class _RunResult:
    items: list[dict]
    error: Optional[str] = None


async def _run_actor_sync(
    actor_id: str,
    run_input: dict,
    timeout: float = APIFY_TIMEOUT,
) -> _RunResult:
    """Wywoluj Apify actor synchronicznie - czekaj na wynik, zwroc dataset.

    UWAGA: actor_id musi byc w formacie 'username~actor-name' (tylda, NIE slash).
    Slash w URL Apify API jest interpretowany jako separator path - rozbija request.
    """
    actor_path = actor_id.replace("/", "~")
    url = f"{APIFY_BASE}/acts/{actor_path}/run-sync-get-dataset-items"
    params = {"token": _token(), "timeout": int(timeout)}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, params=params, json=run_input)
        if r.status_code >= 400:
            return _RunResult(items=[], error=f"HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        if not isinstance(data, list):
            return _RunResult(items=[], error=f"Unexpected response: {str(data)[:200]}")
        return _RunResult(items=data)
    except httpx.TimeoutException:
        return _RunResult(items=[], error=f"Timeout {timeout}s")
    except Exception as e:
        return _RunResult(items=[], error=f"{type(e).__name__}: {e}")


def _username_from_url(url: str) -> str:
    """Z https://www.tiktok.com/@nazwa lub instagram.com/nazwa -> 'nazwa'."""
    u = url.rstrip("/")
    if "@" in u:
        return u.rsplit("@", 1)[1].split("/")[0]
    return u.rsplit("/", 1)[1]


async def apify_tiktok_videos(
    channel_url: str,
    max_videos: int = 10,
) -> list[YoutubeVideo]:
    """Top N filmow z TikTok profilu przez Apify TikTok Scraper."""
    username = _username_from_url(channel_url)
    run_input = {
        "profiles": [username],
        "resultsPerPage": max_videos,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
    }
    log.info("Apify TikTok scrape: @%s (max %d)", username, max_videos)
    result = await _run_actor_sync("clockworks/tiktok-scraper", run_input)
    if result.error:
        log.error("Apify TT failed for @%s: %s", username, result.error)
        return []

    videos = []
    for item in result.items[:max_videos]:
        video_id = str(item.get("id") or "")
        if not video_id:
            continue
        v = YoutubeVideo(
            url=item.get("webVideoUrl") or f"https://www.tiktok.com/@{username}/video/{video_id}",
            video_id=video_id,
            title=(item.get("text") or "")[:200],
            channel=item.get("authorMeta", {}).get("name") or username,
            duration_s=int(item.get("videoMeta", {}).get("duration") or 0),
            view_count=int(item.get("playCount") or 0),
            description=(item.get("text") or "")[:2000],
            platform="tiktok",
        )
        videos.append(v)
    log.info("Apify TT @%s: %d videos", username, len(videos))
    return videos


async def apify_instagram_videos(
    channel_url: str,
    max_videos: int = 10,
) -> list[YoutubeVideo]:
    """Top N reels z IG profilu przez Apify Instagram Scraper."""
    username = _username_from_url(channel_url)
    run_input = {
        "username": [username],
        "resultsType": "posts",
        "resultsLimit": max_videos,
    }
    log.info("Apify Instagram scrape: @%s (max %d)", username, max_videos)
    result = await _run_actor_sync("apify/instagram-scraper", run_input)
    if result.error:
        log.error("Apify IG failed for @%s: %s", username, result.error)
        return []

    videos = []
    for item in result.items[:max_videos]:
        if item.get("type") not in ("Video", "Reel", "Sidecar"):
            continue
        short_code = item.get("shortCode") or item.get("id") or ""
        if not short_code:
            continue
        v = YoutubeVideo(
            url=item.get("url") or f"https://www.instagram.com/reel/{short_code}/",
            video_id=short_code,
            title=(item.get("caption") or "")[:200],
            channel=item.get("ownerUsername") or username,
            duration_s=int(item.get("videoDuration") or 0),
            view_count=int(item.get("videoViewCount") or item.get("videoPlayCount") or 0),
            description=(item.get("caption") or "")[:2000],
            platform="instagram",
        )
        videos.append(v)
    log.info("Apify IG @%s: %d videos", username, len(videos))
    return videos
