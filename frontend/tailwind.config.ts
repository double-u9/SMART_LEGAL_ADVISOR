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
        obsidian: {
          950: "#050505",
          900: "#0A0A0A",
          800: "#121212",
          700: "#1A1A1A",
          600: "#262626",
          500: "#404040",
        },
        platinum: {
          DEFAULT: "#E5E7EB",
          muted: "#9CA3AF",
          dark: "#4B5563",
        },
        gold: {
          DEFAULT: "#D4AF37",
          light: "#E8CC6E",
          dark: "#9E8226",
          muted: "rgba(212, 175, 55, 0.15)",
        },
      },
      fontFamily: {
        heading: ['"Noto Kufi Arabic"', "sans-serif"],
        body: ['"Noto Sans Arabic"', "sans-serif"],
        latin: ['"Inter"', "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "fade-in-up": "fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-right": "slideRight 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        "shimmer": "shimmer 2.5s linear infinite",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideRight: {
          "0%": { opacity: "0", transform: "translateX(-16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 10px rgba(212, 175, 55, 0.1)" },
          "50%": { boxShadow: "0 0 25px rgba(212, 175, 55, 0.3)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      backdropBlur: {
        xs: "2px",
        md: "12px",
        lg: "24px",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
        "full": "9999px",
      },
    },
  },
  plugins: [],
};

export default config;
