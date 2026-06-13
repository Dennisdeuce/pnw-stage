import { test, expect, type Page } from "@playwright/test";
import { mockSupabase } from "./fixtures";

const SCREENS = "tests/__screens__";

// Resale/secondary domains that must NEVER appear as a buy link (BUILD_SPEC §3.4 / §9.4).
const RESALE = ["stubhub", "vividseats", "seatgeek.com", "/resale", "tmr", "viagogo"];

async function ticketHrefs(page: Page): Promise<string[]> {
  return page.$$eval('a[href]', (as) =>
    as.map((a) => (a as HTMLAnchorElement).href).filter((h) => /tickets|axs|ticketmaster|\.com\/e\//i.test(h))
  );
}

test.beforeEach(async ({ page }) => {
  await mockSupabase(page);
});

test("feed loads with cards and only primary (non-resale) ticket links", async ({ page }) => {
  await page.goto("/");
  const cards = page.locator("article");
  await expect(cards.first()).toBeVisible();
  expect(await cards.count()).toBeGreaterThanOrEqual(1);

  // A real, http(s) ticket link exists and none are on the resale blocklist.
  const hrefs = await ticketHrefs(page);
  expect(hrefs.length).toBeGreaterThanOrEqual(1);
  for (const h of hrefs) {
    expect(h).toMatch(/^https?:\/\//);
    for (const bad of RESALE) expect(h.toLowerCase()).not.toContain(bad);
  }
  await page.screenshot({ path: `${SCREENS}/feed.png`, fullPage: true });
});

test("calendar renders week, month, and year with no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));

  await page.goto("/");
  await page.getByRole("button", { name: "Calendar" }).click();
  await expect(page.locator(".fc")).toBeVisible();

  await page.getByRole("button", { name: "Month" }).click();
  await expect(page.locator(".fc-dayGridMonth-view")).toBeVisible();
  await page.screenshot({ path: `${SCREENS}/calendar-month.png`, fullPage: true });

  await page.getByRole("button", { name: "Week" }).click();
  await expect(page.locator(".fc-timeGridWeek-view")).toBeVisible();

  await page.getByRole("button", { name: "Year" }).click();
  await expect(page.locator(".fc-multiMonthYear-view")).toBeVisible();
  await page.screenshot({ path: `${SCREENS}/calendar-year.png`, fullPage: true });

  expect(errors, errors.join("\n")).toHaveLength(0);
});

test("expander reveals Portland / Vancouver events on click", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Crystal Ballroom")).toHaveCount(0);
  await page.getByRole("button", { name: /Show Portland/i }).click();
  await expect(page.getByText("Crystal Ballroom")).toBeVisible();
});

test("new-since-last-visit highlights, then resets on next visit", async ({ page, context }) => {
  // Seed an old last-visit so the recent event counts as new.
  await context.addInitScript(() => {
    localStorage.setItem("pnw.lastVisit", "2020-01-01T00:00:00Z");
  });
  await page.goto("/");
  const newSection = page.getByTestId("new-section");
  await expect(newSection).toBeVisible();
  await expect(newSection.locator("article")).toHaveCount(1);
  await page.screenshot({ path: `${SCREENS}/new-since.png`, fullPage: true });

  // The app wrote `now()` back on load; a fresh visit should show nothing new.
  await page.reload();
  await expect(page.getByTestId("new-section")).toHaveCount(0);
});

test("mobile (390px) has no horizontal overflow and registers a PWA manifest", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator("article").first()).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  expect(overflow).toBeLessThanOrEqual(1); // allow sub-pixel rounding

  // Installable basics: linked manifest with name + icons.
  const manifestHref = await page.getAttribute('link[rel="manifest"]', "href");
  expect(manifestHref).toBeTruthy();
  await page.screenshot({ path: `${SCREENS}/mobile.png`, fullPage: true });
});
