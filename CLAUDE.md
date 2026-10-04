# ValiDate

Analyzes customer interviews to separate real demand from politeness and tells the founder to keep going, narrow down, try a new angle, or pivot. Monorepo, modular monolith: one repo, one product, two app services (Next.js and the Python analyzer) plus Postgres. The `agents/` folder is a hackathon shell for the Fetch.ai ASI:One track (MHacks 2026).

`UPDATE.md` is the handoff file for teammates and their coding agents. Add a changelog entry there whenever the code changes.

## The stack (decided — do not substitute alternatives)

| Part | Technology | Role |
|---|---|---|
| Front + back | Next.js (App Router) + TypeScript | Pages, `/api` route handlers, auth later. **The only thing that talks to the database.** No separate Express/Nest backend. |
| Database | Postgres + Drizzle ORM | Schema and migrations live on the TypeScript side only. |
| Analysis | Python + FastAPI | Transcription (ElevenLabs), sentence splitting, Jev judgments, scoring, OpenAI writes the insights. |
| Fetch.ai / ASI:One (hackathon only) | Python uAgents | Thin shell that calls the same analyzer. No analysis logic of its own. |
| Deploy | Railway: 3 services from this repo (web, analyzer, Postgres) | Each service points at its own folder. |

## Folder map

```
realsignal/
  apps/
    web/                    Next.js: pages + /api routes + database
      app/                  page.tsx (upload), interviews/[id] (result), api/interviews
      lib/analyzer.ts       the only place the web app calls the analyzer
      lib/interviews.ts     processing -> done/failed flow and queries
      lib/contracts/        analyze.ts (GENERATED), values.ts (enum values read from the schema)
      lib/db/               Drizzle schema + migrations (owns Postgres)
  services/
    analyzer/               Python FastAPI (uv)
      app/main.py           POST /analyze, GET /health, stage endpoints /transcribe /judge /write
      app/contracts.py      GENERATED Pydantic models
      app/pipeline/         transcribe.py, split.py, jev.py, scoring.py, writer.py
      fixtures/             mock interviews
      evals/                run.py (accuracy against an answer key), cases/*.json, generate_cases_prompt.md
      tests/
  agents/                   uAgents for ASI:One; they call the analyzer (hackathon) (uv)
    front/                  agent.py, chat_proto.py, flow.py (plans the steps and calls the team)
    intake/ analyst/ strategist/   thin specialists, one analyzer stage each
    */README.md             each agent's Agentverse profile, published on mailbox connect
    specialists.py          each specialist's typed protocol and its chat handler
    chat.py                 Chat Protocol factory (from Fetch's openai-agent template), shared by all agents
    conversation.py         the idea-then-interview conversation, shared by all agents
    team.py                 ask another agent with ctx.send_and_receive
    render.py               reply text (presentation only)
    analyzer_client.py      the only place agents call the analyzer
    models.py               agent-to-agent messages
    contracts.py            GENERATED Pydantic models
  packages/
    contracts/              analyze.schema.json — the shared request/response contract
  docker-compose.yml        local Postgres
  pnpm-workspace.yaml
  .env.example              one .env at the repo root serves every service
```

## The flow

1. Founder uploads an interview in Next.js (audio/video or transcript) plus the idea it tests.
2. Next.js saves the interview in Postgres with status `processing`.
3. Next.js calls the analyzer `POST /analyze` with the idea + transcript (or the audio, as multipart).
4. Analyzer: transcribe (ElevenLabs, with speaker labels) → split into sentences → Jev judges each interviewee sentence → Python computes the score → Jev picks the verdict → OpenAI writes the summary and next steps. Returns one JSON matching the contract.
5. Next.js saves sentences + analysis, sets status `done` (or `failed` with the error), and renders the result.

In ASI:One, the front agent introduces itself and asks for the idea, then asks for the interview (either can arrive first; see `agents/front/flow.py`). With `FRONT_USE_SPECIALISTS=0` it calls `/analyze`; with `1` it chains Intake → Signal Analyst → Strategist via `ctx.send_and_receive`, each calling one stage endpoint.

## Non-negotiable rules

