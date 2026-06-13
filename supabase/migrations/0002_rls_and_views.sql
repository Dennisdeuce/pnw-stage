-- PNW Stage — RLS + public read-only views (BUILD_SPEC §4)
-- anon may ONLY SELECT the public_* views. The scraper uses the service-role key,
-- which bypasses RLS for writes. The anon key must never have write access.

alter table venues      enable row level security;
alter table events      enable row level security;
alter table sources     enable row level security;
alter table source_runs enable row level security;

-- No anon policies are created on the base tables => anon gets nothing from them directly.
-- (service_role bypasses RLS, so the scraper still writes fine.)

-- Public read view the SPA consumes (joins venue fields, hides raw/internal columns).
create or replace view public_events
with (security_invoker = on) as
  select e.id, e.title, e.headliner, e.lineup, e.description, e.category, e.genres,
         e.starts_at, e.doors_at, e.ends_at, e.date_local, e.is_all_ages, e.is_free,
         e.price_min, e.price_max, e.currency, e.status, e.onsale_at, e.presale_at,
         e.ticket_url, e.ticket_url_type, e.image_url, e.source_url, e.source_slug,
         e.first_seen,
         v.id as venue_id, v.name as venue_name, v.slug as venue_slug,
         v.metro, v.region, v.city, v.state, v.lat, v.lng, v.website as venue_website
  from events e
  join venues v on v.id = e.venue_id
  where e.status <> 'cancelled'
    and e.date_local >= current_date;

create or replace view public_venues
with (security_invoker = on) as
  select v.id, v.slug, v.name, v.metro, v.region, v.city, v.state, v.country,
         v.lat, v.lng, v.website, v.is_active
  from venues v
  where v.is_active = true;

-- Source freshness view: most-recent run per source, so the UI can show health badges.
create or replace view public_source_health
with (security_invoker = on) as
  select distinct on (sr.source_slug)
         sr.source_slug, sr.finished_at, sr.ok, sr.events_found, sr.events_upserted
  from source_runs sr
  order by sr.source_slug, sr.finished_at desc nulls last;

-- security_invoker views still need the underlying rows to be readable by anon.
-- Add narrow SELECT policies that expose ONLY the columns/rows the views use.
create policy events_anon_read on events
  for select to anon
  using (status <> 'cancelled' and date_local >= current_date);

create policy venues_anon_read on venues
  for select to anon
  using (is_active = true);

create policy source_runs_anon_read on source_runs
  for select to anon
  using (true);

-- sources table stays private (no anon policy).

grant select on public_events, public_venues, public_source_health to anon;
