# PNW Stage — Continuously-Updated Concert & Comedy Finder

A free, zero-backend web app for concerts, comedy, and arts across the Pacific
Northwest — Seattle core, north to Bellingham, south to Tacoma, with Portland and
Vancouver (WA + BC) behind an expander.

- **Frontend:** React + Vite + TypeScript + Tailwind, installable PWA → **Cloudflare Pages**.
- **Data store:** **Supabase Postgres**. The SPA reads it directly via the anon key under read-only RLS — no API server.
- **Ingestion:** A **Python scraper** run by **GitHub Actions cron at 4 AM Pacific**, writing with the service-role key.

Built to the spec in `BUILD_SPEC_pnw_show_finder.md`. Total cost: **$0/month** within free tiers.

---

## ⚠️ ACTION REQUIRED — make it live (BUILD_SPEC §9.6)

Everything is built, migrated, seeded, and tested. To take it the last mile
(live Ticketmaster data + public URL) add these secrets. They could **not** be
obtained from the build environment (no Ticketmaster account, no Cloudflare token,
and those hosts plus Supabase are outside the build sandbox's network allowlist).

### 1. Supabase service key → GitHub Actions secrets
The anon (public) key is already wired into the frontend. The **service-role**
key is secret and must be copied from the dashboard — it cannot be read via API.

> Supabase dashboard → Project **pnw-stage** → Settings → API → `service_role` key.

```bash
gh secret set SUPABASE_URL --body "https://jryeliesxuzzqpsfeolk.supabase.co"
gh secret set SUPABASE_SERVICE_KEY --body "<service_role key from dashboard>"
```

### 2. Ticketmaster Discovery key (free) → GitHub Actions secret
Get a free key at <https://developer.ticketmaster.com> (5,000 calls/day).

```bash
gh secret set TICKETMASTER_API_KEY --body "<your TM consumer key>"
```

### 3. Cloudflare Pages → GitHub Actions secrets
Create a Pages project named `pnw-stage`, then:

```bash
gh secret set CLOUDFLARE_API_TOKEN --body "<token with Pages:Edit>"
gh secret set CLOUDFLARE_ACCOUNT_ID --body "<your account id>"
# Frontend build-time env (also set these in the Pages project settings):
gh secret set VITE_SUPABASE_URL --body "https://jryeliesxuzzqpsfeolk.supabase.co"
gh secret set VITE_SUPABASE_ANON_KEY --body "<anon key — see below>"
```

Public anon key (safe to publish; read-only under RLS):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpyeWVsaWVzeHV6enFwc2Zlb2xrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEzMDI4MTgsImV4cCI6MjA5Njg3ODgxOH0.19PP9_ibu7y6yVz2Pa9huWq9KzfgqsSF9SNt_vUIyFM
```

### 4. (optional) Bandsintown enrichment
```bash
gh secret set BANDSINTOWN_APP_ID --body "<app id>"
```

### 5. (optional) DICE API key
DICE's per-venue events endpoint accepts an `x-api-key`. Without it the adapter
tries unauthenticated and fails soft (logged to `source_runs`).
```bash
gh secret set DICE_API_KEY --body "<your DICE partner key>"
```

### 6. Apply migration 0005, re-seed, then resolve TM venue ids
The coverage pass added `migrations/0005_platform_tags.sql` (a `venues.aliases`
column + a `source_runs.note` column) and new seed data (aliases, platform tags,
AXS/DICE sources). After the secrets above are set, run, in order:

```bash
# 1) apply the new migration (Supabase SQL editor or CLI):
supabase db push                       # or paste 0005_platform_tags.sql into the SQL editor

cd scraper
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2) re-seed the registry (idempotent upsert by slug):
SUPABASE_URL=... SUPABASE_SERVICE_KEY=... .venv/bin/python seed_venues.py

# 3) cache real Discovery venue ids into venues.tm_venue_id (gated on the TM key):
TICKETMASTER_API_KEY=... SUPABASE_URL=... SUPABASE_SERVICE_KEY=... \
  .venv/bin/python resolve_tm_venues.py
