// Production migrations (Railway pre-deploy). Uses drizzle-orm's migrator, a runtime dependency,
// because drizzle-kit is a dev dependency. Forward-only (SPEC §10).
import { fileURLToPath } from "node:url";
import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";
import pg from "pg";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
await migrate(drizzle(pool), { migrationsFolder: fileURLToPath(new URL("../lib/db/migrations", import.meta.url)) });
await pool.end();
console.log("migrations applied");
