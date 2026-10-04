"""Local smoke test: a fake client says "hi" to the front agent's chat protocol.

Runs both agents in one process, so no mailbox or Agentverse account is needed.
File uploads are not covered here; test those in ASI:One.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import certifi

# python.org builds of Python on macOS ship without root certificates
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents" / "front"))

from chat_proto import chat_proto  # noqa: E402
from uagents import Agent, Bureau, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

front = Agent(name="front-smoke", seed="realsignal-smoke-front")
front.include(chat_proto)

client = Agent(name="client-smoke", seed="realsignal-smoke-client")
client_proto = Protocol(spec=chat_protocol_spec)


@client.on_event("startup")
async def say_hi(ctx: Context):
    await ctx.send(
        front.address,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                StartSessionContent(type="start-session"),
                TextContent(type="text", text="hi"),
            ],
        ),
    )


@client_proto.on_message(ChatMessage)
async def on_reply(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            print(f"REPLY: {item.text}", flush=True)
            os._exit(0 if "You said" in item.text else 1)
        else:
            print(f"GOT: {item}", flush=True)


@client_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print("ACK received", flush=True)


client.include(client_proto)

if __name__ == "__main__":
    bureau = Bureau(port=8099)
    bureau.add(front)
    bureau.add(client)
    bureau.run()
