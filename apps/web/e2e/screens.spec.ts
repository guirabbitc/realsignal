// Screenshots of every audio state for review (E2E_SCREENS=1). Transcription is mocked; nothing is judged here.
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";

import { audioEnabled, createIdea, mockTranscribe, recordedTranscription } from "./helpers";

const OUT = resolve(__dirname, "../../../docs/features/audio-input/screens");

test.skip(process.env.E2E_SCREENS !== "1", "Screenshots only: run with E2E_SCREENS=1.");
test.skip(!audioEnabled, "Audio input is off (AUDIO_INPUT_ENABLED).");

async function openRecord(page: Page, consent = true) {
  const ideaId = await createIdea(page);
  await page.goto(`/ideas/${ideaId}/upload`);
  await page.getByRole("button", { name: "Record", exact: true }).click();
  if (consent) await page.getByLabel(/knows this conversation is being recorded/).check();
}

async function recordAndStop(page: Page) {
  await page.getByRole("button", { name: "Start recording" }).click();
  await expect(page.getByText("Recording", { exact: true })).toBeVisible();
  await page.waitForTimeout(2_000);
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.locator("audio")).toBeVisible();
}

for (const width of [1440, 390]) {
  test.describe(`${width}px`, () => {
    test.use({ viewport: { width, height: width > 600 ? 1000 : 844 } });
    const shot = async (page: Page, state: string) => {
      // From the top, so sticky headers sit where a person sees them.
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: resolve(OUT, `${state}-${width}.png`), fullPage: true });
    };

    test("idle", async ({ page }) => {
      await openRecord(page, false);
      await shot(page, "idle");
    });

    test("recording", async ({ page }) => {
      await openRecord(page);
      await page.getByRole("button", { name: "Start recording" }).click();
      await expect(page.getByText("Recording", { exact: true })).toBeVisible();
      await page.waitForTimeout(2_500);
      await shot(page, "recording");
    });

    test("recorded", async ({ page }) => {
      await openRecord(page);
      await recordAndStop(page);
      await shot(page, "recorded");
    });

    test("uploading", async ({ page }) => {
      await mockTranscribe(page, "hold");
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await expect(page.getByText("Uploading your audio.")).toBeVisible();
      await shot(page, "uploading");
    });

    test("transcribing", async ({ page }) => {
      // A held route never reports the upload as done, so report it here: the page then shows its next state.
      await page.addInitScript(() => {
        const send = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function (body) {
          send.call(this, body);
          setTimeout(() => this.upload.dispatchEvent(new ProgressEvent("load")), 200);
        };
      });
      await mockTranscribe(page, "hold");
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await expect(page.getByText("Transcribing your interview.")).toBeVisible();
      await shot(page, "transcribing");
    });

    test("review", async ({ page }) => {
      await mockTranscribe(page, recordedTranscription());
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await expect(page.getByText("Which voice is you?")).toBeVisible();
      await shot(page, "review");
    });

    test("one voice", async ({ page }) => {
      const example = recordedTranscription();
      const only = example.speakers[0];
      await mockTranscribe(page, {
        ...example,
        speakers: [only],
        turns: example.turns.filter((t) => t.speaker_id === only.id) as typeof example.turns,
        suggested_founder_id: only.id,
      });
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await expect(page.getByText("We only heard one voice.")).toBeVisible();
      await shot(page, "one-voice");
    });

    test("mic denied", async ({ page }) => {
      await page.addInitScript(() => {
        navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException("Permission denied", "NotAllowedError"));
      });
      await openRecord(page);
      await page.getByRole("button", { name: "Start recording" }).click();
      await expect(page.getByText("Your browser blocked the microphone.")).toBeVisible();
      await shot(page, "mic-denied");
    });

    test("failed", async ({ page }) => {
      await mockTranscribe(page, { error: { code: "transcription_failed", reason: "upstream_error" } });
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await expect(page.getByText("Transcription failed.")).toBeVisible();
      await shot(page, "failed");
    });

    test("upload audio", async ({ page }) => {
      const ideaId = await createIdea(page);
      await page.goto(`/ideas/${ideaId}/upload`);
      await page.getByRole("button", { name: "Upload audio" }).click();
      await page.getByLabel(/knows this conversation is being recorded/).check();
      await shot(page, "upload-audio");
    });

    test("transcript handed to the form", async ({ page }) => {
      await mockTranscribe(page, recordedTranscription());
      await openRecord(page);
      await recordAndStop(page);
      await page.getByRole("button", { name: "Use this recording" }).click();
      await page.getByRole("button", { name: "Use this transcript" }).click();
      await expect(page.getByText("Transcript from your audio.")).toBeVisible();
      await shot(page, "transcript-ready");
    });
  });
}
