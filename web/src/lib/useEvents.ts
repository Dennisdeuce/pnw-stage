import { useEffect, useState } from "react";
import { supabase, isConfigured } from "./supabase";
import type { EventRow, SourceHealth } from "./types";

const SELECT = "*";
// PostgREST caps a single response at its server max-rows (1000 here), so we
// page through with ranged requests rather than one unbounded fetch — otherwise
// the feed silently stops at 1000 of the ~1.5k upcoming shows.
const PAGE_SIZE = 500;

// Fetch every matching row by paging until a short page comes back. Order by
// (date_local, id) so the window is stable across requests — no dupes or gaps.
async function fetchAllEvents(expandable: boolean): Promise<EventRow[]> {
  const out: EventRow[] = [];
  for (let from = 0; ; from += PAGE_SIZE) {
    let query = supabase.from("public_events").select(SELECT);
    query = expandable ? query.eq("region", "expandable") : query.neq("region", "expandable");
    const { data, error } = await query
      .order("date_local", { ascending: true })
      .order("id", { ascending: true })
      .range(from, from + PAGE_SIZE - 1);
    if (error) throw error;
    const rows = (data as EventRow[]) ?? [];
    out.push(...rows);
    if (rows.length < PAGE_SIZE) break;
  }
  return out;
}

// True total of upcoming in-region shows, from a count query (head:true, no rows)
// so the header reflects the real number — not the (capped) fetched array length.
async function fetchUpcomingTotal(): Promise<number | null> {
  const { count, error } = await supabase
    .from("public_events")
    .select("*", { count: "exact", head: true })
    .neq("region", "expandable");
  if (error) throw error;
  return count ?? null;
}

// Core dataset = everything in-region (region != 'expandable'). The expandable
// metros (Portland / Vancouver) are fetched lazily the first time the user opens
// the expander (BUILD_SPEC §6.4), so the default payload stays small.
export function useEvents(showExpandable: boolean) {
  const [core, setCore] = useState<EventRow[]>([]);
  const [expandable, setExpandable] = useState<EventRow[] | null>(null);
  const [health, setHealth] = useState<SourceHealth[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load: all core regions (paged) + true count + source health.
  useEffect(() => {
    if (!isConfigured) {
      setError("App is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
      setLoading(false);
      return;
    }
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const [rows, count, { data: h }] = await Promise.all([
          fetchAllEvents(false),
          fetchUpcomingTotal(),
          supabase.from("public_source_health").select("*")
        ]);
        if (!alive) return;
        setCore(rows);
        setTotal(count);
        setHealth((h as SourceHealth[]) ?? []);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Lazy load expandable regions on first reveal (also paged).
  useEffect(() => {
    if (!showExpandable || expandable !== null || !isConfigured) return;
    let alive = true;
    (async () => {
      try {
        const rows = await fetchAllEvents(true);
        if (alive) setExpandable(rows);
      } catch {
        if (alive) setExpandable([]);
      }
    })();
    return () => {
      alive = false;
    };
  }, [showExpandable, expandable]);

  const events = showExpandable && expandable ? [...core, ...expandable] : core;
  return { events, health, total, loading, error };
}
