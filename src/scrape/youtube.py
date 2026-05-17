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
    """Univeralny kontener na source video - YT, TT lub IG (mimo nazwy).
    Nazwa zostawiona dla zgodnosci z generate/critic pipeline'ami."""
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
    platform: str = "youtube"  # "youtube" | "tiktok" | "instagram"


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


def _normalize_channel_to_shorts_tab(url: str) -> str:
    """Zwroc URL zakladki /shorts dla kanalu. Jesli juz tam jest - bez zmian."""
    u = url.rstrip("/")
    if u.endswith("/shorts"):
        return u
    return u + "/shorts"


@dataclass
class ChannelShort:
    """Plytki wpis z listy shortow kanalu (przed pelnym fetchem)."""
    video_id: str
    url: str
    title: str = ""
    view_count: int = 0
    duration_s: int = 0


async def list_channel_shorts(
    channel_url: str,
    scan_depth: int = 30,
    timeout: float = 90.0,
) -> list[ChannelShort]:
    """Listuj top N shortow z zakladki /shorts kanalu (flat-playlist, bez subow).

    Uzywa --flat-playlist + --print zeby uniknac pelnego extracta dla kazdego filmu.
    Zwraca posortowane po views malejaco (najpopularniejsze pierwsze).
    """
    if not _check_ytdlp_available():
        log.error("yt-dlp not installed - cannot list channel shorts")
        return []

    target = _normalize_channel_to_shorts_tab(channel_url)

    # %()j daje JSON per linijka - latwo parsowac, dziala dla yt-dlp >= 2023
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(scan_depth),
        "--print", "%(id)s\t%(title)s\t%(view_count)s\t%(duration)s",
        "--no-warnings",
        "--quiet",
        target,
    ]
    log.info("yt-dlp listing channel shorts: %s (depth=%d)", target, scan_depth)
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
            log.error("yt-dlp channel list timeout (%ss) for %s", timeout, target)
            return []

        if proc.returncode != 0:
            log.error(
                "yt-dlp channel list failed (%d) for %s: %s",
                proc.returncode, target, stderr.decode()[:300],
            )
            return []
    except FileNotFoundError:
        log.error("yt-dlp binary not found in PATH")
        return []

    shorts: list[ChannelShort] = []
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        vid_id, title, views_str, dur_str = parts[0], parts[1], parts[2], parts[3]
        if not vid_id or vid_id == "NA":
            continue
        try:
            views = int(views_str) if views_str and views_str != "NA" else 0
        except ValueError:
            views = 0
        try:
            dur = int(float(dur_str)) if dur_str and dur_str != "NA" else 0
        except ValueError:
            dur = 0
        shorts.append(ChannelShort(
            video_id=vid_id,
            url=f"https://www.youtube.com/shorts/{vid_id}",
            title=title,
            view_count=views,
            duration_s=dur,
        ))

    # Sortuj po views malejaco
    shorts.sort(key=lambda s: s.view_count, reverse=True)
    log.info("Channel %s: %d shorts found (top: %d views)",
             target, len(shorts), shorts[0].view_count if shorts else 0)
    return shorts


async def expand_channel(
    channel_url: str,
    min_views: int = 500_000,
    max_per_channel: int = 10,
    scan_depth: int = 30,
) -> list[str]:
    """Z URL kanalu zwroc liste URL-i shortow ktore spelniaja min_views.

    Limit max_per_channel zeby nie wypompowac wszystkiego z jednego kanalu.
    """
    shorts = await list_channel_shorts(channel_url, scan_depth=scan_depth)
    if not shorts:
        return []
    viral = [s for s in shorts if s.view_count >= min_views]
    if not viral:
        log.warning(
            "Channel %s: zero shorts >= %d views (top has %d). Lowering threshold or refresh channel.",
            channel_url, min_views, shorts[0].view_count,
        )
        return []
    selected = viral[:max_per_channel]
    log.info(
        "Channel %s: %d shorts >= %d views, taking top %d",
        channel_url, len(viral), min_views, len(selected),
    )
    return [s.url for s in selected]
