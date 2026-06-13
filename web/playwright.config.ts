import { defineConfig, devices } from "@playwright/test";

// Runs the production build via `vite preview` and drives it headless. The
// Supabase REST layer is mocked inside the specs (route fulfillment) so the UI
// gates are deterministic and don't depend on network egress or live data.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:4173",
    trace: "on-first-retry"
  },
  webServer: {
    command: "npm run preview",
    port: 4173,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }]
});
