import { getInterviewForFounder } from "@/lib/db/queries";
import { json, notFound, uuidSchema } from "@/lib/http";
import { toResult } from "@/lib/interview-result";
import { getFounderId } from "@/lib/session";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const founderId = await getFounderId();
  if (!founderId || !uuidSchema.safeParse(id).success) return notFound();
  const loaded = await getInterviewForFounder(founderId, id);
  if (!loaded) return notFound();
  return json({
    id: loaded.interview.id,
    idea_id: loaded.interview.ideaId,
    status: loaded.interview.status,
    error: loaded.interview.error,
    result: toResult(loaded),
    // Only after a failure: the founder sees their words are safe and can copy them or try again.
    transcript: loaded.interview.status === "failed" ? loaded.interview.transcript : null,
  });
}
