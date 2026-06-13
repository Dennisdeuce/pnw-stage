"""DICE platform adapter (coverage pass).

ONE config-driven adapter for every DICE venue. DICE exposes per-venue events as
JSON (the v1 `events` shape: a top-level `data` array of event objects), so unlike
HTML scraping this is structured and stable. Start: the-crocodile.

config:
  venue_slug: registry slug every event belongs to
  events_url: the per-venue DICE events JSON endpoint
  dice_venue: DICE permalink slug (used only for logging / url building)
  tz:         optional fallback timezone (DICE returns a per-event `timezone`)

Auth: DICE's public endpoint accepts an `x-api-key`; if env DICE_API_KEY is set we
send it, otherwise we try unauthenticated and fail soft (logged to source_runs).
Failure isolation: a non-200 or shape change yields zero events, never breaks
other adapters (§5.6). The captured fixture in tests/fixtures/ pins the v1 shape.
"""
from __future__ import annotations

import os
from typing import Any

from dateutil import parser as dateparser

from models import RawEvent
from .base import HttpClient

# DICE statuses -> our event status vocabulary.
_STATUS = {
    "on-sale": "on_sale",
    "sold-out": "sold_out",
    "off-sale": "sold_out",
    "cancelled": "cancelled",
    "postponed": "postponed",
    "announced": "announced",
}


class DICEAdapter:
    kind = "dice"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def fetch(self) -> list[RawEvent]:
        cfg = self.config
        venue_slug = cfg["venue_slug"]
        url = cfg["events_url"]
        tz_default = cfg.get("tz", "America/Los_Angeles")

        headers = {"Accept": "application/json"}
        api_key = os.environ.get("DICE_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        resp = self.http.get(url, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"DICE {venue_slug}: HTTP {resp.status_code} from {url}")
        payload = resp.json()
        # v1 shape is {"data": [...]}; tolerate a bare list too.
        items = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []

        out: list[RawEvent] = []
        for it in items:
            ev = self._parse_event(it, venue_slug, tz_default)
            if ev:
                out.append(ev)
        return out

    def _parse_event(self, it: dict, venue_slug: str, tz_default: str) -> RawEvent | None:
        if not isinstance(it, dict):
            return None
        name = it.get("name")
        start = it.get("date") or (it.get("dates") or {}).get("event_start_date")
        if not (name and start):
            return None
        try:
            starts_at = dateparser.parse(str(start))
        except (ValueError, OverflowError, TypeError):
            return None
        tz = it.get("timezone") or tz_default

        images = it.get("event_images") or {}
        image_url = images.get("landscape") or images.get("portrait") or images.get("square")

        # Price: DICE quotes minor units (cents).
        price_min = None
        price = it.get("price") or {}
        amount = price.get("amount")
        if amount is not None:
            try:
                price_min = float(amount) / 100.0
            except (ValueError, TypeError):
                price_min = None
        currency = (price.get("currency") or "USD").upper()

        status = _STATUS.get(str(it.get("status") or "").lower(), "on_sale")

        url = it.get("url")
        if not url and it.get("perm_name"):
            url = f"https://dice.fm/event/{it['perm_name']}"

        # Lineup from summary_lineup if present.
        lineup = []
        for artist in (it.get("summary_lineup") or {}).get("top_artists") or []:
            if isinstance(artist, dict) and artist.get("name"):
                lineup.append(artist["name"])

        return RawEvent(
            source_slug=self.slug,
            venue_slug=venue_slug,
            title=name,
            starts_at=starts_at,
            tz=tz,
            lineup=lineup,
            description=it.get("about", {}).get("description") if isinstance(it.get("about"), dict) else None,
            price_min=price_min,
            currency=currency,
            status=status,
            image_url=image_url,
            # DICE is the primary ticketer — its event url is the buy link.
            venue_primary_url=url,
            source_url=url,
            raw={"platform": "dice", "dice_id": it.get("id")},
        )
