import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#0A0F1C",
          900: "#0D1321",
          800: "#111827",
          700: "#1F2937",
          600: "#374151",
          500: "#4B5563",
        },
        gold: {
          DEFAULT: "#D4AF37",
          light: "#E8CC6E",
          dark: "#B8941F",
          muted: "rgba(212, 175, 55, 0.15)",
        },
        emerald: {
          DEFAULT: "#10B981",
          light: "#34D399",
          dark: "#059669",
        },
      },
      fontFamily: {
        heading: ['"Noto Kufi Arabic"', "sans-serif"],
        body: ['"Noto Sans Arabic"', "sans-serif"],
        latin: ['"Inter"', "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.4s ease-out forwards",
        "slide-right": "slideRight 0.3s ease-out forwards",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "spin-slow": "spin 3s linear infinite",
        "typing": "typing 1.2s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideRight: {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 5px rgba(212, 175, 55, 0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(212, 175, 55, 0.6)" },
        },
        typing: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.3" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
