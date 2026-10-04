"""The front agent's conversation, on the real pipeline with fake Jev and writer."""
import asyncio

import pytest
from chat import Upload
from front import flow
from team import StageFailed

from tests.doubles import IDEA, REAL_PAIN, FakeCtx


def say(ctx, text=None, upload=None):
    return asyncio.run(
        flow.handle_founder_input(ctx, "founder", [text] if text else [], [upload] if upload else [])
    )


def test_greeting_introduces_and_asks_for_the_idea(analyzer):
    reply = say(FakeCtx(), "hi")
    assert "valiDate" in reply and "what idea are you testing" in reply


@pytest.mark.parametrize("message", [IDEA, f"idea: {IDEA}", f"[idea: {IDEA}]", f"@validate idea: {IDEA}"])
def test_idea_in_any_form_is_saved_and_transcript_requested(analyzer, message):
    ctx = FakeCtx()
    say(ctx, "hello")
    reply = say(ctx, message)
    assert ctx.storage.get("idea:founder") == IDEA and "Now send me the interview" in reply


def test_idea_then_transcript_gives_the_read_out(analyzer):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, REAL_PAIN)
    assert "**Verdict: Keep going**" in reply and "Signal score:" in reply
    assert "**Strongest evidence**" in reply and "**Ask next**" in reply


def test_transcript_first_is_kept_until_the_idea_arrives(analyzer):
    ctx = FakeCtx()
    assert "what idea does it test" in say(ctx, REAL_PAIN)
    assert "Verdict" in say(ctx, IDEA)


def test_other_speaker_names_are_mapped_and_the_founder_is_told(analyzer):
    renamed = REAL_PAIN.replace("Founder:", "Interviewer:").replace("Customer:", "Marta:")
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, renamed)
    assert "I read Interviewer as you" in reply and "Verdict" in reply


def test_uploaded_text_file_is_analyzed_and_other_files_are_refused(analyzer):
    ctx = FakeCtx()
    say(ctx, IDEA)
    assert "Verdict" in say(ctx, upload=Upload("text/plain", REAL_PAIN.encode()))
    assert "only read text" in say(ctx, upload=Upload("application/pdf", b"%PDF"))


def test_analysis_failure_is_shown_never_a_default_verdict(analyzer):
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, "Ana: only one speaker here, twice.\nAna: still only me talking.")
    assert "could not analyze" in reply and "Verdict" not in reply


def test_specialists_down_runs_the_same_pipeline_in_the_front_agent(analyzer, monkeypatch):
    async def down(ctx, idea, text):
        raise StageFailed("Intake did not answer")

    monkeypatch.setenv("FRONT_USE_SPECIALISTS", "1")
    monkeypatch.setattr(flow, "_via_specialists", down)
    ctx = FakeCtx()
    say(ctx, IDEA)
    reply = say(ctx, REAL_PAIN)
    assert "Verdict" in reply and "Handled by" not in reply
