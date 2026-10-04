import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.doubles import analyzer  # noqa: F401  (fixture)
