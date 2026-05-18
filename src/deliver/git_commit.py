"""Zapis skryptow do scripts/YYYY-MM-DD/*.md. Workflow GitHub Actions
zrobi commit + push do brancha (krok poza tym plikiem).
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.settings import SCRIPTS_DIR

log = logging.getLogger(__name__)


def save_scripts_to_disk(scripts: list[dict], today: str) -> list[Path]:
    out_dir = SCRIPTS_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, s in enumerate(scripts, 1):
        path = out_dir / f"{i:02d}-{s.get('hook_type', 'unknown')}.md"
        path.write_text(_render_markdown(i, s, today), encoding="utf-8")
        saved.append(path)
    log.info("Saved %d scripts to %s", len(saved), out_dir)
    return saved


def _render_markdown(idx: int, script: dict, today: str) -> str:
    hashtags = " ".join(script.get("hashtags") or [])
    b_roll_lines = []
    for b in (script.get("b_roll_suggestions") or []):
        try:
            b_roll_lines.append(f"- **{b.get('second', '?')}s**: {b.get('shot', '')}")
        except AttributeError:
            continue
    b_roll_md = "\n".join(b_roll_lines) or "_(brak)_"

    scores = script.get("critic_scores") or {}
    scores_md = "\n".join(f"- {k}: **{v}**" for k, v in scores.items()) or "_(brak)_"

    return f"""# Skrypt {idx} - {today}

**Hook type**: {script.get('hook_type', '?')}
**Persona**: {script.get('persona', '?')}
**USP**: {script.get('usp', '?')}
**Pakiet**: {script.get('package_id', '?')}
**Word count**: {script.get('word_count', '?')}
**Estimated seconds**: {script.get('estimated_seconds', '?')}
**Iterations**: {script.get('iterations', 1)}

## Critic scores
{scores_md}

## Hook
{script.get('hook', '')}

## Pełny skrypt (do nagrania)

{script.get('full_script', '')}

## B-roll suggestions
{b_roll_md}

## Hashtagi
`{hashtags}`

## Źródło inspiracji
- Tytuł: {script.get('source_title', '')}
- URL: {script.get('source_url', '')}
"""
