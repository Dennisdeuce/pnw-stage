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

Once 1–3 are set: trigger **Scrape** (`workflow_dispatch`) to load live events,
then **Deploy** to publish. The app works the moment these land — no code changes.

---

## What's already done in this build

| Area | Status |
|---|---|
| Supabase project `pnw-stage` (`jryeliesxuzzqpsfeolk`, us-west-1) | ✅ created |
| Migrations `0001`–`0003` (schema, RLS, idempotent `upsert_event`) | ✅ applied |
| Venue + source registry | ✅ **60 venues, 39 active sources** seeded |
| RLS verified | ✅ anon sees events via `public_events`, anon **write blocked** |
| Demo events for UI/QA (inactive `seed_demo` source) | ✅ 16 events |
| Scraper unit tests (`normalize`, `dedup`, double-run idempotency) | ✅ 16 passed, 2 live-TM skipped |
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
  out so a resale link never appears as a buy link.
- **Seattle Theatre Group** (`stg`): one adapter → Paramount / Moore / Neptune.
- **Per-venue HTML adapters** for clubs, arts, and comedy rooms (config-driven CSS selectors).

> Adding a venue = one registry row in `scraper/seed_venues.py` (+ a selector tweak
> if it's a new HTML layout). Venues are never hardcoded in the UI.

### Honest notes & open items
- **HTML adapters ship with placeholder selectors** (`verified: false`). The build
  sandbox couldn't reach venue sites to validate them, so wrong selectors will just
  yield zero events and show a **"Check source"** badge — they never break other
  adapters (failure isolation, §5.6). Tune selectors per site and flip `verified`.
- **Ticketmaster venue routing:** until real `tm_venue_id`s are resolved and cached
  (populate `venue_index` in the TM sources), TM events land on per-DMA catch-all
  venues (`tm-seattle-tacoma`, `tm-portland`, `tm-vancouver-bc`).
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
