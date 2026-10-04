// Record with Chromium's fake microphone. The transcription is the recorded response unless E2E_REAL=1 (then
// E2E_FAKE_AUDIO must point at a real two-voice .wav, and ElevenLabs is called for real).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

import { audioEnabled, createIdea, mockTranscribe, RECORDINGS, recordedTranscription } from "./helpers";

const real = process.env.E2E_REAL === "1";

test.skip(!audioEnabled, "Audio input is off (AUDIO_INPUT_ENABLED).");
test.skip(real && !process.env.E2E_FAKE_AUDIO, "E2E_REAL=1 needs E2E_FAKE_AUDIO: a .wav of two people talking.");

test("record → stop → use it → confirm the voice → the transcript lands in the box", async ({ page }) => {
  // Keep every stream the page opens, to prove Stop turns the microphone off.
  await page.addInitScript(() => {
    const opened: MediaStream[] = [];
    (window as unknown as { __streams: MediaStream[] }).__streams = opened;
    const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = async (constraints) => {
      const stream = await original(constraints);
      opened.push(stream);
      return stream;
    };
  });
  if (!real) await mockTranscribe(page, recordedTranscription());

  const ideaId = await createIdea(page);
  await page.goto(`/ideas/${ideaId}/upload`);
  await page.getByRole("button", { name: "Record", exact: true }).click();

  const start = page.getByRole("button", { name: "Start recording" });
  await expect(start).toBeDisabled();
  await page.getByLabel(/knows this conversation is being recorded/).check();
  await start.click();
  await expect(page.getByText("Recording", { exact: true })).toBeVisible();
  // With E2E_REAL=1, record the whole fake-mic file (E2E_RECORD_SECONDS) so both voices are heard.
  await page.waitForTimeout(Number(process.env.E2E_RECORD_SECONDS ?? 3) * 1000);
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.locator("audio")).toBeVisible();
  const live = await page.evaluate(() =>
    (window as unknown as { __streams: MediaStream[] }).__streams.flatMap((s) => s.getTracks()).filter((t) => t.readyState === "live").length,
  );
  expect(live, "microphone tracks still live after Stop").toBe(0);

  const [request] = await Promise.all([
    page.waitForRequest("**/api/transcribe"),
    page.getByRole("button", { name: "Use this recording" }).click(),
  ]);
  // Playwright keeps the body only of requests it intercepts, so the fields are checked in the mocked run.
  if (!real) {
    const sent = request.postDataBuffer()!.toString("latin1");
    expect(sent).toContain(`name="idea_id"\r\n\r\n${ideaId}`);
    expect(sent).toContain('name="consent"\r\n\r\ntrue');
    expect(sent).toContain('name="num_speakers"\r\n\r\n2');
    expect(sent).toMatch(/filename="recording\.(webm|m4a)"/);
  }

  await expect(page.getByText("Which voice is you?")).toBeVisible({ timeout: real ? 290_000 : 15_000 });
  await expect(page.getByRole("group", { name: /Which voice is you/ }).getByRole("radio")).toHaveCount(2);
  if (real) return; // the rest checks the recorded response's exact text

  // The guess is the voice asking the questions (it speaks second here), not simply the first voice.
  await expect(page.getByRole("radio", { name: "Voice 2 is me" })).toBeChecked();
  await page.getByRole("radio", { name: "Voice 1 is me" }).check();
  await expect(page.getByText("This is me")).toHaveCount(1);
  await page.getByRole("radio", { name: "Voice 2 is me" }).check();
  await page.getByRole("button", { name: "Use this transcript" }).click();

  const expected = readFileSync(resolve(RECORDINGS, "example.transcript.txt"), "utf8");
  await expect(page.getByRole("textbox", { name: "Transcript" })).toHaveValue(expected);
  await expect(page.getByText("Transcript from your audio.")).toBeVisible();
});
