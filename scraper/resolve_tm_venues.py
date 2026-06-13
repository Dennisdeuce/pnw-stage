"""Resolve & cache real Ticketmaster Discovery venue ids (coverage pass, §step 4).

The seed carries legacy TicketWeb/TM-classic ids as *hints* only. The Discovery
API keys events to its own "K..." venue ids, so this one-shot resolver queries
  GET /discovery/v2/venues?keyword={name}
for each registry venue, picks the best name match (exact-normalized, else
rapidfuzz token-set >= 0.90) preferring the right state/city, and caches the real
Discovery id into `venues.tm_venue_id`. Once cached, the pipeline builds the TM
`venue_index` from it so big-room events route by id (faster + exact) before the
name-matcher even runs.

GATED: runs live only when BOTH TICKETMASTER_API_KEY and Supabase service creds are
present. Otherwise it prints what it would do and exits 0 (documented in README).
Idempotent — safe to re-run; it only writes when it finds a confident match.
"""
from __future__ import annotations

import os
import sys
import time

from venue_match import normalize_venue_name, FUZZY_THRESHOLD
from rapidfuzz import fuzz

API_BASE = "https://app.ticketmaster.com/discovery/v2/venues.json"

# Catch-all rows are not real venues — never resolve them.
_SKIP_SLUGS = {"tm-seattle-tacoma", "tm-portland", "tm-vancouver-bc"}


def _best_match(our_name: str, our_state: str | None, our_city: str | None, candidates: list[dict]):
    """Return (tm_id, score) for the best Discovery venue candidate, or (None, 0)."""
    target = normalize_venue_name(our_name)
    best_id, best_score = None, 0.0
    for c in candidates:
        score = fuzz.token_set_ratio(target, normalize_venue_name(c.get("name")))
        # Reward matching state/city so two same-named rooms don't cross-wire.
        st = (c.get("state") or {}).get("stateCode")
        city = (c.get("city") or {}).get("name")
        if our_state and st and st.upper() == our_state.upper():
            score += 5
        if our_city and city and city.lower() == our_city.lower():
            score += 5
        if score > best_score:
            best_score, best_id = score, c.get("id")
    return best_id, best_score


def resolve(client, api_key: str) -> int:
    import httpx

    res = client.table("venues").select("*").execute()
    venues = [v for v in res.data if v["slug"] not in _SKIP_SLUGS]
    updated = 0
    with httpx.Client(timeout=20.0) as http:
        for v in venues:
            if v.get("tm_venue_id"):
                continue  # already resolved
            params = {"apikey": api_key, "keyword": v["name"], "size": 20}
            if v.get("state"):
                params["stateCode"] = v["state"]
            resp = http.get(API_BASE, params=params)
            if resp.status_code == 401:
                raise SystemExit("Ticketmaster rejected the API key (401).")
            if resp.status_code != 200:
                print(f"[skip] {v['slug']}: HTTP {resp.status_code}", file=sys.stderr)
                continue
            cands = (resp.json().get("_embedded") or {}).get("venues") or []
            tm_id, score = _best_match(v["name"], v.get("state"), v.get("city"), cands)
            if tm_id and score >= FUZZY_THRESHOLD:
                client.table("venues").update({"tm_venue_id": tm_id}).eq("id", v["id"]).execute()
                updated += 1
                print(f"[ok]   {v['slug']} -> {tm_id} (score {score:.0f})")
            else:
                print(f"[miss] {v['slug']}: no confident match (best {score:.0f})")
            time.sleep(0.25)  # stay under 5 req/s
    return updated


def main() -> int:
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not api_key or not (url and key):
        print(
            "GATED: resolve_tm_venues needs TICKETMASTER_API_KEY + SUPABASE_URL + "
            "SUPABASE_SERVICE_KEY. Set them (see README 'ACTION REQUIRED') then run:\n"
            "    python resolve_tm_venues.py\n"
            "Until then, TM events route by venue NAME (adapters/ticketmaster.py)."
        )
        return 0

    from supabase import create_client

    client = create_client(url, key)
    updated = resolve(client, api_key)
    print(f"Resolved {updated} Discovery venue id(s) into venues.tm_venue_id.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
