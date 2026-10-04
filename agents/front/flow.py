"""What the front agent does with a founder's message: collect the idea and the interview,
get it analyzed, and reply. It plans the steps and calls others; it judges nothing itself."""
import os

import pipeline
from chat import Upload
from common import address_of
from conversation import converse
from labels import prepare_transcript
from models import IntakeRequest, Judgement, JudgeTranscript, TranscriptReady, WriteUp, Written
from render import render_analysis
from team import StageFailed, ask
from uagents import Context

from app.models import AnalyzeResult

TEAM_TRACE = "_Handled by the valiDate team: Intake → Signal Analyst → Strategist_"
AFTER_VERDICT = "Send another interview for the same idea, or write `new idea: ...` to test a different one."

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


async def _analyze(ctx: Context, idea: str, text: str) -> str:
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
    return f"{note}{render_analysis(result)}{trace}\n\n{AFTER_VERDICT}"


async def handle_founder_input(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=INTRO, finish=_analyze)
