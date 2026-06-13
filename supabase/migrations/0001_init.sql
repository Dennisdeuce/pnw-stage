-- PNW Stage — core schema
-- venues · sources · events · source_runs
-- See BUILD_SPEC §4. All write access is service-role only (RLS below in 0002).

create extension if not exists pgcrypto;

-- venues: the source-of-truth registry
create table if not exists venues (
  id                    bigint generated always as identity primary key,
  slug                  text unique not null,
  name                  text not null,
  metro                 text not null,            -- 'seattle','tacoma','everett','bellingham','portland','vancouver_wa','vancouver_bc'
  region                text not null,            -- 'core','north','south','eastside','expandable'
  city                  text,
  state                 text,
  country               text default 'US',
  lat                   double precision,
  lng                   double precision,
  website               text,
  official_ticket_base  text,                     -- for building venue_primary links
  tm_venue_id           text,                     -- ticketmaster venue id cache
  source_kind           text not null,            -- 'ics','rss','json','ticketmaster','html'
  source_config         jsonb default '{}'::jsonb,-- feed url, selectors, classification, etc.
  is_active             boolean default true,
  created_at            timestamptz default now()
);

-- sources: one row per ingest adapter (often 1:1 with venue, sometimes 1:many e.g. STG)
create table if not exists sources (
  id          bigint generated always as identity primary key,
  slug        text unique not null,               -- 'stg','ticketmaster_seatac','tractor_tavern',...
  kind        text not null,                      -- 'ics','rss','json','ticketmaster','html'
  config      jsonb default '{}'::jsonb,
  is_active   boolean default true
);

create table if not exists events (
  id              bigint generated always as identity primary key,
  natural_key     text unique not null,           -- sha256(venue_id|date_local|normalized_title) — dedup key (§5.4)
  venue_id        bigint references venues(id),
  title           text not null,
  headliner       text,
  lineup          text[],                         -- openers/support
  description     text,
  category        text not null,                  -- 'music','comedy','arts','other'
  genres          text[],
  starts_at       timestamptz,                    -- show/set time (UTC)
  doors_at        timestamptz,
  ends_at         timestamptz,
  date_local      date not null,                  -- America/Los_Angeles (or venue tz) calendar date
  is_all_ages     boolean,
  is_free         boolean default false,
  price_min       numeric,
  price_max       numeric,
  currency        text default 'USD',
  status          text default 'on_sale',         -- 'on_sale','presale','sold_out','announced','cancelled','postponed'
  onsale_at       timestamptz,
  presale_at      timestamptz,
  ticket_url      text,
  ticket_url_type text,                           -- 'venue_primary','api_primary','artist','venue_page'
  image_url       text,
  source_slug     text references sources(slug),
  source_url      text,
  source_priority int default 100,                -- lower wins when same natural_key seen from 2 sources
  raw             jsonb,
  first_seen      timestamptz default now(),      -- NEVER overwrite on update (drives "new since last visit")
  last_seen       timestamptz default now(),      -- bumped every run the event is still present
  updated_at      timestamptz default now()
);
create index if not exists events_date_local_idx on events (date_local);
create index if not exists events_venue_id_idx   on events (venue_id);
create index if not exists events_category_idx   on events (category);
create index if not exists events_first_seen_idx on events (first_seen);

create table if not exists source_runs (
  id          bigint generated always as identity primary key,
  source_slug text,
  started_at  timestamptz,
  finished_at timestamptz,
  ok          boolean,
  events_found    int,
  events_upserted int,
  error       text
);
create index if not exists source_runs_started_idx on source_runs (started_at desc);
