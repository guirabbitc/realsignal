"""Local smoke test of the whole agent path: no Agentverse account, no paid calls.

Runs the front agent and the three specialists in one process on the real pipeline with fake Jev and
writer, then plays a founder twice: over the Chat Protocol (as ASI:One does) and over the front
agent's REST /chat endpoint (as the web app does).

    uv run --project agents python agents/tests/smoke_chat.py           # run the checks and exit
    uv run --project agents python agents/tests/smoke_chat.py --serve   # keep the team up on port 8099,
                                                                        # for trying the web chat locally
    (add --live to either to use the real Jev and OpenAI from agents/.env: paid, small)
"""
import asyncio
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents"))

ROLES = ("front", "intake", "analyst", "strategist")
for role in ROLES:
    os.environ[f"AGENT_SEED_{role.upper()}"] = f"validate-smoke-{role}"
os.environ["FRONT_USE_SPECIALISTS"] = "1"
os.environ["AGENT_CHAT_KEY"] = "smoke-key"
PORT = 8099

import common
import pipeline
from front.agent import WebChatRequest, WebChatResponse, web_chat
from front.chat_proto import chat_proto
from specialists import (
    analyst_chat_proto,
    analyst_proto,
    intake_chat_proto,
    intake_proto,
    strategist_chat_proto,
    strategist_proto,
)
from uagents import Agent, Bureau, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from tests.doubles import IDEA, REAL_PAIN, fake_services

SERVE, LIVE = "--serve" in sys.argv, "--live" in sys.argv
if not LIVE:
    pipeline.services = lambda: fake_services("real_pain")

front = Agent(name="front-smoke", seed=common.seed_of("front"))
front.include(chat_proto)
front.on_rest_post("/chat", WebChatRequest, WebChatResponse)(web_chat)
team = [front]
for role, proto, chat in (
    ("intake", intake_proto, intake_chat_proto),
    ("analyst", analyst_proto, analyst_chat_proto),
    ("strategist", strategist_proto, strategist_chat_proto),
):
    member = Agent(name=f"{role}-smoke", seed=common.seed_of(role))
    member.include(proto)
    member.include(chat)
    team.append(member)

client = Agent(name="client-smoke", seed="validate-smoke-client")
client_proto = Protocol(spec=chat_protocol_spec)
DONE = "Handled by the valiDate team"
SESSION = f"smoke-{uuid4().hex}"  # agent storage outlives a run, so each run is a new founder


def chat_message(*content) -> ChatMessage:
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=list(content))


def rest(text: str) -> dict:
    body = json.dumps({"key": "smoke-key", "session": SESSION, "text": text}).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/chat", data=body, headers={"content-type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


async def check_rest() -> bool:
    loop = asyncio.get_running_loop()
    intro = await loop.run_in_executor(None, rest, "hi")
    await loop.run_in_executor(None, rest, IDEA)
    verdict = await loop.run_in_executor(None, rest, REAL_PAIN)
    print(f"REST reply:\n{verdict['reply'][:400]}\n", flush=True)
    return "what idea are you testing" in intro["reply"] and DONE in verdict["reply"] and verdict["ok"]


@client.on_event("startup")
async def say_hi(ctx: Context):
    await ctx.send(front.address, chat_message(StartSessionContent(type="start-session"), TextContent(type="text", text="hi")))


@client_proto.on_message(ChatMessage)
async def on_reply(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if not isinstance(item, TextContent):
            continue
        if "One sentence is enough" in item.text and "Got" not in item.text:
            await ctx.send(front.address, chat_message(TextContent(type="text", text=IDEA)))
        elif "Now send me the interview" in item.text:
            await ctx.send(front.address, chat_message(TextContent(type="text", text=REAL_PAIN)))
        elif DONE in item.text:
            print(f"CHAT reply:\n{item.text[:400]}\n", flush=True)
            passed = await check_rest()
            print("PASS" if passed else "FAIL (rest)", flush=True)
            os._exit(0 if passed else 1)
        else:
            print(f"FAIL (chat): {item.text[:300]}", flush=True)
            os._exit(1)


@client_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


client.include(client_proto)

if __name__ == "__main__":
    bureau = Bureau(port=PORT)
    for member in team if SERVE else (*team, client):
        bureau.add(member)
    bureau.run()
