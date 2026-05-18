"""Preferences loader - czyta config/preferences.yaml + walidacja + defaults.

Preferences sa zmienne (user edytuje przez Web Panel). Pipeline czyta je raz
na poczatku kazdego runa.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from src.settings import CONFIG_DIR

log = logging.getLogger(__name__)

PREFERENCES_PATH = CONFIG_DIR / "preferences.yaml"


@dataclass
class EffortProfile:
    """Mapping effort_level -> konkretne parametry generacji."""
    critic_iterations: int
    temperature: float
    multi_attempt_count: int    # ile kandydatow LLM generuje, bierze najlepszego
    label: str


def effort_to_profile(level: int) -> EffortProfile:
    """Mapuj effort_level (1-10) na konkretne parametry."""
    level = max(1, min(10, level))
    if level <= 4:
        return EffortProfile(
            critic_iterations=1,
            temperature=0.70,
            multi_attempt_count=1,
            label="fast",
        )
    if level <= 7:
        return EffortProfile(
            critic_iterations=3,
            temperature=0.85,
            multi_attempt_count=1,
            label="standard",
        )
    return EffortProfile(
        critic_iterations=5,
        temperature=0.95,
        multi_attempt_count=3,
        label="thorough",
    )


@dataclass
class Hashtags:
    count: int = 18
    niche_ratio: float = 0.5
    broad_ratio: float = 0.3
    branded_ratio: float = 0.2


@dataclass
class MultiPlatform:
    enabled: bool = False
    platforms: list[str] = field(default_factory=lambda: ["tiktok"])


@dataclass
class Ratings:
    enabled: bool = True
    use_history_in_prompts: bool = True


@dataclass
class TrendingHooks:
    enabled: bool = False
    daily_count: int = 5


@dataclass
class MultiNiche:
    enabled: bool = False
    active_niches: list[str] = field(default_factory=lambda: ["skala"])


@dataclass
class Preferences:
    """Pelen zestaw preferencji edytowalnych przez user'a."""
    scripts_per_run: int = 3
    cta_intensity: int = 30          # 0-100
    copy_similarity: int = 40        # 0-100
    effort_level: int = 6            # 1-10
    target_seconds: int = 45         # 15-90
    tone: str = "balanced"           # anti_guru|hormozi|storyteller|kontrarian|balanced

    hashtags: Hashtags = field(default_factory=Hashtags)
    multi_platform: MultiPlatform = field(default_factory=MultiPlatform)
    ratings: Ratings = field(default_factory=Ratings)
    trending_hooks: TrendingHooks = field(default_factory=TrendingHooks)
    multi_niche: MultiNiche = field(default_factory=MultiNiche)

    @property
    def effort(self) -> EffortProfile:
        return effort_to_profile(self.effort_level)

    # --- Helpers do generatora ---

    def cta_severity(self) -> str:
        """0-30 = low, 30-70 = medium, 70-100 = high."""
        if self.cta_intensity < 30:
            return "low"
        if self.cta_intensity < 70:
            return "medium"
        return "high"

    def copy_instruction_for_prompt(self) -> str:
        """Tekstowa instrukcja do prompta - jak bardzo klonowac viral."""
        s = self.copy_similarity
        if s <= 20:
            return (
                "Wykorzystaj viral TYLKO jako kontekst tematu. Pisz CALKOWICIE WLASNA "
                "strukture, wlasny ton, wlasny hook. Inspiracja minimalna - tylko temat."
            )
        if s <= 50:
            return (
                "Wykorzystaj WZORZEC hooka z virala (jaki typ - kontrarian/liczba/transformation), "
                "ale wlasne body, wlasne konkrety, wlasne CTA. Subtelna inspiracja."
            )
        if s <= 80:
            return (
                "Mocno trzymaj sie struktury virala: podobny tempo, podobne sekcje, "
                "podobny styl hooka. Ale slownik i konkrety zmieniamy pod Eryka i Skale."
            )
        return (
            "Skopiuj strukture i tempo virala MAKSYMALNIE BLISKO 1:1. Zmieniamy tylko "
            "konkretne slowa pod nasza nisze i CTA pod Skale. Inaczej jak najblizej oryginalu."
        )

    def cta_instruction_for_prompt(self) -> str:
        """Instrukcja o intensywnosci CTA do promptu."""
        c = self.cta_intensity
        if c < 20:
            return (
                "ZERO sprzedazy. CTA = max 1 zdanie soft-touch na koncu "
                "(np. 'wiecej w bio', 'sledz po wiecej'). Filmik ma EDUKOWAC i BUDOWAC ZAUFANIE."
            )
        if c < 50:
            return (
                f"CTA umiarkowane (severity low). Max 15 slow CTA na koncu, "
                f"miekkie - 'sprawdz w bio', 'jak chcesz zobaczyc jak to robie...'. "
                f"Skupienie na value, CTA to bonus."
            )
        if c < 80:
            return (
                f"CTA mocne (severity medium). 20-25 slow CTA z scarcity. "
                f"Wskaz konkretne korzysci pakietu. Link, urgency."
            )
        return (
            f"CTA HARD SELL (severity high). 25-35 slow CTA. "
            f"Scarcity + urgency + risk reversal + konkretna cena/promo. "
            f"Cale body prowadzi do tego zakonczenia."
        )

    def tone_instruction_for_prompt(self) -> str:
        """Instrukcja tonu/stylu."""
        tones = {
            "anti_guru": (
                "Ton: ANTI-GURU. Bezposredni, demaskujacy mity, kontrarian. "
                "Zero 'pozytywnego myslenia', zero 'wierz w siebie'. Konkrety + szczeroSC."
            ),
            "hormozi": (
                "Ton: HORMOZI PL. Mocno biznesowo, agitate -> solve -> CTA, "
                "numerowane konkrety, brak ozdobnikow."
            ),
            "storyteller": (
                "Ton: STORYTELLER. Osobista historia jako hook, emocje, lekcja na koncu. "
                "CTA bardzo subtelne, nie sprzedazowe."
            ),
            "kontrarian": (
                "Ton: KONTRARIAN. Kazda teza odwraca powszechne mysli. "
                "'Wszyscy mowia X, ale prawda jest Y'. Sila w hot-takach."
            ),
            "balanced": (
                "Ton: BALANCED. AI sam wybiera najlepszy ton per skrypt - "
                "mix anti-guru struktury Hormoziego, czasem story, kontrarian gdy pasuje."
            ),
        }
        return tones.get(self.tone, tones["balanced"])


