import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#04060d",
          900: "#070b16",
          850: "#0a0f1e",
          800: "#0d1326",
          700: "#121a33",
          600: "#1a2444",
        },
        rush: {
          DEFAULT: "#2f6bff",
          light: "#5b8bff",
          dark: "#1c48d1",
          cyan: "#3ee8ff",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(63,120,255,0.35)",
        "glow-sm": "0 0 18px rgba(63,120,255,0.35)",
        card: "0 10px 30px -12px rgba(0,0,0,0.55)",
      },
      backgroundImage: {
        "rush-gradient": "linear-gradient(135deg, #2f6bff 0%, #3ee8ff 100%)",
        "navy-radial": "radial-gradient(circle at 50% 0%, #121a33 0%, #070b16 55%, #04060d 100%)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 6s ease-in-out infinite",
        "float-delay": "float 6s ease-in-out 1.5s infinite",
        shimmer: "shimmer 1.8s linear infinite",
        "spin-slow": "spin 6s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-14px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-700px 0" },
          "100%": { backgroundPosition: "700px 0" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
