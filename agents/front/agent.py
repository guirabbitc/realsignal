"""ValiDate front agent: the only agent the founder talks to in ASI:One."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from front.chat_proto import chat_proto  # noqa: E402

DESCRIPTION = (
    "Reads a customer interview and finds evidence of real demand: labels each sentence, scores it, and says keep going, narrow down, try a new angle or pivot."
)

agent = make_agent("FRONT", "ValiDate", DESCRIPTION)
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
