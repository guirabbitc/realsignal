import json

import httpx

from app.contracts import Label, Sentence, Verdict
from app.pipeline import run_analysis
from app.pipeline.jev import JevJudge
from app.pipeline.scoring import compute_score
from app.pipeline.split import split_transcript
from app.pipeline.transcribe import ElevenLabsTranscriber
from tests.conftest import IDEA, fixture_text


def sentence(label, confidence, order=0):
    return Sentence(order=order, speaker="A", text="x", is_interviewee=True, label=label, confidence=confidence)


def test_fixtures_rank_polite_below_mixed_below_real_pain(fakes):
    scores = {
        name: run_analysis(IDEA, fixture_text(name), fakes).score
        for name in ("polite", "mixed", "real_pain")
    }
    assert scores["polite"] < scores["mixed"] < scores["real_pain"], scores


def test_fixture_verdicts_differ(fakes):
    polite = run_analysis(IDEA, fixture_text("polite"), fakes)
    real = run_analysis(IDEA, fixture_text("real_pain"), fakes)
    assert polite.verdict == Verdict.pivot
    assert real.verdict == Verdict.keep_going


def test_score_is_share_of_real_signal():
    assert compute_score([sentence(Label.real_signal, 1.0), sentence(Label.polite, 1.0)]) == 50.0
    assert compute_score([sentence(Label.real_signal, 1.0), sentence(Label.neutral, 1.0)]) == 66.7
    assert compute_score([]) == 0.0


def test_split_orders_sentences_and_finds_the_interviewer():
    drafts = split_transcript("Ana: How do you plan? Why?\nBo: I use a list. It works.\nstill Bo here")
    assert [d.order for d in drafts] == list(range(len(drafts)))
    assert [d.is_interviewee for d in drafts] == [False, False, True, True, True]
    assert drafts[-1].text == "still Bo here"


def test_split_without_speakers_judges_everything():
    drafts = split_transcript("I paid for it last week. It was fine.")
    assert len(drafts) == 2 and all(d.is_interviewee for d in drafts)


def test_jev_client_sends_typed_questions_and_reads_answers():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append((request, body))
        answers = {
            key: {"type": "choice", "choice": "polite", "probabilities": {"polite": 0.9}, "confidence": 0.8}
            for key in body["questions"]
        }
        if "verdict" in body["questions"]:
            answers["verdict"]["choice"] = "pivot"
        return httpx.Response(200, json={"model": "jev-latest", "answers": answers})

    judge = JevJudge("key", http=httpx.Client(transport=httpx.MockTransport(handler)))
    judgments = judge.label_sentences(IDEA, "A: x", [f"sentence {i}" for i in range(25)])

    assert len(judgments) == 25 and judgments[0].label == Label.polite and judgments[0].confidence == 0.8
    request, body = seen[0]
    assert str(request.url) == "https://api.typesafe.ai/v1/systemone"
    assert request.headers["authorization"] == "Bearer key"
    assert body["model"] == "jev-latest" and len(body["questions"]) == 20
    assert body["questions"]["s0"]["type"] == "choice"
    assert set(body["questions"]["s0"]["criteria"]) == {"real_signal", "polite", "neutral"}
    assert len(seen) == 2  # 25 sentences are sent in two batches

    assert judge.pick_verdict(IDEA, [sentence(Label.polite, 0.8)], 0.0) == Verdict.pivot
    assert set(seen[-1][1]["questions"]["verdict"]["criteria"]) == {v.value for v in Verdict}


def test_elevenlabs_client_groups_words_into_speaker_turns():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["xi-api-key"] == "key"
        assert b"scribe_v2" in request.content and b'name="diarize"' in request.content
        return httpx.Response(
            200,
            json={
                "text": "Hi there. Hello.",
                "words": [
                    {"text": "Hi", "type": "word", "speaker_id": "speaker_0"},
                    {"text": " ", "type": "spacing", "speaker_id": "speaker_0"},
                    {"text": "there.", "type": "word", "speaker_id": "speaker_0"},
                    {"text": "(laughs)", "type": "audio_event", "speaker_id": "speaker_0"},
                    {"text": "Hello.", "type": "word", "speaker_id": "speaker_1"},
                ],
            },
        )

    transcriber = ElevenLabsTranscriber("key", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert transcriber.transcribe(b"audio", "call.mp3", "audio/mpeg") == "speaker_0: Hi there.\nspeaker_1: Hello."
