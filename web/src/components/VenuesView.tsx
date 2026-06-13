import { useMemo } from "react";
import type { EventRow, SourceHealth } from "../lib/types";
import { EventCard } from "./EventCard";
import { REGION_LABEL } from "../lib/format";

interface Props {
  events: EventRow[];
  health: SourceHealth[];
  isNew: (e: EventRow) => boolean;
  onOpen: (e: EventRow) => void;
}

export function VenuesView({ events, health, isNew, onOpen }: Props) {
  const healthBySlug = useMemo(() => {
    const m = new Map<string, SourceHealth>();
    health.forEach((h) => m.set(h.source_slug, h));
    return m;
  }, [health]);

  const groups = useMemo(() => {
    const map = new Map<string, EventRow[]>();
    for (const e of events) {
      const arr = map.get(e.venue_slug) ?? [];
      arr.push(e);
      map.set(e.venue_slug, arr);
    }
    return [...map.entries()].sort((a, b) =>
      a[1][0].venue_name.localeCompare(b[1][0].venue_name)
    );
  }, [events]);

  return (
    <div className="flex flex-col gap-8">
      {groups.map(([slug, list]) => {
        const venue = list[0];
        const sources = new Set(list.map((e) => e.source_slug).filter(Boolean) as string[]);
        const fresh = freshness([...sources], healthBySlug);
        return (
          <section key={slug}>
            <div className="mb-3 flex items-end justify-between border-b border-ink-600 pb-2">
              <div>
                <h2 className="font-display text-2xl tracking-wide text-bone">{venue.venue_name}</h2>
                <p className="font-mono text-[11px] uppercase tracking-widest text-moss">
                  {REGION_LABEL[venue.region]} · {venue.city ?? venue.metro} · {list.length} shows
                </p>
              </div>
              <FreshBadge state={fresh} />
            </div>
            <div className="grid gap-3">
              {list.map((e) => (
                <EventCard key={e.id} event={e} isNew={isNew(e)} onOpen={onOpen} />
              ))}
            </div>
          </section>
        );
      })}
      {groups.length === 0 && (
        <p className="rounded-lg border border-ink-600 bg-ink-800 p-8 text-center text-moss">
          No venues match these filters.
        </p>
      )}
    </div>
  );
}

type Fresh = "fresh" | "stale" | "unknown";

function freshness(sources: string[], map: Map<string, SourceHealth>): Fresh {
  let sawHealth = false;
  let allOk = true;
  for (const s of sources) {
    const h = map.get(s);
    if (!h) continue;
    sawHealth = true;
    const recent =
      h.finished_at != null &&
      Date.now() - Date.parse(h.finished_at) < 1000 * 60 * 60 * 48;
    if (!(h.ok && recent)) allOk = false;
  }
  if (!sawHealth) return "unknown";
  return allOk ? "fresh" : "stale";
}

function FreshBadge({ state }: { state: Fresh }) {
  const style =
    state === "fresh"
      ? "text-emerald-300 bg-emerald-500/10"
      : state === "stale"
      ? "text-amber bg-amber/10"
      : "text-moss bg-ink-700";
  const label = state === "fresh" ? "Fresh" : state === "stale" ? "Check source" : "No run yet";
  return (
    <span className={`rounded-sm px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${style}`}>
      {label}
    </span>
  );
}
