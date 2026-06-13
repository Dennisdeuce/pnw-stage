"""Generic HTML scraper (§3.1 last resort).

Fragile by nature — wrapped in source-health monitoring by the pipeline. Use only
when a venue has no .ics/RSS/JSON feed. Everything is config-driven via CSS
selectors so most venues need no bespoke code.

config:
  page_url:   the calendar page to scrape
  venue_slug: registry slug
  base_url:   for resolving relative hrefs (default = page_url origin)
  selectors:  { item, title, date, url, image, description, price }
  date_attr:  optional attribute to read the date from (e.g. "datetime")
  tz:         optional timezone
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from models import RawEvent
from .base import HttpClient


class HTMLAdapter:
    kind = "html"

    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient):
        self.slug = slug
        self.config = config
        self.http = http

    def _text(self, node, selector):
        if not selector or node is None:
            return None
        el = node.select_one(selector)
        return el.get_text(strip=True) if el else None

    def fetch(self) -> list[RawEvent]:
        cfg = self.config
        page_url = cfg["page_url"]
        venue_slug = cfg["venue_slug"]
        base_url = cfg.get("base_url", page_url)
        tz = cfg.get("tz", "America/Los_Angeles")
        sel = cfg["selectors"]
        date_attr = cfg.get("date_attr")

        resp = self.http.get(page_url)
        soup = BeautifulSoup(resp.text, "lxml")

        events: list[RawEvent] = []
        for node in soup.select(sel["item"]):
            title = self._text(node, sel.get("title"))
            if not title:
                continue

            # Date: from an attribute (e.g. <time datetime="...">) or text.
            date_val = None
            if date_attr and sel.get("date"):
                el = node.select_one(sel["date"])
                if el and el.has_attr(date_attr):
                    date_val = el[date_attr]
            if not date_val:
                date_val = self._text(node, sel.get("date"))
            starts_at = None
            if date_val:
                try:
                    starts_at = dateparser.parse(date_val, fuzzy=True)
                except (ValueError, OverflowError):
                    starts_at = None

            # Link
            url = None
            if sel.get("url"):
                a = node.select_one(sel["url"])
                if a and a.has_attr("href"):
                    url = urljoin(base_url, a["href"])

            # Image
            image_url = None
            if sel.get("image"):
                img = node.select_one(sel["image"])
                if img and img.has_attr("src"):
                    image_url = urljoin(base_url, img["src"])

            events.append(
                RawEvent(
                    source_slug=self.slug,
                    venue_slug=venue_slug,
                    title=title,
                    starts_at=starts_at,
                    tz=tz,
                    description=self._text(node, sel.get("description")),
                    image_url=image_url,
                    source_url=url,
                    venue_primary_url=url,
                    raw={},
                )
            )
        return events
