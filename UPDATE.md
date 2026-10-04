# Real Signal: project state and handoff

Read this first if you (or your coding agent) are new to the repo. It says what exists, what was verified, and what is left. The rules the code must follow are in `CLAUDE.md`; run instructions are in `README.md`. Add a changelog entry here whenever the code changes.

Last updated: 2026-10-03, after the migration to the finalized stack.

## What we are building

Real Signal: a founder gives an idea and a customer interview, and gets back each interviewee sentence labelled `real_signal`, `polite` or `neutral` with a confidence, a demand score, a verdict (`keep_going`, `narrow_down`, `try_new_angle`, `pivot`), a summary and next steps.

It is also our entry for the Fetch.ai ASI:One Agent Challenge at MHacks 2026, which needs the workflow to run inside an ASI:One conversation and rejects simple chatbots and API wrappers.

## Source of truth

The finalized stack brief, recorded in `CLAUDE.md`. It replaced the earlier rule that the hackathon build workflow wins over the product board. Where they differ from the brief:

| Topic | Earlier | Now |
| --- | --- | --- |
| Stack | Python uAgents only, web app as a late bonus | Next.js + Postgres is the core; agents are a thin shell |
| Analysis code | Inside the agents (`brain/`) | Only in `services/analyzer` |
| Quote labels | Four categories (compliment, hypothetical, past behavior, commitment) plus signal labels | Only `real_signal`, `polite`, `neutral` |
| Verdicts | keep going, pivot, stop | `keep_going`, `narrow_down`, `try_new_angle`, `pivot` |
| Interview history | `ctx.storage` in the agents | Postgres, owned by the web app. Agents store only the founder's current idea. |
| Python tooling | pip + `requirements.txt` | `uv` + `pyproject.toml` |

Dropped from the hackathon plan for now: the Market Check agent, cross-interview comparison in ASI:One, and the Payment Protocol. The first needs a web-search stage in the analyzer; the other two need interview history, which agents cannot read.

## State

| Part | Status | Verified by |
| --- | --- | --- |
| Contract + drift check | Done | `pnpm contracts:check` passes; fails when a generated file is edited by hand |
| Analyzer | Done, on fakes | `pytest`: 17 tests, offline |
| Database | Done | `docker compose up`, `pnpm db:migrate` on an empty database: 5 tables |
| Web app | Done | Build and typecheck pass. Fixture upload goes `processing` → `done` and the result page shows sentences, score and verdict. With the analyzer stopped, the row goes `failed` with the error. |
| Front agent | Done locally | Smoke test in `direct` mode |
| Specialist agents | Done locally | Smoke test in `specialists` mode gives the same result as `direct` |

**Not verified yet:**

- **Live AI calls.** The ElevenLabs, Jev and OpenAI clients were written from their docs and tested against mocked HTTP only. No API keys were available. Everything seen so far ran in fake mode, where labels come from keyword rules.
- **ASI:One.** No agent has had its mailbox connected. Chatting from ASI:One and uploading a file there are untested.
- **Agents over the network.** The specialists were chained inside one process. Four separate processes talking through Agentverse are untested.
- **Railway.** No deployment config exists.

## Decisions worth knowing

- **Who is the interviewee:** the speaker who asks the most questions is treated as the interviewer; everyone else is judged (`split.py`). With one speaker, every sentence is judged.
- **Score:** share of confidence-weighted evidence that is real signal, 0 to 100. Polite sentences count fully against it, neutral ones count half (`scoring.py`).
- **Jev access:** TypeSafe's HTTP API (`POST /v1/systemone`), not the SDK. `JEV_BASE_URL` and `JEV_MODEL` switch it to OpenRouter. One `choice` question per sentence, 20 per request.
- **Stage endpoints:** `/transcribe`, `/judge` and `/write` exist so each specialist agent wraps one stage. `/analyze` runs the same functions, and a test asserts the two paths give identical results.
- **Agent messages** carry analyzer payloads as dicts and validate them with the generated models, so no contract type is written by hand.
- **Agent chat:** the founder sends `idea: ...` first; the front agent keeps it per sender in `ctx.storage`. A message is treated as a transcript when it has two or more `Speaker:` lines or is longer than 400 characters.
- **Fixtures** are written, not recorded. Replace them with real mock interviews when you have them.
- **Seeds decide addresses.** The README addresses come from Murilo's `.env`. Two machines running the same seed compete for one mailbox, so agree who runs which agent.

## Next

1. Put `ELEVENLABS_API_KEY`, `JEV_API_KEY` and `OPENAI_API_KEY` in `.env`, set `ANALYZER_FAKE_CLIENTS=` (empty), and run one real interview through the web app. Expect to adjust the Jev instructions and the writer prompt.
2. ASI:One check: start the front agent, connect its mailbox, send `idea: ...`, then paste a transcript and upload a `.txt`.
3. Connect the three specialists, set `FRONT_USE_SPECIALISTS=1`, repeat.
4. Decide audio storage and add auth.
5. Railway: three services (web, analyzer, Postgres), analyzer on the private network.
6. Before submission: make the repo public, record the demo video.

## Changelog

- **2026-10-03** Migrated to the finalized stack. Added the contract with generated TS and Pydantic types and a drift check; the FastAPI analyzer with pipeline, fakes, fixtures and tests; the Next.js app with Drizzle schema and migrations; local Postgres; the front agent calling the analyzer; three specialist agents over stage endpoints; `CLAUDE.md`. Moved agent scripts and tests under `agents/`, switched Python to `uv`, removed `brain/`.
- **2026-10-03** Phase 0 scaffold: hello-world front agent with Chat Protocol and upload handling, seed generation, local smoke test.
