"""Ratings loader - czyta data/ratings.json (commitowane przez Telegram callback panelu).

Wykorzystanie:
- Negatywne ratings -> dolaczamy do promptu "AVOID HOOKS LIKE THESE"
- Pozytywne ratings -> wpletamy w preferencji co dziala
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from src.settings import DATA_DIR

log = logging.getLogger(__name__)

RATINGS_PATH = DATA_DIR / "ratings.json"


@dataclass
class Rating:
    script_id: str
    rating: int                # 1 albo -1
    timestamp: str


def load_ratings(path: Path = RATINGS_PATH) -> list[Rating]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Failed to load ratings: %s", e)
        return []
    out: list[Rating] = []
    for item in raw or []:
        try:
            r = Rating(
                script_id=str(item["script_id"]),
                rating=int(item["rating"]),
                timestamp=str(item.get("timestamp", "")),
            )
            if r.rating in (1, -1):
                out.append(r)
        except (KeyError, ValueError, TypeError):
            continue
    return out


def summarize_for_prompt(ratings: list[Rating], scripts_dir: Path, limit: int = 5) -> str:
    """Zwroc tekstowe summary do wstrzykniecia w prompt - ostatnie 5 thumb-down + 5 thumb-up
    z prawdziwym contentem hooka (jezeli plik na dysku).

    Wynik to instrukcja typu "AVOID hooks like X, prefer hooks like Y".
    """
    if not ratings:
        return ""

    # Sortuj malejaco po timestamp
    sorted_r = sorted(ratings, key=lambda r: r.timestamp, reverse=True)
    downvotes = [r for r in sorted_r if r.rating == -1][:limit]
    upvotes = [r for r in sorted_r if r.rating == 1][:limit]

    def _hook_from_script_id(sid: str) -> str:
        """script_id = "2026-05-18/01-founder_line" -> czytaj plik i wyciagnij hook."""
        path = scripts_dir / f"{sid}.md"
        if not path.exists():
            return ""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
        # Naive parser - znajdz linijke po "## Hook"
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("## hook"):
                # nastepna nie-pusta linia
                for nxt in lines[i + 1: i + 5]:
                    if nxt.strip():
                        return nxt.strip()[:160]
        return ""

    parts: list[str] = []
    if downvotes:
        bad = [h for h in (_hook_from_script_id(r.script_id) for r in downvotes) if h]
        if bad:
            parts.append(
                "UNIKAJ hookow podobnych do tych (Eryk je odrzucil):\n"
                + "\n".join(f"  - {h}" for h in bad)
            )
    if upvotes:
        good = [h for h in (_hook_from_script_id(r.script_id) for r in upvotes) if h]
        if good:
            parts.append(
                "PREFERUJ wzorzec podobny do tych (Eryk je polubil):\n"
                + "\n".join(f"  - {h}" for h in good)
            )
    return "\n\n".join(parts)
