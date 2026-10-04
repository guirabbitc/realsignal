/* Generated from packages/contracts/analyze.schema.json. Do not edit; run `pnpm contracts:gen`. */

/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "Kind".
 */
export type Kind = ("interview" | "demo")
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "Category".
 */
export type Category = ("commitment" | "past_pain" | "hypothetical" | "compliment" | "neutral")
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "Verdict".
 */
export type Verdict = ("keep_going" | "narrow_down" | "new_angle" | "pivot" | "need_more_evidence")
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "Probability".
 */
export type Probability = number

/**
 * Request and response of POST /analyze. Single source of truth (SPEC §4 rule 3, §6).
 */
export interface ValidateAiAnalyzerContract {
[k: string]: unknown
}
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "AnalyzeRequest".
 */
export interface AnalyzeRequest {
idea: string
transcript: string
kind: Kind
interviewee_label?: (string | null)
audio_url?: null
}
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "Statement".
 */
export interface Statement {
position: number
speaker: "customer"
quote: string
founder_question: (string | null)
category: Category
category_probs: {
[k: string]: Probability
}
p_real: Probability
confidence: Probability
}
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "AnalyzeResult".
 */
export interface AnalyzeResult {
score: (number | null)
verdict: Verdict
verdict_confidence: (number | null)
founder_talk_ratio: (number | null)
pitched_early: (number | null)
leading_questions: (number | null)
statements: Statement[]
summary: string
reasons: string[]
/**
 * @minItems 3
 * @maxItems 3
 */
next_questions: [string, string, string]
missing_evidence: (string | null)
model_versions: {
jev: string
openai: string
rubric: string
founder_flags: {
talk_ratio: Probability
pitched_early: Probability
leading_questions: Probability
}
}
}
/**
 * This interface was referenced by `ValidateAiAnalyzerContract`'s JSON-Schema
 * via the `definition` "ErrorResponse".
 */
export interface ErrorResponse {
error: {
code: ("bad_key" | "unlabelled_transcript" | "transcript_too_long" | "invalid_request" | "jev_failed" | "openai_failed" | "writer_unverifiable" | "timeout")
message: string
}
}
