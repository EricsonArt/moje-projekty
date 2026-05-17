"""Pipeline generacji skryptu - dla MVP polaczone w jeden prompt
(hook + body + cta + style), Critic osobno.

W Fazie 2 rozbijemy na multi-agent (hook_generator, body_generator, cta_integrator,
style_adapter jako osobne calle).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.llm.router import LLMRouter
from src.scrape.youtube import YoutubeVideo
from src.settings import CONFIG_DIR, PROMPTS_DIR

log = logging.getLogger(__name__)


@dataclass
class TopicChoice:
    persona_id: str          # "marek" | "anna"
    persona_data: dict
    usp_id: str
    usp_data: dict
    package_id: int          # 0 = quiz-only (TOFU), 1-4 = pakiety
    package_data: dict | None
    cta_severity: str        # "low" | "medium" | "high"
    angle: str | None = None
    scarcity: dict | None = None


@dataclass
class GeneratedScript:
    hook: str
    full_script: str
    word_count: int
    estimated_seconds: int
    hashtags: list[str]
    persona: str
    usp: str
    package_id: int
    source_url: str
    source_title: str
    critic_scores: dict = field(default_factory=dict)
    iterations: int = 1


# ---------- Config loading ----------

_CONFIG_CACHE: dict | None = None


def load_configs() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    cfg = {}
    for name in ("product", "icp", "user_voice", "niche_keywords"):
        path = CONFIG_DIR / f"{name}.yaml"
        cfg[name] = yaml.safe_load(path.read_text(encoding="utf-8"))
    _CONFIG_CACHE = cfg
    return cfg


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


# ---------- Topic Picker ----------

def pick_topic_for_today(configs: dict, today: dt.date | None = None) -> TopicChoice:
    """Patrzy na dzien tygodnia, dobiera z weekly_rotation.
    Dla 3 skryptow dziennie kazdy ma INNY hook_type ale ten sam topic/persona."""
    today = today or dt.date.today()
    rotation = configs["icp"]["weekly_rotation"]
    weekday = today.weekday()  # 0=mon, 6=sun
    slot = rotation[weekday]

    persona_id = slot["persona"]
    persona_data = configs["icp"]["personas"][persona_id]

    usp_id = slot["usp"]
    usps = configs["product"]["usps"]
    usp_data = next(u for u in usps if u["id"] == usp_id)

    package_id = slot.get("package", 3)
    package_data = None
    if package_id > 0:
        package_data = next(
            (p for p in configs["product"]["packages"] if p["id"] == package_id), None
        )

    cta_severity = slot.get("cta_severity", "medium")
    angle = slot.get("angle")

    # Wybierz scarcity pasujace do severity
    scarcity_options = configs["product"]["scarcity"]
    matching = [s for s in scarcity_options if s["severity"] == cta_severity]
    scarcity = random.choice(matching) if matching else scarcity_options[0]

    return TopicChoice(
        persona_id=persona_id,
        persona_data=persona_data,
        usp_id=usp_id,
        usp_data=usp_data,
        package_id=package_id,
        package_data=package_data,
        cta_severity=cta_severity,
        angle=angle,
        scarcity=scarcity,
    )


# ---------- Combined Generator (MVP - 1 call zamiast 4) ----------

HOOK_VARIANTS = [
    {"type": "kontrarian", "instruction": "Hook MUSI byc typu KONTRARIAN - 'X NIE potrzebuje Y, oto co dziala'."},
    {"type": "liczba", "instruction": "Hook MUSI zaczynac sie KONKRETNA LICZBA/PROCENT - '97 procent ludzi...'."},
    {"type": "transformation", "instruction": "Hook MUSI byc o TRANSFORMACJI - 'rok temu X, teraz Y'."},
    {"type": "curiosity_gap", "instruction": "Hook MUSI tworzyc CURIOSITY GAP - 'pokaze ci dlaczego X NIE dziala (i co dziala zamiast)'."},
    {"type": "hot_take", "instruction": "Hook MUSI byc HOT TAKE / niepopularna opinia - 'Niepopularna opinia: ...'."},
    {"type": "founder_line", "instruction": "Hook MUSI byc w stylu FOUNDER-LINE Eryka - krotki, deklaratywny, jak 'Twoj biznes dziala kiedy ty spisz'."},
]


def _build_generation_prompt(
    configs: dict,
    topic: TopicChoice,
    source: YoutubeVideo,
    source_transcript: str,
    hook_variant: dict,
) -> str:
    voice = configs["user_voice"]
    product = configs["product"]

    persona_profile = (
        f"Imie: {topic.persona_data['name']}\n"
        f"Wiek: {topic.persona_data['age_range']}\n"
        f"Sytuacja: {topic.persona_data['situation']}\n"
        f"Ból: {topic.persona_data['pain']}\n"
        f"Pragnienie: {topic.persona_data['desire']}\n"
        f"Język - lubi: {', '.join(topic.persona_data['voice_notes']['prefers'])}\n"
        f"Język - unika: {', '.join(topic.persona_data['voice_notes']['avoids'])}\n"
        f"Triggery zakupowe: {'; '.join(topic.persona_data['buying_triggers'])}"
    )

    voice_block = (
        f"Forbidden starts: {', '.join(voice['first_words_rules']['forbidden_starts'])}\n"
        f"Banned phrases: {', '.join(voice['banned_phrases'])}\n"
        f"Signature phrases (mozesz wpletac): {', '.join(voice['signature_phrases'])}\n"
        f"Style: {voice['speaker']['register']}"
    )

    if topic.package_data and topic.package_id > 0:
        pkg = topic.package_data
        package_block = (
            f"PAKIET DO PROMOCJI: #{pkg['id']} - {pkg['name']}\n"
            f"Cena Founders: {pkg['price_founders_label']} (regular: {pkg['price_regular_label'] if 'price_regular_label' in pkg else 'one-time'})\n"
            f"CTA button: {pkg['cta_button']}\n"
            f"Zawiera: {'; '.join(pkg['contains'])}\n"
            f"Use when: {pkg['use_when']}"
        )
        cta_instruction = (
            f"CTA severity: {topic.cta_severity}. "
            f"Scarcity hook: '{topic.scarcity['text'] if topic.scarcity else ''}'. "
            f"Link: {product['funnel']['bio_link']}. "
            f"Risk reversal (wpletaj 1 z tych): {'; '.join(product['risk_reversal'])}"
        )
    else:
        package_block = "PAKIET: BRAK - CTA prowadzi tylko do quizu (TOFU)."
        cta_instruction = (
            f"CTA severity: low. "
            f"CTA ma tylko zachecic do quizu: {product['funnel']['quiz_label']}. "
            f"Link: {product['funnel']['quiz_url']}."
        )

    angle_note = f"\nSPECJALNY ANGLE dzisiejszy: {topic.angle}" if topic.angle else ""

    prompt = f"""Jestes copywriterem viralowych shortow PL dla Eryka Hajduczka (840k+ YT, 36k+ TT),
