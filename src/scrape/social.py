"""Scraper TikTok i Instagram przez yt-dlp + cookies (lokalnie na PC).

Cookies wymagane (eksport z przegladarki, np. rozszerzeniem "Get cookies.txt LOCALLY"):
    data/cookies/tiktok.txt      - dla TikTok
    data/cookies/instagram.txt   - dla Instagram

UWAGA: TT/IG czesto nie eksponuja view_count w --flat-playlist (inaczej niz YT).
Dla bezpieczenstwa (rate limit, ryzyko bana) NIE robimy --dump-json per filmik.
Bierzemy N najnowszych z kanalu - zakladamy ze regularny posting = aktualny styl.

TT/IG nie maja auto-subs PL. Pseudo-transkrypt = title + description z info.json.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.scrape.youtube import RAW_DIR, YoutubeVideo
from src.settings import DATA_DIR

log = logging.getLogger(__name__)

COOKIES_DIR = DATA_DIR / "cookies"
TIKTOK_COOKIES = COOKIES_DIR / "tiktok.txt"
INSTAGRAM_COOKIES = COOKIES_DIR / "instagram.txt"

# Env vars dla trybu chmurowego (GitHub Actions): cookies wkleja sie jako secret,
# workflow exportuje je tutaj, ten modul zapisuje do plikow przed wywolaniem yt-dlp.
ENV_TIKTOK_COOKIES = "TIKTOK_COOKIES_CONTENT"
ENV_INSTAGRAM_COOKIES = "INSTAGRAM_COOKIES_CONTENT"


def _materialize_cookies_from_env() -> None:
    """Jezeli cookies sa w env vars (chmurowy tryb), zapisz do plikow.
    Wywolywane raz przy starcie, zanim cokolwiek probuje uzyc plikow."""
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)

    for env_name, target in [
        (ENV_TIKTOK_COOKIES, TIKTOK_COOKIES),
        (ENV_INSTAGRAM_COOKIES, INSTAGRAM_COOKIES),
    ]:
        content = os.environ.get(env_name, "").strip()
        if not content:
            continue
        if target.exists() and target.stat().st_size > 0:
            # Plik juz istnieje (tryb lokalny) - nie nadpisuj
            continue
        target.write_text(content, encoding="utf-8")
        log.info("Cookies zapisane z env var %s -> %s (%d bajtow)",
                 env_name, target.name, len(content))


# Auto-run przy imporcie - zeby kazdy entry point pipeline'u mial cookies gotowe
_materialize_cookies_from_env()


@dataclass
class SocialShort:
    video_id: str
    url: str
    title: str = ""
    platform: str = ""


def _check_ytdlp() -> bool:
    return shutil.which("yt-dlp") is not None


def _check_cookies(platform: str) -> Path | None:
    cookies_map = {
        "tiktok": TIKTOK_COOKIES,
        "instagram": INSTAGRAM_COOKIES,
    }
    path = cookies_map.get(platform)
    if path and path.exists() and path.stat().st_size > 0:
        return path
    return None


async def _run_ytdlp_listing(
    target_url: str,
    cookies_path: Path | None,
    scan_depth: int,
    timeout: float = 120.0,
) -> str:
    """Wywoluje yt-dlp --flat-playlist i zwraca raw stdout (tab-separated lines)."""
    if not _check_ytdlp():
        log.error("yt-dlp not installed - cannot scrape %s", target_url)
        return ""

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(scan_depth),
        "--print", "%(id)s\t%(title)s\t%(view_count)s\t%(duration)s",
        "--no-warnings",
        "--quiet",
        "--retries", "2",
        "--sleep-requests", "1",
    ]
    if cookies_path:
        cmd.extend(["--cookies", str(cookies_path)])
    cmd.append(target_url)

    log.info("yt-dlp listing: %s (depth=%d, cookies=%s)",
             target_url, scan_depth, bool(cookies_path))
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
            log.error("yt-dlp timeout (%ss) for %s", timeout, target_url)
            return ""

        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")[:500]
            log.error("yt-dlp failed (%d) for %s: %s", proc.returncode, target_url, err)
            return ""
        return stdout.decode("utf-8", errors="replace")
    except FileNotFoundError:
        log.error("yt-dlp binary not found")
        return ""


def _parse_listing(raw: str, platform: str) -> list[SocialShort]:
    out: list[SocialShort] = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0] or parts[0] == "NA":
            continue
        vid_id = parts[0]
        title = parts[1] if len(parts) > 1 else ""

        if platform == "tiktok":
            # TikTok urls musza miec username - flat-playlist daje sam ID.
            # Zostawiamy bare id-URL, yt-dlp znajdzie video po samym ID.
            url = f"https://www.tiktok.com/embed/v2/{vid_id}"
        elif platform == "instagram":
            url = f"https://www.instagram.com/reel/{vid_id}/"
        else:
            continue

        out.append(SocialShort(
            video_id=vid_id, url=url, title=title, platform=platform,
        ))
    return out


async def expand_tiktok_channel(
    channel_url: str,
    max_per_channel: int = 10,
    scan_depth: int = 20,
) -> list[str]:
    """Z TikTok profilu (https://tiktok.com/@nazwa) zwroc URL-e do max N
    najnowszych filmow. Wymaga data/cookies/tiktok.txt."""
    cookies = _check_cookies("tiktok")
    if not cookies:
        log.warning(
            "Brak data/cookies/tiktok.txt - pomijam kanal TT %s. Patrz docs/SETUP-WINDOWS.md.",
            channel_url,
        )
        return []

    raw = await _run_ytdlp_listing(channel_url, cookies, scan_depth)
    if not raw:
        return []
    shorts = _parse_listing(raw, "tiktok")
    selected = shorts[:max_per_channel]
    log.info("TT channel %s: %d videos found, taking %d",
             channel_url, len(shorts), len(selected))

    # Wstaw kanonicznie poprawny URL z handle (potrzebny do pobrania)
    # flat-playlist nie daje pelnego URL z @handle, ale yt-dlp dziala z bare ID via /v/.
    return [s.url for s in selected]


async def expand_instagram_channel(
    channel_url: str,
    max_per_channel: int = 10,
    scan_depth: int = 20,
) -> list[str]:
    """Z IG profilu zwroc URL-e do max N najnowszych rolek. Wymaga
    data/cookies/instagram.txt."""
    cookies = _check_cookies("instagram")
    if not cookies:
        log.warning(
            "Brak data/cookies/instagram.txt - pomijam kanal IG %s. Patrz docs/SETUP-WINDOWS.md.",
            channel_url,
        )
        return []

    raw = await _run_ytdlp_listing(channel_url, cookies, scan_depth)
    if not raw:
        return []
    shorts = _parse_listing(raw, "instagram")
    selected = shorts[:max_per_channel]
    log.info("IG channel %s: %d videos found, taking %d",
             channel_url, len(shorts), len(selected))
    return [s.url for s in selected]


async def cookies_status() -> dict[str, bool]:
    """Zwroc dict {platform: czy_cookies_jest} dla logow startowych."""
    return {
        "tiktok": _check_cookies("tiktok") is not None,
        "instagram": _check_cookies("instagram") is not None,
    }


async def polite_delay(min_s: float = 0.5, max_s: float = 2.0) -> None:
    """Losowe opoznienie miedzy requestami zeby nie wygladalo jak bot."""
    await asyncio.sleep(random.uniform(min_s, max_s))


def _extract_id_from_url(url: str, platform: str) -> str:
    """Wyciagnij ID z URLa social media."""
    if platform == "tiktok":
        # https://www.tiktok.com/@nazwa/video/1234567890 lub embed/v2/123
        if "/video/" in url:
            return url.split("/video/")[1].split("?")[0].split("/")[0]
        if "/embed/v2/" in url:
            return url.split("/embed/v2/")[1].split("?")[0].split("/")[0]
        if "/photo/" in url:
            return url.split("/photo/")[1].split("?")[0].split("/")[0]
    elif platform == "instagram":
        # https://www.instagram.com/reel/ABC123/ lub /p/ABC123/
        for marker in ("/reel/", "/reels/", "/p/", "/tv/"):
            if marker in url:
                return url.split(marker)[1].split("?")[0].rstrip("/").split("/")[0]
    return url.rsplit("/", 1)[-1]


async def fetch_social_video(
    url: str,
    platform: str,
    timeout: float = 90.0,
) -> YoutubeVideo:
    """Pobierz metadata TT/IG przez yt-dlp + cookies. Zwraca YoutubeVideo
    (uniwersalny dataclass) z platform='tiktok' / 'instagram'."""
    video_id = _extract_id_from_url(url, platform)
    video = YoutubeVideo(url=url, video_id=video_id, platform=platform)

    if not _check_ytdlp():
        video.error = "yt-dlp not installed"
        return video

    cookies = _check_cookies(platform)
    if not cookies:
        video.error = f"No cookies file for {platform} (data/cookies/{platform}.txt missing or empty)"
        return video

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    info_json = RAW_DIR / f"{platform}_{video_id}.info.json"

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-info-json",
        "--no-warnings",
        "--quiet",
        "--retries", "2",
        "--cookies", str(cookies),
        "-o", str(RAW_DIR / f"{platform}_%(id)s.%(ext)s"),
        url,
    ]

    log.info("yt-dlp fetching %s video %s", platform, video_id)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            video.error = f"yt-dlp timeout after {timeout}s"
            return video

        if proc.returncode != 0:
            video.error = (
                f"yt-dlp failed ({proc.returncode}): {stderr.decode()[:300]}"
            )
            return video
    except FileNotFoundError:
        video.error = "yt-dlp binary not found"
        return video

    if info_json.exists():
        try:
            data = json.loads(info_json.read_text(encoding="utf-8"))
            video.title = data.get("title") or data.get("description", "")[:80] or ""
            video.channel = (
                data.get("uploader") or data.get("channel")
                or data.get("creator") or ""
            )
            video.duration_s = int(data.get("duration") or 0)
            video.view_count = int(data.get("view_count") or 0)
            video.description = (data.get("description") or "")[:2000]
            video.info_json_path = info_json
        except (json.JSONDecodeError, ValueError) as e:
            log.warning("Failed to parse %s info.json for %s: %s",
                        platform, video_id, e)

    return video


def social_pseudo_transcript(v: YoutubeVideo) -> str:
    """TT/IG nie maja subow. Sklejamy tytul + opis jako pseudo-transkrypt
    do feedu LLM jako materialu inspiracyjnego."""
    parts = []
    if v.title:
        parts.append(f"Tytul: {v.title}")
    if v.description:
        parts.append(f"Opis: {v.description}")
    return "\n".join(parts).strip()


async def fetch_social_many(
    urls: list[tuple[str, str]],
    concurrency: int = 2,
) -> list[YoutubeVideo]:
    """Lista (url, platform). Concurrency=2 zeby nie palic limitu IG/TT."""
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(item: tuple[str, str]) -> YoutubeVideo:
        url, platform = item
        async with sem:
            await polite_delay()
            return await fetch_social_video(url, platform)

    return await asyncio.gather(*(_bounded(it) for it in urls))
