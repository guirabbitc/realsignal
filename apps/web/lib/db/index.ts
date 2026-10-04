import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const globalForDb = globalThis as unknown as { pg?: ReturnType<typeof postgres> };

function client() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL is not set");
  // Reuse one connection pool across hot reloads in dev.
  globalForDb.pg ??= postgres(url);
  return globalForDb.pg;
}

export function getDb() {
  return drizzle(client(), { schema });
}

export { schema };