zalozyciela SaaS-u "Skala" (systemskala.pl). Twoj output zostanie nagrany przez Eryka jako
talking-head wideo (mowi do kamery, 30-60s).

---

PERSONA DOCELOWA:
{persona_profile}

---

GLOS ERYKA (twarde reguly):
{voice_block}

---

USP DO PODKRESLENIA:
{topic.usp_data['short']}
Szczegolowy opis: {topic.usp_data['long']}

---

{package_block}
{angle_note}

---

ZRODLO VIRAL (do inspiracji wzorca, NIE kopiowania):
Tytul: {source.title}
Kanal: {source.channel}
Views: {source.view_count}
Transkrypt (max 800 znakow):
{source_transcript[:800]}

---

WYMUSZONY TYP HOOKA: {hook_variant['type']}
{hook_variant['instruction']}

---

INSTRUKCJA CTA:
{cta_instruction}

---

STRUKTURA SKRYPTU (Hormozi PL):
[1] HOOK - max 12 slow, max 8s, PIERWSZE 2 SLOWA = pattern interrupt
[2] AGITATE - 1-2 zdania konkretnego bólu widza
[3] SOLVE - 3 numerowane kroki/punkty (KONKRETY, nie ogolniki)
[4] PATTERN INTERRUPT - 1 krotkie zdanie lamiace tempo
[5] CTA - max 25 slow, zgodnie z instrukcja powyzej

Total: 75-150 slow (30-60s mowione).

---

REGULY TWARDE (auto-fail):
- ZERO frazy z listy "Banned phrases"
- ZERO startu z "Czesc/Hej/Witam/Dzisiaj/W tym filmie/Pokaze ci"
- ZERO kalki z angielskiego ("pozwol mi", "tutaj jest", "spojrz na to")
- ZERO pytania retorycznego bez payoffu
- Liczby w CTA TYLKO z configu (nie zmysl ceny)
- Hashtagi: 15-20, mix PL+EN

---

ZWROC DOKLADNIE JSON, BEZ MARKDOWN WRAPPING:

{{
  "hook": "tekst hooka",
  "hook_type": "{hook_variant['type']}",
  "first_2_words": "pierwsze dwa slowa",
  "agitate": "1-2 zdania bolu",
  "solve": ["krok 1", "krok 2", "krok 3"],
  "pattern_interrupt": "1 zdanie",
  "cta": "tekst CTA",
  "full_script": "Pelny tekst do nagrania - hook + agitate + solve numerowane + pattern_interrupt + cta. Z pauzami '—' tam gdzie aktor ma sie zatrzymac.",
  "word_count": 120,
  "estimated_seconds": 45,
  "b_roll_suggestions": [
    {{"second": 0, "shot": "talking head"}},
    {{"second": 15, "shot": "..."}}
  ],
  "hashtags": ["#ai", "#fyp", "#tiktokpolska", "..."]
}}
"""
    return prompt


async def generate_one_script(
    router: LLMRouter,
    configs: dict,
    topic: TopicChoice,
    source: YoutubeVideo,
    source_transcript: str,
    hook_variant: dict,
    temperature: float = 0.85,
) -> dict:
    prompt = _build_generation_prompt(configs, topic, source, source_transcript, hook_variant)
    parsed, _resp = await router.call_json(prompt, temperature=temperature, max_tokens=2400)
    if isinstance(parsed, list):
        # LLM sometimes wraps in array - take first
        parsed = parsed[0] if parsed else {}
    return parsed
