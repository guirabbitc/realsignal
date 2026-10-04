// Pure helpers for the read-out page. They group, sort and label what the API returned; they never
// compute a score or a verdict (MISSION invariant 4).
import type { AnalyzeResult, Category, Statement, Verdict } from "@/lib/contracts";

export type InterviewStatus = "processing" | "done" | "failed";

/** GET /api/interviews/:id */
export interface InterviewResponse {
  id: string;
  idea_id: string;
  status: InterviewStatus;
  error: string | null;
  result: AnalyzeResult | null;
}

export type Group = "real" | "polite" | "neutral";

// Category groups are fixed by SPEC §5; weights stay in rubric.json and are not repeated here.
const GROUP: Record<Category, Group> = {
  commitment: "real",
  past_pain: "real",
  hypothetical: "polite",
  compliment: "polite",
  neutral: "neutral",
};

export function groupOf(category: Category): Group {
  return GROUP[category];
}

export const VERDICT_LABEL: Record<Verdict, string> = {
  keep_going: "Keep going",
  narrow_down: "Narrow down",
  new_angle: "Try a new angle",
  pivot: "Pivot",
  need_more_evidence: "Not enough evidence yet",
};

export type StoneKind = "real" | "polite" | "unsure";

export const VERDICT_STONE: Record<Verdict, StoneKind> = {
  keep_going: "real",
  narrow_down: "real",
  new_angle: "real",
  pivot: "polite",
  need_more_evidence: "unsure",
};

export const CATEGORY_LABEL: Record<Category, string> = {
  commitment: "Real · commitment",
  past_pain: "Real · past pain",
  hypothetical: "Polite · hypothetical",
  compliment: "Polite · compliment",
  neutral: "Small talk",
};

const byPosition = (a: Statement, b: Statement) => a.position - b.position;

/** Up to 3 statements in the real group, highest p_real first (SPEC §5). */
export function topReal(statements: Statement[]): Statement[] {
  return statements
    .filter((s) => groupOf(s.category) === "real")
    .sort((a, b) => b.p_real - a.p_real || byPosition(a, b))
    .slice(0, 3);
}

/** Up to 3 statements in the polite group, lowest p_real first (SPEC §5). */
export function topPolite(statements: Statement[]): Statement[] {
  return statements
    .filter((s) => groupOf(s.category) === "polite")
    .sort((a, b) => a.p_real - b.p_real || byPosition(a, b))
    .slice(0, 3);
}

export function countGroups(statements: Statement[]): Record<Group, number> {
  const counts: Record<Group, number> = { real: 0, polite: 0, neutral: 0 };
  for (const s of statements) counts[groupOf(s.category)] += 1;
  return counts;
}

export type FlagKey = "talk_ratio" | "pitched_early" | "leading_questions";

export interface FounderFlag {
  key: FlagKey;
  value: number | null;
  threshold: number;
  /** Shown as a mistake when the value is at or above its threshold (SPEC §5). */
  flagged: boolean;
}

export function founderFlags(result: AnalyzeResult): FounderFlag[] {
  const thresholds = result.model_versions.founder_flags;
  const values: Record<FlagKey, number | null> = {
    talk_ratio: result.founder_talk_ratio,
    pitched_early: result.pitched_early,
    leading_questions: result.leading_questions,
  };
  return (Object.keys(values) as FlagKey[]).map((key) => {
    const value = values[key];
    const threshold = thresholds[key];
    return { key, value, threshold, flagged: value !== null && value >= threshold };
  });
}

export type TranscriptTurn =
  | { speaker: "founder"; text: string; key: string }
  | { speaker: "customer"; statements: Statement[]; key: string };

/**
 * The API returns customer sentences only, each with the founder turn just before it. A gap in
 * `position` means founder sentences sat in between, so that is where the founder turn goes back in.
 * Founder lines that no customer sentence answered are not in the API response and cannot be shown.
 */
export function rebuildTranscript(statements: Statement[]): TranscriptTurn[] {
  const turns: TranscriptTurn[] = [];
  let previous: Statement | null = null;
  for (const s of [...statements].sort(byPosition)) {
    const startsTurn = previous === null || s.position > previous.position + 1;
    const current = turns[turns.length - 1];
    if (!startsTurn && current?.speaker === "customer") {
      current.statements.push(s);
    } else {
      if (s.founder_question) turns.push({ speaker: "founder", text: s.founder_question, key: `f${s.position}` });
      turns.push({ speaker: "customer", statements: [s], key: `c${s.position}` });
    }
    previous = s;
  }
  return turns;
}

export type TextPart = { text: string } | { ref: number; text: string };

/** Splits writer text on `[#12]` references so they can link to that transcript line. Text is unchanged. */
export function splitRefs(text: string, positions: Set<number>): TextPart[] {
  const parts: TextPart[] = [];
  let last = 0;
  for (const match of text.matchAll(/\[#(\d+)\]/g)) {
    const ref = Number(match[1]);
    if (!positions.has(ref)) continue;
    if (match.index > last) parts.push({ text: text.slice(last, match.index) });
    parts.push({ ref, text: match[0] });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last) });
  return parts;
}

// interviews.error stores a code, never the upstream message (CLAUDE.md), so the words live here.
const ERROR_COPY: Record<string, string> = {
  unlabelled_transcript:
    "We couldn’t tell who said what. Start each line with “Founder:” or “Customer:” and add the interview again.",
  transcript_too_long: "The transcript is over 80,000 characters. Split it into parts and add each one.",
  invalid_request: "The analyzer couldn’t read this request. Add the interview again.",
  jev_failed: "The model that judges each sentence didn’t answer. Your transcript is fine. Try again in a minute.",
  openai_failed: "The model that writes the read-out didn’t answer. Your transcript is fine. Try again in a minute.",
  writer_unverifiable:
    "The read-out quoted words that aren’t in your transcript, so we threw it away instead of showing you a made-up quote. Try again.",
  timeout: "The analysis took too long and was stopped. Try again.",
  bad_key: "Our servers couldn’t talk to each other. This one is on us.",
};

export function errorMessage(code: string | null): string {
  return (code && ERROR_COPY[code]) || "Something broke on our side. Try again.";
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
