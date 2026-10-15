import type { Config } from "tailwindcss";

// Tokens from design.md §3 — light theme, 60:30:10 (cream/white · green · bordo)
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cream: { 50: "#FDF6EE", 100: "#FAE9D6", 200: "#F5DABF", 300: "#E8C39C", 400: "#D4A574" },
        green: { 50: "#ECF4F3", 100: "#CFE3E1", 500: "#2F7F78", 600: "#17524E", 700: "#0F3D3A", 900: "#092A28" },
        bordo: { 50: "#FBEFEF", 100: "#F3D6D8", 500: "#9A2A36", 700: "#6C151E", 900: "#4F0F16" },
        ink: { DEFAULT: "#092A28", muted: "#4B5F5D", placeholder: "#5F7270" },
        success: { DEFAULT: "#2F855A", bg: "#E6F4EC" },
        warning: { DEFAULT: "#B7791F", bg: "#FDF1DC" },
        danger: { DEFAULT: "#C62828", bg: "#FDECEC" },
        rank: { gold: "#C9A227", silver: "#9CA3AF", bronze: "#A8672D" },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        heading: ["Poppins", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        sm: "0 1px 2px rgba(9,42,40,.06)",
        md: "0 6px 16px rgba(9,42,40,.10)",
        xl: "0 20px 40px rgba(9,42,40,.18)",
      },
    },
  },
  plugins: [],
};
export default config;
