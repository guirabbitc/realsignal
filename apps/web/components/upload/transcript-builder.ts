// Turns the voices the founder confirmed into the `Founder:` / `Customer:` transcript the analyzer reads.
// Every word stays as transcribed: only whitespace is normalized, and a turn never spans two lines, so each
// line starts with exactly one label.
import type { TranscribeTurn } from "@/lib/contracts";

type Role = "Founder" | "Customer";

export function buildTranscript(turns: readonly Pick<TranscribeTurn, "speaker_id" | "text">[], founderId: string): string {
  const lines: { role: Role; text: string }[] = [];
  for (const turn of turns) {
    const text = turn.text.replace(/\s+/g, " ").trim();
    if (!text) continue;
    // Every voice that is not the founder's is the customer side (a second customer, a colleague).
    const role: Role = turn.speaker_id === founderId ? "Founder" : "Customer";
    const last = lines.at(-1);
    if (last?.role === role) last.text = `${last.text} ${text}`;
    else lines.push({ role, text });
  }
  return lines.map(({ role, text }) => `${role}: ${text}\n`).join("");
}
