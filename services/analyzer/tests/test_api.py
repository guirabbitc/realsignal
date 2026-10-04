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


def test_stage_endpoints_require_the_key(client):
    assert client.post("/judge", json={"idea": IDEA, "transcript": "A: hi"}).status_code == 401
    assert client.post("/write", json={}).status_code == 401
    assert client.post("/transcribe", files={"file": ("a.mp3", b"x", "audio/mpeg")}).status_code == 401


def test_stages_chained_equal_analyze(client, schema):
    request = {"idea": IDEA, "transcript": fixture_text("real_pain")}
    whole = client.post("/analyze", json=request, headers=AUTH).json()

    judged = client.post("/judge", json=request, headers=AUTH)
    assert judged.status_code == 200
    written = client.post("/write", json={"idea": IDEA, "judged": judged.json()}, headers=AUTH)
    assert written.status_code == 200
    assert {**judged.json(), **written.json()} == whole

    for name, body in (("JudgeResponse", judged.json()), ("WriteResponse", written.json())):
        validator = Draft202012Validator({**schema["$defs"][name], "$defs": schema["$defs"]})
        assert list(validator.iter_errors(body)) == []


def test_transcribe_stage_returns_transcript(client):
    response = client.post("/transcribe", files={"file": ("a.mp3", b"x", "audio/mpeg")}, headers=AUTH)
    assert response.status_code == 200 and response.json()["transcript"].startswith("speaker_0:")
