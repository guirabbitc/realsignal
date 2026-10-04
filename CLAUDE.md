# validate.ai conventions

<!-- PROTECTED. The factory cannot edit this file. Humans change it by direct commit. -->

What the product is: [`MISSION.md`](MISSION.md) and [`docs/PRD.md`](docs/PRD.md).
How it is built: [`docs/SPEC.md`](docs/SPEC.md). Read SPEC §4 (ownership rules) before your first edit.

## Language

**English everywhere:** code, identifiers, comments, docs, UI copy, commit messages, PR bodies. No exceptions, even when the conversation is in another language.

## Stack and commands

```bash
pnpm install                                         # JS deps for the whole workspace
docker compose up -d                                 # local Postgres on 5433
pnpm --filter web db:migrate                         # apply Drizzle migrations
pnpm --filter web dev                                # web on http://localhost:3000
cd services/analyzer && uv sync && uv run uvicorn app.main:app --host :: --port 8000
pnpm validate                                        # lint + typecheck + Vitest + pytest (recorded) + contract test; no network
```

- **pnpm, not npm or yarn.** It is a pnpm workspace; other managers break the lockfile.
- **uv, not pip or poetry.** The analyzer and the agents are uv projects.
- **Railway** hosts `web`, `analyzer` and `postgres` on the quarterbackgui@gmail.com account. Run `railway whoami` before any `railway` command.

## Where things live

| Path | What belongs there |
| --- | --- |
| `apps/web/` | Next.js app: pages, `/api` route handlers, server actions, the DB schema. |
| `apps/web/lib/db/queries.ts` | **All** SQL. Every function takes `founderId`. |
| `apps/web/lib/session.ts` | The only code that reads or writes the session cookie. |
| `apps/web/lib/analyzer-client.ts` | The only code that calls the analyzer. |
| `services/analyzer/app/pipeline/` | One file per pipeline step: split, jev, scoring, gate, writer, verify, analyze. |
| `services/analyzer/app/rubric.json` | Weights, thresholds, Jev question texts, model ids. Data, not code. |
| `services/analyzer/fixtures/` | Reference interviews and their expected labels. Human-owned. |
| `packages/contracts/analyze.schema.json` | The analyzer request/response contract. Single source of truth. |
| `agents/` | Fetch.ai uAgent for ASI:One (hackathon). Imports the analyzer pipeline. |
| `docs/` | PRD and SPEC. |

## Architecture rules that matter

1. **Only `apps/web` touches Postgres**, and only through `lib/db/queries.ts`. The analyzer is stateless: JSON in, JSON out.
2. **`founder_id` comes only from the session.** Never from a body, query string or path. Another founder's resource is a 404.
3. **Jev judges, OpenAI writes, Python counts.** Labels and probabilities come from Jev. Score, gate and top quotes come from Python. OpenAI only writes `summary`, `reasons` and `next_questions`, and its schema has no field for a verdict or a score.
4. **Quotes are verbatim.** Statement quotes are exact substrings of the transcript. Quoted spans in writer text pass `verify.py` or are dropped.
5. **The contract is generated, not hand-copied.** Change `analyze.schema.json` first; regenerate the TS types; keep the Pydantic models matching (a test checks this).

## Code style

- TypeScript: strict mode. Server code in route handlers and server actions; no business logic in client components.
- Python: type hints everywhere, Pydantic models at the edges, `async` for all I/O.
- Errors:
  - The analyzer returns `{"error": {"code", "message"}}` with the status codes in SPEC §6.
  - The web app stores `interviews.error` as the code, never the raw upstream message.
  - Never swallow a Jev or OpenAI failure.
- **Logging:** ids, timings, model ids, rubric version, error codes. **Never transcript text, never keys.**
- Comments explain *why*, not what.

## Tests

- **Web:** Vitest in `apps/web/tests/`.
- **Analyzer:** pytest in `services/analyzer/tests/`.
- **E2E:** Playwright and pytest, run with real APIs.
- Unit tests replay recorded Jev/OpenAI responses from `services/analyzer/tests/recordings/`, with no network.
- A new feature comes with tests. A bug fix comes with a regression test that fails before the fix.
- **New coverage goes in the tests folders, never in `harness/`.** The harness is the definition of "working" and is protected.
- Reference fixtures and their `.labels.json` are human-owned. Don't edit them to make a test pass.

## Dependencies

Lockfiles are protected. Adding a dependency needs a human: write what it does, why the existing ones are not enough, and evidence it is maintained.

## Skills in this repo

`.claude/skills/` holds the team's process (Cole Medin's PIV loop and helpers):
- `prime-codebase`
- `piv-plan-implementation` → `piv-implement` → `piv-validate` → `piv-review-changes` → `piv-commit` → `piv-create-pr`
- `archon-cli` for Archon workflows

## What is NOT in this file

- What the product is and will never be → `MISSION.md`
- How the factory behaves unsupervised (PR caps, protected paths, stop rules) → `FACTORY_RULES.md`
