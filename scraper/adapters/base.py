"""Adapter protocol, a polite HTTP client, and the config-driven factory."""
from __future__ import annotations

import time
from typing import Any, Protocol, runtime_checkable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import RawEvent

USER_AGENT = (
    "PNWStageBot/1.0 (+https://github.com/Dennisdeuce/Stage; concert aggregator; "
    "respects robots.txt)"
)


@runtime_checkable
class Adapter(Protocol):
    slug: str
    kind: str  # 'ics' | 'rss' | 'json' | 'ticketmaster' | 'html'

    def fetch(self) -> list[RawEvent]:
        ...


class HttpClient:
    """Shared httpx client with backoff and a per-host rate limit (§10.3: <=1 req/2s)."""

    def __init__(self, min_interval: float = 2.0, timeout: float = 20.0):
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        self._min_interval = min_interval
        self._last_hit: dict[str, float] = {}

    def _throttle(self, url: str) -> None:
        host = httpx.URL(url).host or ""
        now = time.monotonic()
        last = self._last_hit.get(host, 0.0)
        wait = self._min_interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        self._last_hit[host] = time.monotonic()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        self._throttle(url)
        resp = self._client.get(url, **kwargs)
        # Back off on 429/5xx; tenacity will retry these.
        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        return resp

    def close(self) -> None:
        self._client.close()


def build_adapter(source: dict[str, Any], http: HttpClient) -> Adapter:
    """Construct the right adapter from a `sources`/`venues` row.

    `source` must include: slug, kind, config (dict). For venue-bound adapters the
    config carries `venue_slug` and feed/selector details.
    """
    kind = source["kind"]
    # Imported here to avoid a circular import at module load.
    from .ics import ICSAdapter
    from .rss import RSSAdapter
    from .jsonfeed import JSONAdapter
    from .ticketmaster import TicketmasterAdapter
    from .html import HTMLAdapter
    from .stg import STGAdapter

    table = {
        "ics": ICSAdapter,
        "rss": RSSAdapter,
        "json": JSONAdapter,
        "ticketmaster": TicketmasterAdapter,
        "html": HTMLAdapter,
        "stg": STGAdapter,
    }
    cls = table.get(kind)
    if cls is None:
        raise ValueError(f"unknown adapter kind: {kind!r}")
    return cls(slug=source["slug"], config=source.get("config", {}), http=http)
