from datetime import datetime
from zoneinfo import ZoneInfo

from models import RawEvent
from normalize import (
    normalize, normalize_title, split_lineup, detect_all_ages, detect_free,
    detect_status, infer_category, resolve_ticket_url, is_resale,
)


def test_normalize_title_strips_noise_and_punctuation():
    assert normalize_title("Phoebe Bridgers — LIVE in Concert! (21+)") == "phoebe bridgers"
    assert normalize_title("The Mountain Goats 2025 Tour") == "the mountain goats"


def test_split_lineup_with_keywords():
    head, openers = split_lineup("Japanese Breakfast with Hand Habits, Mannequin Pussy", None)
    assert head == "Japanese Breakfast"
    assert openers == ["Hand Habits", "Mannequin Pussy"]


def test_split_lineup_prefers_explicit():
    head, openers = split_lineup("ignored", ["Headliner", "Opener A", "Opener B"])
    assert head == "Headliner"
    assert openers == ["Opener A", "Opener B"]


def test_detect_flags():
    assert detect_all_ages("This is an all ages show") is True
    assert detect_all_ages("Strictly 21+ event") is False
    assert detect_all_ages("no age info") is None
    assert detect_free("Free admission tonight", None) is True
    assert detect_free("", 0) is True
    assert detect_free("", 25) is False


def test_detect_status():
    assert detect_status("This show is SOLD OUT", None) == "sold_out"
    assert detect_status("presale starts friday", None) == "presale"
    assert detect_status("anything", "announced") == "announced"
    assert detect_status("regular show", None) == "on_sale"


def test_infer_category():
    assert infer_category(RawEvent("s", "v", "Stand-up Comedy Night")) == "comedy"
    assert infer_category(RawEvent("s", "v", "Seattle Symphony: Mahler 5")) == "arts"
    assert infer_category(RawEvent("s", "v", "Some Indie Band")) == "music"
    assert infer_category(RawEvent("s", "v", "x", category="comedy")) == "comedy"


def test_is_resale_blocklist():
    assert is_resale("https://www.stubhub.com/foo")
    assert is_resale("https://www.vividseats.com/bar")
    assert is_resale("https://www.ticketmaster.com/event/resale/123")
    assert not is_resale("https://www.axs.com/events/123")
    assert not is_resale("https://www.ticketmaster.com/event/123")


def test_resolve_ticket_url_precedence():
    raw = RawEvent(
        "s", "v", "Show",
        venue_primary_url="https://venue.com/buy",
        api_primary_url="https://www.ticketmaster.com/event/1",
        source_url="https://venue.com/event/1",
    )
    url, kind = resolve_ticket_url(raw)
    assert url == "https://venue.com/buy"
    assert kind == "venue_primary"


def test_resolve_ticket_url_skips_resale():
    raw = RawEvent(
        "s", "v", "Show",
        venue_primary_url="https://www.stubhub.com/x",   # resale -> skipped
        api_primary_url="https://www.ticketmaster.com/event/1",
    )
    url, kind = resolve_ticket_url(raw)
    assert url == "https://www.ticketmaster.com/event/1"
    assert kind == "api_primary"


def test_normalize_full_row_utc_and_local_date():
    # 8pm Pacific show
    raw = RawEvent(
        source_slug="tractor_tavern",
        venue_slug="tractor-tavern",
        title="Charley Crockett with The Blue Drifters",
        starts_at=datetime(2026, 7, 4, 20, 0, tzinfo=ZoneInfo("America/Los_Angeles")),
        venue_primary_url="https://www.tractortavern.com/e/1",
    )
    row = normalize(raw, venue_id=42, source_priority=10)
    assert row is not None
    assert row["venue_id"] == 42
    assert row["date_local"] == "2026-07-04"
    assert row["headliner"] == "Charley Crockett"
    assert row["lineup"] == ["The Blue Drifters"]
    assert row["category"] == "music"
    assert row["ticket_url_type"] == "venue_primary"
    # 8pm PDT == 03:00 UTC next day
    assert row["starts_at"].startswith("2026-07-05T03:00")
    assert len(row["natural_key"]) == 64


def test_normalize_drops_dateless_event():
    raw = RawEvent("s", "v", "No date show", starts_at=None)
    assert normalize(raw, venue_id=1) is None
