"""Local smoke test of the whole agent path, with no Agentverse account and no paid calls.

Starts the analyzer with fake AI clients, runs the front agent (and the specialists) in one
process, and plays a founder: says hi, gives the idea, sends a fixture transcript, and expects a verdict.

    uv run --project agents python agents/tests/smoke_chat.py direct
    uv run --project agents python agents/tests/smoke_chat.py specialists

File uploads are not covered here; test those in ASI:One.
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents"))

MODE = sys.argv[1] if len(sys.argv) > 1 else "direct"
ANALYZER_PORT = 8765
os.environ["ANALYZER_URL"] = f"http://127.0.0.1:{ANALYZER_PORT}"
os.environ["ANALYZER_SECRET"] = "smoke-secret"
os.environ["FRONT_USE_SPECIALISTS"] = "1" if MODE == "specialists" else "0"

import common  # noqa: E402,F401  (certificates; .env does not override the values above)
from front.chat_proto import chat_proto  # noqa: E402
from specialists import analyst_proto, intake_proto, strategist_proto  # noqa: E402
from uagents import Agent, Bureau, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

IDEA = "An app that plans a week of dinners and orders the groceries."
TRANSCRIPT = (ROOT / "services/analyzer/fixtures/real_pain.txt").read_text()

front = Agent(name="front-smoke", seed="realsignal-smoke-front")
front.include(chat_proto)

specialists = []
for prefix, proto in (("INTAKE", intake_proto), ("ANALYST", analyst_proto), ("STRATEGIST", strategist_proto)):
    agent = Agent(name=f"{prefix.lower()}-smoke", seed=f"realsignal-smoke-{prefix.lower()}")
    agent.include(proto)
    os.environ[f"{prefix}_AGENT_ADDRESS"] = agent.address
    specialists.append(agent)

client = Agent(name="client-smoke", seed="realsignal-smoke-client")
client_proto = Protocol(spec=chat_protocol_spec)


def chat(*content) -> ChatMessage:
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=list(content))


def finish(code: int) -> None:
    analyzer.terminate()
    os._exit(code)


@client.on_event("startup")
async def say_hi(ctx: Context):
    await ctx.send(front.address, chat(StartSessionContent(type="start-session"), TextContent(type="text", text="hi")))


@client_proto.on_message(ChatMessage)
async def on_reply(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if not isinstance(item, TextContent):
            continue
        print(f"REPLY:\n{item.text}\n", flush=True)
        if "what idea are you testing" in item.text:
            await ctx.send(front.address, chat(TextContent(type="text", text=IDEA)))
        elif "Now send me the interview" in item.text:
            await ctx.send(front.address, chat(TextContent(type="text", text=TRANSCRIPT)))
        elif "Verdict" in item.text:
            print(f"PASS ({MODE})", flush=True)
            finish(0)
        else:
            print(f"FAIL ({MODE})", flush=True)
            finish(1)


@client_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


client.include(client_proto)


def start_analyzer() -> subprocess.Popen:
    env = {**os.environ, "ANALYZER_FAKE_CLIENTS": "1"}
    process = subprocess.Popen(
        ["uv", "run", "--quiet", "uvicorn", "app.main:app", "--port", str(ANALYZER_PORT), "--log-level", "warning"],
        cwd=ROOT / "services/analyzer",
        env=env,
    )
    for _ in range(60):
        try:
            if httpx.get(f"{os.environ['ANALYZER_URL']}/health", timeout=1).status_code == 200:
                return process
        except httpx.HTTPError:
            time.sleep(0.5)
    process.terminate()
    raise SystemExit("Analyzer did not start")


if __name__ == "__main__":
    analyzer = start_analyzer()
    bureau = Bureau(port=8099)
    for agent in (front, *specialists, client):
        bureau.add(agent)
    bureau.run()
