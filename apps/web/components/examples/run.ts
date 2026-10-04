"use client";

import { apiGet, apiPost, type IdeaSummary } from "@/components/api";
import { EXAMPLE_IDEAS, type Example } from "@/lib/examples";

/**
 * Runs an example under its own example idea, so its verdict does not depend on the founder's ideas:
 * reuses the idea if this browser already has it, creates it otherwise. Returns the new interview id.
 */
export async function runExample(example: Example): Promise<string> {
  const oneLiner = EXAMPLE_IDEAS[example.idea];
  const { ideas } = await apiGet<{ ideas: IdeaSummary[] }>("/api/ideas");
  const ideaId = ideas.find((i) => i.one_liner === oneLiner)?.id ?? (await apiPost<{ id: string }>("/api/ideas", { one_liner: oneLiner })).id;
  const created = await apiPost<{ id: string }>("/api/interviews", {
    idea_id: ideaId,
    transcript: example.transcript,
    kind: example.kind,
    interviewee_label: example.intervieweeLabel,
  });
  return created.id;
}
