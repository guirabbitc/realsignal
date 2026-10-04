// Pure helpers for the idea history page. Scores and verdicts are shown as the API returned them.
import type { IdeaInterviewRow } from "@/components/api";

export type ReadOutRow = IdeaInterviewRow & { verdict: NonNullable<IdeaInterviewRow["verdict"]> };

/** Finished interviews, oldest first (the API lists newest first). */
export function readOuts(rows: IdeaInterviewRow[]): ReadOutRow[] {
  return rows.filter((r): r is ReadOutRow => r.status === "done" && r.verdict !== null).reverse();
}

export function trendCaption(done: ReadOutRow[]): string {
  const scored = done.filter((r) => r.score !== null);
  if (scored.length >= 2) {
    return `From ${scored[0].score} to ${scored[scored.length - 1].score} over ${done.length} read-outs`;
  }
  if (done.length === 1) return "One read-out so far";
  if (done.length > 1) return `${done.length} read-outs`;
  return "No read-outs yet";
}

const MIN_BAR_PX = 44;

/** Bar height in px: 1.5 px per point, never shorter than the diamond it holds. */
export function barHeight(score: number | null): number {
  return Math.max(MIN_BAR_PX, Math.round((score ?? 0) * 1.5));
}

/** "Maria, restaurant owner" → "Maria". */
export function shortName(label: string | null): string {
  const name = label?.split(",")[0].trim();
  return name || "Untitled";
}

/** Processing rows older than this are stale: the API marks them failed when the interview is read. */
export const STALE_PROCESSING_MS = 5 * 60_000;
