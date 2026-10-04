import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import type { IdeaInterviewRow } from "../components/api";
import { barHeight, readOuts, shortName, trendCaption } from "../components/ideas/history";
import { hasSpeakerLabels } from "../components/upload/checks";
import { EXAMPLES } from "../lib/examples";

const FIXTURES = resolve(__dirname, "../../../services/analyzer/fixtures");

describe("examples", () => {
  it("are the polite, mixed and real_pain reference fixtures, copied verbatim", () => {
    expect(EXAMPLES.map((e) => e.key)).toEqual(["polite", "mixed", "real_pain"]);
    for (const example of EXAMPLES) {
      expect(example.transcript).toBe(readFileSync(resolve(FIXTURES, `${example.key}.txt`), "utf8"));
    }
  });
});

describe("hasSpeakerLabels", () => {
  it("accepts Founder:/Customer: lines in any case, with leading spaces", () => {
    expect(hasSpeakerLabels("Founder: hi\nCustomer: hello")).toBe(true);
    expect(hasSpeakerLabels("intro line\n  customer: only the customer")).toBe(true);
  });

  it("rejects transcripts the analyzer would call unlabelled", () => {
    expect(hasSpeakerLabels("YOU: hi\nPAT: hello")).toBe(false);
    expect(hasSpeakerLabels("We talked about Founder: things")).toBe(false);
  });
});

function row(id: string, overrides: Partial<IdeaInterviewRow>): IdeaInterviewRow {
  return { id, kind: "interview", interviewee_label: null, status: "done", score: 50, verdict: "narrow_down", created_at: "2026-10-04T10:00:00Z", ...overrides };
}

describe("idea history", () => {
  // The API lists newest first.
  const rows = [
    row("d", { status: "processing", score: null, verdict: null }),
    row("c", { score: 82, verdict: "keep_going" }),
    row("b", { status: "failed", score: null, verdict: null }),
    row("a", { score: 31, verdict: "new_angle" }),
  ];

  it("keeps finished read-outs only, oldest first", () => {
    expect(readOuts(rows).map((r) => r.id)).toEqual(["a", "c"]);
  });

  it("describes the trend with the API's scores", () => {
    expect(trendCaption(readOuts(rows))).toBe("From 31 to 82 over 2 read-outs");
    expect(trendCaption(readOuts([row("x", {})]))).toBe("One read-out so far");
    expect(trendCaption([])).toBe("No read-outs yet");
  });

  it("never draws a bar shorter than its diamond", () => {
    expect(barHeight(null)).toBe(44);
    expect(barHeight(10)).toBe(44);
    expect(barHeight(100)).toBe(150);
  });

  it("uses the name before the comma", () => {
    expect(shortName("Maria, restaurant owner")).toBe("Maria");
    expect(shortName(null)).toBe("Untitled");
  });
});
