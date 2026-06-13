-- Security hardening for upsert_event (caught by Supabase security advisor).
-- Postgres grants EXECUTE on functions to PUBLIC by default, so revoking from
-- anon/authenticated alone left this SECURITY DEFINER function callable by anyone
-- via /rest/v1/rpc/upsert_event — which would bypass RLS and let anon write events.
-- Lock it to service_role only (the scraper), and pin search_path.

revoke all on function upsert_event(jsonb) from public, anon, authenticated;
alter function upsert_event(jsonb) set search_path = public, pg_temp;
grant execute on function upsert_event(jsonb) to service_role;
