from datetime import date

from dedup import natural_key, merge_rows


def test_natural_key_stable_across_noise():
    a = natural_key(7, date(2026, 7, 4), "Phoebe Bridgers LIVE (21+)")
    b = natural_key(7, "2026-07-04", "phoebe bridgers")
    assert a == b
    assert len(a) == 64


def test_natural_key_differs_by_venue_and_date():
    base = natural_key(7, date(2026, 7, 4), "Band")
    assert base != natural_key(8, date(2026, 7, 4), "Band")
    assert base != natural_key(7, date(2026, 7, 5), "Band")


def test_merge_preserves_first_seen_and_bumps_last_seen():
    existing = {
        "natural_key": "k", "title": "Old Title", "source_priority": 50,
        "first_seen": "2026-01-01T00:00:00Z", "last_seen": "2026-01-01T00:00:00Z",
    }
    incoming = {
        "natural_key": "k", "title": "New Title", "source_priority": 10,
        "first_seen": "2026-06-01T00:00:00Z", "last_seen": "2026-06-13T00:00:00Z",
    }
    merged = merge_rows(existing, incoming)
    # better (lower) priority wins content
    assert merged["title"] == "New Title"
    # first_seen never moves
    assert merged["first_seen"] == "2026-01-01T00:00:00Z"
    # last_seen bumps
    assert merged["last_seen"] == "2026-06-13T00:00:00Z"


def test_merge_keeps_content_when_incoming_is_worse_priority():
    existing = {
        "natural_key": "k", "title": "Authoritative", "source_priority": 10,
        "first_seen": "2026-01-01T00:00:00Z", "last_seen": "2026-01-01T00:00:00Z",
    }
    incoming = {
        "natural_key": "k", "title": "Generic TM Title", "source_priority": 50,
        "first_seen": "2026-06-01T00:00:00Z", "last_seen": "2026-06-13T00:00:00Z",
    }
    merged = merge_rows(existing, incoming)
    assert merged["title"] == "Authoritative"      # worse source can't clobber
    assert merged["first_seen"] == "2026-01-01T00:00:00Z"
    assert merged["last_seen"] == "2026-06-13T00:00:00Z"


def test_double_run_idempotency():
    """Running the same scrape twice must not change first_seen or duplicate."""
    first = {
        "natural_key": "k", "title": "Show", "source_priority": 10,
        "first_seen": "2026-06-13T08:00:00Z", "last_seen": "2026-06-13T08:00:00Z",
    }
    # Second identical run, later in the day (e.g. DST dual-cron).
    second = dict(first, last_seen="2026-06-13T12:00:00Z")
    merged = merge_rows(first, second)
    assert merged["first_seen"] == "2026-06-13T08:00:00Z"  # unchanged
    assert merged["title"] == "Show"
    assert merged["last_seen"] == "2026-06-13T12:00:00Z"
