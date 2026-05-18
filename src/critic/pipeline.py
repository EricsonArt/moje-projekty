"""Critic - 4-wymiarowa ocena skryptu. Verdict PASS / REGENERATE z specific_fix.
W Fazie 2 dodamy cosine_sim check przeciwko source viralowi (sqlite-vec).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.llm.router import LLMRouter

log = logging.getLogger(__name__)

# Threshold dla PASS
SCORE_THRESHOLD = 8


@dataclass
class CriticVerdict:
    verdict: str  # "PASS" | "REGENERATE"
    scores: dict
    auto_fails: list
    specific_fix: str
    summary: str

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

    @property
    def total(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)


def _build_critic_prompt(
    script: dict,
    source_hook: str,
    persona_name: str,
    banned_phrases: list[str],
) -> str:
    full = script.get("full_script", "")
    hook = script.get("hook", "")
    wc = script.get("word_count", len(full.split()))
    sec = script.get("estimated_seconds", "?")

    return f"""Jestes BEZWZGLEDNYM krytykiem skryptow viralowych shortow PL dla Eryka Hajduczka.
Lepiej odrzucic 9 dobrych skryptow niz puscic 1 zly. Eryk ma 840k subskrybentow - jakosc widzi cala widownia.

---

SKRYPT DO OCENY:
{full}

---

HOOK osobno:
{hook}

Word count: {wc}
Estimated seconds: {sec}
Persona: {persona_name}

---

ZRODLO VIRAL (do checku oryginalnosci):
{source_hook}

---

ZAKAZANE FRAZY (auto-fail jezeli wystepuja):
{', '.join(banned_phrases)}

---

OCEN 4 WYMIARY (0-10, threshold {SCORE_THRESHOLD}/10):

1. HOOK_STRENGTH - czy pierwsze 8s lamie scroll?
   - Auto-FAIL: zaczyna sie od "Czesc", "Hej", "Dzisiaj", "W tym filmie", "Pokaze ci", "Witam"
   - Auto-FAIL: pytanie retoryczne bez payoffu

2. ORIGINALITY - czy NIE kopiuje zrodla?
   - Auto-FAIL: >50% slow hooka pokrywa sie z hookiem zrodla
   - Auto-FAIL: struktura solve[] kopiuje 1:1

3. FUNNEL_LOGIC - czy CTA pasuje naturalnie?
   - Auto-FAIL: cena/liczby w CTA niezgodne z faktyczna oferta Skali
   - Auto-FAIL: CTA mowi o "kursach"/"mentoringu" jak Skala to SaaS (Pakiet VIP MA mentoring, ale tylko VIP)

4. POLISH_NATIVE - czy brzmi jak rodzimy PL?
   - Auto-FAIL: kalka z EN ("pozwol mi", "tutaj jest", "spojrz na to")
   - Auto-FAIL: jakakolwiek z zakazanych frazy
   - Penalty: zdania >20 slow

---

ZASADA: jezeli WSZYSTKIE 4 wymiary >= {SCORE_THRESHOLD} i ZERO auto-fail -> PASS.
W przeciwnym razie REGENERATE z specific_fix max 2 zdania (wykonalne w 1 kroku).

---

ZWROC DOKLADNIE JSON, BEZ MARKDOWN:

{{
  "verdict": "PASS" | "REGENERATE",
  "scores": {{
    "hook_strength": <0-10>,
    "originality": <0-10>,
    "funnel_logic": <0-10>,
    "polish_native": <0-10>
  }},
  "auto_fails": ["lista konkretnych fails, pusta jezeli zero"],
  "specific_fix": "konkretna instrukcja co zmienic, max 2 zdania. Pusta string jezeli PASS.",
  "summary": "1 zdanie ogolnej oceny"
}}
"""


async def critique(
    router: LLMRouter,
    script: dict,
    source_hook: str,
    persona_name: str,
    banned_phrases: list[str],
) -> CriticVerdict:
    prompt = _build_critic_prompt(script, source_hook, persona_name, banned_phrases)
    parsed, _resp = await router.call_json(prompt, temperature=0.3, max_tokens=800)
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}

    verdict_raw = str(parsed.get("verdict", "REGENERATE")).upper().strip()
    verdict = "PASS" if verdict_raw == "PASS" else "REGENERATE"

    return CriticVerdict(
        verdict=verdict,
        scores=parsed.get("scores", {}) or {},
        auto_fails=parsed.get("auto_fails", []) or [],
        specific_fix=parsed.get("specific_fix", "") or "",
        summary=parsed.get("summary", "") or "",
    )
