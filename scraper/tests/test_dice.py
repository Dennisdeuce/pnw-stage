"""DICEAdapter unit test against a captured v1 events JSON fixture (offline)."""
import json
from pathlib import Path

from adapters.dice import DICEAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "dice_crocodile.json"


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class _FakeHttp:
    def __init__(self, resp):
        self._resp = resp
        self.headers_seen = None

    def get(self, url, **kwargs):
        self.headers_seen = kwargs.get("headers")
        return self._resp


def _adapter():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    http = _FakeHttp(_Resp(payload))
    return DICEAdapter(
        slug="dice_the-crocodile",
        config={
            "venue_slug": "the-crocodile",
            "dice_venue": "the-crocodile",
            "events_url": "https://api.dice.fm/events?filter%5Bvenues%5D%5B%5D=the-crocodile",
        },
        http=http,
    )


def test_dice_parses_events_and_drops_dateless():
    events = _adapter().fetch()
    # Three items in fixture; the dateless "TBA Show" is dropped.
    assert len(events) == 2
    assert {e.title for e in events} == {"Mannequin Pussy", "Tomberlin"}


def test_dice_field_mapping():
    by_title = {e.title: e for e in _adapter().fetch()}

    mp = by_title["Mannequin Pussy"]
    assert mp.venue_slug == "the-crocodile"
    assert mp.source_slug == "dice_the-crocodile"
    assert mp.tz == "America/Los_Angeles"
    assert mp.status == "on_sale"
    assert mp.price_min == 25.0  # 2500 minor units -> 25.00
    assert mp.currency == "USD"
    assert mp.lineup == ["Mannequin Pussy", "Soul Glo"]
    assert mp.image_url == "https://dice-media.imgix.net/mp-landscape.jpg"
    assert mp.venue_primary_url == "https://dice.fm/event/mannequin-pussy-the-crocodile-2026"

    tom = by_title["Tomberlin"]
    assert tom.status == "sold_out"
    assert tom.price_min == 20.0
    # No landscape -> falls back to portrait image.
    assert tom.image_url == "https://dice-media.imgix.net/tomberlin.jpg"


def test_dice_http_error_raises_for_isolation():
    import pytest

    http = _FakeHttp(_Resp({}, status_code=500))
    adapter = DICEAdapter(
        "dice_x",
        {"venue_slug": "the-crocodile", "events_url": "https://api.dice.fm/x"},
        http,
    )
    with pytest.raises(RuntimeError):
        adapter.fetch()
