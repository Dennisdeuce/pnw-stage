# BUILD SPEC — "PNW Stage" : Continuously-Updated Concert & Comedy Finder

**Audience:** Claude Code, running with `--dangerously-skip-permissions` in DT's authenticated local environment.
**Mandate:** Build → test → fix → deploy in **one continuous run**. No human UAT loop. Use sub-agents and connected tools (GitHub, Supabase, Cloudflare). Stop only if blocked on a secret you genuinely cannot obtain (see §9.6).

---

## 0. TL;DR — The Call

Ship a **free, zero-backend web app**:

- **Frontend:** React + Vite + TypeScript + Tailwind, hosted on **Cloudflare Pages** (free, global, any browser, installable PWA).
- **Data store:** **Supabase Postgres** (free tier). Frontend reads it **directly** via the anon key under read-only RLS. No API server to host or maintain.
- **Ingestion:** A **Python scraper** run by **GitHub Actions cron at 4 AM Pacific**, writing to Supabase with the service-role key.
- **Why this stack wins:** the daily write keeps Supabase off its 7-day inactivity pause; Python's scraping ecosystem (feedparser/ics/BeautifulSoup) beats JS for messy venue HTML; DT already runs Supabase + GitHub. Total cost: **$0/month** within free tiers.

**Tradeoff vs. the alternative (Cloudflare Workers + D1 + Cron Triggers):** Workers cron is more punctual and single-vendor with no pause risk, but DT is less fluent in it and JS is worse at HTML scraping. **Decision: Supabase + GitHub Actions.** Use Cloudflare only for static hosting (and, optionally, a backup cron ping).

---

## 1. Objectives & Non-Negotiables

| # | Requirement | How it's met |
|---|---|---|
| 1 | Accessible anywhere, any browser | Static SPA + PWA. No native app. |
| 2 | Free / near-free hosting | Cloudflare Pages + Supabase free + GitHub Actions free. |
| 3 | Daily refresh at 4 AM Pacific | GH Actions cron (DST-handled, §5.5). |
| 4 | Cover Seattle core + Tacoma (S) → Bellingham (N); expandable Portland / Vancouver WA / Vancouver BC | `metro` + `region` columns; non-core regions collapsed behind an expander. |
| 5 | "New since my last visit" | Client `localStorage` last-visit timestamp vs. event `first_seen` (§6.3). No accounts required. |
| 6 | Calendar: weekly / monthly / annual | FullCalendar views + a list/agenda "Feed" (§6.2). |
| 7 | Rich show detail: openers, set/door time, **primary** ticket link | Normalized schema (§4) + ticket-link precedence (§3.4). |
| 8 | Pull from STG + other booking orgs + per-venue sites | Adapter registry (§3.3, §5.2). |
| 9 | Visually appealing, easy to navigate | Design system in §6.5; read `/mnt/skills/public/frontend-design/SKILL.md` before building UI. |
| 10 | Autonomous build/test/deploy | §9 protocol + acceptance gates. |

---

## 2. Architecture

```
                    ┌─────────────────────────────────────────┐
   4 AM PT (cron)   │  GitHub Actions runner (Python 3.12)     │
   ───────────────► │  scraper/  → adapters → normalize → dedup│
                    │            → upsert (service key)        │
                    └───────────────────┬─────────────────────┘
                                        │ writes
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  Supabase Postgres (free)                │
                    │  events · venues · sources · source_runs │
                    │  RLS: anon = SELECT only on public views │
                    └───────────────────┬─────────────────────┘
                                        │ reads (anon key, supabase-js)
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  React SPA on Cloudflare Pages (PWA)     │
                    │  Feed(New) · Calendar(wk/mo/yr) · Filters│
                    └─────────────────────────────────────────┘
```

No application server exists. The SPA talks to Supabase's auto-generated REST (PostgREST) via `supabase-js`. The scraper is the only writer.

---

## 3. Data-Source Strategy (the hard part — read carefully)

