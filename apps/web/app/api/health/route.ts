// APP_STARTED proof: one call shows web, database and analyzer are all up (SPEC §13, interview R2.3b).
import { sql } from "drizzle-orm";

import { analyzerHealthy } from "@/lib/analyzer-client";
import { getDb } from "@/lib/db/client";

async function dbHealthy(): Promise<boolean> {
  try {
    await getDb().execute(sql`select 1`);
    return true;
  } catch {
    return false;
  }
}

export async function GET() {
  const [db, analyzer] = await Promise.all([dbHealthy(), analyzerHealthy()]);
  const ok = db && analyzer;
  return Response.json(
    { status: ok ? "ok" : "error", db: db ? "ok" : "error", analyzer: analyzer ? "ok" : "error" },
    { status: ok ? 200 : 503 },
  );
}
