import nextVitals from "eslint-config-next/core-web-vitals";

const config = [
  {
    ignores: [".next/**", ".next-pre16-cache-*/**", "node_modules/**"],
  },
  ...nextVitals,
];

export default config;
