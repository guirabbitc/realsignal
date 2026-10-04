import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, type Page } from "@playwright/test";

import type { AnalyzeResult, TranscribeResult } from "../lib/contracts";

export const FIXTURES = resolve(__dirname, "../../../services/analyzer/fixtures");
export const RECORDINGS = resolve(__dirname, "../../../services/analyzer/tests/recordings/audio");
export const IDEA = "WhatsApp bot that takes restaurant reservations";
export const audioEnabled = (process.env.AUDIO_INPUT_ENABLED ?? "true") === "true";

export function recordedTranscription(): TranscribeResult {
  return JSON.parse(readFileSync(resolve(RECORDINGS, "example.transcribe.json"), "utf8"));
}

/** A new founder (fresh cookie in this context) with one idea; returns the idea id. */
export async function createIdea(page: Page): Promise<string> {
  const response = await page.request.post("/api/ideas", { data: { one_liner: IDEA } });
  expect(response.status()).toBe(201);
  return (await response.json()).id;
}

/** Answers /api/transcribe in the browser: a body, a held request (never answers), or an in-band error. */
export async function mockTranscribe(page: Page, answer: TranscribeResult | "hold" | { error: { code: string; reason?: string } }) {
  await page.route("**/api/transcribe", async (route) => {
    if (answer === "hold") return; // left pending: the page stays in its transcribing state
    await route.fulfill({ status: 200, contentType: "application/json", body: ` ${JSON.stringify(answer)}` });
  });
}

export const FAILED_ID = "6f1c2a9e-0b7d-4c41-9a53-2f8e1d7c4b10";
export const FAILED_TRANSCRIPT =
  "Founder: How do you handle reservations today?\nCustomer: I pay someone $300 a month to do it by hand.\n";

/** An interview whose analysis failed (openai_failed); "Try again" moves it to processing. Counts retries. */
export async function mockFailedInterview(page: Page, ideaId: string) {
  const calls = { retry: 0 };
  let status: "failed" | "processing" = "failed";
  await page.route(`**/api/interviews/${FAILED_ID}`, (route) =>
    route.fulfill({
      json:
        status === "failed"
          ? { id: FAILED_ID, idea_id: ideaId, status, error: "openai_failed", result: null, transcript: FAILED_TRANSCRIPT }
          : { id: FAILED_ID, idea_id: ideaId, status, error: null, result: null, transcript: null },
    }),
  );
  await page.route(`**/api/interviews/${FAILED_ID}/retry`, (route) => {
    calls.retry += 1;
    status = "processing";
    return route.fulfill({ status: 202, json: { id: FAILED_ID, status } });
  });
  return calls;
}

/** Polls the API until the analysis finishes; returns the result. */
export async function waitForResult(page: Page, interviewId: string): Promise<AnalyzeResult> {
  let body: { status: string; error: string | null; result: AnalyzeResult | null } | null = null;
  await expect
    .poll(
      async () => {
        body = await (await page.request.get(`/api/interviews/${interviewId}`)).json();
        return body?.status;
      },
      { timeout: 170_000, intervals: [2_000] },
    )
    .not.toBe("processing");
  expect(body!.error, "analysis failed").toBeNull();
  return body!.result!;
}

/** Every statement quote and every quoted span of 3+ words in the writer text is in the transcript. */
export function expectVerbatim(result: AnalyzeResult, transcript: string) {
  for (const statement of result.statements) expect(transcript).toContain(statement.quote);
  const normalized = transcript.replace(/\s+/g, " ");
  for (const text of [result.summary, ...result.reasons]) {
    for (const [, span] of text.matchAll(/[“"]([^”"]+)[”"]/g)) {
      if (span.trim().split(/\s+/).length >= 3) expect(normalized).toContain(span.replace(/\s+/g, " ").trim());
    }
  }
}

export async function submitAndOpenReadOut(page: Page): Promise<string> {
  await page.getByRole("button", { name: "Check my interview" }).click();
  await page.waitForURL(/\/interviews\/[0-9a-f-]{36}$/);
  return page.url().split("/").pop()!;
}
