import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme base colors
        background: {
          DEFAULT: "#0f172a", // deep blue-black
          surface: "#1e293b", // slate
          elevated: "#334155", // lighter slate
        },
        border: {
          DEFAULT: "#334155",
          light: "#475569",
        },
        text: {
          DEFAULT: "#e2e8f0", // off-white
          muted: "#94a3b8", // gray
        },
        accent: {
          DEFAULT: "#6366f1", // purple-blue
          light: "#818cf8",
          dark: "#4f46e5",
        },
        // System colors
        system: {
          agriculture: "#22c55e",
          health: "#ec4899",
          religion: "#fbbf24",
          territory: "#8b5cf6",
          chemistry: "#06b6d4",
          energy: "#f97316",
          materials: "#78716c",
          economy: "#eab308",
          life: "#f43f5e",
          fun: "#a78bfa",
        },
      },
      backgroundImage: {
        "glass-gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)",
      },
      backdropBlur: {
        glass: "20px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 3s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
