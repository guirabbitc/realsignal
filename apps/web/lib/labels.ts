import type { Label, Verdict } from "./contracts/analyze";

export const LABEL_TEXT: Record<Label, string> = {
  real_signal: "Real signal",
  polite: "Polite",
  neutral: "Neutral",
};

export const VERDICT_TEXT: Record<Verdict, string> = {
  keep_going: "Keep going",
  narrow_down: "Narrow down",
  try_new_angle: "Try a new angle",
  pivot: "Pivot",
};
