// ALL SQL lives here (CLAUDE.md). Every read is scoped by founderId (MISSION invariant 1):
// a resource owned by another founder is indistinguishable from one that does not exist.
import { and, desc, eq, inArray, lt, sql } from "drizzle-orm";

import type { AnalyzeResult } from "../contracts";
import { getDb } from "./client";
import { analyses, founders, ideas, interviews, statements } from "./schema";

const STALE_PROCESSING_MS = 5 * 60 * 1000;

export async function createFounder(): Promise<string> {
  const [row] = await getDb().insert(founders).values({}).returning({ id: founders.id });
  return row.id;
}

export async function founderExists(founderId: string): Promise<boolean> {
  const rows = await getDb().select({ id: founders.id }).from(founders).where(eq(founders.id, founderId)).limit(1);
  return rows.length > 0;
}

export async function createIdea(founderId: string, oneLiner: string, targetCustomer: string | null) {
  const [row] = await getDb().insert(ideas).values({ founderId, oneLiner, targetCustomer }).returning();
  return row;
}

export async function listIdeas(founderId: string) {
  const db = getDb();
  const rows = await db.select().from(ideas).where(eq(ideas.founderId, founderId)).orderBy(desc(ideas.createdAt));
  if (rows.length === 0) return [];
  const counts = await db
    .select({ ideaId: interviews.ideaId, count: sql<number>`count(*)::int` })
    .from(interviews)
    .where(inArray(interviews.ideaId, rows.map((r) => r.id)))
    .groupBy(interviews.ideaId);
  const latest = await db
    .selectDistinctOn([interviews.ideaId], { ideaId: interviews.ideaId, verdict: analyses.verdict })
    .from(interviews)
    .innerJoin(analyses, eq(analyses.interviewId, interviews.id))
    .where(inArray(interviews.ideaId, rows.map((r) => r.id)))
    .orderBy(interviews.ideaId, desc(interviews.createdAt));
  return rows.map((r) => ({
    ...r,
    interviewCount: counts.find((c) => c.ideaId === r.id)?.count ?? 0,
    latestVerdict: latest.find((l) => l.ideaId === r.id)?.verdict ?? null,
  }));
}

export async function getIdeaWithInterviews(founderId: string, ideaId: string) {
  const db = getDb();
  const [idea] = await db.select().from(ideas).where(and(eq(ideas.id, ideaId), eq(ideas.founderId, founderId)));
  if (!idea) return null;
  const history = await db
    .select({
      id: interviews.id,
      kind: interviews.kind,
      intervieweeLabel: interviews.intervieweeLabel,
      status: interviews.status,
      createdAt: interviews.createdAt,
      score: analyses.score,
      verdict: analyses.verdict,
    })
    .from(interviews)
    .leftJoin(analyses, eq(analyses.interviewId, interviews.id))
    .where(eq(interviews.ideaId, idea.id))
    .orderBy(desc(interviews.createdAt));
  return { idea, interviews: history };
}

export async function founderOwnsIdea(founderId: string, ideaId: string): Promise<boolean> {
  const rows = await getDb()
    .select({ id: ideas.id })
    .from(ideas)
    .where(and(eq(ideas.id, ideaId), eq(ideas.founderId, founderId)))
    .limit(1);
  return rows.length > 0;
}

/** Returns null when the idea does not belong to this founder. */
export async function createInterview(
  founderId: string,
  input: {
    ideaId: string;
    transcript: string;
    kind: "interview" | "demo";
    intervieweeLabel: string | null;
    source?: "text" | "audio";
  },
) {
  const db = getDb();
  const [idea] = await db
    .select({ id: ideas.id, oneLiner: ideas.oneLiner })
    .from(ideas)
    .where(and(eq(ideas.id, input.ideaId), eq(ideas.founderId, founderId)));
  if (!idea) return null;
  const [row] = await db
    .insert(interviews)
    .values({
      ideaId: idea.id,
      transcript: input.transcript,
      kind: input.kind,
      intervieweeLabel: input.intervieweeLabel,
      source: input.source ?? "text",
    })
    .returning({ id: interviews.id, status: interviews.status });
  return { ...row, idea };
}

/** Subquery: interview ids owned by this founder. Writes go through it so a result can never land under
 *  another founder's interview (the defect FACTORY.md ranks as most harmful). */
function ownedInterview(founderId: string, interviewId: string) {
  return and(
    eq(interviews.id, interviewId),
    inArray(interviews.ideaId, getDb().select({ id: ideas.id }).from(ideas).where(eq(ideas.founderId, founderId))),
  );
}

export async function saveAnalysis(founderId: string, interviewId: string, result: AnalyzeResult): Promise<boolean> {
  return getDb().transaction(async (tx) => {
    const updated = await tx
      .update(interviews)
      .set({ status: "done", error: null, founderTalkRatio: result.founder_talk_ratio })
      .where(and(ownedInterview(founderId, interviewId), eq(interviews.status, "processing")))
      .returning({ id: interviews.id });
    if (updated.length === 0) return false;
    if (result.statements.length > 0) {
      await tx.insert(statements).values(
        result.statements.map((s) => ({
          interviewId,
          position: s.position,
          quote: s.quote,
          founderQuestion: s.founder_question,
          category: s.category,
          categoryProbs: s.category_probs,
          pReal: s.p_real,
          confidence: s.confidence,
        })),
      );
    }
    await tx.insert(analyses).values({
      interviewId,
      score: result.score,
      verdict: result.verdict,
      verdictConfidence: result.verdict_confidence,
      pitchedEarly: result.pitched_early,
      leadingQuestions: result.leading_questions,
      summary: result.summary,
      reasons: result.reasons,
      nextQuestions: result.next_questions,
      missingEvidence: result.missing_evidence,
      modelVersions: result.model_versions as unknown as Record<string, unknown>,
    });
    return true;
  });
}

export async function markInterviewFailed(founderId: string, interviewId: string, code: string): Promise<void> {
  await getDb()
    .update(interviews)
    .set({ status: "failed", error: code })
    .where(and(ownedInterview(founderId, interviewId), eq(interviews.status, "processing")));
}

export async function getInterviewForFounder(founderId: string, interviewId: string) {
  const db = getDb();
  // A processing row older than 5 minutes is marked failed on read (SPEC §6).
  await db
    .update(interviews)
    .set({ status: "failed", error: "timeout" })
    .where(and(
      ownedInterview(founderId, interviewId),
      eq(interviews.status, "processing"),
      lt(interviews.createdAt, new Date(Date.now() - STALE_PROCESSING_MS)),
    ));
  const [interview] = await db.select().from(interviews).where(ownedInterview(founderId, interviewId));
  if (!interview) return null;
  if (interview.status !== "done") return { interview, analysis: null, statements: [] };
  const [analysis] = await db.select().from(analyses).where(eq(analyses.interviewId, interview.id));
  const rows = await db
    .select()
    .from(statements)
    .where(eq(statements.interviewId, interview.id))
    .orderBy(statements.position);
  return { interview, analysis: analysis ?? null, statements: rows };
}
