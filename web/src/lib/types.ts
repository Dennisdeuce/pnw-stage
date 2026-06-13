// Shape of a row from the `public_events` view (BUILD_SPEC §4).
export type Category = "music" | "comedy" | "arts" | "other";
export type Region = "core" | "north" | "south" | "eastside" | "expandable";
export type TicketType = "venue_primary" | "api_primary" | "artist" | "venue_page";
export type Status =
  | "on_sale"
  | "presale"
  | "sold_out"
  | "announced"
  | "cancelled"
  | "postponed";

export interface EventRow {
  id: number;
  title: string;
  headliner: string | null;
  lineup: string[] | null;
  description: string | null;
  category: Category;
  genres: string[] | null;
  starts_at: string | null;
  doors_at: string | null;
  ends_at: string | null;
  date_local: string;
  is_all_ages: boolean | null;
  is_free: boolean;
  price_min: number | null;
  price_max: number | null;
  currency: string;
  status: Status;
  onsale_at: string | null;
  presale_at: string | null;
  ticket_url: string | null;
  ticket_url_type: TicketType | null;
  image_url: string | null;
  source_url: string | null;
  source_slug: string | null;
  first_seen: string;
  venue_id: number;
  venue_name: string;
  venue_slug: string;
  metro: string;
  region: Region;
  city: string | null;
  state: string | null;
  lat: number | null;
  lng: number | null;
  venue_website: string | null;
}

export interface SourceHealth {
  source_slug: string;
  finished_at: string | null;
  ok: boolean | null;
  events_found: number | null;
  events_upserted: number | null;
}
