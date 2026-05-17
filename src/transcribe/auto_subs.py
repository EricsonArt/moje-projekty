"""Parser plikow .vtt z YT auto-subs do clean text.

YT auto-subs maja format:
    WEBVTT
    Kind: captions
    Language: pl

    00:00:00.080 --> 00:00:01.280
    czesc dzisiaj pokaze wam jak

    00:00:01.280 --> 00:00:03.040
    zrobic cos super

I czesto powtarzaja te same slowa w nakladajacych sie cue'sach (auto-sub realtime style).
Trzeba deduplikowac.
"""
from __future__ import annotations

import logging
import re
import yaml
from pathlib import Path

from src.settings import CONFIG_DIR

log = logging.getLogger(__name__)

# Linia z timestampem cue: "00:00:00.000 --> 00:00:01.500"
TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}")
# Inline timestamp tagi w wewnatrz tekstu: "<00:00:01.280>" lub "<c>tag</c>"
INLINE_TAG_RE = re.compile(r"<[^>]+>")


def parse_vtt(path: Path) -> str:
    """Zwraca clean transcript - jeden string, deduplikacja overlap."""
    if not path.exists():
        return ""

    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = raw.splitlines()

    cues: list[str] = []
    current: list[str] = []
    in_cue = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                cues.append(" ".join(current).strip())
                current = []
            in_cue = False
            continue
        if stripped.startswith("WEBVTT") or stripped.startswith("Kind:") or stripped.startswith("Language:"):
            continue
        if TIMESTAMP_RE.match(stripped):
            in_cue = True
            continue
        if in_cue:
            cleaned = INLINE_TAG_RE.sub("", stripped).strip()
            if cleaned:
                current.append(cleaned)

    if current:
        cues.append(" ".join(current).strip())

    # Deduplikacja overlapping cues (YT auto-subs repeat words across cues)
    deduped = _dedupe_overlapping(cues)
    text = " ".join(deduped)
    text = re.sub(r"\s+", " ", text).strip()
    return _postprocess_polish(text)


def _dedupe_overlapping(cues: list[str]) -> list[str]:
    """Usuwa overlap miedzy kolejnymi cue'sami: jezeli cue N konczy sie tym samym,
    czym zaczyna cue N+1, ucinamy."""
    out: list[str] = []
    last_words: list[str] = []
    for cue in cues:
        cue_words = cue.split()
        # Find max overlap between tail of last_words and head of cue_words
        overlap = 0
        max_check = min(len(last_words), len(cue_words), 8)
        for k in range(max_check, 0, -1):
            if last_words[-k:] == cue_words[:k]:
                overlap = k
                break
        new_words = cue_words[overlap:]
        if new_words:
            out.append(" ".join(new_words))
        last_words = (last_words + new_words)[-12:]  # keep small rolling buffer
    return out


_FIXES_CACHE: dict[str, list[str]] | None = None


def _load_whisper_fixes() -> dict[str, list[str]]:
    global _FIXES_CACHE
    if _FIXES_CACHE is not None:
        return _FIXES_CACHE
    path = CONFIG_DIR / "niche_keywords.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        _FIXES_CACHE = data.get("niche_keywords", {}).get("whisper_fixes", {}) or {}
    except (FileNotFoundError, yaml.YAMLError) as e:
        log.warning("Could not load whisper_fixes: %s", e)
        _FIXES_CACHE = {}
    return _FIXES_CACHE


def _postprocess_polish(text: str) -> str:
    """Naprawa typowych pomylek YT auto-subs PL z naszej listy w niche_keywords.yaml."""
    fixes = _load_whisper_fixes()
    if not fixes:
        return text
    for correct, wrongs in fixes.items():
        for wrong in wrongs:
            text = re.sub(rf"\b{re.escape(wrong)}\b", correct, text, flags=re.IGNORECASE)
    return text
