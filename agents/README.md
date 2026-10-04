# agents/: valiDate on Fetch.ai

Four uAgents that expose the analysis in ASI:One and in the web app's chat. They import the analyzer's pipeline (`services/analyzer`) directly and hold no analysis logic of their own.

| Agent | File | Port | What it runs |
| --- | --- | --- | --- |
| valiDate (front) | `front/agent.py` | 8001 | The conversation; plans the steps and calls the others |
| Intake | `intake/agent.py` | 8002 | Speaker labels → `Founder:` / `Customer:` (`labels.py`) |
| Signal Analyst | `analyst/agent.py` | 8003 | `judge_interview`: split, Jev, score, gate, verdict |
| Strategist | `strategist/agent.py` | 8004 | `write_readout`: OpenAI, verify |

The front agent chains them with `ctx.send_and_receive` when `FRONT_USE_SPECIALISTS=1`. If one does not answer in 45 s, it runs the same pipeline itself; there is never a default verdict. Every specialist also speaks the Chat Protocol, so each can be used on its own in ASI:One.

## Run

```bash
cp ../.env.example .env          # keep the agents section; fill in the keys
uv run --project agents python agents/scripts/gen_seeds.py   # fills the seeds, prints the addresses
uv run --project agents python agents/run_team.py            # all four, one terminal; Ctrl+C stops them
```

The first time, open each agent's inspector link from the log and choose Connect → Mailbox. Each agent's `README.md` and description are published to Agentverse at that moment.

## The web chat

The web app's "Chat with the agents" page posts to `/api/agent-chat`, which calls the front agent's REST endpoint `POST /chat` with `AGENT_CHAT_KEY`. It is the same conversation as in ASI:One, so it goes through the same specialists.

The same chat is also a small window on every other page (`components/chat/ChatWidget.tsx`), opened with the "Ask the agents" button at the bottom right. Set `NEXT_PUBLIC_AGENT_PROFILE_URL` to the front agent's Agentverse page to show a link to it in the window.

That endpoint is served on the front agent's own port, not through the Agentverse mailbox. The web app must be able to reach it: set `AGENT_URL` in `apps/web/.env` (`http://localhost:8001` locally). A web app deployed on Railway cannot reach an agent on a laptop without a tunnel.

## Cards and payment (front agent, in ASI:One)

- **Interactive cards.** The verdict comes with an ASI:One card (`cards.py`): the verdict, the score, the strongest quote, and three buttons: every sentence judged, another interview, a new idea. The text reply stays complete, so the web chat and any client that cannot show cards lose nothing.
- **Payment Protocol.** The verdict and read-out are free. The sentence-by-sentence breakdown is the paid extra (`payments.py`): a review card shows the price, then the agent sends a `RequestPayment` for a direct FET transfer on the Fetch testnet. On `CommitPayment` it reads the transaction from the ledger and only then sends `CompletePayment` and the breakdown; otherwise `CancelPayment` with the reason. One transaction unlocks one breakdown, once.
- **Switch.** Set `PAYMENT_FET_AMOUNT` (for example `0.1`) in `agents/.env` to turn payments on. Unset, the breakdown is free. The web chat cannot pay, so with payments on it points to ASI:One.

## Deploy (Railway)

The team runs as the `agents` service in the `validate-ai` project, at `https://agents-production-6673.up.railway.app` (public domain on port 8001, the front agent; `/chat` refuses requests without `AGENT_CHAT_KEY`). It is public because uAgents binds `0.0.0.0` only and Railway's private network may be IPv6-only.

- **Deploy by upload, not from GitHub.** A service built from the repo root would pick up the web service's root `railway.json`, and Railway no longer accepts a custom config path for a new service. Upload a folder holding only `agents/`, `services/analyzer/` and `agents/Dockerfile` at its root:
  ```bash
  rm -rf /tmp/agents-upload && mkdir -p /tmp/agents-upload
  git archive HEAD agents services/analyzer | tar -x -C /tmp/agents-upload
  cp /tmp/agents-upload/agents/Dockerfile /tmp/agents-upload/Dockerfile
  railway up /tmp/agents-upload --path-as-root --service agents --environment production --ci
  ```
- **Variables on `agents`:** the four `AGENT_SEED_*` (the addresses come from them; never change them), `FRONT_USE_SPECIALISTS=1`, `AGENT_CHAT_KEY`, and `TYPESAFE_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL` as references to the analyzer service (`${{analyzer.…}}`).
- **Variables on `web`:** `AGENT_URL` (the URL above) and `AGENT_CHAT_KEY=${{agents.AGENT_CHAT_KEY}}`.
- **One process per seed.** While the Railway team runs, do not run the same seeds on a laptop: both would read the same mailboxes.

## Test

```bash
cd agents && uv run pytest                                    # offline; real pipeline, fake Jev and writer
uv run --project agents python agents/tests/smoke_chat.py     # four agents in one process: chat + REST
uv run --project agents python agents/tests/smoke_chat.py --serve --live   # a local team on port 8099, real APIs
```

## Measure accuracy with the tester agent

`tester/agent.py` is a fifth agent (port 8005) that plays a founder. For every case it chats with the front agent, which runs the whole team, and asks the Signal Analyst for its judgment of each sentence; then it scores both against an answer key.

1. Give `tester/generate_cases_prompt.md` to another LLM. It returns 30 synthetic interviews with an answer key, 10 per reply, as JSON.
2. Save each reply as a file in `tester/cases/`.
3. With the team running: `uv run --project agents python agents/tester/agent.py`. The first time, connect its mailbox from the inspector link and run it again.

The report gives verdict accuracy (exact, and within the key's allowed set), category accuracy (exact, and by group: real / polite / none), founder-flag accuracy, and every disagreement. It also lists broken cases, where the key expects a verdict from an interview too thin to pass the analyzer's gate. `--local` runs the same scoring on the pipeline directly, without agents, which is much faster while tuning. Reports are saved in `tester/results/` (git-ignored).

## Files

| File | What |
| --- | --- |
| `chat.py` | Chat Protocol factory, adapted from Fetch's openai-agent `chat_proto.py` |
| `conversation.py` | Ask for the idea, then for the interview. Logs lengths only, never transcript text. |
| `pipeline.py` | The only place the agents touch the analysis |
| `labels.py` | Speaker-label mapping; mirrors `apps/web/components/upload/checks.ts` |
| `specialists.py` | Each specialist's typed protocol and chat handler |
| `team.py` | Ask another agent and wait for its typed reply |
| `render.py` | Reply text (presentation only) |
| `models.py` | Agent-to-agent messages |
