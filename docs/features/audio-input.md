# Audio input (record + upload) via ElevenLabs Scribe

Working plan and status for the `worktree-audio-input` branch. A fresh session resumes from here.

## Status

| Phase | State | Notes |
| --- | --- | --- |
| 0. Recon and plan | **done, waiting for answers** | Questions at the bottom |
| 1. Analyzer `POST /transcribe` | next | |
| 2. Contract and web API | — | |
| 3. UI | — | |
| 4. Real round trip | — | Needs `ELEVENLABS_API_KEY` |
| 5. Ship (draft PR) | — | |

### Environment (this worktree only)

- Path `.claude/worktrees/audio-input`, branch `worktree-audio-input`, base `d2ddd7d` (origin/main, tagged `mvp`).
- `mvp` tag created on `d2ddd7d` and pushed (it did not exist before).
- `apps/web/.env`: `ANALYZER_URL=http://localhost:8100`, `DATABASE_URL=…/validate_audio`. Web runs on **3100**, analyzer on **8100**.
- Database `validate_audio` created in the shared `realsignal-postgres-1` container; Drizzle migrations applied.
- `.claude/worktrees/` is ignored through `.git/info/exclude` (local only). `.gitignore` is protected, so it was not edited.

Run side by side with main:

```bash
pnpm --filter web dev --port 3100
cd services/analyzer && uv run uvicorn app.main:app --host :: --port 8100
```

### Baseline (Phase 0, before any change)

| Gate | Result |
| --- | --- |
| `pnpm validate`: eslint | pass |
| typecheck (`next typegen && tsc`) | pass |
| Vitest | pass, 37/37 |
| ruff | pass |
| pytest | pass, 48/48 |

## Where the repo differs from the brief

