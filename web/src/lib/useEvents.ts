import { useEffect, useState } from "react";
import { supabase, isConfigured } from "./supabase";
import type { EventRow, SourceHealth } from "./types";

const SELECT = "*";

// Core dataset = everything in-region (region != 'expandable'). The expandable
// metros (Portland / Vancouver) are fetched lazily the first time the user opens
// the expander (BUILD_SPEC §6.4), so the default payload stays small.
export function useEvents(showExpandable: boolean) {
  const [core, setCore] = useState<EventRow[]>([]);
  const [expandable, setExpandable] = useState<EventRow[] | null>(null);
  const [health, setHealth] = useState<SourceHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load: core regions + source health.
  useEffect(() => {
    if (!isConfigured) {
      setError("App is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
      setLoading(false);
      return;
    }
    let alive = true;
    (async () => {
      setLoading(true);
      const [{ data, error: e1 }, { data: h }] = await Promise.all([
        supabase
          .from("public_events")
          .select(SELECT)
          .neq("region", "expandable")
          .order("date_local", { ascending: true }),
        supabase.from("public_source_health").select("*")
      ]);
      if (!alive) return;
      if (e1) setError(e1.message);
      else setCore((data as EventRow[]) ?? []);
      setHealth((h as SourceHealth[]) ?? []);
      setLoading(false);
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Lazy load expandable regions on first reveal.
  useEffect(() => {
    if (!showExpandable || expandable !== null || !isConfigured) return;
    let alive = true;
    (async () => {
      const { data } = await supabase
        .from("public_events")
        .select(SELECT)
        .eq("region", "expandable")
        .order("date_local", { ascending: true });
      if (alive) setExpandable((data as EventRow[]) ?? []);
    })();
    return () => {
      alive = false;
    };
  }, [showExpandable, expandable]);

  const events = showExpandable && expandable ? [...core, ...expandable] : core;
  return { events, health, loading, error };
}
