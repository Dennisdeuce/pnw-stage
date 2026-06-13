"""AXSAdapter unit test against a captured JSON-LD fixture (offline, deterministic)."""
import json
from pathlib import Path

from adapters.axs import AXSAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "axs_showbox.html"


class _Resp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def json(self):
        return json.loads(self.text)


class _FakeHttp:
    def __init__(self, resp):
        self._resp = resp
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        return self._resp


def _adapter():
    http = _FakeHttp(_Resp(FIXTURE.read_text(encoding="utf-8")))
    return AXSAdapter(
        slug="axs_the-showbox",
        config={"venue_slug": "the-showbox", "axs_venue_id": "101491"},
        http=http,
    ), http


def test_axs_parses_jsonld_events():
    adapter, http = _adapter()
    events = adapter.fetch()
    # Three Event-typed blocks (MusicEvent + Event + ComedyEvent); MusicVenue ignored.
    assert len(events) == 3
    titles = {e.title for e in events}
    assert titles == {"Charley Crockett", "Japanese Breakfast", "Comedy Night Live"}
    # The configured page_url was used.
    assert http.calls == ["https://www.axs.com/venues/101491"]


def test_axs_event_fields_and_url_resolution():
    adapter, _ = _adapter()
    by_title = {e.title: e for e in adapter.fetch()}

    crockett = by_title["Charley Crockett"]
    assert crockett.venue_slug == "the-showbox"
    assert crockett.source_slug == "axs_the-showbox"
    assert crockett.starts_at is not None
    assert crockett.starts_at.year == 2026 and crockett.starts_at.month == 7
    assert crockett.price_min == 39.5
    assert crockett.image_url == "https://media.axs.com/charley.jpg"
    # Relative offer url resolved to absolute against the listing origin.
    assert crockett.venue_primary_url == (
        "https://www.axs.com/events/555001/charley-crockett-tickets?src=buy"
    )

    # image given as a list -> first element; no offer -> falls back to event url.
    jbrekkie = by_title["Japanese Breakfast"]
    assert jbrekkie.image_url == "https://media.axs.com/jbrekkie.jpg"
    assert jbrekkie.venue_primary_url.endswith("/events/555002/japanese-breakfast-tickets")
    assert jbrekkie.price_min is None


def test_axs_http_error_raises_for_isolation():
    import pytest

    http = _FakeHttp(_Resp("blocked", status_code=403))
    adapter = AXSAdapter("axs_x", {"venue_slug": "the-showbox", "axs_venue_id": "1"}, http)
    with pytest.raises(RuntimeError):
        adapter.fetch()
