// The real round trip: ElevenLabs + Jev + OpenAI, no mocks. Opt-in (costs money): E2E_REAL=1.
// Audio comes from the team-recorded files (fixtures option a), in E2E_AUDIO_DIR or tests/recordings/audio.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

import { audioEnabled, createIdea, expectVerbatim, FIXTURES, RECORDINGS, submitAndOpenReadOut, waitForResult } from "./helpers";

const AUDIO_DIR = process.env.E2E_AUDIO_DIR ?? RECORDINGS;

test.skip(process.env.E2E_REAL !== "1", "Real ElevenLabs + Jev + OpenAI journey: run with E2E_REAL=1 (costs money).");
test.skip(!audioEnabled, "Audio input is off (AUDIO_INPUT_ENABLED).");

for (const fixture of ["real_pain", "mixed", "polite"] as const) {
  const audioFile = resolve(AUDIO_DIR, `${fixture}.m4a`);

  test(`upload ${fixture} audio → confirm my voice → same band as the text fixture`, async ({ page }) => {
    test.skip(!existsSync(audioFile), `Needs the team-recorded ${audioFile}`);
    const labels = JSON.parse(readFileSync(resolve(FIXTURES, `${fixture}.labels.json`), "utf8"));
    // The founder's voice is the one that says the founder's first line of the script; the founder confirms
    // it on screen like a person would, rather than trusting the guess or the first voice.
    const firstFounderLine = readFileSync(resolve(FIXTURES, `${fixture}.txt`), "utf8")
      .split("\n")
      .find((line) => line.startsWith("Founder:"))!
      .replace("Founder:", "")
      .trim();
    const cue = firstFounderLine.split(/\s+/).slice(-4).join(" ").replace(/[?.!,]$/, "");

    const ideaId = await createIdea(page);
    await page.goto(`/ideas/${ideaId}/upload`);
    await page.getByRole("button", { name: "Upload audio" }).click();
    await page.getByLabel(/knows this conversation is being recorded/).check();
    await page.getByLabel("Choose an audio file").setInputFiles(audioFile);
    const started = Date.now();
    await page.getByRole("button", { name: "Transcribe this file" }).click();
    await expect(page.getByText("Which voice is you?")).toBeVisible({ timeout: 290_000 });
    console.info(`${fixture}: transcription took ${Math.round((Date.now() - started) / 1000)} s`);

    const founderCard = page.locator("label", { hasText: cue }).first();
    await founderCard.getByRole("radio").check();
    await page.getByRole("button", { name: "Use this transcript" }).click();
    const transcript = await page.getByRole("textbox", { name: "Transcript" }).inputValue();
    console.info(`${fixture} transcript:\n${transcript}`);

    const result = await waitForResult(page, await submitAndOpenReadOut(page));
    console.info(`${fixture}: score=${result.score} verdict=${result.verdict}`);
    const band = labels.score_band;
    if (band.min_exclusive !== undefined) expect(result.score!).toBeGreaterThan(band.min_exclusive);
    if (band.min_inclusive !== undefined) expect(result.score ?? 0).toBeGreaterThanOrEqual(band.min_inclusive);
    if (band.max_exclusive !== undefined) expect(result.score ?? 0).toBeLessThan(band.max_exclusive);
    if (band.max_inclusive !== undefined) expect(result.score ?? 0).toBeLessThanOrEqual(band.max_inclusive);
    expect(labels.allowed_verdicts).toContain(result.verdict);
    expect(result.next_questions).toHaveLength(3);
    expectVerbatim(result, transcript);
  });
}
