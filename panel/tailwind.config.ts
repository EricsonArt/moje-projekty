import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0a",
        card: "#141414",
        border: "#262626",
        accent: "#10b981",
        accent2: "#f59e0b",
      },
    },
  },
  plugins: [],
};
export default config;
