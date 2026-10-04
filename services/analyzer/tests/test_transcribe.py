"""POST /transcribe and the turn builder. ElevenLabs is replaced by httpx.MockTransport (no network);
the real-API round trip is the opt-in E2E."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.errors import AudioTooLarge
from app.pipeline import transcribe as scribe
from app.pipeline.split import split_transcript
from app.pipeline.transcribe import build_turns, suggest_founder, summarize_speakers, to_result

AUDIO = Path(__file__).parent / "recordings" / "audio"
SCRIBE_OK = json.loads((AUDIO / "synthetic.scribe.json").read_text())
EXAMPLE = json.loads((AUDIO / "example.transcribe.json").read_text())
KEY = {"X-Analyzer-Key": "test-key"}


def word(text, speaker, kind="word", start=None, end=None):
    return {"text": text, "type": kind, "speaker_id": speaker, "start": start, "end": end}


class FakeScribe:
    """Answers each call with the next scripted response; records what was sent and the temp dir's files."""

    def __init__(self, tmp_dir: Path):
        self.tmp_dir = tmp_dir
        self.responses: list = [httpx.Response(200, json=SCRIBE_OK)]
        self.requests: list[httpx.Request] = []
        self.files_during_call: list[list[Path]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        self.files_during_call.append(list(self.tmp_dir.iterdir()))
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    def body(self, index=0) -> str:
        return self.requests[index].content.decode("latin-1")


@pytest.fixture
def fake(monkeypatch, tmp_path):
    monkeypatch.setenv("ANALYZER_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key")
    monkeypatch.setenv("AUDIO_TMP_DIR", str(tmp_path))
    monkeypatch.delenv("ELEVENLABS_STT_MODEL", raising=False)
    monkeypatch.delenv("AUDIO_MAX_MB", raising=False)
    monkeypatch.setattr(scribe, "RETRY_DELAY_S", 0)
    fake = FakeScribe(tmp_path)
    monkeypatch.setattr(scribe, "make_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(fake)))
    return fake


@pytest.fixture
def client(fake):
    return TestClient(main.app)


def post(client, data=b"fake-m4a-bytes", name="maria interview.m4a", num_speakers="2", headers=KEY):
    fields = {"num_speakers": num_speakers} if num_speakers is not None else {}
    return client.post("/transcribe", files={"file": (name, data, "audio/mp4")}, data=fields, headers=headers)


# --- turn builder (pure) ---


def test_turns_from_the_scribe_response_match_the_committed_example():
    result = to_result(SCRIBE_OK, "scribe_v2")
    assert result.model_dump() == EXAMPLE
    assert [t.speaker_id for t in result.turns] == ["speaker_0", "speaker_1"] * 3 + ["speaker_0"]
    assert result.duration_s == 18.9 and result.language_code == "eng"


def test_audio_events_are_dropped_and_whitespace_collapsed():
    result = to_result(SCRIBE_OK, "scribe_v2")
    assert all("laughter" not in t.text for t in result.turns)
    assert result.turns[2].text == "Honestly it's a mess. I pay someone $300 a month to do it by hand."


def test_word_and_spacing_text_is_kept_exactly():
    turns = build_turns([word("I'd", "a"), word("  \n", "a", "spacing"), word("pay—maybe", "a"),
                         word(" ", "a", "spacing"), word("$1,200/mo.", "a")])
    assert [t.text for t in turns] == ["I'd pay—maybe $1,200/mo."]


def test_spacing_between_voices_never_starts_a_turn_and_empty_turns_are_dropped():
    turns = build_turns([
        word("Hi.", "speaker_0", start=0.0, end=0.5),
        word(" ", "speaker_1", "spacing"),
        word("(cough)", "speaker_1", "audio_event"),
        word(" ", "speaker_0", "spacing"),
        word("Hello?", "speaker_1", start=1.0, end=1.5),
    ])
    assert [(t.speaker_id, t.text, t.start, t.end) for t in turns] == [
        ("speaker_0", "Hi.", 0.0, 0.5), ("speaker_1", "Hello?", 1.0, 1.5)]


def test_a_word_without_a_speaker_continues_the_current_turn():
    turns = build_turns([word("So", "speaker_0"), word(" ", None, "spacing"), word("yes.", None),
                         word(" ", "speaker_1", "spacing"), word("Right.", "speaker_1")])
    assert [(t.speaker_id, t.text) for t in turns] == [("speaker_0", "So yes."), ("speaker_1", "Right.")]


def test_unlabelled_words_before_any_voice_get_their_own_voice_never_a_real_one():
    turns = build_turns([word("Um", None), word(" ", None, "spacing"), word("Okay.", "speaker_0")])
    assert [t.speaker_id for t in turns] == [scribe.UNKNOWN_SPEAKER, "speaker_0"]


def test_speakers_are_summarized_in_speaking_order_with_samples_cut_at_200_chars():
    long = "word " * 80
    turns = build_turns([word("Hi?", "speaker_1", start=0, end=1), word(" ", "speaker_1", "spacing"),
                         word(long, "speaker_0", start=1, end=4), word(" ", "speaker_0", "spacing"),
                         word("Two?", "speaker_1", start=4, end=5), word(" ", "speaker_1", "spacing"),
                         word("Three.", "speaker_0", start=5, end=6), word(" ", "speaker_0", "spacing"),
                         word("Four.", "speaker_1", start=6, end=7)])
    first, second = summarize_speakers(turns)
    assert (first.id, second.id) == ("speaker_1", "speaker_0")
    assert (first.turns, first.words, first.seconds, first.sample) == (3, 3, 3.0, ["Hi?", "Two?"])
    assert len(second.sample[0]) <= 200 and second.sample[1] == "Three."


def test_founder_suggestion_is_the_voice_asking_most_questions():
    assert to_result(SCRIBE_OK, "scribe_v2").suggested_founder_id == "speaker_1"  # speaks second, asks


def test_founder_suggestion_tie_goes_to_whoever_spoke_first():
    turns = build_turns([word("Hi.", "speaker_0"), word(" ", "speaker_0", "spacing"), word("Hey.", "speaker_1")])
    assert suggest_founder(turns, summarize_speakers(turns)) == "speaker_0"


def test_one_voice_is_reported_as_one_voice():
    result = to_result({"words": [word("Just", "speaker_0"), word(" ", "speaker_0", "spacing"),
                                  word("me.", "speaker_0")]}, "scribe_v2")
    assert [s.id for s in result.speakers] == ["speaker_0"] and result.suggested_founder_id == "speaker_0"


def test_the_example_transcript_parses_with_the_expected_turns():
    split = split_transcript((AUDIO / "example.transcript.txt").read_text(), 80000)
    speakers = [t.speaker for t in split.turns]
    assert (speakers.count("founder"), speakers.count("customer")) == (3, 4)


# --- POST /transcribe ---


def test_returns_voices_and_turns_and_sends_the_agreed_fields(client, fake):
    r = post(client)
    assert r.status_code == 200 and r.json() == EXAMPLE
    body = fake.body()
    assert fake.requests[0].headers["xi-api-key"] == "el-test-key"
    for name, value in scribe.scribe_fields("scribe_v2", 2).items():
        assert f'name="{name}"\r\n\r\n{value}\r\n' in body
    assert 'name="diarize"\r\n\r\ntrue' in body and 'name="tag_audio_events"\r\n\r\nfalse' in body
    for never in ("detect_speaker_roles", "no_verbatim", "keyterms", "webhook", "transcript_edit", "entity"):
        assert f'name="{never}' not in body
    assert 'filename="audio.m4a"' in body and "maria" not in body


def test_model_and_speaker_count_come_from_config_and_form(client, fake, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_STT_MODEL", "scribe_v9")
    r = post(client, num_speakers="3")
    assert 'name="num_speakers"\r\n\r\n3' in fake.body() and 'name="model_id"\r\n\r\nscribe_v9' in fake.body()
    assert r.json()["model"] == "scribe_v9"


def test_default_speaker_count_is_two(client, fake):
    post(client, num_speakers=None)
    assert 'name="num_speakers"\r\n\r\n2' in fake.body()


def test_missing_or_wrong_key_is_401(client, fake):
    assert post(client, headers={}).json()["error"]["code"] == "bad_key"
    assert post(client, headers={"X-Analyzer-Key": "nope"}).status_code == 401
    assert fake.requests == []


def test_without_an_elevenlabs_key_it_says_not_configured(client, fake, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY")
    r = post(client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "transcription_not_configured"


def test_too_big_is_413_before_calling_elevenlabs(client, fake, monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_MAX_MB", "1")
    r = post(client, data=b"x" * (1024 * 1024 + 1))
    assert r.status_code == 413 and r.json()["error"]["code"] == "audio_too_large"
    assert fake.requests == [] and list(tmp_path.iterdir()) == []


def test_too_big_is_caught_while_reading_and_leaves_no_file(fake, tmp_path):
    class Upload:
        def __init__(self):
            self.chunks = [b"x" * 1024 * 1024, b"x"]

        async def read(self, size):
            return self.chunks.pop(0) if self.chunks else b""

    with pytest.raises(AudioTooLarge):
        asyncio.run(main._spool(Upload(), ".mp3", 1024 * 1024))
    assert list(tmp_path.iterdir()) == []


def test_empty_file_is_422(client, fake):
    r = post(client, data=b"")
    assert r.status_code == 422 and r.json()["error"]["code"] == "empty_audio"
    assert fake.requests == []


@pytest.mark.parametrize("name,num", [("notes.txt", "2"), ("call.m4a", "5"), ("call.m4a", "0"), ("call.m4a", "two")])
def test_wrong_type_or_speaker_count_is_422(client, fake, name, num):
    r = post(client, name=name, num_speakers=num)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"
    assert fake.requests == []


def test_no_file_field_is_422(client, fake):
    r = client.post("/transcribe", data={"num_speakers": "2"}, headers=KEY)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_no_speech_is_an_error_never_an_empty_transcript(client, fake):
    fake.responses = [httpx.Response(200, json={"language_code": "eng", "text": "", "words": []})]
    r = post(client)
    assert r.status_code == 422 and r.json()["error"]["code"] == "no_speech"


def test_a_5xx_is_retried_once_then_fails_clearly(client, fake):
    fake.responses = [httpx.Response(503), httpx.Response(500)]
    r = post(client)
    assert len(fake.requests) == 2 and r.status_code == 502
    assert r.json()["error"] == {"code": "transcription_failed", "message": "Transcription failed (upstream_error).",
                                 "reason": "upstream_error"}


def test_a_429_is_retried_and_can_still_succeed(client, fake):
    fake.responses = [httpx.Response(429), httpx.Response(200, json=SCRIBE_OK)]
    r = post(client)
    assert len(fake.requests) == 2 and r.status_code == 200 and len(r.json()["turns"]) == 7


def test_a_timeout_is_retried_then_504(client, fake):
    fake.responses = [httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow")]
    r = post(client)
    assert len(fake.requests) == 2
    assert r.status_code == 504 and r.json()["error"]["reason"] == "timeout"


def test_no_retry_when_the_budget_could_not_cover_it(client, fake, monkeypatch):
    monkeypatch.setattr(scribe, "BUDGET_S", scribe.MIN_RETRY_S - 1)
    fake.responses = [httpx.Response(503)]
    assert post(client).json()["error"]["reason"] == "upstream_error"
    assert len(fake.requests) == 1


def test_a_request_elevenlabs_rejects_is_not_retried_and_its_message_not_echoed(client, fake):
    fake.responses = [httpx.Response(401, json={"detail": {"message": "invalid api key"}})]
    r = post(client)
    assert len(fake.requests) == 1
    assert r.status_code == 502 and r.json()["error"]["reason"] == "rejected"
    assert "invalid api key" not in r.text


def test_audio_elevenlabs_cannot_decode_is_422(client, fake):
    fake.responses = [httpx.Response(400, json={"detail": {"message": "Could not decode the audio file"}})]
    r = post(client)
    assert len(fake.requests) == 1
    assert r.status_code == 422 and r.json()["error"]["code"] == "empty_audio"


def test_a_non_json_200_is_a_failure_not_a_transcript(client, fake):
    fake.responses = [httpx.Response(200, text="<html>oops"), httpx.Response(200, text="<html>oops")]
    assert post(client).json()["error"]["code"] == "transcription_failed"


@pytest.mark.parametrize("responses", [
    [httpx.Response(200, json=SCRIBE_OK)],
    [httpx.Response(500), httpx.Response(500)],
    [httpx.Response(200, json={"words": []})],
])
def test_the_temp_audio_file_exists_only_during_the_call(client, fake, tmp_path, responses):
    fake.responses = responses
    post(client)
    assert fake.files_during_call and all(len(files) == 1 for files in fake.files_during_call)
    assert list(tmp_path.iterdir()) == []


def test_logs_never_contain_transcript_text_the_file_name_or_keys(client, fake, caplog):
    caplog.set_level("DEBUG")
    assert post(client).status_code == 200
    fake.responses = [httpx.Response(500), httpx.Response(500)]
    post(client)
    assert "transcribe ok" in caplog.text and "transcribe failed" in caplog.text
    for secret in ("reservations", "comped", "$300", "Honestly", "maria", "el-test-key"):
        assert secret not in caplog.text
