"""Supabase access for the scraper (service-role key — the only writer).

Reads the venue/source registry and persists events through the `upsert_event`
SQL function so the §5.4 merge policy is enforced in the database, not here.
"""
from __future__ import annotations

import os
from typing import Any

from supabase import create_client, Client


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def fetch_venues(client: Client) -> dict[str, dict[str, Any]]:
    """Return {slug: venue_row} for active venues."""
    res = client.table("venues").select("*").eq("is_active", True).execute()
    return {row["slug"]: row for row in res.data}


def fetch_sources(client: Client) -> list[dict[str, Any]]:
    res = client.table("sources").select("*").eq("is_active", True).execute()
    return res.data


def upsert_events(client: Client, rows: list[dict[str, Any]]) -> int:
    """Upsert each event via the upsert_event() RPC. Returns count attempted."""
    count = 0
    for row in rows:
        client.rpc("upsert_event", {"e": row}).execute()
        count += 1
    return count


def record_run(
    client: Client,
    source_slug: str,
    started_at: str,
    finished_at: str,
    ok: bool,
    found: int,
    upserted: int,
    error: str | None,
    note: str | None = None,
) -> None:
    client.table("source_runs").insert(
        {
            "source_slug": source_slug,
            "started_at": started_at,
            "finished_at": finished_at,
            "ok": ok,
            "events_found": found,
            "events_upserted": upserted,
            "error": error,
            "note": note,
        }
    ).execute()
