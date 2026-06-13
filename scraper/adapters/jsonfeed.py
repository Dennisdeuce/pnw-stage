"""JSON endpoint adapter (§3.1).

Many venue calendars are React/Vue front-ends backed by a JSON API the page
already calls. Point this adapter at that endpoint and describe the shape in
config — no HTML parsing, far more stable than scraping.

config:
  feed_url:   the JSON endpoint
  venue_slug: registry slug
  items_path: dotted path to the list of events (e.g. "data.events"); "" = root
  map:        { target_field: dotted_path_within_item }
  tz:         optional timezone (default America/Los_Angeles)
"""
from __future__ import annotations

from typing import Any

from dateutil import parser as dateparser

from models import RawEvent
from .base import HttpClient


def _dig(obj: Any, path: str) -> Any:
    if not path:
        return obj
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


def _parse_dt(value: Any):
    if not value:
        return None
    if isinstance(value, (int, float)):
        # epoch seconds or millis
        from datetime import datetime, timezone
        secs = value / 1000 if value > 1e12 else value
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    try:
        return dateparser.parse(str(value))
    except (ValueError, OverflowError):
        return None


class JSONAdapter:
    kind = "json"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def fetch(self) -> list[RawEvent]:
        cfg = self.config
        venue_slug = cfg["venue_slug"]
        tz = cfg.get("tz", "America/Los_Angeles")
        mapping = cfg.get("map", {})

        resp = self.http.get(cfg["feed_url"])
        payload = resp.json()
        items = _dig(payload, cfg.get("items_path", "")) or []
        if isinstance(items, dict):
            items = list(items.values())

        events: list[RawEvent] = []
        for item in items:
            def m(field: str):
                p = mapping.get(field)
                return _dig(item, p) if p else None

            title = m("title")
            if not title:
                continue
            price_min = m("price_min")
            events.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=venue_slug,
                    title=str(title),
                    starts_at=_parse_dt(m("starts_at")),
                    doors_at=_parse_dt(m("doors_at")),
                    tz=tz,
                    description=m("description"),
                    headliner=m("headliner"),
                    price_min=float(price_min) if price_min not in (None, "") else None,
                    image_url=m("image_url"),
                    source_url=m("source_url"),
                    venue_primary_url=m("ticket_url") or m("source_url"),
                    raw=item if isinstance(item, dict) else {"value": item},
                )
            )
        return events
