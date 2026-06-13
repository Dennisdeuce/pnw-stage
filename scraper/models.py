"""Typed data structures shared across adapters and the pipeline.

A `RawEvent` is what every adapter emits: a loosely-typed, source-shaped record.
`normalize.normalize()` turns it into a `NormalizedEvent` (a dict ready to upsert
into the `events` table). Adapters never touch the database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


# Categories we classify into. Anything unknown falls back to 'other'.
CATEGORIES = ("music", "comedy", "arts", "other")

# ticket_url_type precedence values (BUILD_SPEC §3.4).
TICKET_TYPES = ("venue_primary", "api_primary", "artist", "venue_page")


@dataclass
class RawEvent:
    """Source-shaped event. Fields are optional because sources vary wildly.

    `venue_slug` ties the event back to a row in the `venues` registry so the
    pipeline can resolve `venue_id`, timezone, and source priority.
    """
    source_slug: str
    venue_slug: str
    title: str

    # When — adapters may provide either a tz-aware datetime or a naive one plus
    # a tz name; normalize() resolves to UTC + a local calendar date.
    starts_at: Optional[datetime] = None
    doors_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    tz: str = "America/Los_Angeles"

    # What
    headliner: Optional[str] = None
    lineup: list[str] = field(default_factory=list)
    description: Optional[str] = None
    category: Optional[str] = None          # let normalize() infer if None
    genres: list[str] = field(default_factory=list)

    # Commerce / status
    is_all_ages: Optional[bool] = None
    is_free: Optional[bool] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: str = "USD"
    status: Optional[str] = None
    onsale_at: Optional[datetime] = None
    presale_at: Optional[datetime] = None

    # Links
    ticket_url: Optional[str] = None
    ticket_url_type: Optional[str] = None   # if the adapter already knows the kind
    venue_primary_url: Optional[str] = None # candidate for §3.4 tier 1
    api_primary_url: Optional[str] = None   # candidate for §3.4 tier 2
    artist_offer_url: Optional[str] = None  # candidate for §3.4 tier 3
    source_url: Optional[str] = None        # canonical event page (fallback tier 4)
    image_url: Optional[str] = None

    raw: dict[str, Any] = field(default_factory=dict)


# A NormalizedEvent is just a plain dict keyed by `events` column names.
NormalizedEvent = dict[str, Any]
