"""Ticketmaster Discovery API adapter — primary discovery engine (§3.2).

Free key (5,000 calls/day, 5 req/sec). Query by DMA + classification, paginate
size=200. We FILTER OUT resale (`source == 'tmr'`) so a resale link never appears
as a "buy" link (§3.4). Requires env var TICKETMASTER_API_KEY; without it fetch()
raises, the pipeline logs the source as failed, and the run continues (§5.6, §9.6).
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from dateutil import parser as dateparser

from models import RawEvent
from venue_match import build_index, match_venue
from .base import HttpClient

API_BASE = "https://app.ticketmaster.com/discovery/v2/events.json"
PAGE_SIZE = 200
MAX_PAGES = 5  # 5 * 200 = 1000 events/classification/run — plenty, stays well under budget

# Map TM classification segment -> our category.
_SEGMENT_TO_CATEGORY = {
    "music": "music",
    "comedy": "comedy",
    "arts & theatre": "arts",
}


class TicketmasterAdapter:
    kind = "ticketmaster"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http
        self.api_key = os.environ.get("TICKETMASTER_API_KEY", "")
        # Normalized venue-name index, built from the registry the pipeline injects
        # under `_venues` (name + aliases -> slug). Empty when run standalone.
        self.name_index = build_index(config.get("_venues") or [])
        # TM venue names that fell through to the catch-all this run, with hit
        # counts — surfaced in source_runs.note for alias tuning (§step 1).
        self.unmatched: dict[str, int] = {}

    @property
    def run_notes(self) -> str | None:
        """Diagnostics the pipeline records in source_runs.note (None if clean)."""
        if not self.unmatched:
            return None
        top = sorted(self.unmatched.items(), key=lambda kv: kv[1], reverse=True)[:25]
        names = ", ".join(f"{n}×{c}" for n, c in top)
        return f"unmatched TM venues -> catch-all (add to venues.aliases): {names}"

    def fetch(self) -> list[RawEvent]:
        if not self.api_key:
            raise RuntimeError(
                "TICKETMASTER_API_KEY not set — see README 'ACTION REQUIRED'."
            )
        cfg = self.config
        dma_id = cfg.get("dma_id")
        classifications = cfg.get("classifications", ["music", "comedy"])
        venue_index: dict[str, str] = cfg.get("venue_index", {})
        fallback_slug = cfg["fallback_venue_slug"]
        tz = cfg.get("tz", "America/Los_Angeles")

        out: list[RawEvent] = []
        for classification in classifications:
            out.extend(
                self._fetch_classification(
                    classification, dma_id, venue_index, fallback_slug, tz
                )
            )
        return out

    def _fetch_classification(
        self, classification, dma_id, venue_index, fallback_slug, tz
    ) -> list[RawEvent]:
        results: list[RawEvent] = []
        for page in range(MAX_PAGES):
            params = {
                "apikey": self.api_key,
                "classificationName": classification,
                "size": PAGE_SIZE,
                "page": page,
                "sort": "date,asc",
                "source": "ticketmaster,frontgate,tmr,universe,axs",
            }
            if dma_id:
                params["dmaId"] = dma_id
            elif self.config.get("geo_point"):
                params["geoPoint"] = self.config["geo_point"]
                params["radius"] = self.config.get("radius", 50)
                params["unit"] = "miles"

            resp = self.http.get(API_BASE, params=params)
            if resp.status_code == 401:
                raise RuntimeError("Ticketmaster rejected the API key (401).")
            data = resp.json()
            embedded = data.get("_embedded", {})
            events = embedded.get("events", [])
            for ev in events:
                parsed = self._parse_event(ev, venue_index, fallback_slug, tz)
                if parsed:
                    results.append(parsed)

            page_info = data.get("page", {})
            if page + 1 >= page_info.get("totalPages", 0):
                break
        return results

    def _parse_event(self, ev, venue_index, fallback_slug, tz):
        # §3.4: never surface resale as a buy link.
        if (ev.get("source") or "").lower() == "tmr":
            return None

        tm_venues = (ev.get("_embedded") or {}).get("venues") or []
        tm_venue = tm_venues[0] if tm_venues else {}
        tm_venue_id = tm_venue.get("id")
        tm_venue_name = tm_venue.get("name")

        # Route to a registry venue: 1) resolved Discovery id, 2) normalized name,
        # 3) fuzzy name (>=0.90), else 4) per-DMA catch-all + log for alias tuning.
        venue_slug = venue_index.get(tm_venue_id or "")
        if not venue_slug:
            venue_slug = match_venue(tm_venue_name, self.name_index)
        if not venue_slug:
            venue_slug = fallback_slug
            if tm_venue_name:
                self.unmatched[tm_venue_name] = self.unmatched.get(tm_venue_name, 0) + 1

        dates = ev.get("dates", {})
        start = dates.get("start", {})
        starts_at = None
        if start.get("dateTime"):
            starts_at = dateparser.parse(start["dateTime"])  # tz-aware UTC from TM
        elif start.get("localDate"):
            date_str = start["localDate"] + ("T" + start["localTime"] if start.get("localTime") else "")
            try:
                starts_at = dateparser.parse(date_str)
            except (ValueError, OverflowError):
                starts_at = None
        if starts_at is None:
            return None

        # Status
        status_code = (dates.get("status") or {}).get("code", "onsale")
        status = {
            "onsale": "on_sale",
            "offsale": "sold_out",
            "cancelled": "cancelled",
            "postponed": "postponed",
            "rescheduled": "postponed",
        }.get(status_code, "on_sale")

        # Category from classification segment
        category = None
        classifications = ev.get("classifications") or []
        if classifications:
            seg = ((classifications[0].get("segment") or {}).get("name") or "").lower()
            category = _SEGMENT_TO_CATEGORY.get(seg)

        # Price
        price_min = price_max = None
        ranges = ev.get("priceRanges") or []
        if ranges:
            price_min = ranges[0].get("min")
            price_max = ranges[0].get("max")

        # Lineup from attractions
        attractions = (ev.get("_embedded") or {}).get("attractions") or []
        lineup = [a.get("name") for a in attractions if a.get("name")]

        # Image — pick a reasonably large 16:9
        image_url = None
        images = sorted(ev.get("images") or [], key=lambda i: i.get("width", 0), reverse=True)
        if images:
            image_url = images[0].get("url")

        # Presale
        presale_at = None
        sales = ev.get("sales") or {}
        presales = sales.get("presales") or []
        if presales and presales[0].get("startDateTime"):
            presale_at = dateparser.parse(presales[0]["startDateTime"])
        onsale_at = None
        public_sale = (sales.get("public") or {}).get("startDateTime")
        if public_sale:
            onsale_at = dateparser.parse(public_sale)

        return RawEvent(
            source_slug=self.slug,
            venue_slug=venue_slug,
            title=ev.get("name", "Untitled"),
            starts_at=starts_at,
            tz=tz,
            lineup=lineup,
            category=category,
            price_min=price_min,
            price_max=price_max,
            status=status,
            onsale_at=onsale_at,
            presale_at=presale_at,
            image_url=image_url,
            # TM event url is the primary on-sale link (we already excluded tmr).
            api_primary_url=ev.get("url"),
            source_url=ev.get("url"),
            raw={"tm_id": ev.get("id"), "tm_venue_id": tm_venue_id, "tm_venue_name": tm_venue_name},
        )
