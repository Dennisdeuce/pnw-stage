-- Idempotent event upsert (BUILD_SPEC §5.4).
-- Insert new events with first_seen = now(). On natural_key conflict:
--   * first_seen is preserved (never in the SET list),
--   * last_seen / updated_at always bump (so liveness tracks every run),
--   * content columns update ONLY when the incoming source_priority is better
--     (<=) than the stored one — venue feed beats TM beats generic.
-- This makes double-runs (DST dual-cron) and multi-source overlap safe.

create or replace function upsert_event(e jsonb)
returns void
language plpgsql
security definer
as $$
declare
  better boolean;
begin
  insert into events (
    natural_key, venue_id, title, headliner, lineup, description, category, genres,
    starts_at, doors_at, ends_at, date_local, is_all_ages, is_free,
    price_min, price_max, currency, status, onsale_at, presale_at,
    ticket_url, ticket_url_type, image_url, source_slug, source_url,
    source_priority, raw, first_seen, last_seen, updated_at
  )
  values (
    e->>'natural_key',
    (e->>'venue_id')::bigint,
    e->>'title',
    e->>'headliner',
    case when e ? 'lineup'  and jsonb_typeof(e->'lineup')  = 'array'
         then array(select jsonb_array_elements_text(e->'lineup'))  end,
    e->>'description',
    e->>'category',
    case when e ? 'genres'  and jsonb_typeof(e->'genres')  = 'array'
         then array(select jsonb_array_elements_text(e->'genres'))  end,
    (e->>'starts_at')::timestamptz,
    (e->>'doors_at')::timestamptz,
    (e->>'ends_at')::timestamptz,
    (e->>'date_local')::date,
    (e->>'is_all_ages')::boolean,
    coalesce((e->>'is_free')::boolean, false),
    (e->>'price_min')::numeric,
    (e->>'price_max')::numeric,
    coalesce(e->>'currency', 'USD'),
    coalesce(e->>'status', 'on_sale'),
    (e->>'onsale_at')::timestamptz,
    (e->>'presale_at')::timestamptz,
    e->>'ticket_url',
    e->>'ticket_url_type',
    e->>'image_url',
    e->>'source_slug',
    e->>'source_url',
    coalesce((e->>'source_priority')::int, 100),
    coalesce(e->'raw', '{}'::jsonb),
    now(), now(), now()
  )
  on conflict (natural_key) do update set
    last_seen  = now(),
    updated_at = now(),
    -- content fields: keep old unless the incoming source is at least as authoritative
    venue_id        = case when (excluded.source_priority <= events.source_priority) then excluded.venue_id        else events.venue_id        end,
    title           = case when (excluded.source_priority <= events.source_priority) then excluded.title           else events.title           end,
    headliner       = case when (excluded.source_priority <= events.source_priority) then excluded.headliner       else events.headliner       end,
    lineup          = case when (excluded.source_priority <= events.source_priority) then excluded.lineup          else events.lineup          end,
    description     = case when (excluded.source_priority <= events.source_priority) then excluded.description     else events.description     end,
    category        = case when (excluded.source_priority <= events.source_priority) then excluded.category        else events.category        end,
    genres          = case when (excluded.source_priority <= events.source_priority) then excluded.genres          else events.genres          end,
    starts_at       = case when (excluded.source_priority <= events.source_priority) then excluded.starts_at       else events.starts_at       end,
    doors_at        = case when (excluded.source_priority <= events.source_priority) then excluded.doors_at        else events.doors_at        end,
    ends_at         = case when (excluded.source_priority <= events.source_priority) then excluded.ends_at         else events.ends_at         end,
    date_local      = case when (excluded.source_priority <= events.source_priority) then excluded.date_local      else events.date_local      end,
    is_all_ages     = case when (excluded.source_priority <= events.source_priority) then excluded.is_all_ages     else events.is_all_ages     end,
    is_free         = case when (excluded.source_priority <= events.source_priority) then excluded.is_free         else events.is_free         end,
    price_min       = case when (excluded.source_priority <= events.source_priority) then excluded.price_min       else events.price_min       end,
    price_max       = case when (excluded.source_priority <= events.source_priority) then excluded.price_max       else events.price_max       end,
    currency        = case when (excluded.source_priority <= events.source_priority) then excluded.currency        else events.currency        end,
    status          = case when (excluded.source_priority <= events.source_priority) then excluded.status          else events.status          end,
    onsale_at       = case when (excluded.source_priority <= events.source_priority) then excluded.onsale_at       else events.onsale_at       end,
    presale_at      = case when (excluded.source_priority <= events.source_priority) then excluded.presale_at      else events.presale_at      end,
    ticket_url      = case when (excluded.source_priority <= events.source_priority) then excluded.ticket_url      else events.ticket_url      end,
    ticket_url_type = case when (excluded.source_priority <= events.source_priority) then excluded.ticket_url_type else events.ticket_url_type end,
    image_url       = case when (excluded.source_priority <= events.source_priority) then excluded.image_url       else events.image_url       end,
    source_slug     = case when (excluded.source_priority <= events.source_priority) then excluded.source_slug     else events.source_slug     end,
    source_url      = case when (excluded.source_priority <= events.source_priority) then excluded.source_url      else events.source_url      end,
    source_priority = least(excluded.source_priority, events.source_priority);
end;
$$;

revoke all on function upsert_event(jsonb) from anon, authenticated;
