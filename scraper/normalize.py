"""Turn a RawEvent into a row ready for the `events` table.

Pure functions, no I/O. Heavily unit-tested (see tests/test_normalize.py) because
this is where messy venue data becomes consistent — the part most likely to drift.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from models import RawEvent, NormalizedEvent
from dedup import natural_key

# --- title / lineup parsing -------------------------------------------------

# Words/suffixes that add no identity and only hurt dedup + display.
# No trailing \b: tokens like "21+" end in a non-word char, where \b never matches.
_NOISE = re.compile(
    r"\b(live in concert|in concert|live|tour \d{4}|\d{4} tour|the tour|"
    r"21\s*\+|18\s*\+|all ages|sold out|presented by .*)",
    re.IGNORECASE,
)
_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")

# Separators that introduce the supporting acts after a headliner. Commas need no
# surrounding space ("A, B"); keyword separators ("with", "feat.") need spaces.
_SUPPORT_SPLIT = re.compile(
    r"\s+(?:with|w/|feat\.?|featuring|special guests?|plus)\s+|\s*,\s*|\s+\+\s+",
    re.IGNORECASE,
)


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation + tour/age noise, collapse whitespace.

    Used to build the dedup natural key, NOT for display.
    """
    t = title or ""
    t = _NOISE.sub(" ", t)
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip().lower()
    return t


def split_lineup(title: str, explicit_lineup: list[str] | None) -> tuple[str, list[str]]:
    """Return (headliner, openers). Prefer an explicit lineup if the adapter gave one."""
    if explicit_lineup:
        head = explicit_lineup[0].strip()
        openers = [a.strip() for a in explicit_lineup[1:] if a.strip()]
        return head, openers

    parts = [p.strip() for p in _SUPPORT_SPLIT.split(title or "") if p.strip()]
    if not parts:
        return (title or "").strip(), []
    return parts[0], parts[1:]


# --- flag detection ---------------------------------------------------------

def detect_all_ages(text: str) -> Optional[bool]:
    t = (text or "").lower()
    if "all ages" in t or "all-ages" in t:
        return True
    if re.search(r"\b(21\s*\+|21 and over|21 and up)", t):
        return False
    if re.search(r"\b(18\s*\+|18 and over)", t):
        return False
    return None


def detect_free(text: str, price_min: Optional[float]) -> bool:
    if price_min is not None and price_min == 0:
        return True
    t = (text or "").lower()
    return bool(re.search(r"\b(free admission|free show|no cover|free entry)\b", t))


def detect_status(text: str, given: Optional[str]) -> str:
    if given:
        return given
    t = (text or "").lower()
    if "sold out" in t or "sold-out" in t:
        return "sold_out"
    if "cancel" in t:
        return "cancelled"
    if "postpone" in t:
        return "postponed"
    if "presale" in t or "pre-sale" in t:
        return "presale"
    return "on_sale"


# --- category inference -----------------------------------------------------

_COMEDY_HINTS = re.compile(
    r"\b(comedy|comedian|stand[- ]?up|improv|open mic|funny)\b", re.IGNORECASE
)
_ARTS_HINTS = re.compile(
    r"\b(symphony|orchestra|opera|ballet|recital|chamber|philharmonic|quartet)\b",
    re.IGNORECASE,
)


def infer_category(raw: RawEvent) -> str:
    if raw.category in ("music", "comedy", "arts", "other"):
        return raw.category
    haystack = " ".join(filter(None, [raw.title, raw.description or ""]))
    if _COMEDY_HINTS.search(haystack):
        return "comedy"
    if _ARTS_HINTS.search(haystack):
        return "arts"
    return "music"


# --- ticket link precedence (§3.4) -----------------------------------------

# Never emit these — resale or secondary markets.
RESALE_DOMAINS = (
    "stubhub.", "vividseats.", "seatgeek.com", "ticketsnow.", "tickpick.",
    "viagogo.", "/resale", "tmr.", "ticketmaster-resale",
)


def is_resale(url: str | None) -> bool:
    if not url:
        return False
    u = url.lower()
    return any(d in u for d in RESALE_DOMAINS)


def resolve_ticket_url(raw: RawEvent) -> tuple[Optional[str], Optional[str]]:
    """Return (ticket_url, ticket_url_type) by first non-resale match, §3.4 order."""
    candidates = [
        (raw.venue_primary_url, "venue_primary"),
        (raw.api_primary_url, "api_primary"),
        (raw.artist_offer_url, "artist"),
        # If the adapter already resolved a typed ticket_url, honor it.
        (raw.ticket_url, raw.ticket_url_type or "api_primary"),
        (raw.source_url, "venue_page"),
    ]
    for url, kind in candidates:
        if url and not is_resale(url):
            return url, kind
    return None, None


# --- datetime handling ------------------------------------------------------

def _to_utc(dt: Optional[datetime], tz: str) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt.astimezone(timezone.utc)


def _local_date(dt: Optional[datetime], tz: str) -> Optional[date]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(ZoneInfo(tz)).date()


# --- main entry point -------------------------------------------------------

def normalize(raw: RawEvent, venue_id: int, source_priority: int = 100) -> Optional[NormalizedEvent]:
    """Map a RawEvent to an `events` row dict. Returns None if unusable (no date)."""
    starts_utc = _to_utc(raw.starts_at, raw.tz)
    date_local = _local_date(raw.starts_at, raw.tz)
    if date_local is None:
        # An event with no date can't be placed on a calendar — drop it.
        return None

    headliner, openers = split_lineup(raw.title, raw.lineup)
    desc = raw.description or ""
    text_blob = " ".join(filter(None, [raw.title, desc]))

    ticket_url, ticket_type = resolve_ticket_url(raw)
    price_min = raw.price_min

    row: NormalizedEvent = {
        "natural_key": natural_key(venue_id, date_local, raw.title),
        "venue_id": venue_id,
        "title": (raw.title or "").strip(),
        "headliner": (raw.headliner or headliner) or None,
        "lineup": openers or None,
        "description": desc or None,
        "category": infer_category(raw),
        "genres": raw.genres or None,
        "starts_at": _iso(starts_utc),
        "doors_at": _iso(_to_utc(raw.doors_at, raw.tz)),
        "ends_at": _iso(_to_utc(raw.ends_at, raw.tz)),
        "date_local": date_local.isoformat(),
        "is_all_ages": raw.is_all_ages if raw.is_all_ages is not None else detect_all_ages(text_blob),
        "is_free": raw.is_free if raw.is_free is not None else detect_free(text_blob, price_min),
        "price_min": price_min,
        "price_max": raw.price_max,
        "currency": raw.currency or "USD",
        "status": detect_status(text_blob, raw.status),
        "onsale_at": _iso(_to_utc(raw.onsale_at, raw.tz)),
        "presale_at": _iso(_to_utc(raw.presale_at, raw.tz)),
        "ticket_url": ticket_url,
        "ticket_url_type": ticket_type,
        "image_url": raw.image_url,
        "source_slug": raw.source_slug,
        "source_url": raw.source_url,
        "source_priority": source_priority,
        "raw": raw.raw or {},
    }
    return row


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None
