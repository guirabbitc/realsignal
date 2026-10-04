"""The three specialists. Each wraps one analyzer stage and holds no analysis logic.

Every specialist speaks two protocols:
- its own typed protocol, which the front agent (or any other agent) calls;
- the Chat Protocol, so a person can use that one step directly from ASI:One.
"""
import base64

from uagents import Context, Protocol

import analyzer_client
from chat import Upload, make_chat_protocol
from contracts import JudgeResponse
from conversation import clean, converse, is_small_talk
from models import (
    IntakeRequest,
    Judged,
    JudgeTranscript,
    StageError,
    TranscriptReady,
    WriteUp,
    Written,
)
from render import render_judged, render_written
from team import StageFailed, ask

intake_proto = Protocol(name="ValiDateIntake", version="0.1.0")
analyst_proto = Protocol(name="ValiDateAnalyst", version="0.1.0")
strategist_proto = Protocol(name="ValiDateStrategist", version="0.1.0")


@intake_proto.on_message(IntakeRequest, replies={TranscriptReady, StageError})
async def handle_intake(ctx: Context, sender: str, msg: IntakeRequest):
    try:
        if msg.audio_b64:
            audio = base64.b64decode(msg.audio_b64)
            result = await analyzer_client.transcribe(audio, msg.filename, msg.mime_type)
            transcript = result.transcript
        else:
            transcript = (msg.text or "").strip()
        if not transcript:
            raise ValueError("No transcript text or audio received")
        await ctx.send(sender, TranscriptReady(transcript=transcript))
    except Exception as ex:
        ctx.logger.error(f"Intake failed: {ex}")
        await ctx.send(sender, StageError(stage="Intake", error=str(ex)))


@analyst_proto.on_message(JudgeTranscript, replies={Judged, StageError})
async def handle_judge(ctx: Context, sender: str, msg: JudgeTranscript):
    try:
        judged = await analyzer_client.judge(msg.idea, msg.transcript)
        await ctx.send(sender, Judged(judged=judged.model_dump(mode="json")))
    except Exception as ex:
        ctx.logger.error(f"Signal Analyst failed: {ex}")
        await ctx.send(sender, StageError(stage="Signal Analyst", error=str(ex)))


@strategist_proto.on_message(WriteUp, replies={Written, StageError})
async def handle_write(ctx: Context, sender: str, msg: WriteUp):
    try:
        written = await analyzer_client.write(msg.idea, JudgeResponse.model_validate(msg.judged))
        await ctx.send(sender, Written(written=written.model_dump(mode="json")))
    except Exception as ex:
        ctx.logger.error(f"Strategist failed: {ex}")
        await ctx.send(sender, StageError(stage="Strategist", error=str(ex)))


# --- Chat: each specialist used directly from ASI:One ---

INTAKE_INTRO = (
    "Hi, I'm ValiDate Intake. I turn a customer interview into a clean transcript with one "
    "`Speaker: words` turn per line.\n\n"
    "Send me the interview as a PDF or a recording, or paste the text. "
    "For a verdict on the interview, talk to the ValiDate agent."
)
ANALYST_INTRO = (
    "Hi, I'm the ValiDate Signal Analyst. I label each thing an interviewee said as real "
    "signal, polite or neutral, score the evidence of real demand, and pick a verdict.\n\n"
    "First, what idea does the interview test? One sentence is enough."
)
STRATEGIST_INTRO = (
    "Hi, I'm the ValiDate Strategist. I read a judged customer interview and write what it "
    "means and what to do next. The Signal Analyst does the judging for me.\n\n"
    "First, what idea does the interview test? One sentence is enough."
)


async def _transcript_of(transcript: str | None, file: Upload | None) -> str:
    if transcript:
        return transcript
    return (await analyzer_client.transcribe(file.data, "upload", file.mime_type)).transcript


async def intake_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    try:
        for upload in uploads:
            ctx.logger.info(f"Upload from founder: {upload.mime_type}, {len(upload.data)} bytes")
            transcript = await _transcript_of(
                upload.data.decode("utf-8", errors="replace").strip() if upload.is_text else None, upload
            )
            return f"Here is the transcript:\n\n{transcript}"
        for raw in texts:
            text = clean(raw)
            if text and not is_small_talk(text):
                return f"Here is the transcript:\n\n{text}"
    except Exception as ex:
        ctx.logger.error(f"Intake failed: {ex}")
        return f"I could not read that file. {ex}"
    return INTAKE_INTRO


async def _judge_reply(ctx: Context, idea: str, transcript: str | None, file: Upload | None) -> str:
    judged = await analyzer_client.judge(idea, await _transcript_of(transcript, file))
    return render_judged(judged)


async def analyst_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=ANALYST_INTRO, finish=_judge_reply)


async def _strategy_reply(ctx: Context, idea: str, transcript: str | None, file: Upload | None) -> str:
    transcript = await _transcript_of(transcript, file)
    try:
        reply = await ask(
            ctx, "Signal Analyst", "ANALYST_AGENT_ADDRESS",
            JudgeTranscript(idea=idea, transcript=transcript), Judged,
        )
        judged = JudgeResponse.model_validate(reply.judged)
        source = "_Judged by the ValiDate Signal Analyst._"
    except StageFailed as ex:
        ctx.logger.warning(f"Signal Analyst unavailable ({ex}); calling the analyzer directly")
        judged = await analyzer_client.judge(idea, transcript)
        source = ""
    written = await analyzer_client.write(idea, judged)
    return f"{render_written(written)}\n\n{source}".strip()


async def strategist_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=STRATEGIST_INTRO, finish=_strategy_reply)


intake_chat_proto = make_chat_protocol(intake_chat)
analyst_chat_proto = make_chat_protocol(analyst_chat)
strategist_chat_proto = make_chat_protocol(strategist_chat)
