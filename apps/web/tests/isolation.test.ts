// MISSION invariant 1: a founder only ever sees their own ideas and interviews. Runs against the local DB.
import { randomUUID } from "node:crypto";
import { describe, expect, it } from "vitest";

import type { AnalyzeResult } from "@/lib/contracts";
import {
  createFounder, createIdea, createInterview, getIdeaWithInterviews, getInterviewForFounder, listIdeas,
  markInterviewFailed, saveAnalysis,
} from "@/lib/db/queries";

const result: AnalyzeResult = {
  score: 80, verdict: "keep_going", verdict_confidence: 0.8, founder_talk_ratio: 0.3, pitched_early: 0.1,
  leading_questions: 0.1, statements: [], summary: "s", reasons: [], next_questions: ["a", "b", "c"],
  missing_evidence: null,
  model_versions: { jev: "j", openai: "o", rubric: "1", founder_flags: { talk_ratio: 0.5, pitched_early: 0.5, leading_questions: 0.5 } },
};

async function setup() {
  const a = await createFounder();
  const b = await createFounder();
  const idea = await createIdea(a, `idea ${randomUUID()}`, null);
  const interview = await createInterview(a, { ideaId: idea.id, transcript: "Customer: hi.", kind: "interview", intervieweeLabel: null });
  return { a, b, idea, interviewId: interview!.id };
}

describe("founder isolation", () => {
  it("another founder cannot list, read or attach to an idea", async () => {
    const { b, idea } = await setup();
    expect((await listIdeas(b)).map((i) => i.id)).not.toContain(idea.id);
    expect(await getIdeaWithInterviews(b, idea.id)).toBeNull();
    expect(await createInterview(b, { ideaId: idea.id, transcript: "x", kind: "interview", intervieweeLabel: null })).toBeNull();
  });

  it("another founder cannot read an interview", async () => {
    const { b, interviewId } = await setup();
    expect(await getInterviewForFounder(b, interviewId)).toBeNull();
  });

  it("an analysis can never be saved under another founder's interview", async () => {
    const { a, b, interviewId } = await setup();
    expect(await saveAnalysis(b, interviewId, result)).toBe(false);
    await markInterviewFailed(b, interviewId, "x");
    expect((await getInterviewForFounder(a, interviewId))!.interview.status).toBe("processing");
    expect(await saveAnalysis(a, interviewId, result)).toBe(true);
    expect((await getInterviewForFounder(a, interviewId))!.analysis!.verdict).toBe("keep_going");
  });

  it("two founders submitting at once do not cross", async () => {
    const [one, two] = await Promise.all([setup(), setup()]);
    await Promise.all([saveAnalysis(one.a, one.interviewId, result), saveAnalysis(two.a, two.interviewId, { ...result, verdict: "pivot" })]);
    expect((await getInterviewForFounder(one.a, one.interviewId))!.analysis!.verdict).toBe("keep_going");
    expect((await getInterviewForFounder(two.a, two.interviewId))!.analysis!.verdict).toBe("pivot");
    expect(await getInterviewForFounder(one.a, two.interviewId)).toBeNull();
  });
});
