// Mirrors the analyzer's input rules (SPEC §5 step 2) so the founder hears about them before submitting.
// The API and the analyzer still enforce them; these only save a round trip.

export const MAX_TRANSCRIPT_CHARS = 80_000;

/** True when at least one line starts with `Founder:` or `Customer:` (any case, optional leading spaces). */
export function hasSpeakerLabels(transcript: string): boolean {
  return /^[ \t]*(founder|customer):/im.test(transcript);
}
