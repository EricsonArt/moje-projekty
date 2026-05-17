"""Parser swipe-file.txt - linki ktore Eryk wkleil recznie.

Wspierane formaty (Faza 1.5):
    # komentarze ignorowane
    https://www.youtube.com/@nazwa                -> kanal: pobierz top shorts >= min_views
    https://www.youtube.com/@nazwa/shorts         -> kanal shorts: jak wyzej
    https://www.youtube.com/channel/UCxxx         -> kanal po ID
    https://www.youtube.com/c/nazwa               -> kanal stary format
    https://www.youtube.com/user/nazwa            -> kanal stary format

    https://youtube.com/shorts/XYZ                -> pojedynczy short (bez filtra views)
    https://youtu.be/XYZ                          -> pojedynczy film
    https://www.tiktok.com/@xxx/video/123         -> TikTok (Faza 3)
    https://www.instagram.com/p/XYZ               -> IG (Faza 3)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

# Channel patterns (sprawdzane PRZED video patterns - musza miec priorytet)
YT_CHANNEL_RE = re.compile(
    r"https?://(?:www\.|m\.)?youtube\.com/"
    r"(?:@[\w.\-]+(?:/shorts)?/?$|"          # @handle lub @handle/shorts
    r"channel/UC[\w\-]+/?(?:shorts/?)?$|"   # channel/UCxxx
    r"c/[\w.\-]+/?(?:shorts/?)?$|"          # c/nazwa
    r"user/[\w.\-]+/?(?:shorts/?)?$)",      # user/nazwa
    re.I,
)
YT_VIDEO_RE = re.compile(
    r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[\w\-]+",
    re.I,
)
TIKTOK_RE = re.compile(r"https?://(?:www\.)?tiktok\.com/[\S]+", re.I)
IG_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel)/[\S]+", re.I)


@dataclass
class SourceLink:
    url: str
    kind: str       # "yt_channel" | "yt_video" | "tiktok" | "instagram"

    @property
    def platform(self) -> str:
        if self.kind.startswith("yt_"):
            return "youtube"
        return self.kind


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
        kind = _detect_kind(line)
        if kind:
            links.append(SourceLink(url=line, kind=kind))
        else:
            log.debug("Skipping non-URL line: %s", line[:80])
    return links


def _detect_kind(url: str) -> str | None:
    # Kanaly maja priorytet - inaczej "youtube.com/@nazwa" zlapie video regex
    if YT_CHANNEL_RE.match(url):
        return "yt_channel"
    if YT_VIDEO_RE.match(url):
        return "yt_video"
    if TIKTOK_RE.match(url):
        return "tiktok"
    if IG_RE.match(url):
        return "instagram"
    return None


def filter_supported(links: Iterable[SourceLink]) -> list[SourceLink]:
    """W Fazie 1/1.5 wspieramy YouTube (kanaly + filmy). TT/IG = Faza 3."""
    out: list[SourceLink] = []
    for link in links:
        if link.kind in ("yt_channel", "yt_video"):
            out.append(link)
        else:
            log.warning(
                "Skipping %s link (TikTok/IG scraping comes in Faza 3): %s",
                link.kind, link.url,
            )
    return out
