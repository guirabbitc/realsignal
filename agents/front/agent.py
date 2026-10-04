"""valiDate front agent: the only agent the founder talks to, in ASI:One and in the web app's chat."""
import hmac
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent
from front.chat_proto import chat_proto
from front.flow import handle_founder_input
from uagents import Context, Model

DESCRIPTION = (
    "Reads a customer interview and finds evidence of real demand: labels each sentence, scores it, and says keep going, narrow down, try a new angle or pivot."
)

agent = make_agent("front", "valiDate", DESCRIPTION)
agent.include(chat_proto, publish_manifest=True)


class WebChatRequest(Model):
    key: str
    session: str
    text: str


class WebChatResponse(Model):
    ok: bool
    reply: str


@agent.on_rest_post("/chat", WebChatRequest, WebChatResponse)
async def web_chat(ctx: Context, req: WebChatRequest) -> WebChatResponse:
    """The web app's chat. Same conversation as ASI:One, so it goes through the same specialists.

    Served on this agent's own port, not through the mailbox: the web app must be able to reach it.
    The shared key is in the body because REST handlers do not see request headers.
    """
    expected = os.environ.get("AGENT_CHAT_KEY", "")
    if not expected or not hmac.compare_digest(req.key.encode(), expected.encode()):
        return WebChatResponse(ok=False, reply="bad_key")
    reply = await handle_founder_input(ctx, f"web:{req.session}", [req.text], [])
    return WebChatResponse(ok=True, reply=reply)


if __name__ == "__main__":
    agent.run()
