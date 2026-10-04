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

## Test

```bash
cd agents && uv run pytest                                    # offline; real pipeline, fake Jev and writer
uv run --project agents python agents/tests/smoke_chat.py     # four agents in one process: chat + REST
uv run --project agents python agents/tests/smoke_chat.py --serve --live   # a local team on port 8099, real APIs
```

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
