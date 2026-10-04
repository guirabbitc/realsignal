// "Try again" on a failed analysis: the saved transcript is analyzed again, nothing has to be re-entered.
// Runs against the local DB; the analyzer is mocked.
import { eq } from "drizzle-orm";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { AnalyzeResult } from "@/lib/contracts";
import { getDb } from "@/lib/db/client";
import { createFounder, createIdea, createInterview, getInterviewForFounder, markInterviewFailed } from "@/lib/db/queries";
import { interviews } from "@/lib/db/schema";
import { encodeSession } from "@/lib/session";

const state = vi.hoisted(() => ({ cookie: undefined as string | undefined, later: [] as (() => Promise<unknown>)[] }));

vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: (name: string) => (name === "vai_sid" && state.cookie ? { value: state.cookie } : undefined),
    set: () => undefined,
  }),
}));
vi.mock("next/server", async (original) => ({
  ...(await original<object>()),
  after: (task: () => Promise<unknown>) => state.later.push(task),
}));
vi.mock("@/lib/analyzer-client", async (original) => ({ ...(await original<object>()), analyze: vi.fn() }));

const { AnalyzerCallError, analyze } = await import("@/lib/analyzer-client");
const { POST: retryRoute } = await import("@/app/api/interviews/[id]/retry/route");
const { GET: interviewRoute } = await import("@/app/api/interviews/[id]/route");

const IDEA = "WhatsApp bot that takes restaurant reservations";
const TRANSCRIPT = "Founder: How do you handle reservations today?\nCustomer: I pay someone $300 a month to do it by hand.\n";
const RESULT: AnalyzeResult = {
  score: 80, verdict: "keep_going", verdict_confidence: 0.8, founder_talk_ratio: 0.3, pitched_early: 0.1,
  leading_questions: 0.1, statements: [], summary: "s", reasons: [], next_questions: ["a", "b", "c"],
  missing_evidence: null,
  model_versions: { jev: "j", openai: "o", rubric: "1", founder_flags: { talk_ratio: 0.5, pitched_early: 0.5, leading_questions: 0.5 } },
};

async function failedInterview() {
  const founderId = await createFounder();
  const idea = await createIdea(founderId, IDEA, null);
  const created = await createInterview(founderId, {
    ideaId: idea.id, transcript: TRANSCRIPT, kind: "interview", intervieweeLabel: "Maria", source: "audio",
  });
  await markInterviewFailed(founderId, created!.id, "openai_failed");
  state.cookie = encodeSession(founderId);
  return { founderId, interviewId: created!.id };
}

const params = (id: string) => ({ params: Promise.resolve({ id }) });
const retry = (id: string) => retryRoute(new Request(`http://localhost/api/interviews/${id}/retry`, { method: "POST" }), params(id));
const read = async (id: string) => (await interviewRoute(new Request(`http://localhost/api/interviews/${id}`), params(id))).json();
const runLater = () => Promise.all(state.later.splice(0).map((task) => task()));

afterEach(() => {
  state.cookie = undefined;
  state.later = [];
  vi.mocked(analyze).mockReset();
});

describe("a failed analysis keeps the interview", () => {
  it("shows the saved transcript only while the analysis is failed", async () => {
    const { interviewId } = await failedInterview();
    expect(await read(interviewId)).toMatchObject({ status: "failed", error: "openai_failed", transcript: TRANSCRIPT });

    vi.mocked(analyze).mockResolvedValue(RESULT);
    await retry(interviewId);
    expect((await read(interviewId)).transcript).toBeNull(); // processing
    await runLater();
    expect(await read(interviewId)).toMatchObject({ status: "done", transcript: null });
  });

  it("Try again analyzes the saved transcript, with the same idea, kind and label", async () => {
    const { founderId, interviewId } = await failedInterview();
    vi.mocked(analyze).mockResolvedValue(RESULT);
    const response = await retry(interviewId);
    expect(response.status).toBe(202);
    expect(await response.json()).toEqual({ id: interviewId, status: "processing" });
    await runLater();
    expect(vi.mocked(analyze).mock.calls[0][0]).toEqual({
      idea: IDEA, transcript: TRANSCRIPT, kind: "interview", interviewee_label: "Maria", audio_url: null,
    });
    const loaded = await getInterviewForFounder(founderId, interviewId);
    expect([loaded!.interview.status, loaded!.interview.source, loaded!.analysis!.verdict]).toEqual(["done", "audio", "keep_going"]);
  });

  it("an old interview is not marked timed-out the moment it is tried again", async () => {
    const { founderId, interviewId } = await failedInterview();
    await getDb().update(interviews).set({ createdAt: new Date(Date.now() - 60 * 60 * 1000) }).where(eq(interviews.id, interviewId));
    await retry(interviewId);
    expect((await getInterviewForFounder(founderId, interviewId))!.interview.status).toBe("processing");
  });

  it("failing again keeps the transcript, and it can be tried again", async () => {
    const { interviewId } = await failedInterview();
    vi.mocked(analyze).mockRejectedValueOnce(new AnalyzerCallError("openai_failed")).mockResolvedValueOnce(RESULT);
    await retry(interviewId);
    await runLater();
    expect(await read(interviewId)).toMatchObject({ status: "failed", error: "openai_failed", transcript: TRANSCRIPT });
    expect((await retry(interviewId)).status).toBe(202);
    await runLater();
    expect((await read(interviewId)).status).toBe("done");
  });

  it("only the owner can try again, and only a failed analysis", async () => {
    const { interviewId } = await failedInterview();
    state.cookie = encodeSession(await createFounder());
    expect((await retry(interviewId)).status).toBe(404);
    expect((await retry("not-a-uuid")).status).toBe(404);

    const founderId = await createFounder();
    const idea = await createIdea(founderId, IDEA, null);
    const processing = await createInterview(founderId, { ideaId: idea.id, transcript: TRANSCRIPT, kind: "interview", intervieweeLabel: null });
    state.cookie = encodeSession(founderId);
    const response = await retry(processing!.id);
    expect(response.status).toBe(409);
    expect((await response.json()).error.code).toBe("not_failed");
    expect(analyze).not.toHaveBeenCalled();
  });
});
