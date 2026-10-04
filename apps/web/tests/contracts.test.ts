import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

import { generate, OUT_PATH } from "../scripts/gen-contracts";

it("generated contract types are current with analyze.schema.json (run `pnpm contracts:gen`)", async () => {
  expect(readFileSync(OUT_PATH, "utf8")).toBe(await generate());
});
