import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import type { IdeaInterviewRow } from "../components/api";
import { barHeight, readOuts, shortName, trendCaption } from "../components/ideas/history";
import { detectSpeakers, guessRoles, needsMapping, relabel } from "../components/upload/checks";
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

describe("speaker labels", () => {
  const interviewerAndFounder = [
    "Mock interview",
    "Interviewer: How do you use your data today?",
    "",
    "Founder: Stripe, HubSpot and a few spreadsheets: it works.",
    "Interviewer: Would you pay for it?",
    "Founder: Probably, yes.",
  ].join("\n");

  it("finds each label once, with its line count, ignoring titles, URLs and times", () => {
    expect(detectSpeakers(interviewerAndFounder)).toEqual([
      { key: "interviewer", label: "Interviewer", lines: 2 },
      { key: "founder", label: "Founder", lines: 2 },
    ]);
    expect(detectSpeakers("See https://example.com\n10:30 we started\nno labels here")).toEqual([]);
  });

  it("leaves the standard Founder:/Customer: format alone", () => {
    for (const example of EXAMPLES) expect(needsMapping(detectSpeakers(example.transcript))).toBe(false);
  });

  it("asks who is who when an interviewee is labelled Founder:", () => {
    const speakers = detectSpeakers(interviewerAndFounder);
    expect(needsMapping(speakers)).toBe(true);
    expect(guessRoles(speakers)).toEqual({ interviewer: "founder", founder: "customer" });
  });

  it("guesses YOU as the founder and an unknown name as the customer", () => {
    expect(guessRoles(detectSpeakers("YOU: hi\nPAT: hello"))).toEqual({ you: "founder", pat: "customer" });
    expect(guessRoles(detectSpeakers("Gui: hi\nPeter Smith: hello"))).toEqual({ gui: "founder", "peter smith": "customer" });
  });

  it("asks when nobody is labelled Customer:", () => {
    expect(needsMapping(detectSpeakers("Founder: hi\nFounder: anyone?"))).toBe(true);
  });

  it("rewrites only the labels, keeping every word after the colon", () => {
    const out = relabel(interviewerAndFounder, { interviewer: "founder", founder: "customer" });
    expect(out).toBe(
      [
        "Mock interview",
        "Founder: How do you use your data today?",
        "",
        "Customer: Stripe, HubSpot and a few spreadsheets: it works.",
        "Founder: Would you pay for it?",
        "Customer: Probably, yes.",
      ].join("\n"),
    );
    expect(relabel("Note: aside\r\nPAT: hi", { note: "ignore", pat: "customer" })).toBe("Note: aside\r\nCustomer: hi");
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
