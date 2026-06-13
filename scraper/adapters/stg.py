"""Seattle Theatre Group adapter — one adapter, three venues (§3.3 Tier-A).

Paramount, Moore, and Neptune share stgpresents.org. STG's listing tags each
event with its venue, so this single adapter routes events to the right registry
slug via `venue_map` (venue display name -> slug). Feed-first: if `feed_url`
(JSON) is configured we use it; otherwise we scrape the HTML listing.

config:
  page_url:    HTML listing (scrape fallback)
  feed_url:    optional JSON endpoint (preferred)
  base_url:    for relative links
  venue_map:   { "Paramount Theatre": "paramount-theatre", ... }
  default_venue_slug: used when the venue name can't be matched
  selectors:   CSS selectors for the HTML path (item/title/date/url/image/venue)
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from models import RawEvent
from .base import HttpClient


class STGAdapter:
    kind = "stg"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def _match_venue(self, name: str | None) -> str:
        venue_map: dict[str, str] = self.config.get("venue_map", {})
        if name:
            for label, slug in venue_map.items():
                if label.lower() in name.lower():
                    return slug
        return self.config["default_venue_slug"]

    def fetch(self) -> list[RawEvent]:
        if self.config.get("feed_url"):
            return self._fetch_json()
        return self._fetch_html()

    def _fetch_json(self) -> list[RawEvent]:
        resp = self.http.get(self.config["feed_url"])
        payload = resp.json()
        items = payload.get("events", payload if isinstance(payload, list) else [])
        tz = self.config.get("tz", "America/Los_Angeles")
        out: list[RawEvent] = []
        for it in items:
            title = it.get("title") or it.get("name")
            if not title:
                continue
            try:
                starts_at = dateparser.parse(str(it.get("date") or it.get("startDate")))
            except (ValueError, OverflowError, TypeError):
                starts_at = None
            out.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=self._match_venue(it.get("venue")),
                    title=title,
                    starts_at=starts_at,
                    tz=tz,
                    image_url=it.get("image"),
                    source_url=it.get("url"),
                    # STG's downstream primary ticketer is AXS; the event url is primary.
                    venue_primary_url=it.get("ticketUrl") or it.get("url"),
                    raw=it,
                )
            )
        return out

    def _fetch_html(self) -> list[RawEvent]:
        cfg = self.config
        sel = cfg["selectors"]
        base_url = cfg.get("base_url", cfg["page_url"])
        tz = cfg.get("tz", "America/Los_Angeles")
        resp = self.http.get(cfg["page_url"])
        soup = BeautifulSoup(resp.text, "lxml")

        out: list[RawEvent] = []
        for node in soup.select(sel["item"]):
            title_el = node.select_one(sel["title"]) if sel.get("title") else None
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                continue
            venue_el = node.select_one(sel["venue"]) if sel.get("venue") else None
            venue_name = venue_el.get_text(strip=True) if venue_el else None

            date_el = node.select_one(sel["date"]) if sel.get("date") else None
            starts_at = None
            if date_el:
                raw_date = date_el.get("datetime") or date_el.get_text(strip=True)
                try:
                    starts_at = dateparser.parse(raw_date, fuzzy=True)
                except (ValueError, OverflowError):
                    starts_at = None

            url = None
            if sel.get("url"):
                a = node.select_one(sel["url"])
                if a and a.has_attr("href"):
                    url = urljoin(base_url, a["href"])

            out.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=self._match_venue(venue_name),
                    title=title,
                    starts_at=starts_at,
                    tz=tz,
                    source_url=url,
                    venue_primary_url=url,
                    raw={"venue_name": venue_name},
                )
            )
        return out