### 3.1 Source-type hierarchy — ALWAYS prefer higher tiers
1. **Structured feed** (`.ics` iCal, RSS/Atom, or a JSON endpoint the site already calls). Most stable — does not break on redesigns. **Check every venue for an `.ics`/RSS feed first.**
2. **Official API.** Ticketmaster Discovery (primary). SeatGeek/Bandsintown only if a key is actually obtainable (treat as optional enrichment).
3. **HTML scrape** of the public calendar page. Last resort; fragile; wrap in source-health monitoring.

### 3.2 Ticketmaster Discovery API — primary discovery engine
- Free key at `developer.ticketmaster.com`. **5,000 calls/day, 5 req/sec.** Respect both; exponential backoff on HTTP 429.
- Covers Ticketmaster, TicketWeb, Universe, FrontGate **and Ticketmaster Resale (TMR)** sources. **Filter `source != tmr`** so resale never appears as a "buy" link.
- Query strategy (keeps call count low):
  - By **DMA** (Seattle-Tacoma DMA `id=819`; Portland `820`) and/or `geoPoint` radius, with `classificationName=music` and `classificationName=comedy` (run arts too), paginating `size=200` until exhausted.
  - Also query by `venueId` for the big rooms we know TM carries (Climate Pledge, WaMu Theater, Lumen Field, T-Mobile Park, Tacoma Dome, White River Amphitheatre, Angel of the Winds, ShoWare, Moda Center, etc.). Resolve venueIds once and cache them in `venues.tm_venue_id`.
- Daily budget: a few hundred calls. Well within 5k.
- **Attribution:** TM ToS requires showing ticket links back to TM and not misrepresenting data. Add a small "Event data via Ticketmaster" credit in the footer.

### 3.3 Venue → source map (decoded from the brief; build adapters in this order)

**Tier-A: Seattle Theatre Group (one adapter, three venues)** — Paramount, Moore, Neptune. Source: `stgpresents.org` events listing (check for `.ics`/JSON first; else scrape). Primary ticketer downstream is AXS.

**Tier-A: Big rooms via Ticketmaster API** — Climate Pledge Arena, WaMu Theater, Lumen Field + Event Center, T-Mobile Park, Tacoma Dome, White River Amphitheatre (Auburn), Angel of the Winds Arena (Everett), accesso ShoWare Center (Kent), Marymoor Park (Redmond).

**Tier-B: Clubs (per-venue, feed-first then scrape):**

