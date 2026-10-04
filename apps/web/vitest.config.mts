import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { environment: "node", setupFiles: ["./tests/setup.ts"], include: ["tests/**/*.test.ts"] },
  resolve: { alias: { "@": resolve(__dirname, ".") } },
});
