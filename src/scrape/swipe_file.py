"""Parser swipe-file.txt - linki ktore Eryk wkleil recznie.

Wspierane formaty (Faza 1.5 + lokalny TT/IG):

YouTube:
    https://www.youtube.com/@nazwa                -> kanal: top shorts >= min_views
    https://www.youtube.com/@nazwa/shorts         -> zakladka shorts
    https://www.youtube.com/channel/UCxxx         -> kanal po ID
    https://www.youtube.com/c/nazwa               -> stary format
    https://youtube.com/shorts/XYZ                -> pojedynczy short

TikTok (wymaga cookies w data/cookies/tiktok.txt):
    https://www.tiktok.com/@nazwa                 -> profil: najnowsze shorty
    https://www.tiktok.com/@nazwa/video/123       -> pojedynczy film

Instagram (wymaga cookies w data/cookies/instagram.txt):
    https://www.instagram.com/nazwa               -> profil: najnowsze rolki
    https://www.instagram.com/nazwa/              -> j.w.
    https://www.instagram.com/reel/XYZ            -> pojedyncza rolka
    https://www.instagram.com/p/XYZ               -> pojedynczy post
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

# Kolejnosc regexow ma znaczenie - kanaly PRZED video (inaczej video lapie kanal)

YT_CHANNEL_RE = re.compile(
    r"https?://(?:www\.|m\.)?youtube\.com/"
    r"(?:@[\w.\-]+(?:/shorts)?/?$|"
    r"channel/UC[\w\-]+/?(?:shorts/?)?$|"
    r"c/[\w.\-]+/?(?:shorts/?)?$|"
    r"user/[\w.\-]+/?(?:shorts/?)?$)",
    re.I,
)
YT_VIDEO_RE = re.compile(
    r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[\w\-]+",
    re.I,
)

TIKTOK_CHANNEL_RE = re.compile(
    r"https?://(?:www\.|m\.)?tiktok\.com/@[\w.\-]+/?$",
    re.I,
)
TIKTOK_VIDEO_RE = re.compile(
    r"https?://(?:www\.|m\.)?tiktok\.com/@[\w.\-]+/(?:video|photo)/\d+",
    re.I,
)

# IG: profil to /nazwa/ bez /p/ ani /reel/. Trzeba sprawdzic ostroznie.
IG_CHANNEL_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?!p/|reel/|reels/|stories/|tv/|explore/)"
    r"[\w.\-]+/?$",
    re.I,
)
IG_VIDEO_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w\-]+",
    re.I,
)


@dataclass
class SourceLink:
    url: str
    kind: str
    # Mozliwe wartosci kind:
    #   "yt_channel" | "yt_video"
    #   "tt_channel" | "tt_video"
    #   "ig_channel" | "ig_video"

    @property
    def platform(self) -> str:
        if self.kind.startswith("yt_"):
            return "youtube"
        if self.kind.startswith("tt_"):
            return "tiktok"
        if self.kind.startswith("ig_"):
            return "instagram"
        return "unknown"


def parse_swipe_file(path: Path) -> list[SourceLink]:
    if not path.exists():
        log.warning("Swipe file not found: %s", path)
        return []

    links: list[SourceLink] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        kind = _detect_kind(line)
        if kind:
            links.append(SourceLink(url=line, kind=kind))
        else:
            log.debug("Skipping non-URL line: %s", line[:80])
    return links


def _detect_kind(url: str) -> str | None:
    # Kolejnosc: kanaly przed videos w obrebie platformy
    if YT_CHANNEL_RE.match(url):
        return "yt_channel"
    if YT_VIDEO_RE.match(url):
        return "yt_video"
    if TIKTOK_CHANNEL_RE.match(url):
        return "tt_channel"
    if TIKTOK_VIDEO_RE.match(url):
        return "tt_video"
    if IG_VIDEO_RE.match(url):
        return "ig_video"
    if IG_CHANNEL_RE.match(url):
        return "ig_channel"
    return None


def filter_supported(links: Iterable[SourceLink]) -> list[SourceLink]:
    """Wszystkie 6 rodzajow wspierane (YT/TT/IG, kanaly i video). Cookies wymagane
    dla TT/IG sprawdza warstwa scrape, nie ten parser."""
    return [l for l in links if l.kind in {
        "yt_channel", "yt_video",
        "tt_channel", "tt_video",
        "ig_channel", "ig_video",
    }]
