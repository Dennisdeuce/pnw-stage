import { test, expect, type Page } from "@playwright/test";

// Verifies the LIVE deployed site renders REAL Supabase events (no mocks).
const LIVE = process.env.LIVE_URL || "https://dennisdeuce.github.io/pnw-stage/";
const SCREENS = "tests-live/__screens__";

// Resale/secondary domains that must NEVER appear as a buy link (BUILD_SPEC §3.4).
const RESALE = ["stubhub", "vividseats", "seatgeek.com", "/resale", "tmr", "viagogo"];

async function ticketHrefs(page: Page): Promise<string[]> {
  return page.$$eval("a[href]", (as) =>
    (as as HTMLAnchorElement[])
      .map((a) => a.href)
      .filter((h) => /tickets|axs|ticketmaster|dice\.fm|\.com\/e\//i.test(h))
  );
}

test("LIVE feed renders real event cards with only primary ticket links", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(LIVE, { waitUntil: "networkidle" });

  // The config-error panel must NOT be showing (would mean bad URL/key/base-path).
  await expect(page.getByText("Can’t load shows")).toHaveCount(0);

  // Real cards load asynchronously from Supabase — wait for them.
  const cards = page.locator("article");
  await expect(cards.first()).toBeVisible({ timeout: 30_000 });
  const count = await cards.count();
  expect(count, "expected >=1 real event card").toBeGreaterThanOrEqual(1);
  console.log(`LIVE feed cards: ${count}`);

  // At least one real primary ticket link, none on the resale blocklist.
  const hrefs = await ticketHrefs(page);
  expect(hrefs.length, "expected >=1 ticket link").toBeGreaterThanOrEqual(1);
  for (const h of hrefs) {
    expect(h).toMatch(/^https?:\/\//);
    for (const bad of RESALE) expect(h.toLowerCase()).not.toContain(bad);
  }
  console.log(`LIVE ticket links: ${hrefs.length} (sample: ${hrefs[0]})`);

  await page.screenshot({ path: `${SCREENS}/live-feed.png`, fullPage: true });
  expect(errors, errors.join("\n")).toHaveLength(0);
});

test("LIVE calendar renders week, month, and year", async ({ page }) => {
  await page.goto(LIVE, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Calendar" }).click();
  await expect(page.locator(".fc")).toBeVisible({ timeout: 30_000 });

  await page.locator(".fc-dayGridMonth-button").click();
  await expect(page.locator(".fc-dayGridMonth-view")).toBeVisible();
  await page.screenshot({ path: `${SCREENS}/live-calendar-month.png`, fullPage: true });

  await page.locator(".fc-timeGridWeek-button").click();
  await expect(page.locator(".fc-timeGridWeek-view")).toBeVisible();
  await page.screenshot({ path: `${SCREENS}/live-calendar-week.png`, fullPage: true });

  await page.locator(".fc-multiMonthYear-button").click();
  await expect(page.locator(".fc-multiMonthYear-view")).toBeVisible();
  await page.screenshot({ path: `${SCREENS}/live-calendar-year.png`, fullPage: true });
});
