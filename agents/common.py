"""Shared setup for every agent: load agents/.env, fix certificates, build the Agent."""
import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
# python.org builds of Python on macOS ship without root certificates
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from uagents import Agent, Context
from uagents_core.identity import Identity

# One port per local agent.
PORTS = {"front": 8001, "intake": 8002, "analyst": 8003, "strategist": 8004}


def seed_of(role: str) -> str:
    """One fixed seed per agent, from the environment. The address is derived from it, so never change it."""
    return os.environ[f"AGENT_SEED_{role.upper()}"]


def address_of(role: str) -> str:
    return Identity.from_seed(seed_of(role), 0).address


def make_agent(role: str, name: str, description: str) -> Agent:
    """The description (160 characters at most on Agentverse) and the README.md next to the
    agent's file are published to Agentverse when the mailbox is connected through the inspector."""
    agent = Agent(
        name=name,
        seed=seed_of(role),
        port=int(os.getenv(f"AGENT_PORT_{role.upper()}", PORTS[role])),
        mailbox=True,
        description=description,
        readme_path=str(HERE / role / "README.md"),
    )

    @agent.on_event("startup")
    async def announce(ctx: Context):
        ctx.logger.info(f"{name} address: {agent.address}")

    return agent
