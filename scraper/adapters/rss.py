"""RSS/Atom adapter (§3.1)."""
from __future__ import annotations

from datetime import datetime
from time import mktime
from typing import Any

import feedparser

from models import RawEvent
from .base import HttpClient


class RSSAdapter:
    kind = "rss"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def fetch(self) -> list[RawEvent]:
        url = self.config["feed_url"]
        venue_slug = self.config["venue_slug"]
        tz = self.config.get("tz", "America/Los_Angeles")
        resp = self.http.get(url)
        feed = feedparser.parse(resp.text)

        events: list[RawEvent] = []
        for entry in feed.entries:
            # Prefer an explicit event date; fall back to published date.
            start = None
            for key in ("published_parsed", "updated_parsed"):
                if entry.get(key):
                    start = datetime.fromtimestamp(mktime(entry[key]))
                    break
            events.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=venue_slug,
                    title=entry.get("title", "Untitled"),
                    starts_at=start,
                    tz=tz,
                    description=entry.get("summary"),
                    source_url=entry.get("link"),
                    venue_primary_url=entry.get("link"),
                    raw={"id": entry.get("id")},
                )
            )
        return events
