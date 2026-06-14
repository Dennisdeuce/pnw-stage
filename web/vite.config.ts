import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Deployed as a GitHub Pages PROJECT site at https://dennisdeuce.github.io/pnw-stage/,
// so every asset, the SW scope, and the manifest must live under the /pnw-stage/ base.
const BASE = "/pnw-stage/";

export default defineConfig({
  base: BASE,
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "PNW Stage",
        short_name: "PNW Stage",
        description: "Concerts & comedy across the Pacific Northwest, refreshed daily.",
        theme_color: "#0B0F0D",
        background_color: "#0B0F0D",
        display: "standalone",
        scope: BASE,
        start_url: BASE,
        icons: [
          { src: `${BASE}icon-192.png`, sizes: "192x192", type: "image/png" },
          { src: `${BASE}icon-512.png`, sizes: "512x512", type: "image/png" },
          { src: `${BASE}icon-512.png`, sizes: "512x512", type: "image/png", purpose: "maskable" }
        ]
      }
    })
  ]
});
