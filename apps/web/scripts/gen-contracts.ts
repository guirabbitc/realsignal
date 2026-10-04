// Generates the TS types in lib/ from the JSON schemas in packages/contracts.
// The JSON schemas are the single source of truth (SPEC §4 rule 3). Run: pnpm contracts:gen
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { compile } from "json-schema-to-typescript";

const CONTRACTS = resolve(__dirname, "../../../packages/contracts");

export const TARGETS = [
  { schema: "analyze.schema.json", name: "AnalyzeContract", out: resolve(__dirname, "../lib/contracts.generated.ts") },
  { schema: "transcribe.schema.json", name: "TranscribeContract", out: resolve(__dirname, "../lib/transcribe.generated.ts") },
] as const;

export type Target = (typeof TARGETS)[number];

export async function generate(target: Target): Promise<string> {
  const schema = JSON.parse(readFileSync(resolve(CONTRACTS, target.schema), "utf8"));
  return compile(schema, target.name, {
    unreachableDefinitions: true,
    additionalProperties: false,
    bannerComment: `/* Generated from packages/contracts/${target.schema}. Do not edit; run \`pnpm contracts:gen\`. */`,
    format: false,
  });
}

if (require.main === module) {
  Promise.all(TARGETS.map(async (target) => writeFileSync(target.out, await generate(target))));
}
