"""ValiDate Signal Analyst agent. Called only by the front agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from specialists import analyst_proto  # noqa: E402

DESCRIPTION = (
    "Part of the ValiDate team. Labels each interviewee sentence in a customer interview as real signal, polite or neutral, scores the evidence of real demand, and picks a verdict. Called by the ValiDate front agent."
)

agent = make_agent("ANALYST", "ValiDate Signal Analyst", DESCRIPTION)
agent.include(analyst_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
