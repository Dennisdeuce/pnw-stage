"""Ingestion orchestrator (BUILD_SPEC §5).

For each active source: fetch -> normalize -> upsert, isolated in try/except so
one bad adapter never aborts the others (§5.6). Each source's outcome is logged
to `source_runs`. Exit code is non-zero ONLY when zero events were collected
across all sources (a real outage), so the GitHub Action turns red on outages
but stays green when individual fragile scrapers fail.
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone

from adapters.base import HttpClient, build_adapter
from normalize import normalize
import db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run() -> int:
    client = db.get_client()
    venues = db.fetch_venues(client)
    sources = db.fetch_sources(client)

    if not sources:
        print("No active sources found. Did you seed the registry?", file=sys.stderr)
        return 1

    http = HttpClient()
    total_found = 0
    total_upserted = 0
    ok_sources = 0

    try:
        for source in sources:
            slug = source["slug"]
            started = _now()
            found = upserted = 0
            ok = False
            error = None
            try:
                adapter = build_adapter(source, http)
                raw_events = adapter.fetch()
                found = len(raw_events)

                rows = []
                for raw in raw_events:
                    venue = venues.get(raw.venue_slug)
                    if venue is None:
                        continue  # event references a venue not in the registry
                    priority = source.get("config", {}).get("source_priority",
                                                              venue.get("source_priority", 100))
                    row = normalize(raw, venue_id=venue["id"], source_priority=priority)
                    if row:
                        rows.append(row)

                upserted = db.upsert_events(client, rows)
                ok = True
                ok_sources += 1
                total_found += found
                total_upserted += upserted
                print(f"[ok]   {slug}: found={found} upserted={upserted}")
            except Exception as exc:  # noqa: BLE001 — isolation is the point (§5.6)
                error = f"{type(exc).__name__}: {exc}"
                print(f"[fail] {slug}: {error}", file=sys.stderr)
                traceback.print_exc()
            finally:
                db.record_run(client, slug, started, _now(), ok, found, upserted, error)
    finally:
        http.close()

    pct_ok = (ok_sources / len(sources) * 100) if sources else 0
    print(f"\nSummary: {ok_sources}/{len(sources)} sources ok ({pct_ok:.0f}%), "
          f"{total_found} found, {total_upserted} upserted.")

    # Real outage => non-zero so the workflow shows red.
    if total_found == 0:
        print("ZERO events collected across all sources — failing the run.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
