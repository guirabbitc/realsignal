"""Each specialist used directly through chat, on the real pipeline with fake Jev and writer."""
import asyncio

import specialists
from models import Judgement
from team import StageFailed

from app.pipeline.analyze import Judged
from tests.doubles import IDEA, REAL_PAIN, FakeCtx


def say(handler, ctx, text):
    return asyncio.run(handler(ctx, "founder", [text], []))


def test_intake_labels_the_turns(analyzer):
    assert "valiDate Intake" in say(specialists.intake_chat, FakeCtx(), "hi")
    reply = say(specialists.intake_chat, FakeCtx(), "Ana: Do you cook at home?\nBo: Yes, every day.")
    assert "Founder: Do you cook at home?\nCustomer: Yes, every day." in reply


def test_analyst_shows_every_customer_sentence_with_its_category(analyzer):
    ctx = FakeCtx()
    assert "Signal Analyst" in say(specialists.analyst_chat, ctx, "hello")
    say(specialists.analyst_chat, ctx, IDEA)
    reply = say(specialists.analyst_chat, ctx, REAL_PAIN)
    assert "**Verdict: Keep going**" in reply and "**Each customer sentence**" in reply
    assert "- Past pain (90% real):" in reply or "- Commitment (90% real):" in reply


def test_strategist_asks_the_analyst_agent_then_writes(analyzer, monkeypatch):
    asked = []

    async def ask(ctx, stage, address, message, expected):
        asked.append(stage)
        judged = await specialists.pipeline.judge(message.idea, message.transcript)
        return Judgement(judged=judged.model_dump(mode="json"))

    monkeypatch.setattr(specialists, "ask", ask)
    ctx = FakeCtx()
    say(specialists.strategist_chat, ctx, IDEA)
    reply = say(specialists.strategist_chat, ctx, REAL_PAIN)
    assert asked == ["Signal Analyst"]
    assert "**Ask next**" in reply and "Judged by the valiDate Signal Analyst" in reply
    assert "Verdict" not in reply  # the Strategist only writes


def test_strategist_still_answers_when_the_analyst_agent_is_down(analyzer, monkeypatch):
    async def ask(ctx, stage, address, message, expected):
        raise StageFailed("Signal Analyst did not answer")

    monkeypatch.setattr(specialists, "ask", ask)
    ctx = FakeCtx()
    say(specialists.strategist_chat, ctx, IDEA)
    reply = say(specialists.strategist_chat, ctx, REAL_PAIN)
    assert "**Ask next**" in reply and "Judged by" not in reply


def test_judged_survives_the_hop_between_agents(analyzer):
    judged = asyncio.run(specialists.pipeline.judge(IDEA, REAL_PAIN))
    assert Judged.model_validate(Judgement(judged=judged.model_dump(mode="json")).judged) == judged
