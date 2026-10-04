// Saves the interview, answers 202 at once, and runs the analysis after the response (SPEC §0.6).
import { after } from "next/server";
import { z } from "zod";

import { createInterview } from "@/lib/db/queries";
import { invalid, json, notFound, readJson } from "@/lib/http";
import { runAnalysis } from "@/lib/run-analysis";
import { getFounderId } from "@/lib/session";

export const maxDuration = 300;

const MAX_TRANSCRIPT_CHARS = 80_000;

const createInterviewSchema = z.object({
  idea_id: z.uuid(),
  transcript: z.string().min(1).max(MAX_TRANSCRIPT_CHARS),
  kind: z.enum(["interview", "demo"]),
  interviewee_label: z.string().trim().max(200).nullish(),
  // "audio": the founder confirmed a transcript built from a recording. The analysis is the same either way.
  source: z.enum(["text", "audio"]).default("text"),
});

export async function POST(request: Request) {
  const parsed = createInterviewSchema.safeParse(await readJson(request));
  if (!parsed.success) {
    return invalid(`Send {idea_id, transcript (max ${MAX_TRANSCRIPT_CHARS} chars), kind, interviewee_label?, source?}.`);
  }
  const founderId = await getFounderId();
  if (!founderId) return notFound();

  const { idea_id, transcript, kind, interviewee_label, source } = parsed.data;
  const created = await createInterview(founderId, {
    ideaId: idea_id,
    transcript,
    kind,
    intervieweeLabel: interviewee_label ?? null,
    source,
  });
  if (!created) return notFound();

  // The transcript is saved before this runs, so a failed analysis can always be tried again from it.
  after(() =>
    runAnalysis(founderId, created.id, {
      idea: created.idea.oneLiner,
      transcript,
      kind,
      interviewee_label: interviewee_label ?? null,
      audio_url: null,
    }),
  );

  return json({ id: created.id, status: created.status }, 202);
}
