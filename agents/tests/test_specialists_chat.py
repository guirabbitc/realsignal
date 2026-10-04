"""Each specialist used directly through chat, with a fake context and a fake analyzer. No network."""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import specialists  # noqa: E402
from chat import Upload  # noqa: E402
from contracts import JudgeResponse, TranscribeResponse, WriteResponse  # noqa: E402
from models import Judged  # noqa: E402
from team import StageFailed  # noqa: E402
from tests.test_flow import IDEA, TRANSCRIPT, FakeCtx  # noqa: E402

JUDGED = JudgeResponse(
    transcript=TRANSCRIPT,
    sentences=[
        {"order": 0, "speaker": "Interviewer", "text": "How do you plan dinner?", "is_interviewee": False, "label": None, "confidence": None},
        {"order": 1, "speaker": "Priya", "text": "Last week I paid for a meal kit.", "is_interviewee": True, "label": "real_signal", "confidence": 0.97},
    ],
    score=100,
    verdict="keep_going",
)


@pytest.fixture
def analyzer(monkeypatch):
    async def judge(idea, transcript):
        return JUDGED

    async def write(idea, judged):
        return WriteResponse(summary="It shows real demand.", next_steps=["Ask for a pre-order."])

    async def transcribe(data, filename, mime_type):
        return TranscribeResponse(transcript="A: from the file")

    monkeypatch.setattr(specialists.analyzer_client, "judge", judge)
    monkeypatch.setattr(specialists.analyzer_client, "write", write)
    monkeypatch.setattr(specialists.analyzer_client, "transcribe", transcribe)


def say(handler, ctx, text=None, upload=None):
    return asyncio.run(handler(ctx, "founder", [text] if text else [], [upload] if upload else []))


def test_intake_introduces_itself(analyzer):
    assert "ValiDate Intake" in say(specialists.intake_chat, FakeCtx(), "hi")


def test_intake_returns_the_transcript_of_a_file(analyzer):
    reply = say(specialists.intake_chat, FakeCtx(), upload=Upload("application/pdf", b"%PDF"))
    assert reply == "Here is the transcript:\n\nA: from the file"


def test_analyst_asks_for_the_idea_then_shows_every_label(analyzer):
    ctx = FakeCtx()
    assert "Signal Analyst" in say(specialists.analyst_chat, ctx, "hello")
    assert "Now send me the interview" in say(specialists.analyst_chat, ctx, IDEA)
    reply = say(specialists.analyst_chat, ctx, TRANSCRIPT)
    assert "Verdict: Keep going" in reply
    assert '- Real signal (97%): "Last week I paid for a meal kit."' in reply
    assert "How do you plan dinner?" not in reply  # interviewer sentences are not judged


def test_strategist_asks_the_analyst_agent_then_writes(analyzer, monkeypatch):
    asked = []

    async def ask(ctx, stage, env_name, message, expected):
        asked.append((stage, message.idea))
        return Judged(judged=JUDGED.model_dump(mode="json"))

    monkeypatch.setattr(specialists, "ask", ask)
    ctx = FakeCtx()
    say(specialists.strategist_chat, ctx, IDEA)
    reply = say(specialists.strategist_chat, ctx, TRANSCRIPT)
    assert asked == [("Signal Analyst", IDEA)]
    assert "It shows real demand." in reply and "1. Ask for a pre-order." in reply
    assert "Judged by the ValiDate Signal Analyst" in reply


def test_strategist_still_answers_when_the_analyst_agent_is_down(analyzer, monkeypatch):
    async def ask(ctx, stage, env_name, message, expected):
        raise StageFailed("Signal Analyst did not answer")

    monkeypatch.setattr(specialists, "ask", ask)
    ctx = FakeCtx()
    say(specialists.strategist_chat, ctx, IDEA)
    reply = say(specialists.strategist_chat, ctx, TRANSCRIPT)
    assert "Next steps" in reply and "Judged by" not in reply
