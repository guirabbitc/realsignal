# validate.ai

**An AI coach for customer interviews.** Paste the transcript of a discovery interview or demo, and validate.ai tells you which things the customer said were **real signals of interest** and which were **just politeness**. Then it gives a verdict on what to do next, with the exact quotes to prove it.

> Built at MHacks 2026 (Actually Intelligent + Fetch.ai tracks) by Guilherme Coelho and Murilo Guazzelli. Working name; the final name is open.

**Live:** https://web-production-cd9ee.up.railway.app

## Why

Customers are polite. "Cool idea" and "I'd use that" feel like validation, but they rarely mean anyone will pay. First-time founders count those compliments and spend months building the wrong thing. 42% of failed startups name "no market need" as the main reason (CB Insights). validate.ai reads the interview the way an experienced founder would: it looks for **past behaviour and commitments, not compliments** (The Mom Test).

## How it works

**Jev judges, OpenAI writes, Python counts.**

1. **Split** (Python): the transcript is split into `Founder:` / `Customer:` turns and sentences. Every quote stays word for word.
2. **Judge** (Jev by TypeSafe AI): every customer sentence gets a category (commitment, past pain, hypothetical, compliment, neutral) and a calibrated probability that it is a real signal. Jev also checks the founder for pitching early and for leading questions.
3. **Score** (Python): a 0–100 signal score from a formula anyone can check.
4. **Verdict** (Jev, the mean of 3 calls): keep going, narrow down, try a new angle, or pivot. A **confidence gate** turns it into "not enough evidence yet" when the evidence is thin.
5. **Write** (OpenAI): a plain-English read-out with the reasons and the next 3 questions to ask. It cannot change the verdict.
6. **Verify** (Python): any quote in the read-out that is not verbatim in the transcript is dropped.

## Repository

| Path | What |
| --- | --- |
| `apps/web` | Next.js 16 app: pages, `/api` routes, Drizzle schema, anonymous session. The only thing that touches Postgres. |
| `services/analyzer` | Python + FastAPI analysis pipeline. Stateless. |
| `packages/contracts` | `analyze.schema.json`, the contract both services agree on. |
| `scripts/journey.py` | The 9-step main journey, run against any URL. |
| `docs/` | [`PRD.md`](docs/PRD.md) (what and why) and [`SPEC.md`](docs/SPEC.md) (how). |
| `MISSION.md`, `FACTORY_RULES.md`, `FACTORY.md` | The dark-factory guidance layer (what the autonomous builder may and may not do). |

## Run it locally

Requirements: Node 22+, pnpm, uv, and Docker.

```bash
pnpm install
docker compose up -d                          # Postgres on localhost:5433
cp .env.example apps/web/.env                 # then fill in ANALYZER_KEY and SESSION_SECRET
cp .env.example services/analyzer/.env        # then fill in ANALYZER_KEY, TYPESAFE_API_KEY, OPENAI_API_KEY, OPENAI_MODEL
pnpm --filter web db:migrate
(cd services/analyzer && uv sync && uv run --env-file .env uvicorn app.main:app --host :: --port 8000)
pnpm --filter web dev                         # http://localhost:3000
```

Try it:

```bash
python3 scripts/journey.py http://localhost:3000 real_pain    # expects keep_going, score > 70
python3 scripts/journey.py http://localhost:3000 polite       # expects pivot or need_more_evidence, score < 30
```

## Test

```bash
pnpm validate      # lint + typecheck + Vitest (web) + ruff + pytest (analyzer). No network.
```

`scripts/journey.py` is the end-to-end check. It calls the real Jev and OpenAI.

Browser journeys (Playwright; needs Postgres, and the analyzer for the text journey):

```bash
pnpm --filter web exec playwright install chromium   # once
AUDIO_INPUT_ENABLED=true  pnpm --filter web e2e      # record journey (fake mic) + text journey
AUDIO_INPUT_ENABLED=false pnpm --filter web e2e      # the text journey must pass with audio off too
E2E_REAL=1 pnpm --filter web e2e upload-audio-real   # real ElevenLabs + Jev + OpenAI; costs money
E2E_SCREENS=1 pnpm --filter web e2e screens          # screenshots to docs/features/audio-input/screens/
```

## Audio input

A founder can record an interview in the browser or upload a recording instead of pasting text. ElevenLabs Scribe
transcribes it with speaker separation, the founder confirms which voice is theirs, and the result becomes a normal
`Founder:` / `Customer:` transcript that goes through the same analysis as pasted text. Audio is never stored.

It is off by default. To turn it on:

1. Set `ELEVENLABS_API_KEY` in `services/analyzer/.env` (only the analyzer holds it).
2. Set `AUDIO_INPUT_ENABLED=true` in `apps/web/.env`, and restart both services.
3. Optional: `AUDIO_MAX_MB` (default 100, same value in both services), `AUDIO_MAX_MINUTES` (default 60, recording
   limit), `ELEVENLABS_STT_MODEL` (default `scribe_v2`).

With the flag off the upload form is text only and `POST /api/transcribe` answers 404. Design notes, risks and
status: [`docs/features/audio-input.md`](docs/features/audio-input.md).

## Deploy

Railway project `validate-ai`, with three services: `web`, `analyzer` (private network only) and `Postgres`. See [`docs/SPEC.md` §10](docs/SPEC.md).
