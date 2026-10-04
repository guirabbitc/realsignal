# Real Signal

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

A team of agents that reads a customer-interview transcript, separates real demand from politeness, and tells the founder what to do next: keep going, narrow down, try a new angle, or pivot. Built for the Fetch.ai ASI:One Agent Challenge at MHacks 2026.

Real Signal measures evidence of real demand. It does not judge whether anyone is lying.

## Agents

| Agent | Role | Address | Status |
| --- | --- | --- | --- |
| Real Signal (front) | The agent you talk to in ASI:One. Chat Protocol, file uploads. | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` | Running (hello-world) |
| Intake | Transcribes audio, labels speakers | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` | Planned |
| Signal Analyst | Tags and scores each quote | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` | Planned |
| Market Check | Web search on claims, competitors, prices | `agent1qd0tg2yr8kxutsgm2lanazj7e65z9f6md5ta0gggncnyxyw4ma0q26lsd26` | Planned |
| Pivot Strategist | Patterns across interviews, next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` | Planned |

## Run it

Requires Python 3.10 to 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # or get the team .env to use the addresses above
python scripts/gen_seeds.py   # fills in seeds and addresses, keeps existing ones

python scripts/smoke_chat.py  # local check, prints the agent's reply to "hi"
python agents/front/agent.py  # starts the front agent on port 8001
```

On first start, open the "Agent inspector" link printed in the log and choose **Connect → Mailbox**. The agent is then reachable from ASI:One by its address.

See [UPDATE.md](UPDATE.md) for the project structure, conventions and current state.
