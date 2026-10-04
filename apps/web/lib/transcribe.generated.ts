/* Generated from packages/contracts/transcribe.schema.json. Do not edit; run `pnpm contracts:gen`. */

/**
 * Response of POST /transcribe. Request is multipart/form-data: file (required), num_speakers (optional integer 1-4, default 2). Speakers and turns only: no roles. The founder picks their own voice in the web app.
 */
export interface ValidateAiAnalyzerTranscriptionContract {
[k: string]: unknown
}
/**
 * This interface was referenced by `ValidateAiAnalyzerTranscriptionContract`'s JSON-Schema
 * via the `definition` "TranscribeTurn".
 */
export interface TranscribeTurn {
speaker_id: string
text: string
start: (number | null)
end: (number | null)
}
/**
 * This interface was referenced by `ValidateAiAnalyzerTranscriptionContract`'s JSON-Schema
 * via the `definition` "TranscribeSpeaker".
 */
export interface TranscribeSpeaker {
id: string
turns: number
words: number
seconds: number
/**
 * @minItems 1
 * @maxItems 2
 */
sample: [string]|[string, string]
}
/**
 * This interface was referenced by `ValidateAiAnalyzerTranscriptionContract`'s JSON-Schema
 * via the `definition` "TranscribeResult".
 */
export interface TranscribeResult {
duration_s: (number | null)
language_code: (string | null)
model: string
/**
 * @minItems 1
 */
speakers: [TranscribeSpeaker, ...(TranscribeSpeaker)[]]
/**
 * @minItems 1
 */
turns: [TranscribeTurn, ...(TranscribeTurn)[]]
suggested_founder_id: string
}
/**
 * This interface was referenced by `ValidateAiAnalyzerTranscriptionContract`'s JSON-Schema
 * via the `definition` "TranscribeErrorResponse".
 */
export interface TranscribeErrorResponse {
error: {
code: ("bad_key" | "invalid_request" | "audio_too_large" | "empty_audio" | "no_speech" | "transcription_failed" | "transcription_not_configured")
message: string
reason?: ("rate_limited" | "upstream_error" | "timeout" | "rejected" | null)
}
}
