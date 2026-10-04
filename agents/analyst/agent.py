"""ValiDate Signal Analyst agent. Called by the front agent, and usable on its own in ASI:One."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from specialists import analyst_chat_proto, analyst_proto  # noqa: E402

DESCRIPTION = (
    "ValiDate team: labels each interview sentence as real signal, polite or neutral, scores the evidence of real demand and picks a verdict."
)

agent = make_agent("ANALYST", "ValiDate Signal Analyst", DESCRIPTION)
agent.include(analyst_proto, publish_manifest=True)
agent.include(analyst_chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
