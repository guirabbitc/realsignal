// An idea and its interview history (MISSION Gate 3 step 9).
import { getIdeaWithInterviews } from "@/lib/db/queries";
import { json, notFound, uuidSchema } from "@/lib/http";
import { getFounderId } from "@/lib/session";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const founderId = await getFounderId();
  if (!founderId || !uuidSchema.safeParse(id).success) return notFound();
  const found = await getIdeaWithInterviews(founderId, id);
  if (!found) return notFound();
  return json({
    id: found.idea.id,
    one_liner: found.idea.oneLiner,
    target_customer: found.idea.targetCustomer,
    interviews: found.interviews.map((i) => ({
      id: i.id,
      kind: i.kind,
      interviewee_label: i.intervieweeLabel,
      status: i.status,
      score: i.score,
      verdict: i.verdict,
      created_at: i.createdAt,
    })),
  });
}
