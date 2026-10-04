"""Real Signal front agent: the only agent the founder talks to in ASI:One."""
import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
# python.org builds of Python on macOS ship without root certificates
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from chat_proto import chat_proto  # noqa: E402  (needs .env and SSL_CERT_FILE set first)
from uagents import Agent, Context  # noqa: E402

AGENT_NAME = "Real Signal"
AGENT_SEED = os.environ["FRONT_AGENT_SEED"]
PORT = int(os.getenv("FRONT_AGENT_PORT", "8001"))

agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    mailbox=True,
)

agent.include(chat_proto, publish_manifest=True)


@agent.on_event("startup")
async def announce(ctx: Context):
    ctx.logger.info(f"{AGENT_NAME} front agent address: {agent.address}")


if __name__ == "__main__":
    agent.run()