def _coerce_int(v, default: int, lo: int, hi: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _coerce_str(v, default: str, allowed: list[str] | None = None) -> str:
    if not isinstance(v, str):
        return default
    if allowed and v not in allowed:
        log.warning("Tone '%s' nie jest w %s, uzywam default", v, allowed)
        return default
    return v


def load_preferences(path: Path = PREFERENCES_PATH) -> Preferences:
    """Wczytaj preferences.yaml, waliduj, fallback do defaults dla brakujacych pol."""
    if not path.exists():
        log.warning("Brak %s - uzywam defaults", path)
        return Preferences()

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        log.error("Bledny YAML w %s: %s - uzywam defaults", path, e)
        return Preferences()

    prefs = Preferences(
        scripts_per_run=_coerce_int(raw.get("scripts_per_run"), 3, 1, 10),
        cta_intensity=_coerce_int(raw.get("cta_intensity"), 30, 0, 100),
        copy_similarity=_coerce_int(raw.get("copy_similarity"), 40, 0, 100),
        effort_level=_coerce_int(raw.get("effort_level"), 6, 1, 10),
        target_seconds=_coerce_int(raw.get("target_seconds"), 45, 15, 90),
        tone=_coerce_str(
            raw.get("tone"), "balanced",
            ["anti_guru", "hormozi", "storyteller", "kontrarian", "balanced"],
        ),
    )

    hraw = raw.get("hashtags") or {}
    if isinstance(hraw, dict):
        mix = hraw.get("mix") or {}
        prefs.hashtags = Hashtags(
            count=_coerce_int(hraw.get("count"), 18, 5, 30),
            niche_ratio=float(mix.get("niche", 0.5)),
            broad_ratio=float(mix.get("broad", 0.3)),
            branded_ratio=float(mix.get("branded", 0.2)),
        )

    mpraw = raw.get("multi_platform") or {}
    if isinstance(mpraw, dict):
        prefs.multi_platform = MultiPlatform(
            enabled=bool(mpraw.get("enabled", False)),
            platforms=list(mpraw.get("platforms") or ["tiktok"]),
        )

    rraw = raw.get("ratings") or {}
    if isinstance(rraw, dict):
        prefs.ratings = Ratings(
            enabled=bool(rraw.get("enabled", True)),
            use_history_in_prompts=bool(rraw.get("use_history_in_prompts", True)),
        )

    traw = raw.get("trending_hooks") or {}
    if isinstance(traw, dict):
        prefs.trending_hooks = TrendingHooks(
            enabled=bool(traw.get("enabled", False)),
            daily_count=_coerce_int(traw.get("daily_count"), 5, 1, 20),
        )

    nraw = raw.get("multi_niche") or {}
    if isinstance(nraw, dict):
        prefs.multi_niche = MultiNiche(
            enabled=bool(nraw.get("enabled", False)),
            active_niches=list(nraw.get("active_niches") or ["skala"]),
        )

    log.info(
        "Preferences loaded: scripts=%d, cta=%d%%, copy=%d%%, effort=%d (%s), len=%ds, tone=%s",
        prefs.scripts_per_run, prefs.cta_intensity, prefs.copy_similarity,
        prefs.effort_level, prefs.effort.label, prefs.target_seconds, prefs.tone,
    )
    return prefs
