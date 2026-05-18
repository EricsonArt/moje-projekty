"""Multi-platform output - z 1 wygenerowanego skryptu robi 3 wariacje
(TikTok / Instagram Reels / YouTube Shorts).

Tweak'i per platforma:
- target length (TT 30s, Reels 45s, Shorts 60s)
- hashtagi platform-specific
- CTA wording (np. "link w bio" vs "checkout in description")
"""
from __future__ import annotations

import copy
from dataclasses import dataclass


PLATFORM_PROFILES = {
    "tiktok": {
        "label": "TikTok",
        "target_seconds": 30,
        "hashtag_pool": ["#fyp", "#foryoupage", "#viral", "#tiktokpolska", "#polska"],
        "cta_link": "link w bio",
    },
    "instagram": {
        "label": "Instagram Reels",
        "target_seconds": 45,
        "hashtag_pool": ["#reels", "#instagramreels", "#instaviral", "#explore", "#instabusiness"],
        "cta_link": "link w bio",
    },
    "youtube_shorts": {
        "label": "YouTube Shorts",
        "target_seconds": 60,
        "hashtag_pool": ["#shorts", "#shortsfeed", "#youtubeshorts", "#shortvideo"],
        "cta_link": "link w opisie",
    },
}


def adapt_script_for_platform(script: dict, platform: str) -> dict:
    """Zwroc plytka kopie skryptu z drobnymi tweakami pod platforme."""
    profile = PLATFORM_PROFILES.get(platform)
    if not profile:
        return script

    adapted = copy.deepcopy(script)
    adapted["platform"] = platform
    adapted["platform_label"] = profile["label"]

    # Hashtagi: zamien pierwsze 2-3 pierwsze na platform-specific
    base_hashtags = adapted.get("hashtags") or []
    if isinstance(base_hashtags, list) and base_hashtags:
        platform_tags = profile["hashtag_pool"][:3]
        # Wyrzuc duplikaty z platform tags z bazowych
        filtered = [h for h in base_hashtags if h not in platform_tags]
        adapted["hashtags"] = platform_tags + filtered

    # CTA placeholder swap (jezeli mam "link w bio" w skrypcie zamien na to z profilu)
    full = adapted.get("full_script", "")
    if isinstance(full, str):
        for placeholder in ("link w bio", "link w opisie", "checkout in description"):
            if placeholder in full.lower():
                full = full.replace(placeholder, profile["cta_link"])
                full = full.replace(placeholder.capitalize(), profile["cta_link"])
        adapted["full_script"] = full

    return adapted


def fan_out_to_platforms(script: dict, platforms: list[str]) -> list[dict]:
    """Z 1 oryginalnego skryptu zrob N wersji per platforma. Jezeli platforms pusta -
    zwroc tylko oryginal."""
    if not platforms:
        return [script]
    return [adapt_script_for_platform(script, p) for p in platforms]
