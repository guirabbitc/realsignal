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
| `agents` | Fetch.ai uAgents for ASI:One and the web chat: a front agent and three specialists that run the analyzer pipeline, plus a tester. See [`agents/README.md`](agents/README.md). |
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

### If every page except the home page says "This page doesn't exist"

This happened once in local development: `/` loaded, but `/ideas`, `/chat` and every idea page returned the not-found page, while the `/api` routes kept working and the data was saved correctly.

- **Why:** `next dev` was started on top of a `apps/web/.next` folder that a production `next build` had just written, while `next typegen` (part of `pnpm validate`) was writing to the same folder. The dev server came up with a route table that knew only the home page. Nothing was wrong in the code or the database.
- **Fix:** stop the dev server, delete the build folder, start it again:

```bash
rm -rf apps/web/.next && pnpm --filter web dev
```

- **Avoid it:** don't run `pnpm --filter web build` or `pnpm validate` in this folder while the dev server is running. Use a second checkout (`git worktree add`) for that.

## Test

```bash
pnpm validate      # lint + typecheck + Vitest (web) + ruff + pytest (analyzer). No network.
```

`scripts/journey.py` is the end-to-end check. It calls the real Jev and OpenAI.

## Deploy

Railway project `validate-ai`, with three services: `web`, `analyzer` (private network only) and `Postgres`. See [`docs/SPEC.md` §10](docs/SPEC.md).