| # | Brief says | Repo reality | Plan |
| --- | --- | --- | --- |
| D1 | `main` is tagged `mvp` | No tag existed | Tagged `d2ddd7d` (team decision, 2026-10-04) |
| D2 | `pipeline/transcribe.py` may be a stub | It does not exist | Create it |
| D3 | `services/analyzer/fixtures/audio/…` for audio fixtures | `services/analyzer/fixtures/**` is **protected** (FACTORY_RULES §5) and human-owned | Put audio, the recorded Scribe response and the expected transcript in `services/analyzer/tests/recordings/audio/` (not protected; SPEC §12 already names `tests/recordings/`). Hand-written text fixtures stay untouched. |
| D4 | Playwright E2E, "the existing text journey must still pass" | No Playwright in the repo: no config, no specs, no dependency. There is no existing text journey | Adding `@playwright/test` is a new dependency + lockfile change → asked below. The text journey would be new too. |
| D5 | `respx` for tests | `httpx.MockTransport` (part of `httpx`, already installed) does the same job | Drop `respx`. Only `python-multipart` is new on the Python side. |
| D6 | Phase 5: append to `docs/SPEC.md` | `docs/SPEC.md` is **protected** (Governance group) | Asked below. Fallback: keep everything in this file and the README. |
| D7 | Consent checkbox before Record / Upload audio | The upload form **already** has a required consent checkbox for every submission: "The interviewee knew this conversation was recorded" | Reuse the same state. In audio modes, show it *before* the recorder/file picker with the brief's wording + the ElevenLabs line, and block recording/upload until it's ticked. Text modes keep today's checkbox and wording unchanged. |
| D8 | Voice review is new | The form already has a "Who is who?" role picker (`WhoIsWho`, `checks.ts`) for pasted transcripts with other labels | New voice-review cards reuse its visual pattern (radio group, ink border). The built transcript uses `Founder:`/`Customer:`, so `WhoIsWho` does not appear for it. |
| D9 | One voice → "still allow continuing" | The form **blocks** submit when nobody is `Customer:` ("Nobody is the customer") | Open question Q-A below. |
| D10 | `POST /api/interviews` accepts `source` | It doesn't; `createInterview` has no `source` param. The `input_source` enum and `interviews.source` column **do** include `audio` | No migration needed. Add `source` to the zod schema and to `createInterview`. |
| D11 | Unit tests replay recordings | Analyzer unit tests use in-code fakes (`LabelledJev`, `ScriptedWriter`); `tests/recordings/` does not exist yet | ElevenLabs gets a recorded JSON response (D3 location) replayed through `httpx.MockTransport`. |
| D12 | "SPEC B.1, B.5 step 1" | SPEC numbers them §1 and §5 step 1 | Naming only |
| D13 | Audio is the next feature | MISSION lists "audio and video upload, in-browser recording" under **Backlog: not now, but not never** (a human decides when) | The team brief is that decision. Flagged for the PR. |
| D14 | `ELEVENLABS_API_KEY` lives in the analyzer env | Not in `services/analyzer/.env` and not in `.env.example` | Unit tests don't need it. Phases 4+ do: **a human adds it** to this worktree's `services/analyzer/.env`. Phase 5 adds the name to `.env.example` too (the brief's list omits it). |

### ElevenLabs docs check (live, 2026-10-04)

Matches the brief: endpoint, `xi-api-key`, multipart, `scribe_v2`, `num_speakers` ≤ 32, `seed` 0–2147483647 best-effort, `detect_speaker_roles` +10 % and needs `diarize`, `no_verbatim` (scribe_v2 only), files < 5 GB and ≥ 100 ms, `enable_logging=false` enterprise-only, word `type` ∈ `word | spacing | audio_event`, `speaker_id` per word.

Differences and additions:
- The live page does **not** state defaults for `diarize` or `tag_audio_events`. We set both explicitly, so it doesn't matter.
- The response has `audio_duration_secs` (nullable). Use it for `duration_s`; fall back to the last word's `end`.
- `language_code` in the response is documented as e.g. `"eng"` (ISO-639-3) even though the request takes `"en"`. Pass it through as a string; don't compare it to `"en"`.
- `speaker_id` and `start`/`end` are nullable per word. A word with no `speaker_id` continues the current turn (never invents a speaker).

### Next.js 16 (installed `16.3.8`, docs in `node_modules/next/dist/docs`)

- Server Actions: 1 MB default body limit → confirmed, use a **route handler** (`runtime = "nodejs"`).
- Route handlers have no body cap unless a `proxy` (ex-middleware) exists; then it's 10 MB (`proxyClientMaxBodySize`). **The app has no proxy.** If one is ever added, audio upload breaks above 10 MB. Note this in the route's comment.
- `request.formData()` buffers the whole file in memory (≤ `AUDIO_MAX_MB` per request). Fine at current traffic. Streaming pass-through goes under "Later".

### Railway limits (docs.railway.com, specs and limits)

- "HTTP requests can run for up to 15 minutes if data keeps transferring … and are otherwise closed after **5 minutes with no data transferred**."
- "Request bodies must finish uploading within **5 minutes**."
- The analyzer is private-only, so web → analyzer is not behind the edge. The edge applies only to **browser → web**.
- Community reports (not in the docs) say the edge closes requests with no response bytes after 60 s. Unverified.

## Risks

1. **Timeouts don't nest as written.** Browser → web (Railway: 5 min with no bytes) → analyzer (Node `fetch` default `headersTimeout` is 300 s) → ElevenLabs (proposed 300 s × 2 attempts = up to 600 s). As proposed, the web call dies before the analyzer's retry finishes.
   **Proposal:** one total budget in the analyzer, `TRANSCRIBE_BUDGET_S = 270`. Each attempt gets the time left. Retry once on 429/5xx/timeout only if ≥ 60 s remain. Web client timeout 285 s. `/api/transcribe` sends the response headers at once and writes a whitespace byte every 15 s, then the JSON (leading whitespace is valid JSON), so the Railway edge never sees a silent request. Pre-checks (flag, consent, ownership, size) still return normal status codes. Only the analyzer outcome is in-band: `{error:{code}}` with status 200. Async jobs for longer files stay "Later".
2. **Scribe processing time for long files is unknown.** I won't guess. Phase 4 measures it on the fixtures; the README states what we measured.
3. **Upload time.** Railway needs the body uploaded within 5 min. 100 MB needs ≥ ~2.7 Mbit/s up. The recorder uses Opus at 64 kbit/s (`audioBitsPerSecond`): 60 min ≈ 29 MB. Uploaded WAV files hit the cap fast (60 min of 16-bit 44.1 kHz stereo ≈ 600 MB); the UI says "use .m4a or .mp3".
4. **Diarization errors.** Scribe can split one person into two voices or merge two. With `num_speakers` set, merges are likelier than splits. The review screen shows talk time + 2 sample lines per voice, so the founder can catch it. We never "fix" it silently.
5. **80,000-character cap.** 60 min at ~150 wpm ≈ 50k chars; fast talkers ≈ 65k. A longer result fails the existing check with the existing message. `AUDIO_MAX_MINUTES = 60` keeps us under it.
6. **PR size.** Feature + tests will pass 500 lines / 12 files. A word-level Scribe recording alone is thousands of lines when pretty-printed. Plan: two stacked PRs (as the brief says). Store recordings minified (one line) and say so in the PR. The cap is about reviewable code, not recorded data. Human call.

## Plan by phase

### Phase 1: Analyzer (`services/analyzer`)

| File | Change |
| --- | --- |
| `app/pipeline/transcribe.py` | **new.** `call_scribe()` (httpx, multipart, fixed params, seed constant, total budget, one retry), `build_turns(words)` (group by `speaker_id`, keep `word`/`spacing` text, drop `audio_event`, collapse whitespace, drop empty turns), `summarize_speakers()`, `suggest_founder()` (most turns ending in `?`, tie → first to speak). |
| `app/main.py` | `POST /transcribe` (multipart, `X-Analyzer-Key`, size → 413, empty/unreadable → 422, missing key → 503). Temp file in `finally`. Logs only: request id, bytes, duration, ms, model, speaker count, error code. |
| `app/models.py` | `TranscribeTurn`, `TranscribeSpeaker`, `TranscribeResult`, `TranscribeErrorResponse`. |
| `app/errors.py` | `AudioTooLarge` 413, `EmptyAudio` 422, `NoSpeech` 422, `TranscriptionFailed` 502/504 (+ `reason`), `TranscriptionNotConfigured` 503. |
| `tests/test_transcribe.py` | **new.** Turns from the recording, `audio_event` dropped, grouping, founder suggestion (incl. tie), 401 / 413 / 422, 5xx → one retry → `transcription_failed`, 429 retry, budget exhaustion, temp file gone, `caplog` has no transcript words, zero words → `no_speech` (never empty success). |
| `tests/recordings/audio/` | **new.** `example.transcribe.json` (our TranscribeResult), `example.scribe.json` (raw Scribe response), `example.transcript.txt` (expected built transcript), the small audio files. |
| `tests/test_split.py` | + split parses `example.transcript.txt` with the expected founder/customer turn counts. |
| `pyproject.toml` + `uv.lock` | `python-multipart` (**needs approval**). |

`/health` stays unchanged: it must not go red when audio is off.

### Phase 2: Contract and web API

| File | Change |
| --- | --- |
| `packages/contracts/transcribe.schema.json` | **new, protected, draft below.** `package.json` `files`/`exports` gain it. |
| `apps/web/scripts/gen-contracts.ts` | Also compiles `transcribe.schema.json` → `lib/transcribe.generated.ts`. |
| `services/analyzer/tests/test_contract.py` | + transcribe models match the schema; a real `/transcribe` response validates. |
| `apps/web/tests/contracts.test.ts` | + generated transcribe types are current. |
| `apps/web/lib/analyzer-client.ts` | + `transcribe(file, numSpeakers)`: multipart, `X-Analyzer-Key`, 285 s timeout. |
| `apps/web/lib/db/queries.ts` | + `founderOwnsIdea(founderId, ideaId)`; `createInterview` takes `source`. |
| `apps/web/app/api/transcribe/route.ts` | **new.** Node runtime. Order: flag → ownership (404) → `consent === "true"` (400) → size (413) / type (422) → analyzer. Heartbeat body (Risk 1). Stores nothing. |
| `apps/web/app/api/interviews/route.ts` | `source: "text" | "audio"`, default `"text"`. |
| `apps/web/lib/audio-config.ts` | **new.** Reads `AUDIO_INPUT_ENABLED`, `AUDIO_MAX_MB`, `AUDIO_MAX_MINUTES` on the server. |
| `apps/web/tests/transcribe-route.test.ts` | **new.** Rejects: flag off (404), other founder's idea (404), no consent (400), too big (413); passes the result through; `/api/interviews` saves `source = audio`. |

### Phase 3: UI (`apps/web/components/upload/`)

| File | Change |
| --- | --- |
| `transcript-builder.ts` | **new.** `buildTranscript(turns, founderId)`: one line per turn, consecutive same-role turns merged, whitespace normalized, no line breaks inside a turn. |
| `AudioInput.tsx` | **new.** Consent block, Record / Upload audio, people select (2–4), transcribing state, review cards. |
| `useRecorder.ts` | **new.** MediaRecorder state machine (idle → asking → recording → recorded), `isTypeSupported` (`audio/webm;codecs=opus` → `audio/mp4`), 64 kbit/s, auto-stop at `AUDIO_MAX_MINUTES` with a 5-min warning, stop all tracks on Stop and unmount, `beforeunload` while recording, mic-denied state. |
| `UploadForm.tsx` | Four modes when the flag is on (two when off, identical to today). Hands the built transcript to the textarea; sends `source`. |
| `app/ideas/[id]/upload/page.tsx` | Passes the server-side audio config as props. |
| `tests/transcript-builder.test.ts` | 2 and 3 speakers, founder = `speaker_1`, merge, whitespace, and `buildTranscript(example.transcribe.json) === example.transcript.txt`. |
| `e2e/` | Fake-mic journey + upload journey (if Playwright is approved). Screens to `docs/features/audio-input/screens/` at 1440 and 390. |

Design rules followed: existing tokens only; `danger` only for app errors (the recording dot uses `ink`); `brand` only on the one main action per screen.

### Phase 4: Real round trip

Opt-in `E2E_REAL=1`. Per fixture: text vs audio score and verdict, transcription diff against the `.txt`, ElevenLabs time per file, cost of the run. Bands are not loosened.

### Phase 5: Ship

`.env.example` names (`ELEVENLABS_API_KEY`, `ELEVENLABS_STT_MODEL`, `AUDIO_INPUT_ENABLED`, `AUDIO_MAX_MB`, `AUDIO_MAX_MINUTES`). README "Audio input" section. SPEC section only if approved. Push the branch; open the **draft** PR(s). No merge.

## Contract draft: `packages/contracts/transcribe.schema.json`

Not written yet. It goes into the repo only after approval.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://validate.ai/contracts/transcribe.schema.json",
  "title": "validate.ai analyzer transcription contract",
  "description": "Response of POST /transcribe. Request is multipart/form-data: file (required), num_speakers (optional integer 1-4, default 2). Speakers and turns only: no roles. The founder picks their own voice in the web app.",
  "$defs": {
    "TranscribeTurn": {
      "type": "object",
      "additionalProperties": false,
      "required": ["speaker_id", "text", "start", "end"],
      "properties": {
        "speaker_id": { "type": "string", "minLength": 1 },
        "text": { "type": "string", "minLength": 1 },
        "start": { "type": ["number", "null"], "minimum": 0 },
        "end": { "type": ["number", "null"], "minimum": 0 }
      }
    },
    "TranscribeSpeaker": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "turns", "words", "seconds", "sample"],
      "properties": {
        "id": { "type": "string", "minLength": 1 },
        "turns": { "type": "integer", "minimum": 1 },
        "words": { "type": "integer", "minimum": 0 },
        "seconds": { "type": "number", "minimum": 0 },
        "sample": {
          "type": "array",
          "minItems": 1,
          "maxItems": 2,
          "items": { "type": "string", "minLength": 1, "maxLength": 200 }
        }
      }
    },
    "TranscribeResult": {
      "type": "object",
      "additionalProperties": false,
      "required": ["duration_s", "language_code", "model", "speakers", "turns", "suggested_founder_id"],
      "properties": {
        "duration_s": { "type": ["number", "null"], "minimum": 0 },
        "language_code": { "type": ["string", "null"] },
        "model": { "type": "string", "minLength": 1 },
        "speakers": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/TranscribeSpeaker" } },
        "turns": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/TranscribeTurn" } },
        "suggested_founder_id": { "type": "string", "minLength": 1 }
      }
    },
    "TranscribeErrorResponse": {
      "type": "object",
      "additionalProperties": false,
      "required": ["error"],
      "properties": {
        "error": {
          "type": "object",
          "additionalProperties": false,
          "required": ["code", "message"],
          "properties": {
            "code": {
              "type": "string",
              "enum": [
                "bad_key", "invalid_request", "audio_too_large", "empty_audio", "no_speech",
                "transcription_failed", "transcription_not_configured"
              ]
            },
            "message": { "type": "string" },
            "reason": {
              "type": ["string", "null"],
              "enum": ["rate_limited", "upstream_error", "timeout", "rejected", null]
            }
          }
        }
      }
    }
  }
}
```

| Status | Code |
| --- | --- |
| 401 | `bad_key` |
| 413 | `audio_too_large` |
| 422 | `invalid_request` (no file, bad `num_speakers`), `empty_audio` (0 bytes / unreadable / < 100 ms), `no_speech` (Scribe returned no words) |
| 502 | `transcription_failed` with `reason` `rate_limited` / `upstream_error` / `rejected` |
| 503 | `transcription_not_configured` (no `ELEVENLABS_API_KEY`) |
| 504 | `transcription_failed` with `reason: "timeout"` |

`analyze.schema.json` does not change.

## Proposed numbers (need confirmation)

| Name | Proposed | Why |
| --- | --- | --- |
| `AUDIO_MAX_MB` | 100 | 60 min at 128 kbit/s ≈ 58 MB fits with room. Upload must finish in 5 min on Railway. |
| `AUDIO_MAX_MINUTES` | 60 | Fits the 80k-char cap (Risk 5). |
| Recorder bitrate | 64 kbit/s Opus | Speech is clear at this rate; 60 min ≈ 29 MB. |
| `TRANSCRIBE_BUDGET_S` (analyzer, total) | 270 | Replaces "300 s per call" so the timeouts nest (Risk 1). |
| Web → analyzer timeout | 285 s | Under Node `fetch`'s 300 s default header timeout. |
| Heartbeat interval | 15 s | Well under any Railway no-data limit. |
| `num_speakers` | 1–4, default 2 | Brief. |
| Scribe `seed` | fixed constant in code | Brief. |

## New dependencies

| Package | Where | Why | Lockfile |
| --- | --- | --- | --- |
| `python-multipart` | analyzer runtime | FastAPI needs it to parse `UploadFile`; nothing installed does this | `services/analyzer/uv.lock` |
| `@playwright/test` (+ Chromium download) | web devDependency | The brief's E2E journeys; the repo has no browser test runner | `pnpm-lock.yaml` |
| ~~`respx`~~ | — | **Dropped:** `httpx.MockTransport` covers it | — |

## Open questions

Asked in Phase 0 through the question tool:
1. Audio fixtures: (a) the team records `real_pain` and `polite`, or (b) a TTS script.
2. `AUDIO_MAX_MB` / `AUDIO_MAX_MINUTES`.
3. Approvals: contract draft, `python-multipart`, `@playwright/test`, editing protected `docs/SPEC.md`.
4. Consent wording kept as a draft.

Still open, with a proposed answer (build against it unless told otherwise):
- **Q-A (D9)** One voice found: the existing form blocks a transcript with no `Customer:`. Proposed: for an audio-built transcript, show the honest one-voice note and **allow** submit. The gate returns `need_more_evidence` (SPEC §5: a founder-only transcript always does). Text paste keeps today's block.
- **Q-B (Risk 1)** Heartbeat body on `/api/transcribe`: proposed yes.
- **Q-C (Risk 6)** Minified recordings and two stacked PRs: proposed yes.
- **Q-D** `source` after a transcription: proposed `audio` while the textarea holds the audio-built transcript, edits included. It resets to `text` when the founder clears the box or loads a .txt.

## Later (not in this branch)

Streaming pass-through upload (no buffering in web), async transcription jobs + webhooks for > 60 min, live transcript while recording, tab/Zoom audio capture, keyterms from the idea text, languages other than English, audio via Fetch.ai agents.
