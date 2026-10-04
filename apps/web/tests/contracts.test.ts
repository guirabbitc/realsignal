import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

import { generate, TARGETS } from "../scripts/gen-contracts";

it.each(TARGETS)("generated types are current with $schema (run `pnpm contracts:gen`)", async (target) => {
  expect(readFileSync(target.out, "utf8")).toBe(await generate(target));
});
