import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { buildTranscript } from "../components/upload/transcript-builder";
import type { TranscribeResult } from "../lib/contracts";

// The same files the analyzer's pytest uses: one recording, one expected transcript, checked on both sides.
const RECORDINGS = resolve(__dirname, "../../../services/analyzer/tests/recordings/audio");
const example: TranscribeResult = JSON.parse(readFileSync(resolve(RECORDINGS, "example.transcribe.json"), "utf8"));
const expected = readFileSync(resolve(RECORDINGS, "example.transcript.txt"), "utf8");

const turn = (speaker_id: string, text: string) => ({ speaker_id, text });

describe("buildTranscript", () => {
  it("matches the transcript the analyzer test parses, with the suggested founder voice", () => {
    expect(buildTranscript(example.turns, example.suggested_founder_id)).toBe(expected);
  });

  it("labels two voices, with the founder as speaker_1", () => {
    expect(buildTranscript([turn("speaker_0", "Hi."), turn("speaker_1", "What happened?")], "speaker_1")).toBe(
      "Customer: Hi.\nFounder: What happened?\n",
    );
  });

  it("makes every other voice the customer side when there are three", () => {
    const turns = [turn("speaker_0", "How do you do it today?"), turn("speaker_1", "Spreadsheets."), turn("speaker_2", "And email.")];
    expect(buildTranscript(turns, "speaker_0")).toBe("Founder: How do you do it today?\nCustomer: Spreadsheets. And email.\n");
  });

  it("merges consecutive turns that get the same role", () => {
    const turns = [turn("a", "One."), turn("a", "Two."), turn("b", "Three."), turn("c", "Four."), turn("a", "Five.")];
    expect(buildTranscript(turns, "a")).toBe("Founder: One. Two.\nCustomer: Three. Four.\nFounder: Five.\n");
  });

  it("normalizes whitespace and never breaks a turn across lines, keeping every word", () => {
    const turns = [turn("a", "  So\nwhat\tdid it  cost?  "), turn("b", "Customer: $1,200/mo — maybe.\r\n")];
    expect(buildTranscript(turns, "a")).toBe("Founder: So what did it cost?\nCustomer: Customer: $1,200/mo — maybe.\n");
  });

  it("is empty when nothing was said, and founder-only when only the founder's voice was heard", () => {
    expect(buildTranscript([turn("a", "   ")], "a")).toBe("");
    expect(buildTranscript([turn("a", "Hello?")], "a")).toBe("Founder: Hello?\n");
  });
});