```

`resolve_tm_venues.py` is **gated** — with no key it prints what it would do and
exits 0. It only needs to run once (and after adding venues); the resolved ids are
cached, after which Ticketmaster events route to their venue row by id. Until then
they route by venue **name** (aliases + fuzzy match) and any unmatched name is
logged to `source_runs.note` so you can promote it into `venues.aliases`.

### Cloudflare Pages
The repo's **Deploy** workflow (`.github/workflows/deploy.yml`) already builds
`web/` with `npm ci && npm run build` and publishes `web/dist` to a Pages project
named `pnw-stage`. If you prefer Cloudflare's native Git integration instead, point
it at this repo with **root directory = `web`**, **build command = `npm ci && npm
run build`**, **output directory = `web/dist`**, and the two `VITE_*` build vars.

Once 1–6 are set: trigger **Scrape** (`workflow_dispatch`) to load live events,
then **Deploy** to publish. The app works the moment these land — no code changes.

```bash
# trigger the two workflows once secrets are in place:
gh workflow run "Scrape (daily 4 AM Pacific)"
gh workflow run "Deploy (Cloudflare Pages)"
```

---

## What's already done in this build

| Area | Status |
|---|---|
| Supabase project `pnw-stage` (`jryeliesxuzzqpsfeolk`, us-west-1) | ✅ created |
| Migrations `0001`–`0004` (schema, RLS, idempotent + locked `upsert_event`) | ✅ applied |
| Migration `0005_platform_tags` (`venues.aliases`, `source_runs.note`) | ⏳ apply with step 6 |
| Venue + source registry | ✅ **60 venues, 40 active sources** (3 TM · 4 AXS · 1 DICE · 31 HTML · 1 STG); 8 inactive (4 tail-HTML + 4 platform placeholders) |
| TM venue-name routing (aliases + fuzzy ≥0.90) + AXS/DICE platform adapters | ✅ built + unit-tested |
| RLS verified | ✅ anon sees events via `public_events`, anon **write blocked** |
| Demo events for UI/QA (inactive `seed_demo` source) | ✅ 16 events |
| Scraper unit tests (`normalize`, `dedup`, TM-match, AXS, DICE, seed) | ✅ 35 passed, 2 live-TM skipped |
| Frontend build (`tsc` + `vite build`) + PWA service worker/manifest | ✅ passes |
| Playwright e2e suite (feed / calendar wk·mo·yr / expander / new-since / mobile) | ✅ written, mocked, CI-runnable |

### Deferred to you (environment limits, not code gaps)
- **Live Ticketmaster pull** — needs the free API key (step 2).
- **Cloudflare deploy + production smoke** — needs the token (step 3); no Cloudflare tooling in the build sandbox.
- **Running Playwright here** — the browser CDN and Supabase host were both outside the build sandbox's egress allowlist. The suite runs in CI (`.github/workflows/ci.yml`) and locally.

---

## Architecture

```
 4 AM PT cron ─► GitHub Actions (Python) ─► adapters ─► normalize ─► dedup ─► upsert (service key)
                                                                                    │
                                                                                    ▼
                                              Supabase Postgres  (RLS: anon = SELECT on public_* views)
                                                                                    │ anon key
                                                                                    ▼
                                              React SPA on Cloudflare Pages (Feed · Calendar · Venues)
