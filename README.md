# Real Signal

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

Real Signal reads a customer interview, separates real demand from politeness, and tells the founder what to do next: keep going, narrow down, try a new angle, or pivot. Every verdict cites the sentences behind it.

It measures evidence of real demand. It does not judge whether anyone is lying.

## How it works

1. The founder uploads an interview (transcript or recording) and the idea it tests.
2. The analyzer transcribes it, splits it into sentences, and labels each interviewee sentence as real signal, polite or neutral, with a confidence.
3. A demand score is computed from those labels, a verdict is chosen, and a summary with next steps is written.

There are two ways in: the web app, and a team of agents in ASI:One (built for the Fetch.ai ASI:One Agent Challenge at MHacks 2026). Both use the same analyzer.

## Agents

| Agent | Role | Address |
| --- | --- | --- |
| Real Signal (front) | The agent you talk to in ASI:One. Chat Protocol, file uploads. Plans the steps and calls the others. | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| Intake | Turns a recording into a transcript with speaker labels | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| Signal Analyst | Labels each sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| Strategist | Writes the summary and next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |

## Run it locally

You need Node 20+, [pnpm](https://pnpm.io), [uv](https://docs.astral.sh/uv/), Python 3.12 and Docker (only for the local database).

```bash
cp .env.example .env
```

Fill in `.env`: set `ANALYZER_SECRET` (`openssl rand -hex 32`). To try everything without API keys, set `ANALYZER_FAKE_CLIENTS=1`; results are then produced by keyword rules, not real analysis. For real analysis, leave it empty and set `ELEVENLABS_API_KEY`, `JEV_API_KEY` and `OPENAI_API_KEY`.

### 1. Postgres

```bash
docker compose up -d --wait
pnpm install
pnpm db:migrate
```

### 2. Analyzer (port 8000)

```bash
cd services/analyzer
uv run uvicorn app.main:app --port 8000
```

`curl localhost:8000/health` shows whether it runs in `live` or `fake` mode.

### 3. Web app (port 3000)

```bash
pnpm dev:web
```

Open http://localhost:3000, enter an idea, and paste or upload an interview. Sample transcripts are in `services/analyzer/fixtures/`.

### 4. Agents (optional, for ASI:One)

```bash
uv run --project agents python agents/scripts/gen_seeds.py   # fills seeds and addresses in .env
uv run --project agents python agents/front/agent.py
```

On first start, open the "Agent inspector" link in the log and choose **Connect → Mailbox**. In ASI:One, message the agent: first `idea: <your idea>`, then paste the transcript or upload it as a `.txt` file.

To run the full team, start `agents/intake/agent.py`, `agents/analyst/agent.py` and `agents/strategist/agent.py` the same way, connect each mailbox, and set `FRONT_USE_SPECIALISTS=1`.

## Tests

```bash
cd services/analyzer && uv run pytest     # offline, no paid API calls
pnpm contracts:check                      # generated types match the contract
pnpm -r build && pnpm typecheck
uv run --project agents python agents/tests/smoke_chat.py specialists
```

See [UPDATE.md](UPDATE.md) for the current state and [CLAUDE.md](CLAUDE.md) for the rules the code follows.
