// GENERATED from packages/contracts/analyze.schema.json. Do not edit: run `pnpm contracts:generate`.

/**
 * How one interviewee sentence reads as evidence of demand.
 *
 * This interface was referenced by `AnalyzeContract`'s JSON-Schema
 * via the `definition` "Label".
 */
export type Label = "real_signal" | "polite" | "neutral";
/**
 * What the founder should do after this interview.
 *
 * This interface was referenced by `AnalyzeContract`'s JSON-Schema
 * via the `definition` "Verdict".
 */
export type Verdict = "keep_going" | "narrow_down" | "try_new_angle" | "pivot";

/**
 * The analyzer's request and response. The single source of truth: TypeScript types and Pydantic models are generated from this file.
 */
export interface AnalyzeContract {
  request: AnalyzeRequest;
  response: AnalyzeResponse;
}
/**
 * JSON body of POST /analyze. For audio, send multipart/form-data instead with the fields `idea` and `file`.
 *
 * This interface was referenced by `AnalyzeContract`'s JSON-Schema
 * via the `definition` "AnalyzeRequest".
 */
export interface AnalyzeRequest {
  /**
   * The idea this interview tests.
   */
  idea: string;
  /**
   * Interview text, one `Speaker: words` turn per line.
   */
  transcript: string;
}
/**
 * This interface was referenced by `AnalyzeContract`'s JSON-Schema
 * via the `definition` "AnalyzeResponse".
 */
export interface AnalyzeResponse {
  /**
   * The transcript that was analyzed (produced by transcription when audio was sent).
   */
  transcript: string;
  sentences: Sentence[];
  /**
   * Demand score, computed in Python.
   */
  score: number;
  verdict: Verdict;
  summary: string;
  next_steps: string[];
}
/**
 * This interface was referenced by `AnalyzeContract`'s JSON-Schema
 * via the `definition` "Sentence".
 */
export interface Sentence {
  /**
   * Position in the transcript, starting at 0.
   */
  order: number;
  speaker: string;
  text: string;
  is_interviewee: boolean;
  /**
   * Null for interviewer sentences, which are not judged.
   */
  label: Label | null;
  /**
   * Confidence in the label, 0 to 1. Null when label is null.
   */
  confidence: number | null;
}
