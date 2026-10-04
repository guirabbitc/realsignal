import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_clients
from app.pipeline import Clients
from app.pipeline.jev import FakeJudge
from app.pipeline.transcribe import FakeTranscriber
from app.pipeline.writer import FakeWriter

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
IDEA = "An app that plans a week of dinners and orders the groceries."
SECRET = "test-secret"


@pytest.fixture
def fakes() -> Clients:
    return Clients(transcriber=FakeTranscriber(), judge=FakeJudge(), writer=FakeWriter())


@pytest.fixture
def client(fakes, monkeypatch):
    """The API with fake AI clients: no test ever makes a paid call."""
    monkeypatch.setenv("ANALYZER_SECRET", SECRET)
    app.dependency_overrides[get_clients] = lambda: fakes
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def schema() -> dict:
    return json.loads((ROOT / "packages/contracts/analyze.schema.json").read_text())


def fixture_text(name: str) -> str:
    return (FIXTURES / f"{name}.txt").read_text()
