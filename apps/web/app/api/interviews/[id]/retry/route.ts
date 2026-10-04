// Analyzes a failed interview again from the transcript we saved, so an outage (OpenAI, Jev, the analyzer)
// never costs the founder their interview: no pasting or recording it again.
import { after } from "next/server";

import { getInterviewForFounder, restartFailedInterview } from "@/lib/db/queries";
import { json, notFound, uuidSchema } from "@/lib/http";
import { runAnalysis } from "@/lib/run-analysis";
import { getFounderId } from "@/lib/session";

export const maxDuration = 300;

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const founderId = await getFounderId();
  if (!founderId || !uuidSchema.safeParse(id).success) return notFound();

  const restarted = await restartFailedInterview(founderId, id);
  if (!restarted) {
    if (!(await getInterviewForFounder(founderId, id))) return notFound();
    return json({ error: { code: "not_failed", message: "Only a failed analysis can be tried again." } }, 409);
  }

  after(() =>
    runAnalysis(founderId, restarted.id, {
      idea: restarted.ideaOneLiner,
      transcript: restarted.transcript,
      kind: restarted.kind,
      interviewee_label: restarted.intervieweeLabel,
      audio_url: null,
    }),
  );
  return json({ id: restarted.id, status: "processing" }, 202);
}
