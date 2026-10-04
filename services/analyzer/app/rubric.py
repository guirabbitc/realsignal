"""Loads rubric.json. The rubric is data: weights, thresholds, question texts, model ids (SPEC §4 rule 8)."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

RUBRIC_PATH = Path(__file__).with_name("rubric.json")


@lru_cache(maxsize=1)
def load_rubric() -> dict[str, Any]:
    return json.loads(RUBRIC_PATH.read_text())
