"""Stand-ins for Jev, OpenAI and the uAgents context. No network, no paid calls.

The Jev and writer doubles are the analyzer's own (services/analyzer/tests/conftest.py), fed with the
human labels of its fixtures, so the agents are tested against the same reference interviews.
"""
import importlib.util
import logging
from pathlib import Path

import pipeline
import pytest

from app.pipeline.jev import Judge
from app.rubric import load_rubric

ANALYZER = Path(__file__).resolve().parents[2] / "services" / "analyzer"
_spec = importlib.util.spec_from_file_location("analyzer_doubles", ANALYZER / "tests" / "conftest.py")
analyzer_doubles = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(analyzer_doubles)

IDEA = "WhatsApp bot that takes restaurant reservations"
REAL_PAIN = (ANALYZER / "fixtures" / "real_pain.txt").read_text()
POLITE = (ANALYZER / "fixtures" / "polite.txt").read_text()


def fake_services(name: str = "real_pain"):
    judge = Judge(analyzer_doubles.labelled_jev_for(name), load_rubric())
    return judge, analyzer_doubles.ScriptedWriter()


class FakeStorage:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value


class FakeCtx:
    def __init__(self):
        self.storage = FakeStorage()
        self.logger = logging.getLogger("test")


@pytest.fixture
def analyzer(monkeypatch):
    """The real pipeline with fake Jev and writer."""
    monkeypatch.setattr(pipeline, "services", lambda: fake_services("real_pain"))
    monkeypatch.setenv("FRONT_USE_SPECIALISTS", "0")
    for role in ("front", "intake", "analyst", "strategist"):
        monkeypatch.setenv(f"AGENT_SEED_{role.upper()}", f"test-seed-{role}")
