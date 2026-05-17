"""Parser swipe-file.txt - linki do viralowych shortow ktore Eryk wkleil recznie.

Format:
    # komentarze ignorowane
    https://youtube.com/shorts/XYZ
    https://www.tiktok.com/@xxx/video/123456 # tiktok skip w MVP
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

YT_RE = re.compile(r"https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/[\S]+", re.I)
TIKTOK_RE = re.compile(r"https?://(?:www\.)?tiktok\.com/[\S]+", re.I)
IG_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel)/[\S]+", re.I)


@dataclass
class SourceLink:
    url: str
    platform: str  # "youtube" | "tiktok" | "instagram"


def parse_swipe_file(path: Path) -> list[SourceLink]:
    if not path.exists():
        log.warning("Swipe file not found: %s", path)
        return []

    links: list[SourceLink] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Strip trailing inline comments
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        platform = _detect_platform(line)
        if platform:
            links.append(SourceLink(url=line, platform=platform))
        else:
            log.debug("Skipping non-URL line: %s", line[:80])
    return links


def _detect_platform(url: str) -> str | None:
    if YT_RE.match(url):
        return "youtube"
    if TIKTOK_RE.match(url):
        return "tiktok"
    if IG_RE.match(url):
        return "instagram"
    return None


def filter_supported(links: Iterable[SourceLink]) -> list[SourceLink]:
    """W Fazie 1 wspieramy tylko YouTube. Reszta - skip z warningiem."""
    out: list[SourceLink] = []
    for link in links:
        if link.platform == "youtube":
            out.append(link)
        else:
            log.warning(
                "Skipping %s link (TikTok/IG scraping comes in Faza 3): %s",
                link.platform, link.url,
            )
    return out
