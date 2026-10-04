"""ValiDate Strategist agent. Called only by the front agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from specialists import strategist_proto  # noqa: E402

agent = make_agent("STRATEGIST", "ValiDate Strategist")
agent.include(strategist_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
