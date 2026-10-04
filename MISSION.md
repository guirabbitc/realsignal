# Mission

<!-- Owner: humans only. On the protected list; the factory cannot edit this file. -->

**Derived from:** [`docs/PRD.md`](docs/PRD.md) (engineering decisions: [`docs/SPEC.md`](docs/SPEC.md))
**Last reconciled with that PRD:** 2026-10-04

## What validate.ai is

validate.ai is an AI coach for customer interviews. A founder pastes the transcript of a discovery interview or demo. validate.ai judges every sentence the customer said as a real signal of interest or as politeness, turns those judgments into a 0–100 signal score, and gives one verdict: keep going, narrow down, try a new angle, pivot, or not enough evidence yet. It quotes the exact words behind the verdict, points out the founder's own interviewing mistakes, and suggests the next 3 questions to ask. Across interviews it keeps a history per idea, so the founder can see whether the evidence is getting stronger.

**Design assumptions:**
- One founder per browser, with no accounts in the MVP.
- English only.
- Transcripts are labelled `Founder:` / `Customer:`.
- One deployment on Railway.

The judgment is made by a calibrated model, the explanation is written by a separate model, and the score is plain arithmetic. These three jobs never mix.

## Who it is for

- First-time and student founders who have just finished a customer interview or demo and want to know what was real, so they can decide what to do next before building for months.

validate.ai is not a research repository (Dovetail), a sales-call analyser (Gong), or a meeting note-taker (Otter).

## Core capabilities (in scope)

The factory may accept work in these areas.

**Ideas and intake**
- Create and list ideas (one sentence: what, and for whom).
- Submit a speaker-labelled transcript (paste or `.txt`), marked as an interview or a demo, with an interviewee label.

**Analysis**
- Per-sentence judgment of every customer sentence: category and real-signal probability.
- Signal score, verdict, and the confidence gate.
- The read-out: verdict reasons, top real quotes, top polite quotes, founder mistakes (talk time, pitching early, leading questions), the next 3 questions.

**History**
- The interviews for an idea, with their verdicts, in one view.

**Chat access (hackathon)**
- The same analysis from ASI:One through a Fetch.ai uAgent.

**Quality of the above**
- Bug fixes, performance, accessibility, error states, loading states, tests, and docs for anything listed here.

## Out of scope (the factory must never build this)

Work asking for any of these is rejected at triage, even when it is popular, well argued and easy to build. This is the permanent list. Anything merely deferred is in the backlog section below, not here.

**Judging people**
- Hiring, employee-performance, dating, or any use where the person interviewed is the one being evaluated. validate.ai judges statements about a product, never the person.

**Covert analysis**
- Analysing a conversation recorded or uploaded without the interviewee knowing it was recorded.

**Data use**
- Selling, sharing or training on founders' interview data.

**Verdicts without evidence**
- Telling a founder their idea is good or bad without quoting the words behind it.

**Inferring traits**
- Inferring emotions, personality or protected traits about the interviewee.

## Backlog: not now, but not never

These are **not** out of scope. Triage marks them **deferred** (a human decides when), never rejected:

- audio and video upload, in-browser recording, call bots
- voice tone or facial expression analysis
- accounts and login
- payments, subscriptions, accelerator licences, cohort dashboard
- cross-interview report, next-interview script, follow-up email draft
- sending email; calendar or CRM integrations
- mobile app; languages other than English

## Hard invariants (not tunable by any work item)

These are properties that define validate.ai. No work item can change them, however good its reason; changing one takes a human commit.

1. **A founder only ever sees their own ideas and interviews.** The founder identity comes only from the signed session cookie, and every query is scoped by it. Leaking one founder's interview to another is the worst failure this product can have.
2. **Every quote shown to a founder appears word for word in the transcript.** A paraphrase presented as a quote is a fabrication.
3. **No verdict without evidence, and the confidence gate is never skipped.** `need_more_evidence` is set only by the gate. Thin evidence always produces it, never a guessed verdict.
4. **Jev judges, OpenAI writes, Python counts.** The writer never sets or changes a label, a probability, the score or the verdict, and its text never contradicts them.
5. **There is never a default or fallback verdict.** If the judgment fails, the analysis fails visibly.
6. **No secrets or transcript text in logs or in the repository.**
7. **The factory cannot modify governance files.** `MISSION.md`, `FACTORY_RULES.md`, `CLAUDE.md` and `FACTORY.md` are the constitution. A change touching any of them is an automatic reject.

*Invariants 1–6 came from the PRD and the team brief. Invariant 7 was added because the factory runs unattended.*

## Allowed evolutions

Explicitly in scope, so the factory does not reject them as drift:

- Better wording and presentation of the read-out (subject to human review of tone, below).
- Performance of the analyzer within the rubric's concurrency setting.
- More test coverage, more recorded fixtures for unit tests, better error messages.

## Definition of done

Every change the factory ships clears all three gates.

**Gate 1: static checks and tests pass.** `pnpm validate` (lint, typecheck, Vitest, pytest with recorded responses, contract test).

**Gate 2: the product rules hold.**
- Every quote is verbatim.
- `polite < mixed < real_pain` on the reference interviews.
- A founder-only transcript gives `need_more_evidence`.
- Founder B cannot read founder A's data.

**Gate 3: the main journey passes as a real founder would take it.**

1. Health: `GET /api/health` returns `{"status":"ok","db":"ok","analyzer":"ok"}`.
2. Create the idea "WhatsApp bot that takes restaurant reservations".
3. Submit the `real_pain` reference transcript for it.
4. The interview shows `processing`.
5. The interview reaches `done` within 2 minutes.
6. The verdict is `keep_going` with a score above 70.
7. At least one real-signal quote exists word for word in the transcript.
8. The read-out has exactly 3 next questions.
9. The idea's history lists the interview with the same verdict.

This runs on every change that touches runnable code, including changes that "seem unrelated".

## Non-goals

validate.ai is explicitly not trying to be a general transcription tool, a research repository, a sales-intelligence product, or a platform with a public API.

When in doubt, the answer is "that is out of scope."

## Open questions: decisions nobody has made yet

These are undecided, not forbidden. **The factory may propose an answer to any of them**, build against it, and record what it assumed. The merge is then held for a human. See `FACTORY_RULES.md` §7.

- **Q1** Which OpenAI model writes the read-out (`OPENAI_MODEL`)?
- **Q2** What founder-mistake thresholds apply (talk ratio, pitched early, leading questions)? Proposed 0.5 each.
- **Q3** Does upload require a consent confirmation ("the interviewee knew this was recorded")?
- **Q4** Is there a per-browser daily analysis cap, and at what number?
- **Q5** Where does the ASI:One agent run during judging?
- **Q6** How is "the founder changed their questions or idea" measured?

**Except these, which do stop the factory.** They are on the irreversible list (`FACTORY_RULES.md` §7.3):

- anything about identity, the session cookie, or who may see whose data
- migrating, deleting or changing the shape of stored data
- changing the rubric (weights, thresholds, Jev model version, question texts) or the analyzer contract

Once a question is answered, it moves to `.factory/decisions.md` with its answer and date. **A decision is asked once.**

## What the factory does NOT own (permanently human)

A green gate means the layer a machine can check is intact. It never means the product is good. These are reviewed by a person, on purpose, permanently:

- the tone and wording of the read-out
- the look of the UI
- whether the advice actually helps founders
- the demo
- the ASI:One chat experience

The factory owns the analysis pipeline, the API, the data model and isolation, the gate and the scoring: the layer whose correctness can be asserted. Most of the risk lives there.
