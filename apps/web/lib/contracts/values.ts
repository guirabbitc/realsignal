// Label and verdict values, read from the contract so they are defined in one place.
import schema from "@realsignal/contracts/analyze.schema.json";
import type { Label, Verdict } from "./analyze";

export const LABELS = schema.$defs.Label.enum as [Label, ...Label[]];
export const VERDICTS = schema.$defs.Verdict.enum as [Verdict, ...Verdict[]];
