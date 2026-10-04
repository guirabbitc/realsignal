import path from "node:path";
import { config } from "dotenv";
import { defineConfig } from "drizzle-kit";

config({ path: path.resolve(process.cwd(), "../../.env") });

export default defineConfig({
  dialect: "postgresql",
  schema: "./lib/db/schema.ts",
  out: "./lib/db/migrations",
  dbCredentials: { url: process.env.DATABASE_URL! },
});
