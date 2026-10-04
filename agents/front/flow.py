"""What the front agent does with a founder's message: collect the idea and the interview,
get it analyzed, and reply. It plans the steps and calls others; it judges nothing itself."""
import base64
import os

from uagents import Context

import analyzer_client
from chat import Upload
from contracts import AnalyzeResponse, JudgeResponse, WriteResponse
from conversation import converse
from models import IntakeRequest, Judged, JudgeTranscript, TranscriptReady, WriteUp, Written
from render import render_analysis
from team import StageFailed, ask

TEAM_TRACE = "_Handled by the ValiDate team: Intake → Signal Analyst → Strategist_"
AFTER_VERDICT = "Send another interview for the same idea, or write `new idea: ...` to test a different one."

INTRO = (
    "Hi, I'm ValiDate. I read a customer interview and tell you how much evidence of "
    "real demand is in it: what people actually did, paid for or committed to, as "
    "opposed to polite compliments.\n\n"
    "First, what idea are you testing? One sentence is enough."
)


def use_specialists() -> bool:
    return os.getenv("FRONT_USE_SPECIALISTS", "") == "1"


async def _via_specialists(ctx: Context, idea: str, transcript: str | None, file: Upload | None) -> AnalyzeResponse:
    intake = IntakeRequest(
        text=transcript,
        audio_b64=base64.b64encode(file.data).decode() if file else None,
        mime_type=file.mime_type if file else "text/plain",
    )
    ready = await ask(ctx, "Intake", "INTAKE_AGENT_ADDRESS", intake, TranscriptReady)
    judged = await ask(
        ctx, "Signal Analyst", "ANALYST_AGENT_ADDRESS",
        JudgeTranscript(idea=idea, transcript=ready.transcript), Judged,
    )
    written = await ask(
        ctx, "Strategist", "STRATEGIST_AGENT_ADDRESS", WriteUp(idea=idea, judged=judged.judged), Written
    )
    return AnalyzeResponse(
        **JudgeResponse.model_validate(judged.judged).model_dump(),
        **WriteResponse.model_validate(written.written).model_dump(),
    )


async def _direct(idea: str, transcript: str | None, file: Upload | None) -> AnalyzeResponse:
    if file:
        return await analyzer_client.analyze_audio(idea, file.data, "upload", file.mime_type)
    return await analyzer_client.analyze(idea, transcript)


async def _analyze(ctx: Context, idea: str, transcript: str | None, file: Upload | None) -> str:
    trace = ""
    if use_specialists():
        try:
            result = await _via_specialists(ctx, idea, transcript, file)
            trace = f"\n\n{TEAM_TRACE}"
            ctx.logger.info("Answered through the specialists")
        except StageFailed as ex:
            # Planned fallback: the front agent calls the analyzer itself.
            ctx.logger.warning(f"Specialists unavailable ({ex}); calling the analyzer directly")
            result = await _direct(idea, transcript, file)
    else:
        result = await _direct(idea, transcript, file)
    return f"{render_analysis(result)}{trace}\n\n{AFTER_VERDICT}"


async def handle_founder_input(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=INTRO, finish=_analyze)
