// Filter state lives in the URL query string so any view is shareable and
// restorable (BUILD_SPEC §6.6).
import type { Category, Region } from "./types";

export type SaleState = "any" | "on_sale" | "presale";

export interface Filters {
  categories: Category[];
  regions: Region[]; // which non-expandable regions are active
  showExpandable: boolean; // the Portland/Vancouver expander
  priceCeiling: number | null;
  allAges: boolean;
  freeOnly: boolean;
  hasTickets: boolean;
  sale: SaleState;
  query: string;
}

export const ALL_REGIONS: Region[] = ["core", "north", "south", "eastside"];

export const DEFAULT_FILTERS: Filters = {
  categories: [],
  regions: [...ALL_REGIONS],
  showExpandable: false,
  priceCeiling: null,
  allAges: false,
  freeOnly: false,
  hasTickets: false,
  sale: "any",
  query: ""
};

export function filtersFromParams(p: URLSearchParams): Filters {
  const list = (k: string) => (p.get(k) ? p.get(k)!.split(",").filter(Boolean) : null);
  return {
    categories: (list("cat") as Category[]) ?? [],
    regions: (list("region") as Region[]) ?? [...ALL_REGIONS],
    showExpandable: p.get("expand") === "1",
    priceCeiling: p.get("price") ? Number(p.get("price")) : null,
    allAges: p.get("ages") === "1",
    freeOnly: p.get("free") === "1",
    hasTickets: p.get("tix") === "1",
    sale: (p.get("sale") as SaleState) ?? "any",
    query: p.get("q") ?? ""
  };
}

export function paramsFromFilters(f: Filters): URLSearchParams {
  const p = new URLSearchParams();
  if (f.categories.length) p.set("cat", f.categories.join(","));
  // Only record regions when they differ from the default (all on).
  if (f.regions.length !== ALL_REGIONS.length) p.set("region", f.regions.join(","));
  if (f.showExpandable) p.set("expand", "1");
  if (f.priceCeiling != null) p.set("price", String(f.priceCeiling));
  if (f.allAges) p.set("ages", "1");
  if (f.freeOnly) p.set("free", "1");
  if (f.hasTickets) p.set("tix", "1");
  if (f.sale !== "any") p.set("sale", f.sale);
  if (f.query) p.set("q", f.query);
  return p;
}

// Client-side predicate (we also push most of this to Postgres in the query).
export function matches(e: {
  category: Category;
  region: Region;
  price_min: number | null;
  is_all_ages: boolean | null;
  is_free: boolean;
  ticket_url: string | null;
  status: string;
  title: string;
  headliner: string | null;
  venue_name: string;
}, f: Filters): boolean {
  if (f.categories.length && !f.categories.includes(e.category)) return false;

  const regionAllowed =
    e.region === "expandable" ? f.showExpandable : f.regions.includes(e.region);
  if (!regionAllowed) return false;

  if (f.priceCeiling != null && e.price_min != null && e.price_min > f.priceCeiling)
    return false;
  if (f.allAges && e.is_all_ages !== true) return false;
  if (f.freeOnly && !e.is_free) return false;
  if (f.hasTickets && !e.ticket_url) return false;
  if (f.sale === "on_sale" && e.status !== "on_sale") return false;
  if (f.sale === "presale" && e.status !== "presale") return false;

  if (f.query) {
    const q = f.query.toLowerCase();
    const hay = `${e.title} ${e.headliner ?? ""} ${e.venue_name}`.toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}
