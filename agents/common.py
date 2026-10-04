"""Shared setup for every agent: load the root .env, fix certificates, build the Agent."""
import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
# python.org builds of Python on macOS ship without root certificates
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from uagents import Agent, Context  # noqa: E402  (needs .env and SSL_CERT_FILE set first)


def make_agent(prefix: str, name: str, description: str) -> Agent:
    """One fixed seed and one port per agent, both from the environment.

    The description (160 characters at most on Agentverse) and the README.md next to the
    agent's file are published to Agentverse
    when the mailbox is connected through the inspector.
    """
    agent = Agent(
        name=name,
        seed=os.environ[f"{prefix}_AGENT_SEED"],
        port=int(os.environ[f"{prefix}_AGENT_PORT"]),
        mailbox=True,
        description=description,
        readme_path=str(Path(__file__).resolve().parent / prefix.lower() / "README.md"),
    )

    @agent.on_event("startup")
    async def announce(ctx: Context):
        ctx.logger.info(f"{name} address: {agent.address}")

    return agent
