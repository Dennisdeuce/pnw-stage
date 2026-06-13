"""Live Ticketmaster integration test (BUILD_SPEC §9.3).

Skips automatically when TICKETMASTER_API_KEY is absent, so unit CI stays green
without secrets. When a key IS present, it asserts the adapter returns at least
one Seattle-DMA music event and one comedy event with the required fields.
"""
import os

import pytest

from adapters.base import HttpClient
from adapters.ticketmaster import TicketmasterAdapter

pytestmark = pytest.mark.skipif(
    not os.environ.get("TICKETMASTER_API_KEY"),
    reason="TICKETMASTER_API_KEY not set — skipping live integration test.",
)


def _run(classifications):
    http = HttpClient()
    try:
        adapter = TicketmasterAdapter(
            slug="ticketmaster_seatac",
            config={
                "dma_id": 819,
                "classifications": classifications,
                "fallback_venue_slug": "tm-seattle-tacoma",
                "venue_index": {},
            },
            http=http,
        )
        return adapter.fetch()
    finally:
        http.close()


def test_live_music_events_present():
    events = _run(["music"])
    assert len(events) >= 1
    ev = events[0]
    assert ev.title
    assert ev.starts_at is not None
    assert ev.venue_slug
    # never a resale buy link
    assert (ev.raw.get("source") or "").lower() != "tmr"


def test_live_comedy_events_present():
    events = _run(["comedy"])
    assert len(events) >= 1
