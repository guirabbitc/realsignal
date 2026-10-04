import { describe, expect, it } from "vitest";

import {
  countGroups,
  errorMessage,
  founderFlags,
  rebuildTranscript,
  splitRefs,
  topPolite,
  topReal,
} from "../components/read-out/view-model";
import type { AnalyzeResult, Category, Statement } from "../lib/contracts";

function st(position: number, category: Category, p_real: number, founder_question: string | null = null): Statement {
  return { position, speaker: "customer", quote: `q${position}`, founder_question, category, category_probs: {}, p_real, confidence: 0.9 };
}

function result(overrides: Partial<AnalyzeResult>): AnalyzeResult {
  return {
    score: 50,
    verdict: "narrow_down",
    verdict_confidence: 0.7,
    founder_talk_ratio: 0.3,
    pitched_early: 0.1,
    leading_questions: 0.1,
    statements: [],
    summary: "",
    reasons: [],
    next_questions: ["a", "b", "c"],
    missing_evidence: null,
    model_versions: {
      jev: "jev",
      openai: "gpt",
      rubric: "1",
      founder_flags: { talk_ratio: 0.5, pitched_early: 0.5, leading_questions: 0.5 },
    },
    ...overrides,
  };
}

describe("top quotes", () => {
  const statements = [
    st(2, "past_pain", 0.7),
    st(4, "commitment", 0.95),
    st(6, "neutral", 0.99),
    st(8, "compliment", 0.2),
    st(10, "hypothetical", 0.05),
    st(12, "past_pain", 0.8),
    st(14, "past_pain", 0.6),
    st(16, "compliment", 0.3),
    st(18, "hypothetical", 0.4),
  ];

  it("takes up to 3 real statements, highest p_real first, never neutral", () => {
    expect(topReal(statements).map((s) => s.position)).toEqual([4, 12, 2]);
  });

  it("takes up to 3 polite statements, lowest p_real first", () => {
    expect(topPolite(statements).map((s) => s.position)).toEqual([10, 8, 16]);
  });

  it("does not reorder the input", () => {
    expect(statements.map((s) => s.position)).toEqual([2, 4, 6, 8, 10, 12, 14, 16, 18]);
  });

  it("counts statements by group", () => {
    expect(countGroups(statements)).toEqual({ real: 4, polite: 4, neutral: 1 });
  });
});

describe("founder flags", () => {
  it("flags a value at or above its threshold from model_versions", () => {
    const flags = founderFlags(result({ founder_talk_ratio: 0.5, pitched_early: 0.49, leading_questions: 0.9 }));
    expect(flags.map((f) => [f.key, f.flagged])).toEqual([
      ["talk_ratio", true],
      ["pitched_early", false],
      ["leading_questions", true],
    ]);
  });

  it("never flags a value the analyzer did not measure", () => {
    const [talk] = founderFlags(result({ founder_talk_ratio: null }));
    expect(talk).toMatchObject({ value: null, flagged: false });
  });
});

describe("rebuildTranscript", () => {
  it("puts the founder turn back wherever positions skip, and groups one customer turn", () => {
    const turns = rebuildTranscript([st(5, "neutral", 0.1, "Second?"), st(2, "past_pain", 0.9, "First?"), st(3, "neutral", 0.2, "First?")]);
    expect(turns.map((t) => (t.speaker === "founder" ? `F:${t.text}` : `C:${t.statements.map((s) => s.position)}`))).toEqual([
      "F:First?",
      "C:2,3",
      "F:Second?",
      "C:5",
    ]);
  });

  it("starts with the customer when nobody asked a question first", () => {
    const turns = rebuildTranscript([st(1, "neutral", 0.1, null)]);
    expect(turns).toHaveLength(1);
    expect(turns[0].speaker).toBe("customer");
  });
});

describe("splitRefs", () => {
  it("links known positions and keeps the text identical", () => {
    const text = "They lost money [#3] and asked for the pilot [#9]. See [#99].";
    const parts = splitRefs(text, new Set([3, 9]));
    expect(parts.map((p) => p.text).join("")).toBe(text);
    expect(parts.filter((p) => "ref" in p).map((p) => ("ref" in p ? p.ref : 0))).toEqual([3, 9]);
  });
});

describe("errorMessage", () => {
  it("explains known codes and falls back for unknown ones", () => {
    expect(errorMessage("timeout")).toMatch(/too long/);
    expect(errorMessage("something_new")).toMatch(/on our side/);
    expect(errorMessage(null)).toMatch(/on our side/);
  });
});
