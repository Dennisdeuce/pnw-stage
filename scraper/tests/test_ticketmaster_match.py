"""TM venue-name matching: venue_match helpers + TicketmasterAdapter routing.

Offline — exercises the §step-1 path that routes DMA events to the right venue row
by name/alias before falling back to the per-DMA catch-all.
"""
from adapters.ticketmaster import TicketmasterAdapter
from venue_match import normalize_venue_name, build_index, match_venue

VENUES = [
    {"slug": "the-showbox", "name": "The Showbox",
     "aliases": ["Showbox at the Market", "The Showbox", "Showbox Theatre"]},
    {"slug": "the-crocodile", "name": "The Crocodile", "aliases": ["Crocodile Cafe"]},
    {"slug": "wamu-theater", "name": "WaMu Theater",
     "aliases": ["WaMu Theater", "WAMU Theatre", "WAMU Theater"]},
    {"slug": "paramount-theatre", "name": "Paramount Theatre", "aliases": []},
    {"slug": "moore-theatre", "name": "Moore Theatre", "aliases": []},
    {"slug": "tractor-tavern", "name": "Tractor Tavern", "aliases": []},
    {"slug": "climate-pledge-arena", "name": "Climate Pledge Arena", "aliases": []},
]


# --- pure helpers -----------------------------------------------------------

def test_normalize_strips_filler_tokens():
    assert normalize_venue_name("The Showbox") == "showbox"
    assert normalize_venue_name("Paramount Theatre") == "paramount"
    assert normalize_venue_name("WAMU Theater, Seattle") == "wamu"
    assert normalize_venue_name("Moore Theater Seattle") == "moore"


def test_build_index_includes_names_and_aliases():
    idx = build_index(VENUES)
    assert idx[normalize_venue_name("Showbox at the Market")] == "the-showbox"
    assert idx[normalize_venue_name("Crocodile Cafe")] == "the-crocodile"
    assert idx["wamu"] == "wamu-theater"


def test_match_exact_alias_and_name():
    idx = build_index(VENUES)
    assert match_venue("Showbox at the Market", idx) == "the-showbox"
    assert match_venue("The Crocodile", idx) == "the-crocodile"
    assert match_venue("Crocodile Cafe", idx) == "the-crocodile"
    assert match_venue("WAMU Theatre", idx) == "wamu-theater"


def test_match_fuzzy_above_threshold():
    idx = build_index(VENUES)
    # token-set superset -> ratio 100, routes via the fuzzy fallback.
    assert match_venue("Tractor Tavern Ballroom", idx) == "tractor-tavern"


def test_match_returns_none_when_unknown():
    idx = build_index(VENUES)
    assert match_venue("Some Random Venue XYZ", idx) is None


# --- adapter routing --------------------------------------------------------

def _tm_event(venue_name=None, venue_id=None, date="2026-07-04"):
    return {
        "name": "Some Show",
        "dates": {"start": {"localDate": date}},
        "_embedded": {"venues": [{"name": venue_name, "id": venue_id}]},
        "url": "https://www.ticketmaster.com/event/abc",
    }


def _adapter():
    return TicketmasterAdapter(
        slug="ticketmaster_seatac",
        config={"_venues": VENUES, "fallback_venue_slug": "tm-seattle-tacoma"},
        http=None,
    )


def _route(adapter, ev, venue_index=None):
    raw = adapter._parse_event(ev, venue_index or {}, "tm-seattle-tacoma", "America/Los_Angeles")
    return raw.venue_slug


def test_adapter_routes_by_alias_name():
    a = _adapter()
    assert _route(a, _tm_event("Showbox at the Market")) == "the-showbox"
    assert _route(a, _tm_event("Paramount Theatre")) == "paramount-theatre"
    assert not a.unmatched  # all matched, nothing logged


def test_adapter_resolved_id_wins_over_name():
    a = _adapter()
    # Even with a junk name, a resolved Discovery id routes correctly.
    slug = _route(a, _tm_event("Totally Different Name", venue_id="K123"),
                  venue_index={"K123": "climate-pledge-arena"})
    assert slug == "climate-pledge-arena"


def test_adapter_unmatched_falls_back_and_logs():
    a = _adapter()
    assert _route(a, _tm_event("Nowhere Special Lounge")) == "tm-seattle-tacoma"
    assert _route(a, _tm_event("Nowhere Special Lounge")) == "tm-seattle-tacoma"
    assert a.unmatched["Nowhere Special Lounge"] == 2
    note = a.run_notes
    assert note and "Nowhere Special Lounge" in note
