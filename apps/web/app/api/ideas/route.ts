import { z } from "zod";

import { createIdea, listIdeas } from "@/lib/db/queries";
import { invalid, json, readJson } from "@/lib/http";
import { getFounderId, getOrCreateFounderId } from "@/lib/session";

const createIdeaSchema = z.object({
  one_liner: z.string().trim().min(1).max(500),
  target_customer: z.string().trim().max(200).nullish(),
});

export async function POST(request: Request) {
  const parsed = createIdeaSchema.safeParse(await readJson(request));
  if (!parsed.success) return invalid("Send {one_liner, target_customer?}.");
  const founderId = await getOrCreateFounderId();
  const idea = await createIdea(founderId, parsed.data.one_liner, parsed.data.target_customer ?? null);
  return json({ id: idea.id, one_liner: idea.oneLiner, target_customer: idea.targetCustomer, created_at: idea.createdAt }, 201);
}

export async function GET() {
  const founderId = await getFounderId();
  if (!founderId) return json({ ideas: [] });
  const ideas = await listIdeas(founderId);
  return json({
    ideas: ideas.map((i) => ({
      id: i.id,
      one_liner: i.oneLiner,
      target_customer: i.targetCustomer,
      interview_count: i.interviewCount,
      latest_verdict: i.latestVerdict,
      created_at: i.createdAt,
    })),
  });
}
