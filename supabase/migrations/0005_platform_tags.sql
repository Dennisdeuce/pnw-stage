-- PNW Stage — platform tags + venue aliases (coverage pass).
--
-- The 35-HTML-scraper model was wrong: ticketing fragments onto ~5 platforms
-- (Ticketmaster/TicketWeb, AXS, DICE, Tessitura, Tixr). This migration adds the
-- columns that let us (a) route Ticketmaster Discovery events to their real venue
-- row by NAME (not just a resolved tm_venue_id), and (b) record which platform a
-- venue actually sells on so config-driven platform adapters can target it.
--
-- Mirrored exactly in scraper/seed_venues.py — keep the two in lock-step (no drift).

-- (a) Alternate venue names seen in feeds (e.g. TM's "Showbox at the Market").
--     Used to build the normalized name index in adapters/ticketmaster.py.
alter table venues add column if not exists aliases text[] default '{}'::text[];

-- (b) source_runs gets a free-text note so a successful run can still report
--     diagnostics — specifically the TM venue names that fell through to the
--     per-DMA catch-all, so we can promote them into venues.aliases over time.
alter table source_runs add column if not exists note text;

-- Platform hints themselves live in jsonb (venues.source_config.platform /
-- axs_venue_id / tm_web_venue_id and sources.config), so no column is needed for
-- them — seed_venues.py writes them. This migration only adds the two columns
-- above that the SQL layer must know about.
