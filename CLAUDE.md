# CLAUDE.md — PNW Stage

Read before acting. These are hard-won rules from real failures in this repo.

## Operating principle (the meta-rule)
Verify the ACTUAL current state before instructing the user or acting — never pattern-match to how a third-party platform "used to" work. Supabase/Cloudflare/Ticketmaster UIs, key systems, and APIs change. Before giving click-by-click steps, confirm the real layout (read the page or search current docs). A confident wrong instruction sends the user somewhere they can't recover from, which is worse than pausing to check.

## Supabase: NEW API keys only — there is NO legacy service_role
- Project `pnw-stage` (ref `jryeliesxuzzqpsfeolk`) was created after Supabase's Nov-2025 key migration. It has ONLY `sb_publishable_…` and `sb_secret_…` keys. There is NO legacy `anon`/`service_role` JWT and NO "Legacy API keys" tab. Never tell anyone to use a service_role key or look for legacy keys here.
- Scraper auth uses an `sb_secret_…` key (GitHub secret `SUPABASE_SERVICE_KEY`). The Python `supabase` package MUST be a version that sends `sb_secret_` on the `apikey` header, NOT `Authorization: Bearer`. The original `supabase==2.9.1` predates new keys → sends Bearer → Postgres rejects the non-JWT and SILENTLY falls back to the `anon` role. Keep `supabase` current; never reintroduce an old pin.
- Frontend (`web/`) uses the PUBLISHABLE key (`sb_publishable_…`) as `VITE_SUPABASE_ANON_KEY` — not a legacy `eyJ…` anon JWT.

## Symptom → cause map
- Scrape exits 1, "no active sources", `source_runs` empty → the client is authenticating as `anon`, not service-role. `sources` is RLS-locked to service-role, so anon reads 0 rows and the pipeline aborts before the loop. Debug AUTH/ROLE first, not the scrapers.
- Fast role check: `set local role anon; select count(*) from sources;` → anon must see 0; a correct service key sees all.

## Dependency pins must satisfy BOTH runtime and platform
- Runtime: Python 3.12 (CI) and 3.14 (local). Pins need wheels for both (e.g. rapidfuzz>=3.14, lxml>=6.0). `ics==0.7.2` requires `tatsu==5.15.1` pinned or `import ics` crashes.
- Never pin a library to a version that predates a platform API change (see the supabase/new-keys lesson).

## Project facts
- Repo: `Dennisdeuce/pnw-stage`. Supabase ref: `jryeliesxuzzqpsfeolk`.
- GH Actions secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (sb_secret_…), `TICKETMASTER_API_KEY`.
- Migration 0005 columns (`venues.aliases`, `source_runs.note`) were applied directly to the live DB; run full 0005 + re-seed before relying on AXS/DICE/alias coverage.
- Hosting: Cloudflare Pages — root `web`, build `npm ci && npm run build`, output `web/dist`; env `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY` (= publishable key).
- Reliable data sources: Ticketmaster Discovery (DMA queries) + STG. AXS/DICE are experimental, validated only against captured fixtures.
