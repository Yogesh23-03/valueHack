import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0A0A0F",
        surface: "rgba(18, 18, 26, 0.6)",
        primary: "#7C5CFF",
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      animation: {
        shimmer: "shimmer 2s linear infinite",
        drift: "drift 10s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
        drift: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: ".5" },
        }
      }
    },
  },
  plugins: [],
};
export default config;
