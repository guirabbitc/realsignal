"""ValiDate Strategist agent. Called by the front agent, and usable on its own in ASI:One."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from specialists import strategist_chat_proto, strategist_proto  # noqa: E402

DESCRIPTION = (
    "ValiDate team: turns a judged customer interview into a summary that cites the evidence, plus concrete next steps for the founder."
)

agent = make_agent("STRATEGIST", "ValiDate Strategist", DESCRIPTION)
agent.include(strategist_proto, publish_manifest=True)
agent.include(strategist_chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
