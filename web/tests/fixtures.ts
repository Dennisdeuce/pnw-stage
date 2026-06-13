import type { Page } from "@playwright/test";

// Minimal but representative public_events rows. `first_seen` uses placeholders
// the installer rewrites at runtime so "new since last visit" is testable.
function ev(overrides: Record<string, unknown>) {
  return {
    id: 0,
    title: "Untitled",
    headliner: null,
    lineup: null,
    description: null,
    category: "music",
    genres: null,
    starts_at: null,
    doors_at: null,
    ends_at: null,
    date_local: "2026-06-20",
    is_all_ages: null,
    is_free: false,
    price_min: 30,
    price_max: 45,
    currency: "USD",
    status: "on_sale",
    onsale_at: null,
    presale_at: null,
    ticket_url: "https://www.axs.com/events/demo",
    ticket_url_type: "api_primary",
    image_url: null,
    source_url: "https://example.com",
    source_slug: "seed_demo",
    first_seen: "2020-01-01T00:00:00Z",
    venue_id: 1,
    venue_name: "The Showbox",
    venue_slug: "the-showbox",
    metro: "seattle",
    region: "core",
    city: "Seattle",
    state: "WA",
    lat: null,
    lng: null,
    venue_website: null,
    ...overrides
  };
}

// Two core events (one brand new), one expandable (Portland) revealed by expander.
export const CORE_EVENTS = [
  ev({ id: 1, headliner: "Japanese Breakfast", title: "Japanese Breakfast", date_local: "2026-06-20", first_seen: "RECENT", lineup: ["Hand Habits"] }),
  ev({ id: 2, headliner: "Kamasi Washington", title: "Kamasi Washington", category: "music", date_local: "2026-07-15", venue_name: "Jazz Alley", venue_slug: "jazz-alley", first_seen: "2020-01-01T00:00:00Z" }),
  ev({ id: 3, headliner: "Nate Bargatze", title: "Nate Bargatze", category: "comedy", date_local: "2026-06-27", venue_name: "Tacoma Comedy Club", venue_slug: "tacoma-comedy-club", region: "south", first_seen: "2020-01-01T00:00:00Z", ticket_url: "https://www.tacomacomedyclub.com/e/x", ticket_url_type: "venue_primary" })
];

export const EXPANDABLE_EVENTS = [
  ev({ id: 9, headliner: "Khruangbin", title: "Khruangbin", date_local: "2026-07-18", venue_name: "Crystal Ballroom", venue_slug: "crystal-ballroom", region: "expandable", metro: "portland", city: "Portland", state: "OR", ticket_url: "https://www.crystalballroompdx.com/e/x", ticket_url_type: "venue_primary" })
];

export const SOURCE_HEALTH = [
  { source_slug: "seed_demo", finished_at: new Date().toISOString(), ok: true, events_found: 3, events_upserted: 3 }
];

// Intercept the Supabase REST calls the app makes and fulfill with fixtures.
export async function mockSupabase(page: Page) {
  const recent = new Date(Date.now() - 1000 * 60 * 60).toISOString(); // 1h ago

  await page.route("**/rest/v1/public_events**", (route) => {
    const url = route.request().url();
    const isExpandable = url.includes("region=eq.expandable");
    const rows = (isExpandable ? EXPANDABLE_EVENTS : CORE_EVENTS).map((r) => ({
      ...r,
      first_seen: r.first_seen === "RECENT" ? recent : r.first_seen
    }));
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(rows) });
  });

  await page.route("**/rest/v1/public_source_health**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SOURCE_HEALTH) })
  );
}
