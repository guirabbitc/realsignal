// Rebuilds the AnalyzeResult shape from stored rows, so the API returns what the analyzer returned.
import type { AnalyzeResult } from "./contracts";
import type { getInterviewForFounder } from "./db/queries";

type Loaded = NonNullable<Awaited<ReturnType<typeof getInterviewForFounder>>>;

export function toResult({ interview, analysis, statements }: Loaded): AnalyzeResult | null {
  if (!analysis) return null;
  return {
    score: analysis.score,
    verdict: analysis.verdict,
    verdict_confidence: analysis.verdictConfidence,
    founder_talk_ratio: interview.founderTalkRatio,
    pitched_early: analysis.pitchedEarly,
    leading_questions: analysis.leadingQuestions,
    statements: statements.map((s) => ({
      position: s.position,
      speaker: "customer" as const,
      quote: s.quote,
      founder_question: s.founderQuestion,
      category: s.category,
      category_probs: s.categoryProbs,
      p_real: s.pReal,
      confidence: s.confidence,
    })),
    summary: analysis.summary,
    reasons: analysis.reasons,
    next_questions: analysis.nextQuestions as AnalyzeResult["next_questions"],
    missing_evidence: analysis.missingEvidence,
    model_versions: analysis.modelVersions as unknown as AnalyzeResult["model_versions"],
  };
}
