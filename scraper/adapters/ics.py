"""iCal (.ics) adapter — the most stable source type (§3.1)."""
from __future__ import annotations

from typing import Any

from ics import Calendar

from models import RawEvent
from .base import HttpClient


class ICSAdapter:
    kind = "ics"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def fetch(self) -> list[RawEvent]:
        url = self.config["feed_url"]
        venue_slug = self.config["venue_slug"]
        tz = self.config.get("tz", "America/Los_Angeles")
        resp = self.http.get(url)
        cal = Calendar(resp.text)

        events: list[RawEvent] = []
        for ev in cal.events:
            start = ev.begin.datetime if ev.begin else None
            end = ev.end.datetime if ev.end else None
            events.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=venue_slug,
                    title=ev.name or "Untitled",
                    starts_at=start,
                    ends_at=end,
                    tz=tz,
                    description=ev.description or None,
                    source_url=ev.url or self.config.get("page_url"),
                    venue_primary_url=ev.url or None,
                    raw={"uid": ev.uid, "location": ev.location},
                )
            )
        return events
