"""AXS platform adapter (coverage pass).

ONE config-driven adapter for every AXS venue — not a scraper per club. AXS venue
listing pages (axs.com/venues/{axs_venue_id}) embed their events as schema.org
JSON-LD (`<script type="application/ld+json">`), which is far more stable than
CSS selectors. We parse those Event objects into RawEvents.

config:
  venue_slug:   registry slug every event from this page belongs to
  axs_venue_id: numeric AXS venue id (used to build page_url if not given)
  page_url:     listing page (default https://www.axs.com/venues/{axs_venue_id})
  tz:           optional timezone (default America/Los_Angeles)

Failure isolation: a 403/blocked page or markup change yields zero events and a
red source-health badge — it never breaks other adapters (§5.6). The exact live
markup is bot-protected, so the captured fixture in tests/fixtures/ pins the
JSON-LD shape this parser targets; validate against a live page when AXS allows.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from models import RawEvent
from .base import HttpClient

# schema.org @type values that represent a ticketed show.
_EVENT_TYPES = {"event", "musicevent", "comedyevent", "theaterevent", "festival"}


def _is_event(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    t = obj.get("@type")
    types = [t] if isinstance(t, str) else (t or [])
    return any(str(x).lower() in _EVENT_TYPES for x in types)


def _iter_jsonld(soup: BeautifulSoup):
    """Yield every dict found in any ld+json block (unwrapping @graph / lists)."""
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                if "@graph" in node and isinstance(node["@graph"], list):
                    stack.extend(node["@graph"])
                yield node


class AXSAdapter:
    kind = "axs"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def _page_url(self) -> str:
        if self.config.get("page_url"):
            return self.config["page_url"]
        return f"https://www.axs.com/venues/{self.config['axs_venue_id']}"

    def fetch(self) -> list[RawEvent]:
        cfg = self.config
        venue_slug = cfg["venue_slug"]
        tz = cfg.get("tz", "America/Los_Angeles")
        page_url = self._page_url()

        resp = self.http.get(page_url)
        if resp.status_code >= 400:
            raise RuntimeError(f"AXS {venue_slug}: HTTP {resp.status_code} from {page_url}")
        soup = BeautifulSoup(resp.text, "lxml")

        out: list[RawEvent] = []
        seen: set[str] = set()
        for obj in _iter_jsonld(soup):
            if not _is_event(obj):
                continue
            ev = self._parse_event(obj, venue_slug, tz, page_url)
            if ev and ev.title not in seen:
                seen.add(ev.title + str(ev.starts_at))
                out.append(ev)
        return out

    def _parse_event(self, obj, venue_slug, tz, base_url) -> RawEvent | None:
        name = obj.get("name")
        start = obj.get("startDate") or obj.get("startTime")
        if not (name and start):
            return None
        try:
            starts_at = dateparser.parse(str(start))
        except (ValueError, OverflowError, TypeError):
            return None

        url = obj.get("url")
        if isinstance(url, str) and url:
            url = urljoin(base_url, url)
        else:
            url = None

        image = obj.get("image")
        if isinstance(image, dict):
            image = image.get("url")
        if isinstance(image, list):
            image = image[0] if image else None

        offers = obj.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        price_min = None
        offer_url = None
        if isinstance(offers, dict):
            raw_price = offers.get("price") or offers.get("lowPrice")
            try:
                price_min = float(raw_price) if raw_price is not None else None
            except (ValueError, TypeError):
                price_min = None
            offer_url = offers.get("url")
            if isinstance(offer_url, str):
                offer_url = urljoin(base_url, offer_url)

        return RawEvent(
            source_slug=self.slug,
            venue_slug=venue_slug,
            title=name,
            starts_at=starts_at,
            tz=tz,
            description=obj.get("description"),
            price_min=price_min,
            image_url=image if isinstance(image, str) else None,
            # AXS is the primary ticketer for these rooms — the offer/event url buys.
            venue_primary_url=offer_url or url,
            source_url=url,
            raw={"platform": "axs"},
        )
