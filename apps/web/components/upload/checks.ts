// Mirrors the analyzer's input rules (SPEC §5 step 2) so the founder hears about them before submitting.
// The analyzer reads only `Founder:` (the person interviewing) and `Customer:` (the person interviewed);
// real transcripts often say `Interviewer:`, `YOU:` or a name, so the form maps those labels first.

export const MAX_TRANSCRIPT_CHARS = 80_000;

export type Role = "founder" | "customer" | "ignore";

export interface Speaker {
  /** Lower-case label, used as the key. */
  key: string;
  /** The label as first written. */
  label: string;
  lines: number;
}

// "Name:" or "First Last:" at the start of a line, up to 3 words, followed by a space or the line end
// (so "http://" and "10:30" are not speakers).
const LABEL_LINE = /^([ \t]*)([A-Za-z][\w.'’&-]*(?: [\w.'’&-]+){0,2}):(?=\s|$)/;

export function detectSpeakers(transcript: string): Speaker[] {
  const found = new Map<string, Speaker>();
  for (const line of transcript.split(/\r?\n/)) {
    const label = line.match(LABEL_LINE)?.[2];
    if (!label) continue;
    const key = label.toLowerCase();
    const seen = found.get(key);
    if (seen) seen.lines += 1;
    else found.set(key, { key, label, lines: 1 });
  }
  return [...found.values()];
}

const STANDARD = new Set(["founder", "customer"]);
const INTERVIEWER = new Set(["interviewer", "you", "me", "i", "q", "host"]);
const INTERVIEWEE = new Set(["customer", "interviewee", "client", "user", "a", "guest", "prospect"]);

/** True when the labels are not just Founder:/Customer:, or nobody is labelled Customer:. */
export function needsMapping(speakers: Speaker[]): boolean {
  return speakers.some((s) => !STANDARD.has(s.key)) || !speakers.some((s) => s.key === "customer");
}

/**
 * A first guess the founder confirms. "Founder:" is the interviewer unless another label already is
 * (an interviewee who is a founder). Unknown names: the first to speak is the interviewer.
 */
export function guessRoles(speakers: Speaker[]): Record<string, Role> {
  const roles: Record<string, Role> = {};
  const hasInterviewerWord = speakers.some((s) => INTERVIEWER.has(s.key));
  for (const s of speakers) {
    if (INTERVIEWEE.has(s.key)) roles[s.key] = "customer";
    else if (INTERVIEWER.has(s.key)) roles[s.key] = "founder";
    else if (s.key === "founder") roles[s.key] = hasInterviewerWord ? "customer" : "founder";
  }
  let founderTaken = Object.values(roles).includes("founder");
  for (const s of speakers) {
    if (roles[s.key]) continue;
    roles[s.key] = founderTaken ? "customer" : "founder";
    founderTaken = true;
  }
  return roles;
}

/** Rewrites only the speaker labels; everything after each colon is kept byte for byte. */
export function relabel(transcript: string, roles: Record<string, Role>): string {
  return transcript
    .split("\n")
    .map((line) =>
      line.replace(LABEL_LINE, (whole, indent: string, label: string) => {
        const role = roles[label.toLowerCase()];
        if (role === "founder") return `${indent}Founder:`;
        if (role === "customer") return `${indent}Customer:`;
        return whole;
      }),
    )
    .join("\n");
}
