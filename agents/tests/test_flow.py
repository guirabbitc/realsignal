"""The front agent's conversation, with a fake context and a fake analyzer. No network."""
import asyncio
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts import AnalyzeResponse  # noqa: E402
from front import flow  # noqa: E402

TRANSCRIPT = "Interviewer: How do you plan dinner?\nPriya: Last week I paid for a meal kit."
IDEA = "An app that plans a week of dinners and orders the groceries."


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
def calls(monkeypatch):
    seen = []

    async def fake_analyze(idea, transcript):
        seen.append((idea, transcript))
        return AnalyzeResponse(
            transcript=transcript, sentences=[], score=50, verdict="narrow_down",
            summary="Summary.", next_steps=["Step one."],
        )

    async def fake_analyze_file(idea, data, filename, mime_type):
        seen.append((idea, mime_type, len(data)))
        return AnalyzeResponse(
            transcript="from file", sentences=[], score=50, verdict="narrow_down",
            summary="Summary.", next_steps=["Step one."],
        )

    monkeypatch.setattr(flow.analyzer_client, "analyze", fake_analyze)
    monkeypatch.setattr(flow.analyzer_client, "analyze_audio", fake_analyze_file)
    monkeypatch.setenv("FRONT_USE_SPECIALISTS", "0")
    return seen


def say(ctx, text=None, upload=None):
    return asyncio.run(
        flow.handle_founder_input(ctx, "founder", [text] if text else [], [upload] if upload else [])
    )


def test_greeting_introduces_and_asks_for_the_idea(calls):
    reply = say(FakeCtx(), "hi")
    assert "ValiDate" in reply and "what idea are you testing" in reply


@pytest.mark.parametrize(
    "message",
    [
        IDEA,
        f"idea: {IDEA}",
        f"[idea: {IDEA}]",
        f"@validate idea: {IDEA}",
        f"My idea is {IDEA}",
    ],
)
def test_idea_in_any_form_is_saved_and_transcript_requested(calls, message):
    ctx = FakeCtx()
    say(ctx, "hello")
    reply = say(ctx, message)
    assert ctx.storage.get("idea:founder") == IDEA
    assert "Now send me the interview" in reply and not calls


def test_idea_then_transcript_gives_a_verdict(calls):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, TRANSCRIPT)
    assert "Verdict: Narrow down" in reply and calls == [(IDEA, TRANSCRIPT)]


def test_transcript_first_is_kept_until_the_idea_arrives(calls):
    ctx = FakeCtx()
    reply = say(ctx, TRANSCRIPT)
    assert "what idea does it test" in reply and not calls
    reply = say(ctx, IDEA)
    assert "Verdict" in reply and calls == [(IDEA, TRANSCRIPT)]


def test_uploaded_text_file_is_analyzed(calls):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, upload=flow.Upload("text/plain", TRANSCRIPT.encode()))
    assert "Verdict" in reply and calls == [(IDEA, TRANSCRIPT)]


def test_small_talk_after_the_idea_does_not_replace_it(calls):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, "thanks")
    assert ctx.storage.get("idea:founder") == IDEA and "I have your idea" in reply


def test_new_idea_replaces_the_old_one(calls):
    ctx = FakeCtx()
    say(ctx, IDEA)
    say(ctx, "new idea: A tool that books dog walkers")
    assert ctx.storage.get("idea:founder") == "A tool that books dog walkers"


def test_specialists_down_falls_back_to_the_analyzer(calls, monkeypatch):
    async def down(ctx, idea, transcript, audio):
        raise flow.StageFailed("Intake did not answer")

    monkeypatch.setenv("FRONT_USE_SPECIALISTS", "1")
    monkeypatch.setattr(flow, "_via_specialists", down)
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, TRANSCRIPT)
    assert "Verdict" in reply and "Handled by" not in reply and calls == [(IDEA, TRANSCRIPT)]


def test_pdf_upload_is_sent_to_the_analyzer_as_a_file(calls):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, upload=flow.Upload("application/pdf", b"%PDF-1.4 fake"))
    assert "Verdict" in reply and calls == [(IDEA, "application/pdf", 13)]


def test_pdf_sent_before_the_idea_is_kept(calls):
    ctx = FakeCtx()
    reply = say(ctx, upload=flow.Upload("application/pdf", b"%PDF-1.4 fake"))
    assert "what idea does it test" in reply and not calls
    reply = say(ctx, IDEA)
    assert "Verdict" in reply and calls == [(IDEA, "application/pdf", 13)]
