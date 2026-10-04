// A failed analysis must never cost the founder their interview: the saved transcript is on screen, can be
// copied or downloaded, and "Try again" re-runs the analysis. The interview API is mocked so the failure is
// deterministic; the routes themselves are covered by tests/retry-route.test.ts.
import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";

import { createIdea, FAILED_ID, FAILED_TRANSCRIPT, mockFailedInterview } from "./helpers";

test("a failed analysis shows the saved transcript, lets you keep it, and tries again", async ({ page }) => {
  const calls = await mockFailedInterview(page, await createIdea(page));
  await page.goto(`/interviews/${FAILED_ID}`);

  await expect(page.getByText("Analysis failed.")).toBeVisible();
  const saved = page.getByRole("region", { name: "Your saved transcript" });
  await expect(saved).toContainText("I pay someone $300 a month to do it by hand.");

  const [download] = await Promise.all([page.waitForEvent("download"), saved.getByRole("button", { name: "Download .txt" }).click()]);
  expect(download.suggestedFilename()).toBe("interview-transcript.txt");
  expect(readFileSync(await download.path(), "utf8")).toBe(FAILED_TRANSCRIPT);

  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByText("Reading your interview.")).toBeVisible();
  expect(calls.retry).toBe(1);
});
