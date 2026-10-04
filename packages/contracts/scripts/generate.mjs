// Generates the TypeScript types and Pydantic models from analyze.schema.json.
// With --check, generates into a temp folder and fails if the committed files differ.
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compileFromFile } from "json-schema-to-typescript";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const schema = join(root, "packages/contracts/analyze.schema.json");
const targets = {
  ts: join(root, "apps/web/lib/contracts/analyze.ts"),
  py: join(root, "services/analyzer/app/contracts.py"),
};
const banner =
  "GENERATED from packages/contracts/analyze.schema.json. Do not edit: run `pnpm contracts:generate`.";

async function generateTs(out) {
  const ts = await compileFromFile(schema, {
    bannerComment: `// ${banner}`,
    unreachableDefinitions: true,
    additionalProperties: false,
  });
  writeFileSync(out, ts);
}

function generatePy(out) {
  execFileSync(
    "uv",
    [
      "run", "--quiet", "--project", join(root, "services/analyzer"),
      "datamodel-codegen",
      "--input", schema,
      "--input-file-type", "jsonschema",
      "--output", out,
      "--output-model-type", "pydantic_v2.BaseModel",
      "--target-python-version", "3.12",
      "--use-standard-collections",
      "--use-union-operator",
      "--disable-timestamp",
      "--formatters", "builtin",
      "--custom-file-header", `# ${banner}`,
    ],
    { stdio: "inherit" },
  );
}

const check = process.argv.includes("--check");
const dir = check ? mkdtempSync(join(tmpdir(), "contracts-")) : null;
const out = check
  ? { ts: join(dir, "analyze.ts"), py: join(dir, "contracts.py") }
  : targets;

await generateTs(out.ts);
generatePy(out.py);

if (check) {
  const drifted = Object.keys(targets).filter(
    (k) => readFileSync(out[k], "utf8") !== readFileSync(targets[k], "utf8"),
  );
  if (drifted.length) {
    for (const k of drifted) console.error(`DRIFT: ${relative(root, targets[k])} does not match the schema`);
    console.error("Run `pnpm contracts:generate` and commit the result.");
    process.exit(1);
  }
  console.log("Contracts match the schema.");
} else {
  console.log("Generated:", Object.values(targets).map((t) => relative(root, t)).join(", "));
}
