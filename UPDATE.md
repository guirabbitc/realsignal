# Real Signal: project state and handoff

Read this first if you (or your coding agent) are new to the repo. It says what exists, how to run it, the rules we code by, and what to build next. Keep it current: add a changelog entry whenever the code changes.

Last updated: 2026-10-03, end of Phase 0 scaffolding.

## What we are building

Real Signal, for the Fetch.ai ASI:One Agent Challenge at MHacks 2026. A founder opens ASI:One, pastes or uploads a customer-interview transcript, and in one conversation gets a scored verdict, the quotes behind it and a concrete next step. It must act like an agent that does things, not a chatbot: the track rejects simple chatbots and API wrappers.

Two source documents drive the work:

- **Build workflow** ("Real Signal — MHacks Build Workflow"): the hackathon plan, with seven phases, each with a "done when".
- **Board artifact** (Real Signal Board): the wider product overview.

**Rule: when they differ, the build workflow wins, and the difference is reported to Murilo.** Exceptions are listed under "Decisions and deviations".

## State

| Phase | Status |
| --- | --- |
| 0. Prove the pipe | Code done. Waiting on the manual check in ASI:One (see "Next"). |
| 1. Demo data and rubric | Not started. Can run in parallel with Phase 0. |
| 2. Brain v1, offline | Not started |
| 3. MVP end to end (tag `mvp`) | Not started |
| 4. Go multi-agent | Not started |
| 5. Actions and Fetch extras | Not started |
| 6. Freeze and submit | Not started |

Verified so far:

- `scripts/smoke_chat.py` passes: a local client sends "hi", the front agent acknowledges, sends the `{"attachments": "true"}` metadata, and replies `Real Signal is alive. You said: "hi"`.
- `agents/front/agent.py` starts on port 8001, publishes the `AgentChatProtocol` manifest and registers on the Almanac API.

Not verified yet: the mailbox connection, a chat from inside ASI:One, and a file upload. The download path (`ExternalStorage`) has never run against a real upload.

## Structure

```
realsignal/
├── README.md             Public face: run steps, agent name/address table, Innovation Lab badge (all required for submission)
├── UPDATE.md             This file
├── requirements.txt      uagents 0.26.0, uagents-core 0.4.11, python-dotenv, certifi
├── .env.example          Every variable, no values. Committed.
├── .env                  Seeds, addresses, ports, API keys. Git-ignored. Never commit.
├── models.py             Shared message classes for agent-to-agent messages. Empty until Phase 4; holds the agreed vocabulary as comments.
├── agents/
│   └── front/
│       ├── agent.py      Front agent: loads .env, Agent(seed, port 8001, mailbox=True), includes chat_proto
│       └── chat_proto.py Chat Protocol handlers: ack, session start, text, file download
├── brain/                Framework-agnostic logic as plain Python functions. Empty until Phase 2 (analyze(transcript) -> JSON).
├── fixtures/             The 3 mock interview transcripts and the scoring rubric. Empty until Phase 1.
└── scripts/
    ├── gen_seeds.py      Creates .env if missing, fills one fixed seed and derived address per agent. Safe to rerun: keeps existing seeds.
    └── smoke_chat.py     Local test of the chat handler, both agents in one process. No Agentverse needed. Does not cover uploads.
```

Specialist agents will live in `agents/intake/`, `agents/analyst/`, `agents/market/` and `agents/strategist/` (Phase 4), each with its own `agent.py`.

## How to run

