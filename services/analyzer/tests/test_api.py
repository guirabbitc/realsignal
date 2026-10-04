from jsonschema import Draft202012Validator

from tests.conftest import IDEA, SECRET, fixture_text

AUTH = {"X-Analyzer-Key": SECRET}


def test_health_is_open(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_rejects_missing_key(client):
    response = client.post("/analyze", json={"idea": IDEA, "transcript": "A: hi"})
    assert response.status_code == 401


def test_analyze_rejects_wrong_key(client):
    response = client.post(
        "/analyze", json={"idea": IDEA, "transcript": "A: hi"}, headers={"X-Analyzer-Key": "nope"}
    )
    assert response.status_code == 401


def test_analyze_rejects_body_outside_contract(client):
    response = client.post("/analyze", json={"idea": IDEA}, headers=AUTH)
    assert response.status_code == 422


def test_analyze_response_matches_contract(client, schema):
    response = client.post(
        "/analyze", json={"idea": IDEA, "transcript": fixture_text("mixed")}, headers=AUTH
    )
    assert response.status_code == 200
    validator = Draft202012Validator({**schema["$defs"]["AnalyzeResponse"], "$defs": schema["$defs"]})
    assert list(validator.iter_errors(response.json())) == []


def test_interviewer_sentences_are_not_judged(client):
    body = client.post(
        "/analyze", json={"idea": IDEA, "transcript": fixture_text("mixed")}, headers=AUTH
    ).json()
    interviewer = [s for s in body["sentences"] if not s["is_interviewee"]]
    assert interviewer and all(s["speaker"] == "Interviewer" for s in interviewer)
    assert all(s["label"] is None and s["confidence"] is None for s in interviewer)
    assert all(s["label"] is not None for s in body["sentences"] if s["is_interviewee"])


def test_analyze_accepts_audio_as_multipart(client):
    response = client.post(
        "/analyze",
        data={"idea": IDEA},
        files={"file": ("call.mp3", b"not real audio", "audio/mpeg")},
        headers=AUTH,
    )
    assert response.status_code == 200
    assert response.json()["transcript"].startswith("speaker_0:")
