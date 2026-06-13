import { format, parseISO } from "date-fns";
import type { EventRow } from "./types";

export function showDate(e: EventRow): string {
  return format(parseISO(e.date_local), "EEE MMM d");
}

export function showTime(iso: string | null): string | null {
  if (!iso) return null;
  return format(parseISO(iso), "h:mma").toLowerCase();
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
  expandable: "Expanded"
};

export const CATEGORY_LABEL: Record<string, string> = {
  music: "Music",
  comedy: "Comedy",
  arts: "Arts",
  other: "Other"
};
