"""What the front agent does with a founder's message: remember the idea, get the
interview analyzed, and reply. It plans the steps and calls others; it judges nothing itself."""
import base64
import os
import re
from dataclasses import dataclass

from uagents import Context

import analyzer_client
from contracts import AnalyzeResponse, JudgeResponse, Label, WriteResponse
from models import (
    IntakeRequest,
    Judged,
    JudgeTranscript,
    StageError,
    TranscriptReady,
    WriteUp,
    Written,
)

STAGE_TIMEOUT_SECONDS = 300
TOP_QUOTES = 3
SPEAKER_LINE = re.compile(r"^\s*[^:\n]{1,40}:\s+\S", re.MULTILINE)

VERDICT_TEXT = {
    "keep_going": "Keep going",
    "narrow_down": "Narrow down",
    "try_new_angle": "Try a new angle",
    "pivot": "Pivot",
}

HELP = (
    "I read a customer interview and tell you how much evidence of real demand is in it.\n\n"
    "1. Tell me the idea you are testing: `idea: an app that plans dinners and orders groceries`\n"
    "2. Paste the interview transcript, or upload it as a .txt file or a recording."
)


@dataclass
class Upload:
    mime_type: str
    data: bytes

    @property
    def is_text(self) -> bool:
        return self.mime_type.startswith("text/")


class StageFailed(Exception):
    pass


def use_specialists() -> bool:
    return os.getenv("FRONT_USE_SPECIALISTS", "") == "1"


def looks_like_transcript(text: str) -> bool:
    return len(SPEAKER_LINE.findall(text)) >= 2 or len(text) > 400


async def _ask(ctx: Context, stage: str, env_name: str, message, expected):
    """Send one typed message to a specialist and wait for its typed reply."""
    reply, status = await ctx.send_and_receive(
        os.environ[env_name], message, response_type={expected, StageError}, timeout=STAGE_TIMEOUT_SECONDS
    )
    if isinstance(reply, expected):
        return reply
    if isinstance(reply, StageError):
        raise StageFailed(f"{reply.stage} failed: {reply.error}")
    raise StageFailed(f"{stage} did not answer ({status})")


async def _via_specialists(ctx: Context, idea: str, transcript: str | None, audio: Upload | None) -> AnalyzeResponse:
    intake = IntakeRequest(
        text=transcript,
        audio_b64=base64.b64encode(audio.data).decode() if audio else None,
        mime_type=audio.mime_type if audio else "text/plain",
    )
    ready = await _ask(ctx, "Intake", "INTAKE_AGENT_ADDRESS", intake, TranscriptReady)
    judged = await _ask(
        ctx, "Signal Analyst", "ANALYST_AGENT_ADDRESS",
        JudgeTranscript(idea=idea, transcript=ready.transcript), Judged,
    )
    written = await _ask(
        ctx, "Strategist", "STRATEGIST_AGENT_ADDRESS", WriteUp(idea=idea, judged=judged.judged), Written
    )
    return AnalyzeResponse(
        **JudgeResponse.model_validate(judged.judged).model_dump(),
        **WriteResponse.model_validate(written.written).model_dump(),
    )


async def _direct(idea: str, transcript: str | None, audio: Upload | None) -> AnalyzeResponse:
    if audio:
        return await analyzer_client.analyze_audio(idea, audio.data, "recording", audio.mime_type)
    return await analyzer_client.analyze(idea, transcript)


def render(result: AnalyzeResponse) -> str:
    quotes = sorted(
        (s for s in result.sentences if s.label == Label.real_signal),
        key=lambda s: s.confidence or 0,
        reverse=True,
    )[:TOP_QUOTES]
    lines = [
        f"**Verdict: {VERDICT_TEXT[result.verdict.value]}**",
        f"Demand score: {result.score:g} / 100",
        "",
        result.summary,
        "",
    ]
    if quotes:
        lines.append("**Strongest evidence**")
        lines += [f'- "{s.text}" ({s.speaker}, {round((s.confidence or 0) * 100)}%)' for s in quotes]
        lines.append("")
    lines.append("**Next steps**")
    lines += [f"{i}. {step}" for i, step in enumerate(result.next_steps, 1)]
    return "\n".join(lines)


async def handle_founder_input(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    idea_key = f"idea:{sender}"
    transcript: str | None = None
    audio: Upload | None = None
    saved_idea = False

    for text in texts:
        stripped = text.strip()
        if stripped.lower().startswith("idea:"):
            ctx.storage.set(idea_key, stripped[5:].strip())
            saved_idea = True
        elif looks_like_transcript(stripped):
            transcript = stripped
    for upload in uploads:
        if upload.is_text:
            transcript = upload.data.decode("utf-8", errors="replace").strip()
        else:
            audio = upload

    idea = ctx.storage.get(idea_key)
    if not transcript and not audio:
        if saved_idea:
            return f'Idea saved: "{idea}". Now paste the interview transcript, or upload it as a .txt file or a recording.'
        return HELP
    if not idea:
        return "Before I read the interview, tell me the idea it tests, like this: `idea: <one sentence>`. Then send the interview again."

    try:
        if use_specialists():
            result = await _via_specialists(ctx, idea, transcript, None if transcript else audio)
        else:
            result = await _direct(idea, transcript, None if transcript else audio)
    except Exception as ex:
        ctx.logger.error(f"Analysis failed: {ex}")
        return f"I could not analyze this interview. {ex}"
    return render(result)
