// The text path must behave the same with the audio flag on and off. Uses the real analyzer (Jev + OpenAI).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

import { audioEnabled, createIdea, expectVerbatim, FIXTURES, submitAndOpenReadOut, waitForResult } from "./helpers";

test("paste real_pain → keep_going above 70, verbatim receipts, 3 next questions", async ({ page }) => {
  const health = await (await page.request.get("/api/health")).json();
  test.skip(health.analyzer !== "ok", "The analyzer at ANALYZER_URL is not up; this journey uses real Jev and OpenAI.");

  const ideaId = await createIdea(page);
  await page.goto(`/ideas/${ideaId}/upload`);
  const modes = page.getByRole("group", { name: /How to add the/ }).getByRole("button");
  await expect(modes).toHaveText(audioEnabled ? ["Paste text", "Upload .txt", "Record", "Upload audio"] : ["Paste text", "Upload .txt"]);

  const transcript = readFileSync(resolve(FIXTURES, "real_pain.txt"), "utf8");
  await page.getByRole("textbox", { name: "Transcript" }).fill(transcript);
  await page.getByLabel("The interviewee knew this conversation was recorded").check();
  const interviewId = await submitAndOpenReadOut(page);
  const result = await waitForResult(page, interviewId);

  expect(result.verdict).toBe("keep_going");
  expect(result.score).toBeGreaterThan(70);
  expect(result.next_questions).toHaveLength(3);
  expectVerbatim(result, transcript);
  await expect(page.getByText("Keep going").first()).toBeVisible();
});

test("POST /api/transcribe exists only when the flag is on", async ({ page }) => {
  const ideaId = await createIdea(page);
  const response = await page.request.post("/api/transcribe", {
    multipart: { idea_id: ideaId, consent: "true", file: { name: "a.m4a", mimeType: "audio/mp4", buffer: Buffer.from("x") } },
  });
  // With the flag on, the outcome (here: whatever the analyzer says) comes back in-band with a 200.
  expect(response.status()).toBe(audioEnabled ? 200 : 404);
});