Python 3.10 to 3.12.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && python scripts/gen_seeds.py
python scripts/smoke_chat.py     # expect: REPLY: Real Signal is alive. You said: "hi"
python agents/front/agent.py
```

Then open the "Agent inspector" link from the log and choose Connect → Mailbox.

Three things to know:

- **Seeds decide addresses.** `gen_seeds.py` on a fresh `.env` creates new seeds, so new addresses. The addresses in the README come from Murilo's `.env`. To run those same agents, get that `.env` from Murilo privately.
- **One machine per seed.** Two machines running the same seed compete for one mailbox. Agree who runs the front agent before a demo. For solo development, use your own seeds.
- **Certificates on macOS.** `agent.py` and `smoke_chat.py` set `SSL_CERT_FILE` to certifi's bundle, because python.org builds of Python otherwise fail with `CERTIFICATE_VERIFY_FAILED`. Keep those two lines above the `uagents` imports in any new agent.

Expected and harmless in the log: "I do not have enough funds to register on Almanac contract". The Almanac API registration is the one we need, and it succeeds.

## Conventions (binding)

From the build workflow. Each one copies a working Fetch example in `fetchai/uAgent-Examples`.

| Rule | Why | Copy from |
| --- | --- | --- |
| The front agent's chat handling comes from the deployed openai-agent | It already handles uploads | `6-deployed-agents/knowledge-base/openai-agent/chat_proto.py` |
| Orchestrate with `ctx.send_and_receive`, and check each reply with `isinstance` | Steps run in order with no manual bookkeeping | `6-deployed-agents/chained/blog-creator-agent` |
| One shared `models.py` with every message class | Every agent sends and expects the same fields | blog-creator-agent |
| A fixed seed per agent, in the git-ignored `.env` with the addresses | A new seed breaks the README and routing | |
| `mailbox=True`, and a separate port per local agent (8001 to 8005) | Current way to reach Agentverse; two agents can't share a port | |
| Interview history lives in `ctx.storage`, never in Python globals | Storage survives restarts | hosted-agent example |
| Brain code is plain Python in `brain/`, with no uagents imports | It must work unchanged in any framework | |
| Python adds up every score | Jev is unreliable at counting | |

Do not:

- Copy anything about Agentverse or ASI:One from the examples repo's `5-documentation/guides/agents` folder. It targets uagents 0.17, the old `mailbox="KEY@…"` format and DeltaV.
- Use the experimental `ChatAgent` for the front agent. It ignores uploads and cuts replies at 1,024 tokens.
- Pass `endpoint=` together with `mailbox=True`.
- Write "lie detector" anywhere. We measure evidence of real demand, never whether someone is lying.
- Break `mvp` once it is tagged. New work goes on a branch and merges only after the full ASI:One flow still works.

## Decisions and deviations

| Topic | Board artifact | Build workflow | What we do |
| --- | --- | --- | --- |
| Stack | Next.js, TypeScript, Postgres, Railway | Python uAgents, `ctx.storage` | **Workflow.** The web app is a Phase 5 bonus that calls the front agent's REST endpoint. |
| Verdicts | keep going, narrow down, try a new angle, pivot | keep going, pivot, stop | **Artifact** (Murilo's decision). Four verdicts everywhere, including the Jev verdict choice. |
| Quote labels | real signal, politeness, neutral, with confidence | compliment, hypothetical, past behavior, commitment | **Both** (Murilo's decision). The category drives the weighted score; the signal label and confidence are what the founder sees. |

Proposed roll-up from category to signal label, to confirm in Phase 2: past behavior and commitment → real signal; compliment and hypothetical → politeness; unclear or mid-range probability → neutral; confidence = Jev's yes/no probability.

How `chat_proto.py` differs from Fetch's template: the LLM call (`get_completion`) is replaced by a fixed reply, and a downloaded file is base64-decoded and summarised (mime type, size, first 200 characters). Everything else is unchanged. In Phase 3, that reply is where `brain.analyze(...)` gets called.

## Next

1. **Finish Phase 0 (manual, needs Agentverse and ASI:One accounts; code `MHACKS26MHACKSAV` gives the free month):** connect the mailbox from the inspector link, give the agent a name and description on Agentverse, then in ASI:One send it "hi" and upload a small `.txt`. Done when both get a reply. If the upload fails, the fallback is pasted text, which already works.
2. **Phase 1:** three mock interviews for one fake startup (polite, real pain with a commitment, mixed) as text files in `fixtures/`, plus the scoring rubric as a JSON schema with a weight per category.
3. **Phase 2:** `analyze(transcript) -> JSON` in `brain/`. The LLM extracts the statements and writes the reasons, Jev makes every judgment, Python adds up the score. Done when the three fixtures rank polite < mixed < real pain on 3 runs in a row.
4. Keys still needed: `LLM_API_KEY` and `JEV_API_KEY` in `.env`.

## Changelog

- **2026-10-03** Phase 0 scaffold: project layout, pinned dependencies, `.env` handling with `gen_seeds.py`, hello-world front agent with Chat Protocol and upload handling, local smoke test, README, this file.
