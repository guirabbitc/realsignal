// Generates lib/contracts.generated.ts from packages/contracts/analyze.schema.json.
// The JSON schema is the single source of truth (SPEC §4 rule 3). Run: pnpm contracts:gen
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { compile } from "json-schema-to-typescript";

export const SCHEMA_PATH = resolve(__dirname, "../../../packages/contracts/analyze.schema.json");
export const OUT_PATH = resolve(__dirname, "../lib/contracts.generated.ts");

export async function generate(): Promise<string> {
  const schema = JSON.parse(readFileSync(SCHEMA_PATH, "utf8"));
  return compile(schema, "AnalyzeContract", {
    unreachableDefinitions: true,
    additionalProperties: false,
    bannerComment: "/* Generated from packages/contracts/analyze.schema.json. Do not edit; run `pnpm contracts:gen`. */",
    format: false,
  });
}

if (require.main === module) {
  generate().then((ts) => writeFileSync(OUT_PATH, ts));
}
