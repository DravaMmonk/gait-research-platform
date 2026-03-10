import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13212d",
        mist: "#edf4f7",
        ember: "#d95d39",
        moss: "#5a7d4d",
      },
    },
  },
  plugins: [],
};

export default config;
