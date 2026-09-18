import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: { baseURL: process.env.BASE_URL || "http://127.0.0.1:8080" },
  retries: process.env.CI ? 2 : 0,
});

