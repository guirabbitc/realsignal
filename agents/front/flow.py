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

INTRO = (
    "Hi, I'm ValiDate. I read a customer interview and tell you how much evidence of "
    "real demand is in it: what people actually did, paid for or committed to, as "
    "opposed to polite compliments.\n\n"
    "First, what idea are you testing? One sentence is enough."
)
ASK_TRANSCRIPT = (
    "Now send me the interview: paste the transcript, or upload it as a .txt file. "
    "One `Speaker: words` turn per line works best."
)
AFTER_VERDICT = "Send another interview for the same idea, or write `new idea: ...` to test a different one."

# A leading @mention, quotes or brackets around the message, and an optional "idea:" label.
MENTION = re.compile(r"^(?:@\S+\s+)+")
WRAPPERS = "[](){}\"'`\u201c\u201d "
IDEA_LABEL = re.compile(r"^(?:my\s+|the\s+)?(new\s+)?idea\s*(?:is\b|[:\-])\s*", re.IGNORECASE)
GREETING = re.compile(
    r"^(hi|hello|hey|yo|help|start|test|ok|okay|thanks|thank you|good (morning|afternoon|evening)|"
    r"what (can|do) you do|who are you|how does (this|it) work)\b[\s!?.]*$",
    re.IGNORECASE,
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
        "",  # a blank line: chat clients render a single newline as a space
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


def clean(text: str) -> str:
    """Drop a leading @mention and any quotes or brackets wrapped around the message."""
    return MENTION.sub("", text.strip()).strip(WRAPPERS)


def read_idea(text: str) -> tuple[str, bool]:
    """Return (idea text, whether it was explicitly labelled as an idea)."""
    match = IDEA_LABEL.match(text)
    if match:
        return text[match.end():].strip(WRAPPERS), True
    return text, False


def is_small_talk(text: str) -> bool:
    return bool(GREETING.match(text)) or len(text.split()) < 3


async def _analyze(ctx: Context, idea: str, transcript: str | None, audio: Upload | None) -> str:
    try:
        if use_specialists():
            result = await _via_specialists(ctx, idea, transcript, audio)
        else:
            result = await _direct(idea, transcript, audio)
    except Exception as ex:
        ctx.logger.error(f"Analysis failed: {ex}")
        return f"I could not analyze this interview. {ex}"
    return f"{render(result)}\n\n{AFTER_VERDICT}"


async def handle_founder_input(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    """A short conversation: ask for the idea, then for the interview, then analyze.

    Either can arrive first. An interview sent before the idea is kept until the idea arrives.
    """
    idea_key, pending_key = f"idea:{sender}", f"pending:{sender}"
    transcript: str | None = None
    audio: Upload | None = None
    new_idea: str | None = None
    small_talk = False

    for raw in texts:
        text = clean(raw)
        ctx.logger.info(f"Text from founder: {text[:120]!r}")
        if not text:
            continue
        candidate, labelled = read_idea(text)
        if labelled and candidate:
            new_idea = candidate
        elif looks_like_transcript(text):
            transcript = text
        elif is_small_talk(text):
            small_talk = True
        elif not ctx.storage.get(idea_key):
            new_idea = candidate
        else:
            small_talk = True
    for upload in uploads:
        ctx.logger.info(f"Upload from founder: {upload.mime_type}, {len(upload.data)} bytes")
        if upload.is_text:
            transcript = upload.data.decode("utf-8", errors="replace").strip()
        else:
            audio = upload

    if new_idea:
        ctx.storage.set(idea_key, new_idea)
    idea = ctx.storage.get(idea_key)
    if not transcript and not audio:
        transcript = ctx.storage.get(pending_key) if new_idea else None

    if transcript or audio:
        if not idea:
            if transcript:
                ctx.storage.set(pending_key, transcript)
                return "Got the interview. Before I read it: what idea does it test? One sentence is enough."
            return "Got the recording. Before I read it: what idea does it test? Tell me in one sentence, then upload the recording again."
        ctx.storage.set(pending_key, None)
        return await _analyze(ctx, idea, transcript, None if transcript else audio)

    if new_idea:
        return f'Got it. The idea: "{idea}".\n\n{ASK_TRANSCRIPT}'
    if idea and small_talk:
        return f'I have your idea: "{idea}".\n\n{ASK_TRANSCRIPT}\n\nTo test a different idea, write `new idea: ...`.'
    return INTRO
