"""Normalized venue-name matching (coverage pass, §step 1).

Ticketmaster Discovery returns a venue *name* on every event but not always an id
we've resolved. To route those events to the right `venues` row we normalize names
(lowercase; strip "the", punctuation, "seattle", "theatre/theater") and match —
exact-normalized first, then a rapidfuzz token-set fallback at >= 0.90.

Pure functions, fully unit-testable without a network or DB.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from rapidfuzz import fuzz

_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")
# Tokens that add no venue identity and only hurt matching.
_DROP_TOKENS = {"the", "seattle", "theatre", "theater"}

FUZZY_THRESHOLD = 90.0  # token_set_ratio is 0..100


def normalize_venue_name(name: str | None) -> str:
    """Lowercase, strip punctuation + filler tokens, collapse whitespace."""
    t = _PUNCT.sub(" ", (name or "").lower())
    t = _WS.sub(" ", t).strip()
    tokens = [tok for tok in t.split(" ") if tok and tok not in _DROP_TOKENS]
    return " ".join(tokens)


def build_index(venues: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Map normalized name/alias -> venue slug.

    Each venue contributes its `name` and every entry in its `aliases` list. On a
    collision the first writer wins (names are seeded before generic aliases).
    """
    index: dict[str, str] = {}
    for v in venues:
        slug = v.get("slug")
        if not slug:
            continue
        candidates = [v.get("name")] + list(v.get("aliases") or [])
        for cand in candidates:
            key = normalize_venue_name(cand)
            if key and key not in index:
                index[key] = slug
    return index


def match_venue(name: str | None, index: dict[str, str]) -> Optional[str]:
    """Return the matched venue slug, or None.

    1) exact normalized lookup, 2) rapidfuzz token_set_ratio >= FUZZY_THRESHOLD.
    """
    key = normalize_venue_name(name)
    if not key:
        return None
    if key in index:
        return index[key]
    best_slug: Optional[str] = None
    best_score = 0.0
    for cand_key, slug in index.items():
        score = fuzz.token_set_ratio(key, cand_key)
        if score > best_score:
            best_score, best_slug = score, slug
    if best_score >= FUZZY_THRESHOLD:
        return best_slug
    return None
