/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Mukuru brand palette
        mukuru: {
          green:      "#00843D", // primary CTA green
          "green-dark": "#005C2B",
          "green-light": "#E6F4EC",
          orange:     "#F47920", // secondary accent
          "orange-light": "#FEF0E5",
          navy:       "#1A2B4A",
          gray:       "#4A5568",
          "gray-light": "#F7F8FA",
          "gray-border": "#E2E8F0",
        },
        // Risk tiers
        safe:    { DEFAULT: "#059669", bg: "#ECFDF5", text: "#065F46" },
        caution: { DEFAULT: "#D97706", bg: "#FFFBEB", text: "#92400E" },
        risk:    { DEFAULT: "#DC2626", bg: "#FEF2F2", text: "#991B1B" },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'Courier New'", "Courier", "monospace"],
      },
      keyframes: {
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
      },
      animation: {
        blink: "blink 1s step-end infinite",
      },
    },
  },
  plugins: [],
}

