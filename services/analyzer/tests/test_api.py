import pytest
from fastapi.testclient import TestClient

from app import main
from tests.conftest import ScriptedWriter, labelled_jev_for, load_fixture


@pytest.fixture
def client(monkeypatch, make_judge):
    monkeypatch.setenv("ANALYZER_KEY", "test-key")
    main.get_services.cache_clear()
    monkeypatch.setattr(main, "get_services", lambda: (make_judge(labelled_jev_for("real_pain")), ScriptedWriter()))
    return TestClient(main.app)


def body(transcript):
    return {"idea": "WhatsApp bot that takes restaurant reservations", "transcript": transcript, "kind": "interview"}


def test_health_ok_when_configured(client, monkeypatch):
    for name in ("TYPESAFE_API_KEY", "OPENAI_API_KEY", "OPENAI_MODEL"):
        monkeypatch.setenv(name, "set")
    assert client.get("/health").json() == {"status": "ok"}


def test_health_reports_missing_config_names_only(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    r = client.get("/health")
    assert r.status_code == 503 and "TYPESAFE_API_KEY" in r.json()["missing_config"]
    assert "sk-secret-value" not in r.text


def test_missing_or_wrong_key_is_401(client):
    assert client.post("/analyze", json=body("Customer: hi.")).json()["error"]["code"] == "bad_key"
    r = client.post("/analyze", json=body("Customer: hi."), headers={"X-Analyzer-Key": "nope"})
    assert r.status_code == 401


def test_unlabelled_transcript_is_422(client):
    r = client.post("/analyze", json=body("no labels here"), headers={"X-Analyzer-Key": "test-key"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unlabelled_transcript"


def test_too_long_is_422(client):
    r = client.post("/analyze", json=body("Customer: " + "a" * 80001), headers={"X-Analyzer-Key": "test-key"})
    assert r.json()["error"]["code"] == "transcript_too_long"


def test_invalid_body_is_422(client):
    r = client.post("/analyze", json={"idea": "x"}, headers={"X-Analyzer-Key": "test-key"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_analyze_ok(client):
    transcript, _ = load_fixture("real_pain")
    r = client.post("/analyze", json=body(transcript), headers={"X-Analyzer-Key": "test-key"})
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] == "keep_going" and data["score"] > 70 and len(data["next_questions"]) == 3


def test_transcript_never_reaches_the_logs(client, caplog):
    transcript, _ = load_fixture("real_pain")
    with caplog.at_level("DEBUG"):
        client.post("/analyze", json=body(transcript), headers={"X-Analyzer-Key": "test-key"})
    assert "900 dollars" not in caplog.text and "Honestly" not in caplog.text