| Brief said | Real venue | Notes / ticketer |
|---|---|---|
| showbox | The Showbox | AEG; AXS. Showbox + SoDo share a calendar host. |
| shoebox south | Showbox SoDo | same as above |
| little red hand | **Little Red Hen** (Green Lake, country) | own site |
| rusty tractor | **Tractor Tavern** (Ballard) | own site; etix/dice common |
| El Corazón | El Corazón (Eastlake) | own site/box office |
| — | The Crocodile (+ Here-After/Madame Lou's) | own site |
| — | Neumos / Barboza | own site |
| — | Nectar Lounge | own site |
| — | The Triple Door | own site |
| — | Dimitriou's Jazz Alley | own site |
| — | Benaroya Hall (Seattle Symphony) | seattlesymphony.org |

**Tier-B: Performing arts / university:**

| Brief said | Real venue |
|---|---|
| University of Washington concert hall | **Meany Center** (`meanycenter.org`) |
| venue next to Climate Pledge | **McCaw Hall** + **The Vera Project** (both at Seattle Center, adjacent) — build both |

**Tier-B: Comedy:**

| Brief said | Real venue |
|---|---|
| Tacoma comedy club | **Tacoma Comedy Club** (own ticketer, often Tixr) |
| comedy club in University District | **Jet City Improv** (Roosevelt/U-District) |
| — | Comedy Underground (Pioneer Square) |
| — | Parlor Live (Bellevue) |
| — | Laughs Comedy Club (Kirkland) |
| Emerald City comedy club | **UNRESOLVED — TODO** (see §11) |
| St. Jackson's comedy club, Tacoma | **UNRESOLVED — TODO** (see §11) |

**Tier-C: North toward Bellingham (collapsed by default if user is in Seattle core, but in-region):** Tulalip Resort Casino (Amphitheatre + Orca Ballroom) ["Lala Casino"], Edmonds Center for the Arts, Mount Baker Theatre (Bellingham), Wild Buffalo (Bellingham), Skagit Valley Casino. Many are TM-listed; check API before scraping.

**Tier-C: South / Eastside:** Pantages Theater + Broadway Center (Tacoma Arts Live), Temple Theatre, McMenamins Elks Temple / Spanish Ballroom (Tacoma), Emerald Queen Casino, Chateau Ste. Michelle (Woodinville, summer). 

**Expandable metros (behind a button, §6.4):**
- **Portland, OR:** Moda Center, Roseland, Crystal Ballroom, Aladdin, Revolution Hall, Keller Auditorium, Arlene Schnitzer, Helium Comedy. (Mostly TM/Etix.)
- **Vancouver, WA:** ilani Casino, RV Inn Style Resorts Amphitheater (Ridgefield).
- **Vancouver, BC:** Rogers Arena, Commodore Ballroom, Orpheum, Queen Elizabeth Theatre, Vogue Theatre, BC Place, Yuk Yuk's. (TM-CA + scrape.)

> Build the registry so adding a venue = adding one config row + (if needed) one adapter function. Do **not** hardcode venues in UI.

### 3.4 Ticket-link precedence (the "not third-party" rule, corrected)
For each event, resolve `ticket_url` by first match:
1. Venue's own official ticket/box-office URL (from feed/scrape).
2. **Primary** ticketer on-sale URL from the API (AXS, TM primary, Etix, DICE, Tixr, See Tickets). For TM, use the event `url`, but **only if `source != tmr`**.
3. Bandsintown artist **offer** URL of type `Tickets` (genuine artist-page listing), if Bandsintown enrichment is enabled.
4. Fallback: venue event page (no direct buy).

**Never** emit StubHub, Vivid, SeatGeek-resale, or TM-Resale links. Store `ticket_url_type` ∈ `{venue_primary, api_primary, artist, venue_page}` and show a "primary on-sale" badge so the distinction is visible. **Honest note for the user:** true artist-direct links are rare; "primary, not resale" is the real guarantee.

### 3.5 Enrichment (optional, P2)
- **Openers / lineup / description / set time** often come from the venue feed itself. Where missing, optionally query **Bandsintown** by headliner artist name to pull lineup + description (ToS: artist-scoped keys; treat as best-effort, gate behind a feature flag, don't hard-depend).
- Artist image/genre: Ticketmaster attractions, or MusicBrainz (free) as fallback.

---

## 4. Data Model (Supabase / Postgres DDL)

```sql
-- venues: the source-of-truth registry
create table venues (
  id              bigint generated always as identity primary key,
  slug            text unique not null,
  name            text not null,
  metro           text not null,           -- 'seattle','tacoma','everett','bellingham','portland','vancouver_wa','vancouver_bc'
  region          text not null,           -- 'core','north','south','eastside','expandable'
  city            text, state text, country text default 'US',
  lat             double precision, lng double precision,
  website         text,
  official_ticket_base text,               -- for building venue_primary links
  tm_venue_id     text,                     -- ticketmaster venue id cache
  source_kind     text not null,            -- 'ics','rss','json','ticketmaster','html'
  source_config   jsonb default '{}',       -- feed url, selectors, classification, etc.
  is_active       boolean default true,
  created_at      timestamptz default now()
);

create table sources (                      -- one row per ingest adapter (often 1:1 with venue, sometimes 1:many e.g. STG)
  id              bigint generated always as identity primary key,
  slug            text unique not null,     -- 'stg','ticketmaster_seatac','tractor_tavern',...
  kind            text not null,            -- 'ics','rss','json','ticketmaster','html'
  config          jsonb default '{}',
  is_active       boolean default true
);

create table events (
  id              bigint generated always as identity primary key,
  natural_key     text unique not null,     -- sha256(venue_id|date_local|normalized_title) — dedup key (§5.4)
  venue_id        bigint references venues(id),
  title           text not null,
  headliner       text,
  lineup          text[],                   -- openers/support
  description     text,
  category        text not null,            -- 'music','comedy','arts','other'
  genres          text[],
  starts_at       timestamptz,              -- show/set time (UTC)
  doors_at        timestamptz,
  ends_at         timestamptz,
  date_local      date not null,            -- America/Los_Angeles (or venue tz) calendar date
  is_all_ages     boolean,
  is_free         boolean default false,
  price_min       numeric, price_max numeric, currency text default 'USD',
  status          text default 'on_sale',   -- 'on_sale','presale','sold_out','announced','cancelled','postponed'
  onsale_at       timestamptz,              -- when tickets go on sale (for alerts)
  presale_at      timestamptz,
  ticket_url      text,
  ticket_url_type text,                     -- 'venue_primary','api_primary','artist','venue_page'
  image_url       text,
  source_slug     text references sources(slug),
  source_url      text,                     -- canonical event page on the source
  source_priority int default 100,          -- lower wins when same natural_key seen from 2 sources
  raw             jsonb,                     -- original payload for debugging/re-parse
  first_seen      timestamptz default now(),-- NEVER overwrite on update (drives "new since last visit")
  last_seen       timestamptz default now(),-- bumped every run the event is still present
  updated_at      timestamptz default now()
);
create index on events (date_local);
create index on events (venue_id);
create index on events (category);
create index on events (first_seen);

create table source_runs (                  -- observability / source health
  id          bigint generated always as identity primary key,
  source_slug text, started_at timestamptz, finished_at timestamptz,
  ok boolean, events_found int, events_upserted int, error text
);

-- Public read-only view the SPA consumes (joins venue fields, hides raw/internal)
create view public_events as
  select e.id, e.title, e.headliner, e.lineup, e.description, e.category, e.genres,
         e.starts_at, e.doors_at, e.date_local, e.is_all_ages, e.is_free,
         e.price_min, e.price_max, e.currency, e.status, e.onsale_at, e.presale_at,
         e.ticket_url, e.ticket_url_type, e.image_url, e.source_url, e.first_seen,
         v.name as venue_name, v.slug as venue_slug, v.metro, v.region,
         v.city, v.lat, v.lng, v.website as venue_website
  from events e join venues v on v.id = e.venue_id
  where e.status != 'cancelled' and e.date_local >= current_date;
```

**RLS:** enable on `events`/`venues`; grant `anon` `SELECT` only via `public_events` and a `public_venues` view + a `source_runs` "freshness" view. Service-role key (scraper only, GH secret) bypasses RLS for writes. **Anon key must never have write.**

---

## 5. Ingestion Pipeline

### 5.1 Stack
`python 3.12`, `httpx`, `beautifulsoup4`, `lxml`, `feedparser`, `ics` (iCal), `python-dateutil`, `tenacity` (retry/backoff), `supabase` (py). One module per adapter under `scraper/adapters/`.

### 5.2 Adapter contract
```python
# every adapter returns a list[RawEvent] (typed dict) — pure, no DB writes
class Adapter(Protocol):
    slug: str
    kind: str  # 'ics' | 'rss' | 'json' | 'ticketmaster' | 'html'
    def fetch(self) -> list[RawEvent]: ...
```
Generic adapters do most of the work, configured by `source_config`:
- `ICSAdapter`, `RSSAdapter`, `JSONAdapter` (CSS/JSONPath in config).
- `TicketmasterAdapter` (DMA/geo/venueId queries).
- `HTMLAdapter` (CSS selectors in config; the fragile path).
Only write a bespoke adapter when a venue's markup can't be expressed in config.

### 5.3 Normalize
Map every `RawEvent` → `events` columns. Parse dates to the venue's tz → store UTC `starts_at` + `date_local`. Split headliner/openers ("X with Y, Z" / "X, Y, Z"). Detect all-ages, free, sold-out, presale from text. Resolve `ticket_url` per §3.4.

### 5.4 Dedup & merge (idempotent upsert)
`natural_key = sha256(venue_id | date_local | normalize(title))` where `normalize` lowercases, strips punctuation, collapses whitespace, drops "live", "21+", tour suffixes.
Upsert on `natural_key`:
- Insert → set `first_seen=now()`.
- Conflict → **keep original `first_seen`**, bump `last_seen=now()`, and overwrite fields **only from the lower `source_priority`** source (venue feed beats TM beats generic). This makes double-runs and multi-source overlap safe — critical for the DST dual-cron (§5.5) and the no-UAT mandate.

### 5.5 Scheduling — 4 AM Pacific with DST handled
GitHub cron is UTC and DST-blind. Schedule **two** entries and let idempotent upsert absorb the harmless extra run:
```yaml
on:
  schedule:
    - cron: '0 11 * * *'   # 04:00 PDT (Mar–Nov)
    - cron: '0 12 * * *'   # 04:00 PST (Nov–Mar)
  workflow_dispatch: {}
```
Inside the job, optionally early-exit if it's not ~04:00 in `America/Los_Angeles`, but it's not required because upserts are idempotent. Add `concurrency: { group: scrape, cancel-in-progress: false }`.
> Caveat to surface in README: GH scheduled runs can be delayed minutes under load and are disabled after 60 days of **repo** inactivity. The daily commit of `source_runs` summary + the daily DB write keep both GH and Supabase alive.

### 5.6 Failure isolation
Each adapter runs in try/except; a failure logs to `source_runs` (`ok=false`, error) and **never aborts** the others. Pipeline exit code is 0 unless **zero** events were collected across all sources (that's a real outage → non-zero so the workflow shows red).

---

## 6. Frontend

### 6.1 Stack
React + Vite + TS + Tailwind; `@supabase/supabase-js`; `@fullcalendar/react` (dayGrid month, timeGrid week, multiMonthYear) for calendar; `date-fns`; `lucide-react` icons. PWA via `vite-plugin-pwa`. **Read `/mnt/skills/public/frontend-design/SKILL.md` before writing any UI.**

### 6.2 Views (top-level tabs)
1. **Feed / "New"** (default): reverse-chron list of events with `first_seen > lastVisit` highlighted and pinned to a "🆕 New since your last visit (N)" section at top; rest below. Cards show poster, headliner, openers, venue, date, door/show time, price range, status badge, primary "Get Tickets" button.
2. **Calendar:** FullCalendar with Week / Month / Year toggles. Click a day → that day's shows; click an event → detail drawer.
3. **By Venue:** grouped, with per-venue freshness badge (from `source_runs`).

### 6.3 "New since last visit" (no auth)
On load, read `localStorage['pnw.lastVisit']`; compute new = events with `first_seen > lastVisit`. Render the count + highlights. **Then** write `now()` back to `localStorage` (so the next visit's diff is correct). Provide a "mark all seen" and a "show me what changed since [date]" picker. (P1 upgrade: optional Supabase magic-link auth to sync across devices + followed artists/venues.)

### 6.4 Geography UX
Default scope = **Seattle core + north-to-Bellingham + south-to-Tacoma** (all `region != 'expandable'`). A prominent **"+ Show Portland / Vancouver WA / Vancouver BC"** expander loads the `expandable` regions on click (lazy query). Region chips let users toggle north/south/eastside.

### 6.5 Design direction
Editorial, gig-poster energy — not a generic admin table. Dark-first theme, high-contrast type, one confident accent, poster imagery as the hero of each card, generous spacing, fast skeleton loaders. Fully responsive; works on any mobile browser and installs as a PWA. WCAG AA contrast; keyboard navigable; `prefers-reduced-motion` respected.

### 6.6 Filters (apply across all views)
Category (music/comedy/arts), date range, metro/region, genre, price ceiling, all-ages, free-only, on-sale-now vs. presale/announced, "has tickets." Filter state in URL query params (shareable, restorable).

---

## 7. Suggested Features (prioritized — build P0/P1, scaffold P2)

**P0 (in scope this build):**
- New-since-last-visit feed; week/month/year calendar; venue expander; primary-only ticket links; price + status badges; PWA install; source-freshness badges; shareable filtered URLs.

**P1 (build if time, else stub cleanly):**
- **Subscribe to calendar:** generate a `webcal`/`.ics` feed of the user's current filtered view (downloadable + subscribable in Apple/Google Calendar).
- **On-sale & presale alerts:** "Add to calendar" for `onsale_at`; a "On sale this week" rail.
- **Follow artists/venues** (localStorage list) → personalized New feed.
- **Map view** (Leaflet + OpenStreetMap tiles, free) plotting venues.
- **Spotify/Apple embed** for the headliner in the detail drawer.

**P2 (scaffold + TODO):**
- Optional Supabase auth for cross-device sync + email weekly digest of new shows (Supabase scheduled function + a free email sender).
- Same-tour multi-night grouping; "similar artists you follow"; genre recommendations.
- Admin "source health" dashboard page reading `source_runs`.

---

## 8. Repo Layout
```
pnw-stage/
├─ scraper/
│  ├─ adapters/ (ics.py, rss.py, json.py, ticketmaster.py, html.py, stg.py, ...)
│  ├─ normalize.py  dedup.py  pipeline.py  registry.py  models.py
│  ├─ seed_venues.py            # inserts the §3.3 registry
│  ├─ tests/ (test_normalize.py, test_dedup.py, test_ticketmaster_live.py)
│  └─ requirements.txt
├─ web/  (Vite app: src/, public/, vite.config.ts, tailwind, pwa)
│  └─ tests/ (e2e.spec.ts  — Playwright)
├─ supabase/ (migrations/*.sql, seed.sql)
├─ .github/workflows/ (scrape.yml, deploy.yml, ci.yml)
└─ README.md  (setup, secrets, known caveats, source map)
```

---

## 9. Autonomous Build & Deploy Protocol  ← satisfies "one continuous build, no UAT"

Execute these phases in order. After each phase, run its gate; if the gate fails, fix and re-run that phase before advancing. Use sub-agents for parallelizable work (e.g., one agent per adapter cluster).

**9.1 Provision.** Create the GitHub repo (`gh repo create Dennisdeuce/pnw-stage --private`). Create/locate a Supabase project; apply migrations (`supabase db push` or REST). If a Supabase project must be created and you lack a token, fall through to §9.6.

**9.2 Schema + seed.** Apply §4 DDL; run `seed_venues.py` to load the §3.3 registry. **Gate:** `select count(*) from venues` ≥ 30; RLS verified (anon cannot write — test with anon key).

**9.3 Ingestion.** Build adapters feed-first. Implement Ticketmaster adapter against a **real key** and run it live. **Gates:**
- Unit: `test_normalize`, `test_dedup` green (incl. a double-run idempotency test asserting `first_seen` unchanged and no dup rows).
- Live integration: Ticketmaster adapter returns ≥ 1 Seattle-DMA music event and ≥ 1 comedy event; parsed fields non-null for required columns.
- Full pipeline dry-run upserts to Supabase; `source_runs` shows ≥ 70% of active sources `ok=true`. Sources that fail are logged, not fatal.

**9.4 Frontend.** Build views §6 against live Supabase data. **Gates (Playwright, headless, screenshot each):**
- Feed loads with ≥ 1 card and a working ticket link (href is http(s), not a resale domain — assert against a blocklist: stubhub, vividseats, seatgeek.com/…/resale, ticketmaster…/resale, tmr).
- Calendar renders in week, month, AND year modes without console errors.
- Expander reveals Portland/Vancouver events on click.
- "New since last visit" highlights correctly: seed `localStorage` to an old date → assert ≥1 highlighted; reload → assert count resets.
- Mobile viewport (390px) screenshot has no overflow; Lighthouse PWA installable check passes.
Save screenshots to `web/tests/__screens__/` as the visual QA artifact (this replaces human UAT).

**9.5 Deploy.**
- Frontend → Cloudflare Pages (`wrangler pages deploy web/dist` or Pages Git integration). Set `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY` as Pages env vars.
- Commit `scrape.yml`; trigger it once via `workflow_dispatch`; confirm a green run and fresh rows.
- **Post-deploy smoke:** Playwright hits the **live Cloudflare URL** and re-runs the 9.4 gates against production. Must be green.

**9.6 Secrets / blocked-input handling.** Needed: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (GH secret), `SUPABASE_ANON_KEY` (Pages), `TICKETMASTER_API_KEY` (GH + obtain free), optional `BANDSINTOWN_APP_ID`, `CLOUDFLARE_API_TOKEN`. Try, in order: local env vars, `gh secret list`, `.env`, Supabase/Cloudflare CLIs already authed. **If and only if** a required secret is unobtainable, write it to `README.md` "ACTION REQUIRED" with the exact command to set it, set everything else up so the app runs the moment it's added, and continue — do not halt the whole build for one missing key.

**9.7 Definition of done.** Live Cloudflare URL serves real PNW events; GH Actions cron is scheduled and has one green manual run; all 9.x gates pass; README documents setup, the source map, and known caveats (§10). Print the URL.

---

## 10. Risks & Governance (call these out in README)

1. **"Artist-direct" is largely infeasible** — primary sellers are TM/AXS. Guarantee is **primary, never resale** (§3.4). Don't overstate.
2. **Scraper fragility** — HTML adapters break on redesign. Mitigations: feed-first, source-health table, freshness badges, failure isolation. Expect periodic adapter maintenance; this is inherent to a free aggregator, not a defect.
3. **Legal / ToS** — respect `robots.txt`, rate-limit (≤1 req/2s per host), set a descriptive User-Agent, cache. Display facts (dates/lineups/prices aren't copyrightable) not copied prose/images beyond fair thumbnail use. Honor TM/SeatGeek branding + no-resale-competition terms. SeatGeek's ToS forbids displaying other sellers' listings — that's why it's demoted to optional.
4. **DST / cron drift** — dual UTC cron + idempotent upsert (§5.5).
5. **Free-tier ceilings** — Supabase 500MB/5GB egress (events table is tiny; fine), TM 5k calls/day (we use a few hundred). Add a usage note; upgrade path is Supabase Pro ($25/mo) only if it ever matters.
6. **No-UAT risk** — per-venue under-collection can be silent. Mitigated by data-sanity gates (§9.3) + visible per-venue freshness so gaps surface without a human.

---

## 11. Open Items / Decode Notes (resolve during build; don't silently guess)
- **"Emerald City comedy club"** — no confident match. Leave a TODO adapter stub; during build, web-search "Emerald City comedy Seattle/Tacoma," and if a real venue is found, add a registry row; else omit and note in README.
- **"St. Jackson's comedy club, Tacoma"** — unresolved. Same handling. (Tacoma Comedy Club is already covered — this may be a duplicate/mis-transcription.)
- **"venue next to Climate Pledge"** — built as **McCaw Hall** + **The Vera Project**; confirm which the user meant later.
- **Little Red Hen** is country/dance-focused — keep it (live music) but tag genre so users can filter.

---

## 12. Kickoff — paste-ready

> Run from the parent dir where the repo should live. Launch Claude Code on its own line, then give it the prompt as the next step (don't append the prompt to the launch line).

```
cd ~/projects
```
```
claude --dangerously-skip-permissions
```
Then, as the first message to Claude Code:

> Build the app defined in `BUILD_SPEC_pnw_show_finder.md` (in this directory). Follow §9 exactly: build → test → fix → deploy in one continuous run, using sub-agents and the connected GitHub/Supabase/Cloudflare tools, with no UAT loop. Read `/mnt/skills/public/frontend-design/SKILL.md` before the UI. Obtain the free Ticketmaster Discovery key and test adapters live. Don't stop for anything except a genuinely unobtainable secret (handle per §9.6). When done, run the post-deploy Playwright smoke test against the live Cloudflare URL and print the URL.
