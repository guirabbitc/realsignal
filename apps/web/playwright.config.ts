// Browser journeys. Not part of `pnpm validate`: they need Postgres and, for the text and real-audio journeys,
// the analyzer with real Jev, OpenAI and ElevenLabs keys.
//   AUDIO_INPUT_ENABLED=true|false   the flag the dev server starts with (default true)
//   E2E_REAL=1                       also run the real ElevenLabs upload journey (costs money)
//   E2E_FAKE_AUDIO=/path/to.wav      what the fake microphone plays (default: Chromium's beep)
import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.E2E_PORT ?? 3100);
const fakeAudio = process.env.E2E_FAKE_AUDIO ? [`--use-file-for-fake-audio-capture=${process.env.E2E_FAKE_AUDIO}`] : [];

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  expect: { timeout: 15_000 },
  workers: 1,
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://localhost:${PORT}`,
    launchOptions: { args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", ...fakeAudio] },
  },
  webServer: {
    command: `pnpm dev --port ${PORT}`,
    url: `http://localhost:${PORT}/ideas`,
    reuseExistingServer: false,
    timeout: 180_000,
    env: { AUDIO_INPUT_ENABLED: process.env.AUDIO_INPUT_ENABLED ?? "true" },
  },
});
