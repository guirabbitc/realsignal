// POST /api/transcribe checks (flag, ownership, consent, size, type) and `source` on POST /api/interviews.
// Runs against the local DB; the analyzer is mocked (the real round trip is the opt-in E2E).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TranscribeResult } from "@/lib/contracts";
import { createFounder, createIdea, getInterviewForFounder } from "@/lib/db/queries";
import { encodeSession, SESSION_COOKIE } from "@/lib/session";

const state = vi.hoisted(() => ({ cookie: undefined as string | undefined }));

vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: (name: string) => (name === "vai_sid" && state.cookie ? { value: state.cookie } : undefined),
    set: () => undefined,
  }),
}));
vi.mock("next/server", async (original) => ({ ...(await original<object>()), after: () => undefined }));
vi.mock("@/lib/analyzer-client", async (original) => ({
  ...(await original<object>()),
  transcribe: vi.fn(),
  analyze: vi.fn(),
}));

const { AnalyzerCallError, transcribe } = await import("@/lib/analyzer-client");
const { POST: transcribeRoute } = await import("@/app/api/transcribe/route");
const { POST: interviewsRoute } = await import("@/app/api/interviews/route");

const RECORDINGS = resolve(__dirname, "../../../services/analyzer/tests/recordings/audio");
const EXAMPLE: TranscribeResult = JSON.parse(readFileSync(resolve(RECORDINGS, "example.transcribe.json"), "utf8"));

function audio(bytes = 2048, name = "call.m4a", type = "audio/mp4"): File {
  return new File([new Uint8Array(bytes)], name, { type });
}

function upload(fields: Record<string, string | File | undefined>): Request {
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) if (value !== undefined) form.set(key, value);
  return new Request("http://localhost/api/transcribe", { method: "POST", body: form });
}

async function signedInFounderWithIdea() {
  const founderId = await createFounder();
  const idea = await createIdea(founderId, "WhatsApp bot that takes restaurant reservations", null);
  state.cookie = encodeSession(founderId);
  return { founderId, ideaId: idea.id };
}

beforeEach(() => {
  expect(SESSION_COOKIE).toBe("vai_sid");
  vi.stubEnv("AUDIO_INPUT_ENABLED", "true");
  vi.stubEnv("AUDIO_MAX_MB", "1");
  vi.mocked(transcribe).mockReset().mockResolvedValue(EXAMPLE);
});

afterEach(() => {
  vi.unstubAllEnvs();
  state.cookie = undefined;
});

describe("POST /api/transcribe", () => {
  it("is a 404 when the flag is off, even for a valid request", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    vi.stubEnv("AUDIO_INPUT_ENABLED", "false");
    const response = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio() }));
    expect(response.status).toBe(404);
    expect(transcribe).not.toHaveBeenCalled();
  });

  it("is a 404 without a session or for another founder's idea", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    state.cookie = undefined;
    expect((await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio() }))).status).toBe(404);
    state.cookie = encodeSession(await createFounder());
    expect((await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio() }))).status).toBe(404);
    expect(transcribe).not.toHaveBeenCalled();
  });

  it.each([undefined, "false", "on"])("rejects consent=%s with 400", async (consent) => {
    const { ideaId } = await signedInFounderWithIdea();
    const response = await transcribeRoute(upload({ idea_id: ideaId, consent, file: audio() }));
    expect(response.status).toBe(400);
    expect((await response.json()).error.code).toBe("consent_required");
    expect(transcribe).not.toHaveBeenCalled();
  });

  it("rejects audio over AUDIO_MAX_MB with 413", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    const response = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio(1024 * 1024 + 1) }));
    expect(response.status).toBe(413);
    expect((await response.json()).error.code).toBe("audio_too_large");
    expect(transcribe).not.toHaveBeenCalled();
  });

  it("rejects an empty file, a non-audio file and a bad speaker count", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    const empty = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio(0) }));
    expect([empty.status, (await empty.json()).error.code]).toEqual([422, "empty_audio"]);
    const text = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio(10, "notes.txt", "text/plain") }));
    expect(text.status).toBe(422);
    const five = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", num_speakers: "5", file: audio() }));
    expect(five.status).toBe(422);
    expect(transcribe).not.toHaveBeenCalled();
  });

  it("passes the voices and turns through, after a heartbeat byte, and stores nothing", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    const file = audio(4096, "recording.webm", "audio/webm;codecs=opus");
    const response = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", num_speakers: "3", file }));
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toContain("no-transform");
    const body = await response.text();
    expect(body.startsWith(" ")).toBe(true);
    expect(JSON.parse(body)).toEqual(EXAMPLE);
    const [sent, extension, speakers] = vi.mocked(transcribe).mock.calls[0];
    expect([sent.size, extension, speakers]).toEqual([4096, ".webm", 3]);
  });

  it("reports an analyzer failure in-band, by code, never as a transcript", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    vi.mocked(transcribe).mockRejectedValue(new AnalyzerCallError("transcription_failed", "timeout"));
    const response = await transcribeRoute(upload({ idea_id: ideaId, consent: "true", file: audio() }));
    expect(JSON.parse(await response.text())).toEqual({
      error: { code: "transcription_failed", message: "Transcription failed.", reason: "timeout" },
    });
  });
});

describe("POST /api/interviews source", () => {
  function create(body: object): Request {
    return new Request("http://localhost/api/interviews", { method: "POST", body: JSON.stringify(body) });
  }

  it("saves source = audio when sent, and text by default", async () => {
    const { founderId, ideaId } = await signedInFounderWithIdea();
    const transcript = readFileSync(resolve(RECORDINGS, "example.transcript.txt"), "utf8");
    const fromAudio = await interviewsRoute(create({ idea_id: ideaId, transcript, kind: "interview", source: "audio" }));
    const fromText = await interviewsRoute(create({ idea_id: ideaId, transcript, kind: "interview" }));
    expect([fromAudio.status, fromText.status]).toEqual([202, 202]);
    const audioRow = await getInterviewForFounder(founderId, (await fromAudio.json()).id);
    const textRow = await getInterviewForFounder(founderId, (await fromText.json()).id);
    expect([audioRow!.interview.source, textRow!.interview.source]).toEqual(["audio", "text"]);
  });

  it("rejects any other source", async () => {
    const { ideaId } = await signedInFounderWithIdea();
    const response = await interviewsRoute(create({ idea_id: ideaId, transcript: "Customer: hi.", kind: "interview", source: "video" }));
    expect(response.status).toBe(422);
  });
});
