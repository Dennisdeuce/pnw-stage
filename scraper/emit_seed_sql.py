"""Emit idempotent seed SQL from the registry in seed_venues.py.

Lets us seed via any SQL channel (Supabase MCP, psql, dashboard) without needing
the service-role key in this environment. `python emit_seed_sql.py > seed.sql`.
"""
from __future__ import annotations

import json

from seed_venues import venue_rows, source_rows


def _sql_str(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def _sql_json(d: dict) -> str:
    return "'" + json.dumps(d).replace("'", "''") + "'::jsonb"


def emit() -> str:
    out: list[str] = []

    vcols = ["slug", "name", "metro", "region", "city", "state", "country",
             "lat", "lng", "website", "source_kind", "is_active", "source_config"]
    vvals = []
    for v in venue_rows():
        row = [
            _sql_str(v["slug"]), _sql_str(v["name"]), _sql_str(v["metro"]),
            _sql_str(v["region"]), _sql_str(v["city"]), _sql_str(v["state"]),
            _sql_str(v["country"]), _sql_str(v["lat"]), _sql_str(v["lng"]),
            _sql_str(v["website"]), _sql_str(v["source_kind"]),
            _sql_str(v["is_active"]), _sql_json(v["source_config"]),
        ]
        vvals.append("(" + ", ".join(row) + ")")
    out.append(
        f"insert into venues ({', '.join(vcols)}) values\n"
        + ",\n".join(vvals)
        + "\non conflict (slug) do update set "
        + ", ".join(f"{c}=excluded.{c}" for c in vcols if c != "slug")
        + ";"
    )

    scols = ["slug", "kind", "is_active", "config"]
    svals = []
    for s in source_rows():
        row = [_sql_str(s["slug"]), _sql_str(s["kind"]),
               _sql_str(s["is_active"]), _sql_json(s["config"])]
        svals.append("(" + ", ".join(row) + ")")
    out.append(
        f"insert into sources ({', '.join(scols)}) values\n"
        + ",\n".join(svals)
        + "\non conflict (slug) do update set "
        + ", ".join(f"{c}=excluded.{c}" for c in scols if c != "slug")
        + ";"
    )
    return "\n\n".join(out)


if __name__ == "__main__":
    print(emit())
