"""Seed the venue + source registry (BUILD_SPEC §3.3).

Run once after migrations: `python seed_venues.py`. Idempotent — upserts by slug.

Source-type strategy (§3.1): feed-first. Big rooms come through the Ticketmaster
Discovery API (queried by DMA, not per-venue). Clubs/arts/comedy use per-venue
HTML adapters whose CSS selectors live in `source_config.selectors`.

IMPORTANT (honesty note): the HTML `page_url`/`selectors` below are best-effort
scaffolding. This build environment is network-restricted, so they could not be
validated live. Wrong selectors simply yield zero events and surface as a red
source-health badge — they never break other adapters (§5.6). Tune them against
each live site and flip `verified` to true.

Ticketmaster venue routing: until real `tm_venue_id`s are resolved and cached
(populate `venue_index` in the TM sources / `venues.tm_venue_id`), TM events land
on per-DMA catch-all venues (tm-seattle-tacoma, tm-portland, tm-vancouver-bc).
"""
from __future__ import annotations

import os

# A generic selector template for venue calendar pages. Override per-venue as needed.
GENERIC_SELECTORS = {
    "item": ".event, .eventItem, article.event, li.event",
    "title": ".title, .event-title, h3, h2",
    "date": "time, .date, .event-date",
    "url": "a",
    "image": "img",
    "description": ".description, .summary",
}

# --- Venue aliases (mirrors migration 0005's venues.aliases column) ----------
# Alternate names a venue appears under in the Ticketmaster Discovery feed. These
# feed the normalized name index in adapters/ticketmaster.py so a DMA event whose
# TM venue name is "Showbox at the Market" routes to `the-showbox` instead of the
# per-DMA catch-all. Keep in lock-step with what 0005 documents — no drift.
ALIASES: dict[str, list[str]] = {
    "the-showbox": ["Showbox at the Market", "The Showbox", "Showbox Theatre"],
    "showbox-sodo": ["Showbox SoDo", "Showbox SODO", "Showbox Sodo"],
    "the-crocodile": ["Crocodile Cafe", "The Crocodile"],
    "wamu-theater": ["WaMu Theater", "WAMU Theatre", "WAMU Theater"],
}

# --- Platform tags (the §coverage insight: ticketing fragments onto ~5 platforms)
# Instead of 35 bespoke HTML scrapers we tag each fragmented venue with the
# platform it actually sells on, plus the ids those platform adapters need.
#   platform        : 'axs' | 'dice' | 'tessitura' | 'tixr' | 'house'
#   axs_venue_id    : numeric AXS venue id (axs.com/venues/{id})
#   tm_web_venue_id : legacy TicketWeb/TM-classic id (hint; the Discovery K-id is
#                     resolved separately by resolve_tm_venues.py into tm_venue_id)
#   dice_venue      : DICE per-venue permalink slug
# axs/dice adapters EXIST -> their sources are active. The tail (tessitura/tixr/
# house) has no adapter yet -> those sources are seeded is_active=False.
VENUE_PLATFORMS: dict[str, dict] = {
    "the-showbox":    {"platform": "axs",  "axs_venue_id": "101491"},
    "showbox-sodo":   {"platform": "axs",  "axs_venue_id": "101493"},
    "tractor-tavern": {"platform": "axs",  "axs_venue_id": "123396", "tm_web_venue_id": "123019"},
    "the-crocodile":  {"platform": "dice", "axs_venue_id": "102301", "tm_web_venue_id": "123027",
                       "dice_venue": "the-crocodile"},
    # ---- tail: tagged now, adapters deferred (sources stay inactive) ----
    "jazz-alley":         {"platform": "house"},
    "benaroya-hall":      {"platform": "tessitura"},
    "meany-center":       {"platform": "tessitura"},
    "tacoma-comedy-club": {"platform": "tixr"},
}

# Platforms we have a working adapter for today.
_ADAPTER_READY = {"axs", "dice"}

