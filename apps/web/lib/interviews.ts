import { asc, desc, eq } from "drizzle-orm";
import { analyzeAudio, analyzeTranscript } from "./analyzer";
import { getDb, schema } from "./db";

const { analyses, founders, ideas, interviews, signals } = schema;

// No auth yet: every interview belongs to this one founder.
const DEFAULT_FOUNDER = { email: "founder@realsignal.local", name: "Founder" };

async function defaultFounderId(): Promise<string> {
  const db = getDb();
  await db.insert(founders).values(DEFAULT_FOUNDER).onConflictDoNothing();
  const [founder] = await db.select().from(founders).where(eq(founders.email, DEFAULT_FOUNDER.email));
  return founder.id;
}

export type NewInterview = {
  ideaTitle: string;
  ideaDescription: string;
  title: string;
  transcript?: string;
  audio?: File;
};

/** Saves the interview as `processing`, runs the analyzer, then saves the result as `done` or `failed`. */
export async function createAndAnalyze(input: NewInterview): Promise<string> {
  const db = getDb();
  const founderId = await defaultFounderId();
  const [idea] = await db
    .insert(ideas)
    .values({ founderId, title: input.ideaTitle, description: input.ideaDescription })
    .returning();
  const [interview] = await db
    .insert(interviews)
    .values({
      ideaId: idea.id,
      title: input.title,
      source: input.audio ? "audio" : "transcript",
      transcript: input.transcript ?? null,
      status: "processing",
    })
    .returning();

  const ideaText = `${input.ideaTitle}: ${input.ideaDescription}`;
  try {
    const result = input.audio
      ? await analyzeAudio(ideaText, input.audio)
      : await analyzeTranscript({ idea: ideaText, transcript: input.transcript! });

    await db.transaction(async (tx) => {
      if (result.sentences.length > 0) {
        await tx.insert(signals).values(
          result.sentences.map((s) => ({
            interviewId: interview.id,
            order: s.order,
            speaker: s.speaker,
            text: s.text,
            isInterviewee: s.is_interviewee,
            label: s.label,
            confidence: s.confidence,
          })),
        );
      }
      await tx.insert(analyses).values({
        interviewId: interview.id,
        score: result.score,
        verdict: result.verdict,
        summary: result.summary,
        nextSteps: result.next_steps,
        raw: result,
      });
      await tx
        .update(interviews)
        .set({ status: "done", transcript: result.transcript, updatedAt: new Date() })
        .where(eq(interviews.id, interview.id));
    });
  } catch (error) {
    await db
      .update(interviews)
      .set({ status: "failed", error: error instanceof Error ? error.message : String(error), updatedAt: new Date() })
      .where(eq(interviews.id, interview.id));
  }
  return interview.id;
}

export async function getInterview(id: string) {
  const db = getDb();
  const [row] = await db
    .select({ interview: interviews, idea: ideas })
    .from(interviews)
    .innerJoin(ideas, eq(interviews.ideaId, ideas.id))
    .where(eq(interviews.id, id));
  if (!row) return null;
  const sentences = await db.select().from(signals).where(eq(signals.interviewId, id)).orderBy(asc(signals.order));
  const [analysis] = await db.select().from(analyses).where(eq(analyses.interviewId, id));
  return { ...row, sentences, analysis: analysis ?? null };
}

export async function listInterviews() {
  const db = getDb();
  return db
    .select({
      id: interviews.id,
      title: interviews.title,
      status: interviews.status,
      createdAt: interviews.createdAt,
      ideaTitle: ideas.title,
      score: analyses.score,
      verdict: analyses.verdict,
    })
    .from(interviews)
    .innerJoin(ideas, eq(interviews.ideaId, ideas.id))
    .leftJoin(analyses, eq(analyses.interviewId, interviews.id))
    .orderBy(desc(interviews.createdAt))
    .limit(20);
}