```

The scraper is the only writer. The SPA talks to Supabase's auto-generated REST
(PostgREST) via `supabase-js`.

## Repo layout
```
scraper/   Python ingestion: adapters/, normalize, dedup, pipeline, seed_venues, tests
web/       Vite React app: src/ (components, lib), tests/ (Playwright)
supabase/  migrations/*.sql
.github/   workflows: ci.yml, scrape.yml, deploy.yml
```

## Local development

**Scraper**
```bash
cd scraper
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q                 # unit tests
# live run (needs env): SUPABASE_URL, SUPABASE_SERVICE_KEY, TICKETMASTER_API_KEY
.venv/bin/python seed_venues.py               # (re)seed registry
.venv/bin/python pipeline.py                  # full ingest
```

**Frontend**
```bash
cd web
cp .env.example .env        # fill in the URL + anon key above
npm install
npm run dev                 # http://localhost:5173
npm run build               # type-check + production build
npx playwright install chromium && npm run test:e2e
```

## Data sources (the source map, BUILD_SPEC §3.3)

- **Ticketmaster Discovery API** (primary): queried by DMA — Seattle/Tacoma `819`,
  Portland `820` — plus a Vancouver BC geo query. Resale (`source=tmr`) is filtered
  out so a resale link never appears as a buy link. Each event's TM **venue name**
  is matched to a registry row (alias index, then rapidfuzz token-set ≥0.90) so big
  rooms — including Tractor Tavern & The Crocodile, which are already in the TM
  catalog — land on their own venue instead of the per-DMA catch-all.
- **Platform adapters** (config-driven, one class for many venues — *not* a scraper
  per club): **AXS** (`adapters/axs.py`, parses schema.org JSON-LD on the venue
  listing — Showbox, Showbox SoDo, Tractor, Crocodile) and **DICE**
  (`adapters/dice.py`, per-venue events JSON — Crocodile). Tagged-but-deferred
  platforms (Tessitura → Benaroya/Meany, Tixr → Tacoma Comedy, house → Jazz Alley)
  are seeded as **inactive** placeholders until their adapters are built.
- **Seattle Theatre Group** (`stg`): one adapter → Paramount / Moore / Neptune.
- **Per-venue HTML adapters** for the remaining clubs/arts/comedy rooms (config-driven CSS selectors).

> **Why platforms, not 35 scrapers:** ticketing fragments onto ~5 platforms
> (Ticketmaster/TicketWeb, AXS, DICE, Tessitura, Tixr). One adapter per *platform*
> + a per-venue config row covers far more venues with far less fragile code.
> Venue→platform mapping lives in `VENUE_PLATFORMS` in `scraper/seed_venues.py`.

> Adding a venue = one registry row in `scraper/seed_venues.py` (+ a selector tweak
> if it's a new HTML layout). Venues are never hardcoded in the UI.

### Honest notes & open items
- **HTML adapters ship with placeholder selectors** (`verified: false`). The build
  sandbox couldn't reach venue sites to validate them, so wrong selectors will just
  yield zero events and show a **"Check source"** badge — they never break other
  adapters (failure isolation, §5.6). Tune selectors per site and flip `verified`.
- **Ticketmaster venue routing:** events now route by venue **name** (alias index +
  fuzzy ≥0.90) the moment the seed is applied — no id resolution required. Running
  `resolve_tm_venues.py` additionally caches real Discovery ids into
  `venues.tm_venue_id` for exact id-based routing. Names that still don't match fall
  to the per-DMA catch-all (`tm-seattle-tacoma`, `tm-portland`, `tm-vancouver-bc`)
  **and** are logged to `source_runs.note` so you can promote them into
  `venues.aliases`.
- **AXS/DICE markup not live-validated here:** AXS bot-blocks the build sandbox and
  DICE needs a key, so the adapters are pinned to captured fixtures
  (`scraper/tests/fixtures/`) matching each platform's real JSON shape. Like the HTML
  adapters, a markup/shape change yields zero events + a red badge, never a crash.
- **Unresolved venues** "Emerald City comedy club" and "St. Jackson's, Tacoma"
  (likely a mis-transcription of Tacoma Comedy Club) were left out pending confirmation.
- **"Artist-direct" tickets are largely infeasible** — primary sellers are TM/AXS.
  The real guarantee is **primary, never resale** (§3.4), surfaced as a badge.

## Risks & governance (BUILD_SPEC §10)
- **Scraper fragility:** feed-first, source-health table, freshness badges, failure isolation.
- **DST / cron drift:** dual UTC cron + idempotent upsert.
- **Free-tier ceilings:** events table is tiny; TM budget is a few hundred of 5k/day.
- **No-UAT risk:** data-sanity gates + visible per-venue freshness surface gaps without a human.
- **ToS:** rate-limited (≤1 req/2s/host), descriptive User-Agent, facts not copied prose,
  TM attribution in the footer, no resale links.
