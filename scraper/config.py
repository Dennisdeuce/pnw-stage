"""Environment configuration for the scraper."""
from __future__ import annotations

import os


def env(name: str, required: bool = False, default: str | None = None) -> str | None:
    val = os.environ.get(name, default)
    if required and not val:
        raise SystemExit(
            f"Missing required env var {name}. See README 'ACTION REQUIRED'."
        )
    return val


SUPABASE_URL = env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = env("SUPABASE_SERVICE_KEY")
TICKETMASTER_API_KEY = env("TICKETMASTER_API_KEY")
