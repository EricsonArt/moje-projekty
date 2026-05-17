"""YouTube Shorts scraper - yt-dlp przez subprocess.
Sciaga metadata + polskie auto-subs do data/raw/. Nie pobiera audio/wideo.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.settings import DATA_DIR

log = logging.getLogger(__name__)

RAW_DIR = DATA_DIR / "raw"


@dataclass
class YoutubeVideo:
    url: str
    video_id: str
    title: str = ""
    channel: str = ""
    duration_s: int = 0
    view_count: int = 0
    description: str = ""
    transcript_path: Optional[Path] = None
    info_json_path: Optional[Path] = None
    error: Optional[str] = None


def _check_ytdlp_available() -> bool:
    return shutil.which("yt-dlp") is not None


def _extract_video_id(url: str) -> str:
    # https://youtube.com/shorts/XYZ -> XYZ
    # https://youtu.be/XYZ -> XYZ
    # https://www.youtube.com/watch?v=XYZ -> XYZ
    if "shorts/" in url:
        return url.split("shorts/")[1].split("?")[0].split("/")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("/")[0]
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return url.rsplit("/", 1)[-1]


async def fetch_video(url: str, timeout: float = 60.0) -> YoutubeVideo:
    """Sciaga metadata + auto-subs PL przez yt-dlp. Nie pobiera audio."""
    video_id = _extract_video_id(url)
    video = YoutubeVideo(url=url, video_id=video_id)

    if not _check_ytdlp_available():
        video.error = "yt-dlp not installed. pip install yt-dlp"
        return video

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-subs",
        "--sub-langs", "pl,pl-orig,en",
        "--sub-format", "vtt",
        "--write-info-json",
        "--no-warnings",
        "--quiet",
        "-o", str(RAW_DIR / "%(id)s.%(ext)s"),
        url,
    ]

    log.info("yt-dlp fetching %s", url)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            video.error = f"yt-dlp timeout after {timeout}s"
            return video

        if proc.returncode != 0:
            video.error = f"yt-dlp failed ({proc.returncode}): {stderr.decode()[:300]}"
            return video
    except FileNotFoundError:
        video.error = "yt-dlp binary not found in PATH"
        return video

    # Parse info.json
    info_json = RAW_DIR / f"{video_id}.info.json"
    if info_json.exists():
        try:
            data = json.loads(info_json.read_text(encoding="utf-8"))
            video.title = data.get("title", "")
            video.channel = data.get("channel") or data.get("uploader", "")
            video.duration_s = int(data.get("duration") or 0)
            video.view_count = int(data.get("view_count") or 0)
            video.description = (data.get("description") or "")[:1000]
            video.info_json_path = info_json
        except (json.JSONDecodeError, ValueError) as e:
            log.warning("Failed to parse info.json for %s: %s", video_id, e)

    # Find transcript - prefer pl, fallback pl-orig, then en
    for lang in ("pl", "pl-orig", "en"):
        vtt = RAW_DIR / f"{video_id}.{lang}.vtt"
        if vtt.exists():
            video.transcript_path = vtt
            break

    if not video.transcript_path:
        video.error = "No transcript file (.vtt) - video may have subs disabled"

    return video


async def fetch_many(urls: list[str], concurrency: int = 3) -> list[YoutubeVideo]:
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(u: str) -> YoutubeVideo:
        async with sem:
            return await fetch_video(u)

    return await asyncio.gather(*(_bounded(u) for u in urls))
