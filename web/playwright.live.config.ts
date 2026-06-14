import { defineConfig, devices } from "@playwright/test";

// LIVE verification config — drives the deployed GitHub Pages site with NO mocks
// and NO local web server, so it proves real Supabase data renders in production.
// Kept in its own testDir so the default (mocked) suite never picks it up.
export default defineConfig({
  testDir: "./tests-live",
  fullyParallel: false,
  retries: 2,
  reporter: [["list"]],
  use: {
    baseURL: process.env.LIVE_URL || "https://dennisdeuce.github.io/pnw-stage/",
    trace: "on-first-retry"
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }]
});