# (slug, name, metro, region, city, state, website, source_kind, lat, lng)
VENUES = [
    # ---- Seattle core: STG ----
    ("paramount-theatre", "Paramount Theatre", "seattle", "core", "Seattle", "WA", "https://www.stgpresents.org", "stg", 47.6131, -122.3318),
    ("moore-theatre", "Moore Theatre", "seattle", "core", "Seattle", "WA", "https://www.stgpresents.org", "stg", 47.6109, -122.3417),
    ("neptune-theatre", "Neptune Theatre", "seattle", "core", "Seattle", "WA", "https://www.stgpresents.org", "stg", 47.6615, -122.3138),
    # ---- Seattle core: big rooms via Ticketmaster ----
    ("climate-pledge-arena", "Climate Pledge Arena", "seattle", "core", "Seattle", "WA", "https://www.climatepledgearena.com", "ticketmaster", 47.6221, -122.3540),
    ("wamu-theater", "WaMu Theater", "seattle", "core", "Seattle", "WA", "https://www.wamutheater.com", "ticketmaster", 47.5952, -122.3318),
    ("lumen-field", "Lumen Field & Event Center", "seattle", "core", "Seattle", "WA", "https://www.lumenfield.com", "ticketmaster", 47.5952, -122.3316),
    ("t-mobile-park", "T-Mobile Park", "seattle", "core", "Seattle", "WA", "https://www.mlb.com/mariners/ballpark", "ticketmaster", 47.5914, -122.3325),
    # ---- Seattle core: clubs (HTML) ----
    ("the-showbox", "The Showbox", "seattle", "core", "Seattle", "WA", "https://www.showboxpresents.com", "html", 47.6086, -122.3387),
    ("showbox-sodo", "Showbox SoDo", "seattle", "core", "Seattle", "WA", "https://www.showboxpresents.com", "html", 47.5806, -122.3340),
    ("little-red-hen", "Little Red Hen", "seattle", "core", "Seattle", "WA", "https://www.littleredhen.com", "html", 47.6797, -122.3275),
    ("tractor-tavern", "Tractor Tavern", "seattle", "core", "Seattle", "WA", "https://www.tractortavern.com", "html", 47.6686, -122.3848),
    ("el-corazon", "El Corazón", "seattle", "core", "Seattle", "WA", "https://www.elcorazonseattle.com", "html", 47.6196, -122.3306),
    ("the-crocodile", "The Crocodile", "seattle", "core", "Seattle", "WA", "https://www.thecrocodile.com", "html", 47.6133, -122.3430),
    ("neumos", "Neumos", "seattle", "core", "Seattle", "WA", "https://www.neumos.com", "html", 47.6140, -122.3199),
    ("barboza", "Barboza", "seattle", "core", "Seattle", "WA", "https://www.thebarboza.com", "html", 47.6140, -122.3199),
    ("nectar-lounge", "Nectar Lounge", "seattle", "core", "Seattle", "WA", "https://www.nectarlounge.com", "html", 47.6517, -122.3553),
    ("the-triple-door", "The Triple Door", "seattle", "core", "Seattle", "WA", "https://www.thetripledoor.net", "html", 47.6080, -122.3360),
    ("jazz-alley", "Dimitriou's Jazz Alley", "seattle", "core", "Seattle", "WA", "https://www.jazzalley.com", "html", 47.6157, -122.3360),
    ("benaroya-hall", "Benaroya Hall (Seattle Symphony)", "seattle", "core", "Seattle", "WA", "https://www.seattlesymphony.org", "html", 47.6080, -122.3370),
    ("meany-center", "Meany Center (UW)", "seattle", "core", "Seattle", "WA", "https://www.meanycenter.org", "html", 47.6557, -122.3093),
    ("mccaw-hall", "McCaw Hall", "seattle", "core", "Seattle", "WA", "https://www.mccawhall.com", "html", 47.6248, -122.3499),
    ("the-vera-project", "The Vera Project", "seattle", "core", "Seattle", "WA", "https://www.theveraproject.org", "html", 47.6244, -122.3543),
    # ---- Comedy ----
    ("comedy-underground", "Comedy Underground", "seattle", "core", "Seattle", "WA", "https://www.comedyunderground.com", "html", 47.6010, -122.3340),
    ("jet-city-improv", "Jet City Improv", "seattle", "core", "Seattle", "WA", "https://www.jetcityimprov.org", "html", 47.6628, -122.3215),
    ("tacoma-comedy-club", "Tacoma Comedy Club", "tacoma", "south", "Tacoma", "WA", "https://www.tacomacomedyclub.com", "html", 47.2510, -122.4410),
    ("parlor-live-bellevue", "Parlor Live (Bellevue)", "seattle", "eastside", "Bellevue", "WA", "https://bellevue.parlorlive.com", "html", 47.6160, -122.2010),
    ("laughs-comedy-kirkland", "Laughs Comedy Club (Kirkland)", "seattle", "eastside", "Kirkland", "WA", "https://www.laughscomedy.com", "html", 47.6800, -122.2080),
    # ---- South / Eastside big rooms (TM) ----
    ("tacoma-dome", "Tacoma Dome", "tacoma", "south", "Tacoma", "WA", "https://www.tacomadome.org", "ticketmaster", 47.2366, -122.4267),
    ("white-river-amphitheatre", "White River Amphitheatre", "tacoma", "south", "Auburn", "WA", "https://www.whiteriveramphitheatre.com", "ticketmaster", 47.2230, -122.0680),
    ("showare-center", "accesso ShoWare Center", "tacoma", "south", "Kent", "WA", "https://www.showarecenter.com", "ticketmaster", 47.3810, -122.2470),
    ("marymoor-park", "Marymoor Park", "seattle", "eastside", "Redmond", "WA", "https://www.marymoorconcerts.com", "ticketmaster", 47.6580, -122.1180),
    ("emerald-queen-casino", "Emerald Queen Casino", "tacoma", "south", "Tacoma", "WA", "https://www.emeraldqueen.com", "ticketmaster", 47.2090, -122.4360),
    ("chateau-ste-michelle", "Chateau Ste. Michelle", "seattle", "eastside", "Woodinville", "WA", "https://www.ste-michelle.com", "ticketmaster", 47.7350, -122.1620),
    # ---- South / Eastside arts (HTML) ----
    ("pantages-theater", "Pantages Theater (Tacoma Arts Live)", "tacoma", "south", "Tacoma", "WA", "https://www.tacomaartslive.org", "html", 47.2530, -122.4400),
    ("temple-theatre", "Temple Theatre", "tacoma", "south", "Tacoma", "WA", "https://www.templetheater.com", "html", 47.2530, -122.4380),
    ("mcmenamins-elks-temple", "McMenamins Elks Temple / Spanish Ballroom", "tacoma", "south", "Tacoma", "WA", "https://www.mcmenamins.com", "html", 47.2520, -122.4390),
    # ---- North toward Bellingham ----
    ("tulalip-resort-casino", "Tulalip Resort Casino", "everett", "north", "Tulalip", "WA", "https://www.tulalipresortcasino.com", "ticketmaster", 48.0620, -122.1810),
    ("angel-of-the-winds-arena", "Angel of the Winds Arena", "everett", "north", "Everett", "WA", "https://www.angelofthewindsarena.com", "ticketmaster", 47.9770, -122.2030),
    ("skagit-valley-casino", "Skagit Valley Casino Resort", "bellingham", "north", "Bow", "WA", "https://www.theskagit.com", "ticketmaster", 48.5760, -122.3110),
    ("edmonds-center-arts", "Edmonds Center for the Arts", "everett", "north", "Edmonds", "WA", "https://www.ec4arts.org", "html", 47.8110, -122.3770),
    ("mount-baker-theatre", "Mount Baker Theatre", "bellingham", "north", "Bellingham", "WA", "https://www.mountbakertheatre.com", "html", 48.7510, -122.4790),
    ("wild-buffalo", "Wild Buffalo House of Music", "bellingham", "north", "Bellingham", "WA", "https://www.wildbuffalo.net", "html", 48.7520, -122.4780),
    # ---- Expandable: Portland ----
    ("moda-center", "Moda Center", "portland", "expandable", "Portland", "OR", "https://www.rosequarter.com", "ticketmaster", 45.5316, -122.6668),
    ("keller-auditorium", "Keller Auditorium", "portland", "expandable", "Portland", "OR", "https://www.portland5.com", "ticketmaster", 45.5120, -122.6790),
    ("arlene-schnitzer", "Arlene Schnitzer Concert Hall", "portland", "expandable", "Portland", "OR", "https://www.portland5.com", "ticketmaster", 45.5180, -122.6820),
    ("roseland-theater", "Roseland Theater", "portland", "expandable", "Portland", "OR", "https://www.roselandpdx.com", "html", 45.5270, -122.6760),
    ("crystal-ballroom", "Crystal Ballroom", "portland", "expandable", "Portland", "OR", "https://www.crystalballroompdx.com", "html", 45.5220, -122.6850),
    ("aladdin-theater", "Aladdin Theater", "portland", "expandable", "Portland", "OR", "https://www.aladdin-theater.com", "html", 45.4970, -122.6540),
    ("revolution-hall", "Revolution Hall", "portland", "expandable", "Portland", "OR", "https://www.revolutionhall.com", "html", 45.5180, -122.6360),
    ("helium-comedy-portland", "Helium Comedy Club (Portland)", "portland", "expandable", "Portland", "OR", "https://portland.heliumcomedy.com", "html", 45.5050, -122.6610),
    # ---- Expandable: Vancouver WA ----
    ("ilani-casino", "ilani Casino Resort", "vancouver_wa", "expandable", "Ridgefield", "WA", "https://www.ilaniresort.com", "html", 45.8470, -122.7350),
    ("rv-inn-amphitheater", "RV Inn Style Resorts Amphitheater", "vancouver_wa", "expandable", "Ridgefield", "WA", "https://www.rvinnstyleamp.com", "ticketmaster", 45.8330, -122.7270),
    # ---- Expandable: Vancouver BC ----
    ("rogers-arena", "Rogers Arena", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.rogersarena.com", "ticketmaster", 49.2778, -123.1089),
    ("commodore-ballroom", "Commodore Ballroom", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.commodoreballroom.com", "ticketmaster", 49.2810, -123.1230),
    ("orpheum-vancouver", "Orpheum Theatre", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.vancouvercivictheatres.com", "html", 49.2800, -123.1210),
    ("vogue-theatre", "Vogue Theatre", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.voguetheatre.com", "html", 49.2810, -123.1200),
    ("yuk-yuks-vancouver", "Yuk Yuk's (Vancouver)", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.yukyuks.com", "html", 49.2820, -123.1180),
    # ---- Ticketmaster per-DMA catch-all venues (until tm_venue_id mapping is resolved) ----
    ("tm-seattle-tacoma", "Other Seattle–Tacoma venues (Ticketmaster)", "seattle", "core", "Seattle", "WA", "https://www.ticketmaster.com", "ticketmaster", None, None),
    ("tm-portland", "Other Portland venues (Ticketmaster)", "portland", "expandable", "Portland", "OR", "https://www.ticketmaster.com", "ticketmaster", None, None),
    ("tm-vancouver-bc", "Other Vancouver BC venues (Ticketmaster)", "vancouver_bc", "expandable", "Vancouver", "BC", "https://www.ticketmaster.ca", "ticketmaster", None, None),
]


def venue_rows() -> list[dict]:
    rows = []
    for slug, name, metro, region, city, state, website, kind, lat, lng in VENUES:
        rows.append({
            "slug": slug,
            "name": name,
            "metro": metro,
            "region": region,
            "city": city,
            "state": state,
            "country": "CA" if state == "BC" else "US",
            "lat": lat,
            "lng": lng,
            "website": website,
            "source_kind": kind,
            "is_active": True,
            "aliases": ALIASES.get(slug, []),
            # Platform hints {platform, axs_venue_id, tm_web_venue_id, dice_venue}.
            "source_config": dict(VENUE_PLATFORMS.get(slug, {})),
        })
    return rows


def source_rows() -> list[dict]:
    """One source per adapter. STG = 1 source for 3 venues; TM = per-DMA."""
    sources: list[dict] = []

    # STG (Paramount/Moore/Neptune) — feed-first, scrape fallback.
    sources.append({
        "slug": "stg",
        "kind": "stg",
        "is_active": True,
        "config": {
            "page_url": "https://www.stgpresents.org/tickets/calendar",
            "base_url": "https://www.stgpresents.org",
            "default_venue_slug": "paramount-theatre",
            "source_priority": 10,
            "venue_map": {
                "Paramount": "paramount-theatre",
                "Moore": "moore-theatre",
                "Neptune": "neptune-theatre",
            },
            "selectors": {
                "item": ".calendar-item, .event",
                "title": ".title, h3",
                "date": "time, .date",
                "url": "a",
                "venue": ".venue, .location",
            },
            "verified": False,
        },
    })

    # Ticketmaster — Seattle/Tacoma DMA 385, Portland DMA 228, Vancouver BC by geo.
    # NOTE: these are Ticketmaster's OWN Discovery `dmaId` values, NOT Nielsen DMA
    # codes. The original 819 (Nielsen Seattle-Tacoma) / 820 (Nielsen Portland)
    # matched nothing and returned 0 events; TM's ids are 385 (Seattle) / 228
    # (Portland), confirmed live against the Discovery API.
    sources.append({
        "slug": "ticketmaster_seatac",
        "kind": "ticketmaster",
        "is_active": True,
        "config": {
            "dma_id": 385,
            "classifications": ["music", "comedy", "arts & theatre"],
            "fallback_venue_slug": "tm-seattle-tacoma",
            "source_priority": 50,
            "venue_index": {},  # populate tm_venue_id -> venue_slug to route big rooms
            "tz": "America/Los_Angeles",
        },
    })
    sources.append({
        "slug": "ticketmaster_portland",
        "kind": "ticketmaster",
        "is_active": True,
        "config": {
            "dma_id": 228,
            "classifications": ["music", "comedy", "arts & theatre"],
            "fallback_venue_slug": "tm-portland",
            "source_priority": 50,
            "venue_index": {},
            "tz": "America/Los_Angeles",
        },
    })
    sources.append({
        "slug": "ticketmaster_vancouver_bc",
        "kind": "ticketmaster",
        "is_active": True,
        "config": {
            "geo_point": "49.2827,-123.1207",
            "radius": 25,
            "classifications": ["music", "comedy"],
            "fallback_venue_slug": "tm-vancouver-bc",
            "source_priority": 50,
            "venue_index": {},
            "tz": "America/Vancouver",
        },
    })

    # The tail venues (jazz-alley/benaroya/meany/tacoma-comedy) fragment onto
    # platforms with no adapter yet — drop their dead generic-HTML source and seed
    # an inactive platform-tagged placeholder instead. Tractor/Crocodile/Showbox &
    # the big rooms KEEP their HTML source active until a live TM run confirms the
    # name-matcher attaches their events (BUILD §coverage step 5).
    tail_slugs = {s for s, p in VENUE_PLATFORMS.items() if p["platform"] not in _ADAPTER_READY}

    # Per-venue HTML sources for every html venue (tail ones inactive).
    html_venues = [(slug, website) for slug, _n, _m, _r, _c, _s, website, kind, *_ in VENUES if kind == "html"]
    for slug, website in html_venues:
        sources.append({
            "slug": slug,
            "kind": "html",
            "is_active": slug not in tail_slugs,
            "config": {
                "venue_slug": slug,
                "page_url": website,           # TODO: point at the actual calendar path
                "base_url": website,
                "source_priority": 10,         # venue-direct beats platform beats TM
                "selectors": GENERIC_SELECTORS,
                "platform": VENUE_PLATFORMS.get(slug, {}).get("platform"),
                "verified": False,
            },
        })

    # ---- Platform adapters (config-driven, NOT per-venue code) ----
    # AXS: one source per venue with a confirmed axs_venue_id.
    for slug, p in VENUE_PLATFORMS.items():
        axs_id = p.get("axs_venue_id")
        if not axs_id:
            continue
        sources.append({
            "slug": f"axs_{slug}",
            "kind": "axs",
            "is_active": True,
            "config": {
                "venue_slug": slug,
                "axs_venue_id": axs_id,
                "page_url": f"https://www.axs.com/venues/{axs_id}",
                "source_priority": 20,         # platform-primary: below venue-direct(10), above TM(50)
            },
        })

    # DICE: one source per venue with a dice_venue permalink.
    for slug, p in VENUE_PLATFORMS.items():
        dice_venue = p.get("dice_venue")
        if not dice_venue:
            continue
        sources.append({
            "slug": f"dice_{slug}",
            "kind": "dice",
            "is_active": True,
            "config": {
                "venue_slug": slug,
                "dice_venue": dice_venue,
                "events_url": f"https://api.dice.fm/events?filter%5Bvenues%5D%5B%5D={dice_venue}&page%5Bsize%5D=50",
                "source_priority": 20,
            },
        })

    # Tail: tessitura/tixr/house placeholders — seeded inactive until adapters exist.
    for slug, p in VENUE_PLATFORMS.items():
        platform = p["platform"]
        if platform in _ADAPTER_READY:
            continue
        sources.append({
            "slug": f"{platform}_{slug}",
            "kind": platform,
            "is_active": False,
            "config": {
                "venue_slug": slug,
                "platform": platform,
                "source_priority": 20,
                "note": "adapter not built yet — see VENUE_PLATFORMS",
            },
        })
    return sources


def main() -> None:
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not (url and key):
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY. See README.")
    client = create_client(url, key)

    venues = venue_rows()
    sources = source_rows()
    client.table("venues").upsert(venues, on_conflict="slug").execute()
    client.table("sources").upsert(sources, on_conflict="slug").execute()
    print(f"Seeded {len(venues)} venues and {len(sources)} sources.")


if __name__ == "__main__":
    main()
