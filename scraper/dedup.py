"""Dedup key + merge policy (BUILD_SPEC §5.4).

natural_key = sha256(venue_id | date_local | normalize(title)).

Merge policy on conflict:
  - keep the original `first_seen` (drives "new since last visit"),
  - bump `last_seen`,
  - overwrite content fields ONLY from a lower (better) `source_priority`.

`merge_rows` implements the policy in-process so it can be unit-tested without a
database; the live pipeline relies on the same rules via Postgres upsert + the
`source_priority` guard (see db.py).
"""
from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Any

_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")
_NOISE = re.compile(
    r"\b(live in concert|in concert|live|tour \d{4}|\d{4} tour|the tour|"
    r"21\s*\+|18\s*\+|all ages|sold out)",
    re.IGNORECASE,
)


def _normalize_for_key(title: str) -> str:
    t = _NOISE.sub(" ", title or "")
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip().lower()
    return t


def natural_key(venue_id: int, date_local: date | str, title: str) -> str:
    d = date_local.isoformat() if isinstance(date_local, date) else str(date_local)
    basis = f"{venue_id}|{d}|{_normalize_for_key(title)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


# Fields that carry the original sighting and must never be clobbered on update.
_PRESERVE_ON_CONFLICT = ("first_seen",)
# Bookkeeping fields managed by the pipeline, not by source priority.
_BOOKKEEPING = ("natural_key", "venue_id", "last_seen", "updated_at")


def merge_rows(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Return the row to persist when `incoming` collides with `existing`.

    `existing` is what's already stored; `incoming` is the freshly scraped row.
    Lower source_priority wins for content. first_seen is always preserved.
    """
    merged = dict(existing)

    inc_priority = incoming.get("source_priority", 100)
    cur_priority = existing.get("source_priority", 100)

    if inc_priority <= cur_priority:
        # Incoming source is at least as authoritative — take its content.
        for k, v in incoming.items():
            if k in _PRESERVE_ON_CONFLICT:
                continue
            merged[k] = v

    # Always preserve the original first sighting.
    merged["first_seen"] = existing.get("first_seen")
    # Always refresh liveness.
    merged["last_seen"] = incoming.get("last_seen") or existing.get("last_seen")
    return merged
