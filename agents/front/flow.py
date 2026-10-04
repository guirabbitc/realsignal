"""What the front agent does with a founder's message: collect the idea and the interview,
get it analyzed, and reply. It plans the steps and calls others; it judges nothing itself."""
import os
from uuid import uuid4

import payments
import pipeline
from cards import ANOTHER, BREAKDOWN, CANCEL, NEW_IDEA, read_action, result_card, unlock_card
from chat import Reply, Upload
from common import address_of
from conversation import ASK_TRANSCRIPT, converse, idea_key
from labels import prepare_transcript
from models import IntakeRequest, Judgement, JudgeTranscript, TranscriptReady, WriteUp, Written
from render import render_analysis, render_judged
from team import StageFailed, ask
from uagents import Context

from app.models import AnalyzeResult

TEAM_TRACE = "_Handled by the valiDate team: Intake → Signal Analyst → Strategist_"
AFTER_VERDICT = (
    "Send another interview for the same idea, or write `new idea: ...` to test a different one. "
    "Write `breakdown` to see every customer sentence with its judgment."
)
NEXT_IDEA = "What idea are you testing next? One sentence is enough."
NO_INTERVIEW_YET = "I have no interview to break down yet. Send me one first."
NOT_CHARGED = "No problem, nothing was charged."
PAID_IN_ASI_ONE = "The sentence-by-sentence breakdown is a paid extra. You can unlock it by talking to valiDate in ASI:One."

INTRO = (
    "Hi, I'm valiDate. I read a customer interview and tell you how much real interest is in "
    "it: what the customer actually did, paid for or committed to, as opposed to polite compliments.\n\n"
    "First, what idea are you testing? One sentence is enough."
)


def use_specialists() -> bool:
    return os.getenv("FRONT_USE_SPECIALISTS", "") == "1"


async def _via_specialists(ctx: Context, idea: str, text: str) -> tuple[AnalyzeResult, str]:
    ready = await ask(ctx, "Intake", address_of("intake"), IntakeRequest(text=text), TranscriptReady)
    judged = await ask(
        ctx, "Signal Analyst", address_of("analyst"),
        JudgeTranscript(idea=idea, transcript=ready.transcript), Judgement,
    )
    written = await ask(
        ctx, "Strategist", address_of("strategist"),
        WriteUp(idea=idea, transcript=ready.transcript, judged=judged.judged), Written,
    )
    return AnalyzeResult.model_validate(written.result), ready.note


async def _direct(idea: str, text: str) -> tuple[AnalyzeResult, str]:
    transcript, note = prepare_transcript(text)
    return await pipeline.analyze(idea, transcript), note


def _breakdown_key(sender: str) -> str:
    return f"breakdown:{sender}"


async def paid_breakdown(ctx: Context, sender: str, reference: str) -> str | None:
    """Called by the payment protocol once a transfer is verified: the breakdown that was paid for."""
    saved = ctx.storage.get(_breakdown_key(sender))
    if not saved or saved["id"] != reference:
        return None
    ctx.storage.set(_breakdown_key(sender), {**saved, "paid": True})
    return saved["text"]


async def _on_action(ctx: Context, sender: str, action: str) -> str:
    """A click on one of the cards' buttons."""
    ctx.logger.info(f"Card action: {action} (payments {'on' if payments.enabled() else 'off'})")
    idea = ctx.storage.get(idea_key(sender))
    if action == ANOTHER:
        return f'I have your idea: "{idea}"\n\n{ASK_TRANSCRIPT}' if idea else INTRO
    if action == NEW_IDEA:
        ctx.storage.set(idea_key(sender), None)
        return NEXT_IDEA
    if action == CANCEL:
        return f"{NOT_CHARGED} {AFTER_VERDICT}"

    saved = ctx.storage.get(_breakdown_key(sender))
    if not saved:
        return NO_INTERVIEW_YET
    if saved["paid"] or not payments.enabled():
        return saved["text"]
    # Only an agent can answer a payment request; the web chat's founder is not one.
    if not sender.startswith("agent1"):
        return PAID_IN_ASI_ONE
    price = payments.price()
    if action == BREAKDOWN:
        return Reply(
            f"The breakdown of all {saved['sentences']} customer sentences costs {price} FET on the Fetch testnet.",
            "review",
            unlock_card(price, saved["sentences"]),
        )
    await payments.request(ctx, sender, saved["id"], "valiDate: sentence-by-sentence breakdown of one interview")
    return (
        f"I sent you a payment request for {price} FET on the Fetch testnet. "
        "As soon as the transfer is confirmed on the ledger, the breakdown arrives here."
    )


async def _analyze(ctx: Context, sender: str, idea: str, text: str) -> str:
    trace = ""
    if use_specialists():
        try:
            result, note = await _via_specialists(ctx, idea, text)
            trace = f"\n\n{TEAM_TRACE}"
            ctx.logger.info("Answered through the specialists")
        except StageFailed as ex:
            # The same analysis, run by the front agent itself. Never a default verdict.
            ctx.logger.warning(f"Specialists unavailable ({ex}); running the pipeline here")
            result, note = await _direct(idea, text)
    else:
        result, note = await _direct(idea, text)
    note = f"_{note}_\n\n" if note else ""
    ctx.storage.set(
        _breakdown_key(sender),
        {"id": uuid4().hex, "text": render_judged(result), "sentences": len(result.statements), "paid": False},
    )
    return Reply(f"{note}{render_analysis(result)}{trace}\n\n{AFTER_VERDICT}", "custom", result_card(result))


async def handle_founder_input(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    action = None if uploads else read_action(texts)
    if action:
        return await _on_action(ctx, sender, action)

    async def finish(ctx: Context, idea: str, transcript: str) -> str:
        return await _analyze(ctx, sender, idea, transcript)

    return await converse(ctx, sender, texts, uploads, intro=INTRO, finish=finish)
