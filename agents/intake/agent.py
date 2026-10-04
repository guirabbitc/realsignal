"""ValiDate Intake agent. Called only by the front agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import make_agent  # noqa: E402
from specialists import intake_proto  # noqa: E402

DESCRIPTION = (
    "Part of the ValiDate team. Turns what a founder sends (pasted text, a PDF or a recording) into a clean customer interview transcript with speaker labels. Called by the ValiDate front agent."
)

agent = make_agent("INTAKE", "ValiDate Intake", DESCRIPTION)
agent.include(intake_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
