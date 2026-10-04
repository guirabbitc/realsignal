"""How one agent asks another for one step of the work and waits for the answer."""
import os

from uagents import Context

from models import StageError

# Per request. Kept short so an agent that is down does not stall the founder for long.
STAGE_TIMEOUT_SECONDS = 45


class StageFailed(Exception):
    pass


async def ask(ctx: Context, stage: str, env_name: str, message, expected):
    """Send one typed message to the agent whose address is in `env_name` and return its typed reply."""
    reply, status = await ctx.send_and_receive(
        os.environ[env_name], message, response_type={expected, StageError}, timeout=STAGE_TIMEOUT_SECONDS
    )
    if isinstance(reply, expected):
        return reply
    if isinstance(reply, StageError):
        raise StageFailed(f"{reply.stage} failed: {reply.error}")
    raise StageFailed(f"{stage} did not answer ({status})")
