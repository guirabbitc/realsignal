# The factory

<!-- Maintainer: whoever raises the autonomy dial. Update the level and date in the same commit. Protected. -->

**Current autonomy level: 0.** The guidance layer exists. Nothing runs unattended yet.
**Target level: 3.** Auto-merge when every structural gate is green.
**Raised to this level on:** 2026-10-04
**Stop button:** the board's stop switch, or `touch .factory/STOP` in the repo root.
**Built from PRD:** [`docs/PRD.md`](docs/PRD.md). `MISSION.md` is its compression; change one, change both.

## Build plan

| When | What |
| --- | --- |
| **MHacks (Oct 3–4, 2026)** | Guidance layer (this file, `MISSION.md`, `FACTORY_RULES.md`, `CLAUDE.md`) + the walking skeleton (SPEC §13). The team builds the MVP by hand with the PIV skills. |
| **After MHacks** | Validation harness → workflow runner → deployment checks → the trigger, in that order. The trigger is built last on purpose. |

## The process this encodes

The team's PIV loop, with the approvals removed. Today nobody reads the plan or the diff (interview R1.2), so every check that matters must be code.

1. `prime-codebase`: load context.
2. `piv-plan-implementation`: plan from the card (premium model).
3. `piv-implement`: execute the plan task by task.
4. `piv-validate`: `pnpm validate` plus the main journey; one PASS/FAIL.
5. `piv-review-changes`: technical review of the diff.
6. `piv-commit`: one atomic, conventional commit.
7. `piv-create-pr`: push and open the PR, with the card id in the body.

## The five components, as planned here

| # | Component | This repo's version | Status |
| --- | --- | --- | --- |
| 1 | Workflow-driven repo | Claude Code (`claude -p`) running the PIV skills | after MHacks |
| 2 | The trigger | Continuous pickup, a 5-min idle poll of the **validate.ai build board** (Claude artifact) | after MHacks |
| 3 | Deployment | Railway (`web`, `analyzer`, `postgres`); rollback = redeploy the previous deployment | skeleton |
| 4 | Guidance layer | `MISSION.md` · `FACTORY_RULES.md` · `CLAUDE.md` | **done** |
| 5 | Validation harness | HTTP driver against `/api/*`; hidden scenarios in a private sibling repo | after MHacks |

## The gates that will be code

1. **`APP_STARTED`:** emitted only when `GET /api/health` returns `{"status":"ok","db":"ok","analyzer":"ok"}`.
2. **`E2E_PASSED steps=9`:** the main journey below, against real Jev and OpenAI.
3. **The guard:** fails closed on any protected path (`FACTORY_RULES.md` §5) or a PR over 500 lines / 12 files.
4. **The product-rule checks:**
   - verbatim quotes
   - `polite < mixed < real_pain`
   - founder-only → `need_more_evidence`
   - isolation

## The end-to-end path

The single journey that gates every merge (`MISSION.md` Gate 3):

1. Health returns ok for web, db and analyzer.
2. Create the idea "WhatsApp bot that takes restaurant reservations".
3. Submit the `real_pain` reference transcript.
4. The interview shows `processing`.
5. It reaches `done` within 2 minutes.
6. The verdict is `keep_going` and the score is above 70.
7. At least one real-signal quote is verbatim in the transcript.
8. There are exactly 3 next questions.
9. The idea's history lists the interview with the same verdict.

**Required step count:** 9.
**Last deliberately broken and confirmed failing:** never (the harness is not built yet).

## Deliberate defects the checks must catch (from interview R2.5b)

The one that would hurt most: **an analysis saved under the wrong idea or founder.**

Also:
- the score formula reversed (polite counted as real)
- the confidence gate removed
- a paraphrased quote passing the verbatim check
- the verdict hardcoded to `keep_going`
- the talk ratio computed on the customer instead of the founder
- `neutral` sentences counted as polite

## The autonomy ladder

| Level | Automatic | Reached |
| --- | --- | --- |
| 1 | an accepted card produces a PR | |
| 2 | the validator runs and posts a verdict | |
| 3 | the validator auto-merges on green structural gates | |
| 4 | self-triage; the scheduled check files its own cards | |
| 5 | writes its own cards from the mission | |

**Before level 1, these must be true:**

- [ ] The walking skeleton runs locally and on Railway.
- [ ] The reference fixtures (`polite`, `mixed`, `real_pain`) are written and approved by a human.
- [ ] The validate.ai build board exists, and the runner can read and write its cards.
- [ ] `gh auth status` passes on the runner (the expired `GH_TOKEN` in `~/.archon/.env` is removed).
- [ ] The private sibling repo for hidden scenarios exists.

**Before level 3, also:**

- [ ] Where the factory runs is decided (an always-on machine).
- [ ] The escalation channel is a real command (`FACTORY_NOTIFY_CMD`).
- [ ] The main journey has been broken on purpose and seen failing.
- [ ] Every deliberate defect above is caught.

## Operating notes

- **Coding agent:** Claude Code, `claude -p`.
- **Model routing:** planning `claude-opus-5-5`; implementation, fixes and triage `claude-sonnet-5-5`.
- **Pace:** continuous pickup, a 5-min idle poll, concurrency 1.
- **Where it runs:** TBD (decide after MHacks).
- **What reaches a human:** cards in `needs-human`. The channel is TBD (decide after MHacks). Without one, the factory is unmonitored, so it must not run unattended.
- **Cost:** not measured yet. Jev is about US$0.04 per 1M input tokens; OpenAI dominates the per-analysis cost.
- **Known gotchas:**
  - The repo is **public**: hidden scenarios and real transcripts never go in it.
  - Jev is not deterministic, so the verdict averages 3 calls (SPEC §0.2).
  - Railway's `web` service builds from the repo root (SPEC §0.4).

## Incident log

Append only. Each entry is a rule that now exists because of it.

| Date | What happened | What changed as a result |
| --- | --- | --- |