- **Python never touches the database.** The analyzer receives data and returns JSON. No DB driver or connection string in `services/` or `agents/`.
- **One contract, one place.** `packages/contracts/analyze.schema.json` (JSON Schema) defines the `/analyze` request and response. Generate TS types from it for `apps/web` and Pydantic models for `services/analyzer` (or validate against it in tests). Add a script/CI check that fails if either side drifts from the schema. Never hand-duplicate these types.
- **The analyzer is private.** Only Next.js (and the hackathon agents) call it, over Railway's private network, with a shared secret in a header (e.g. `X-Analyzer-Key`, from `ANALYZER_SECRET`). Reject requests without it. `/health` can be open.
- **Jev makes the judgments; the LLM only writes text; Python does the math.** Jev returns typed answers (choice / score / yes-no probability) and is unreliable at counting, so all totals and the score are computed in `scoring.py`. Use the official TypeSafe Python SDK or the OpenRouter decisions endpoint — check their current docs, don't guess the API shape. Keep the Jev calls behind one module (`jev.py`) so the provider can be swapped.
- **Labels and verdicts** (use exactly these, defined once in the contract):
  - Per sentence: `real_signal` | `polite` | `neutral`, with a confidence (0–1).
  - Verdict: `keep_going` | `narrow_down` | `try_new_angle` | `pivot`.
- **ElevenLabs** for transcription with speaker diarization; check the current docs for the right endpoint/model. Keep it behind `transcribe.py`.
- **No paid API calls in tests.** Every external client (ElevenLabs, Jev, OpenAI) sits behind an interface with a fake/mock used in tests; tests run on the fixtures.
- **Secrets only in env vars.** Maintain `.env.example` with every variable (DATABASE_URL, ANALYZER_URL, ANALYZER_SECRET, ELEVENLABS_API_KEY, JEV_API_KEY, OPENAI_API_KEY, agent seeds, AGENTVERSE settings). Never commit real values.
- **Tooling:** pnpm workspaces for JS/TS. For Python, use `uv` + `pyproject.toml` unless the repo already uses something else (tell me if so).

### agents/ specifics

- `uagents` current version (0.26+), `mailbox=True`, a fixed `seed` per agent from env, one port per local agent.
- The front agent implements the Chat Protocol by hand, modeled on Fetch's `6-deployed-agents/knowledge-base/openai-agent/chat_proto.py` in github.com/fetchai/uAgent-Examples (it handles file uploads: reply `{"attachments": "true"}` on session start, download `ResourceContent` via `ExternalStorage`). Do **not** use the experimental `ChatAgent`, and do **not** copy patterns from `5-documentation/guides/agents` (outdated: uagents 0.17, DeltaV/`ai_engine`).
- Agent-to-agent calls use `ctx.send_and_receive` with typed `Model` classes (see `6-deployed-agents/chained/blog-creator-agent`).
- The agents call the analyzer over HTTP with the same contract and secret. They contain no analysis logic.
- Framing: we measure evidence of real demand, never whether someone is lying. Never write "lie detector".

## Commands

```bash
docker compose up -d --wait                 # local Postgres
pnpm install
pnpm db:migrate                             # apply Drizzle migrations
pnpm db:generate                            # after editing apps/web/lib/db/schema.ts
pnpm dev:web                                # http://localhost:3000
cd services/analyzer && uv run uvicorn app.main:app --port 8000
cd services/analyzer && uv run pytest
cd services/analyzer && uv run python -m evals.run     # accuracy on evals/cases/*.json (real Jev; --fake is free)
pnpm contracts:generate                     # after editing analyze.schema.json
pnpm contracts:check                        # fails if generated files drifted
pnpm -r build && pnpm typecheck
uv run --project agents python agents/tests/smoke_chat.py direct        # or: specialists
cd agents && uv run pytest tests/test_flow.py                           # the front agent's conversation
uv run --project agents python agents/front/agent.py
uv run --project agents python agents/run_team.py                        # all four agents, one terminal
```

## How to change things

- **Contract:** edit `analyze.schema.json`, run `pnpm contracts:generate`, commit the three generated files. Never edit `analyze.ts` or either `contracts.py` by hand.
- **Database:** edit `apps/web/lib/db/schema.ts`, run `pnpm db:generate`, commit the migration. Label and verdict enums come from `lib/contracts/values.ts`, which reads the schema.
- **External clients:** each has a real class and a fake in its pipeline module. `ANALYZER_FAKE_CLIENTS=1` runs the analyzer on the fakes; `/health` reports `mode`.
- **Score:** only in `scoring.py`. Models never count or add.

## Open questions

- Audio storage is not decided. For the MVP, audio goes straight to the analyzer and is not persisted.
- Auth is not built. Every interview belongs to one default founder (`lib/interviews.ts`).
- The real ElevenLabs, Jev and OpenAI clients are written from the docs and tested against mocked HTTP only. They have not run against the live APIs.
