"""Guards on the seed registry: aliases + platform tags + source activation.

Pure (no Supabase) — calls venue_rows()/source_rows() directly. Keeps the seed in
lock-step with migration 0005 and the adapter set so the registry can't drift.
"""
from adapters.base import build_adapter
from seed_venues import venue_rows, source_rows

KNOWN_ADAPTER_KINDS = {"ics", "rss", "json", "ticketmaster", "html", "stg", "axs", "dice"}


def _venue(rows, slug):
    return next(r for r in rows if r["slug"] == slug)


def _source(rows, slug):
    return next(r for r in rows if r["slug"] == slug)


def test_aliases_seeded_on_venues():
    rows = venue_rows()
    assert "Showbox at the Market" in _venue(rows, "the-showbox")["aliases"]
    assert "Crocodile Cafe" in _venue(rows, "the-crocodile")["aliases"]
    assert "WAMU Theatre" in _venue(rows, "wamu-theater")["aliases"]
    # Every venue carries an aliases list (mirrors the text[] column default).
    assert all(isinstance(r["aliases"], list) for r in rows)


def test_platform_hints_in_source_config():
    rows = venue_rows()
    croc = _venue(rows, "the-crocodile")["source_config"]
    assert croc["platform"] == "dice"
    assert croc["tm_web_venue_id"] == "123027"
    assert _venue(rows, "tractor-tavern")["source_config"]["axs_venue_id"] == "123396"
    assert _venue(rows, "the-showbox")["source_config"]["axs_venue_id"] == "101491"


def test_platform_sources_generated_and_activated():
    rows = source_rows()
    # AXS + DICE adapters exist -> active.
    assert _source(rows, "axs_the-showbox")["is_active"] is True
    assert _source(rows, "axs_the-showbox")["config"]["axs_venue_id"] == "101491"
    assert _source(rows, "dice_the-crocodile")["is_active"] is True
    # Tail platforms have no adapter yet -> inactive placeholders.
    assert _source(rows, "house_jazz-alley")["is_active"] is False
    assert _source(rows, "tessitura_benaroya-hall")["is_active"] is False
    assert _source(rows, "tessitura_meany-center")["is_active"] is False
    assert _source(rows, "tixr_tacoma-comedy-club")["is_active"] is False


def test_big_room_html_sources_stay_active_tail_disabled():
    rows = source_rows()
    # Step 5: Tractor/Croc/Showbox HTML kept active until a live TM run confirms.
    for slug in ("tractor-tavern", "the-crocodile", "the-showbox"):
        assert _source(rows, slug)["is_active"] is True
    # Tail venues' dead generic-HTML sources are disabled (moved to platforms).
    for slug in ("jazz-alley", "benaroya-hall", "meany-center", "tacoma-comedy-club"):
        assert _source(rows, slug)["is_active"] is False


def test_every_active_source_has_a_real_adapter():
    rows = source_rows()
    for s in rows:
        if s["is_active"]:
            assert s["kind"] in KNOWN_ADAPTER_KINDS, f"{s['slug']} -> {s['kind']}"
            # build_adapter must construct without error for active sources.
            build_adapter(s, http=None)


# --- migration 0006 curation mirror -----------------------------------------

def test_curated_tm_venue_ids_and_aliases_seeded():
    rows = venue_rows()
    gorge = _venue(rows, "gorge-amphitheatre")
    assert gorge["tm_venue_id"] == "KovZpZAEkk1A"
    assert "The Gorge" in gorge["aliases"]
    # Existing venue: only tm_venue_id/aliases/is_active overridden (kind preserved).
    benaroya = _venue(rows, "benaroya-hall")
    assert benaroya["tm_venue_id"] == "Z7r9jZadcG"
    assert benaroya["source_kind"] == "html"  # not flipped to ticketmaster on conflict


def test_eastern_wa_venues_seeded_inactive():
    rows = venue_rows()
    for slug in ("knitting-factory-spokane", "northern-quest-casino",
                 "toyota-center-kennewick", "numerica-veterans-arena"):
        v = _venue(rows, slug)
        assert v["is_active"] is False, slug
        assert v["region"] == "spokane" or v["metro"] == "eastern_wa"


def test_seatac_source_carries_geo_filter_only():
    rows = source_rows()
    gf = _source(rows, "ticketmaster_seatac")["config"]["geo_filter"]
    assert gf["max_miles"] == 130
    assert gf["keep_tm_venue_ids"] == ["KovZpZAEkk1A"]  # Gorge kept
    # Portland/Vancouver must NOT be anchored to Seattle (no geo_filter).
    assert "geo_filter" not in _source(rows, "ticketmaster_portland")["config"]
    assert "geo_filter" not in _source(rows, "ticketmaster_vancouver_bc")["config"]
