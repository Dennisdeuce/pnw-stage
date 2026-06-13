/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Evergreen-black base — PNW forest at night, not pure black.
        ink: {
          900: "#0B0F0D",
          800: "#101713",
          700: "#16201A",
          600: "#1E2A22"
        },
        bone: "#ECF2EC",
        moss: "#7E8C82",
        // One confident accent: marquee signal coral.
        coral: "#FF5A3C",
        // Sparing cool secondary for riso duotone + presale.
        sky: "#4DA8FF",
        amber: "#F5B544"
      },
      fontFamily: {
        display: ["Anton", "Impact", "sans-serif"],
        sans: ["'Space Grotesk'", "system-ui", "sans-serif"],
        mono: ["'Space Mono'", "ui-monospace", "monospace"]
      },
      boxShadow: {
        flyer: "0 1px 0 rgba(255,255,255,0.04), 0 18px 40px -24px rgba(0,0,0,0.9)"
      },
      keyframes: {
        flicker: {
          "0%, 100%": { opacity: "1" },
          "45%": { opacity: "0.92" },
          "50%": { opacity: "0.7" },
          "55%": { opacity: "0.95" }
        }
      },
      animation: {
        flicker: "flicker 4s ease-in-out infinite"
      }
    }
  },
  plugins: []
};
