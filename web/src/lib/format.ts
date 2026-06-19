import { format, parseISO } from "date-fns";
import type { EventRow } from "./types";

// Every PNW show is in Pacific time. starts_at/doors_at/ends_at are stored as
// UTC instants, so they MUST be formatted in this zone — never the viewer's
// local zone — or a Central/Eastern visitor sees the wrong time (and the day can
// shift). date_local is already the Pacific calendar date; keep using it for the
// date label so weekdays never drift.
const PACIFIC_TZ = "America/Los_Angeles";

// Wall-clock parts (year/month/day/hour/minute) of a UTC instant, in Pacific.
function pacificParts(iso: string): Record<string, string> {
  const out: Record<string, string> = {};
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: PACIFIC_TZ,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
  for (const p of fmt.formatToParts(new Date(iso))) out[p.type] = p.value;
  // h23 yields 00..23; guard against engines that emit "24" for midnight.
  if (out.hour === "24") out.hour = "00";
  return out;
}

// True when the instant lands exactly on midnight Pacific — i.e. a date-only
// listing with no real start time (show "Time TBA" rather than "12:00 AM").
export function isPacificMidnight(iso: string | null): boolean {
  if (!iso) return false;
  const p = pacificParts(iso);
  return p.hour === "00" && p.minute === "00";
}

export function showDate(e: EventRow): string {
  return format(parseISO(e.date_local), "EEE MMM d");
}

// "8:30pm" in Pacific time. null when there's no time or it's a date-only
// (midnight Pacific) listing — callers decide whether to show "Time TBA".
export function showTime(iso: string | null): string | null {
  if (!iso || isPacificMidnight(iso)) return null;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: PACIFIC_TZ,
    hour: "numeric",
    minute: "2-digit"
  })
    .format(new Date(iso))
    .replace(/\s/g, "") // drop the (narrow) space before AM/PM
    .toLowerCase();
}

// The label for an event's start: the Pacific time, or "Time TBA" for a
// date-only listing, or null when there's no start_at at all.
export function showTimeLabel(iso: string | null): string | null {
  if (!iso) return null;
  return showTime(iso) ?? "Time TBA";
}

// Offset-less Pacific wall-clock ISO ("2026-06-19T20:30:00") for FullCalendar,
// which we leave in its default 'local' zone so it renders these digits verbatim
// (no source offset => no conversion), keeping every event on its Pacific day.
export function pacificNaiveISO(iso: string): string {
  const p = pacificParts(iso);
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:00`;
}

export function priceLabel(e: EventRow): string {
  if (e.is_free) return "Free";
  if (e.price_min == null) return "—";
  if (e.price_max != null && e.price_max !== e.price_min) {
    return `$${Math.round(e.price_min)}–${Math.round(e.price_max)}`;
  }
  return `$${Math.round(e.price_min)}`;
}

export function posterFor(e: EventRow): string {
  return e.image_url ?? `https://picsum.photos/seed/pnw-${e.id}/800/1000`;
}

export const REGION_LABEL: Record<string, string> = {
  core: "Seattle core",
  north: "North",
  south: "South",
  eastside: "Eastside",
  "central wa": "Central WA",
  kitsap: "Kitsap",
  puyallup: "Puyallup",
  expandable: "Expanded"
};

export const CATEGORY_LABEL: Record<string, string> = {
  music: "Music",
  comedy: "Comedy",
  arts: "Arts",
  other: "Other"
};
