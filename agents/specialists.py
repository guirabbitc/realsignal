"""The three specialists. Each runs one part of the analyzer's pipeline and holds no analysis logic.

Every specialist speaks two protocols:
- its own typed protocol, which the front agent (or any other agent) calls;
- the Chat Protocol, so a person can use that one step directly from ASI:One.
"""
import pipeline
from chat import Upload, make_chat_protocol
from common import address_of
from conversation import TEXT_ONLY, clean, converse, is_small_talk
from labels import prepare_transcript
from models import (
    IntakeRequest,
    Judgement,
    JudgeTranscript,
    StageError,
    TranscriptReady,
    WriteUp,
    Written,
)
from render import render_judged, render_written
from team import StageFailed, ask
from uagents import Context, Protocol

from app.pipeline.analyze import Judged

intake_proto = Protocol(name="ValiDateIntake", version="0.2.0")
analyst_proto = Protocol(name="ValiDateAnalyst", version="0.2.0")
strategist_proto = Protocol(name="ValiDateStrategist", version="0.2.0")


def _reason(ex: Exception) -> str:
    return str(getattr(ex, "message", ex))


@intake_proto.on_message(IntakeRequest, replies={TranscriptReady, StageError})
async def handle_intake(ctx: Context, sender: str, msg: IntakeRequest):
    try:
        transcript, note = prepare_transcript(msg.text)
        await ctx.send(sender, TranscriptReady(transcript=transcript, note=note))
    except Exception as ex:
        ctx.logger.error(f"Intake failed: {type(ex).__name__}")
        await ctx.send(sender, StageError(stage="Intake", error=_reason(ex)))


@analyst_proto.on_message(JudgeTranscript, replies={Judgement, StageError})
async def handle_judge(ctx: Context, sender: str, msg: JudgeTranscript):
    try:
        judged = await pipeline.judge(msg.idea, msg.transcript)
        await ctx.send(sender, Judgement(judged=judged.model_dump(mode="json")))
    except Exception as ex:
        ctx.logger.error(f"Signal Analyst failed: {type(ex).__name__}")
        await ctx.send(sender, StageError(stage="Signal Analyst", error=_reason(ex)))


@strategist_proto.on_message(WriteUp, replies={Written, StageError})
async def handle_write(ctx: Context, sender: str, msg: WriteUp):
    try:
        result = await pipeline.write(msg.idea, msg.transcript, Judged.model_validate(msg.judged))
        await ctx.send(sender, Written(result=result.model_dump(mode="json")))
    except Exception as ex:
        ctx.logger.error(f"Strategist failed: {type(ex).__name__}")
        await ctx.send(sender, StageError(stage="Strategist", error=_reason(ex)))


# --- Chat: each specialist used directly from ASI:One ---

INTAKE_INTRO = (
    "Hi, I'm valiDate Intake. I get a customer interview ready for analysis: I work out who is "
    "the interviewer and who is the customer, and label every turn `Founder:` or `Customer:`.\n\n"
    "Paste the transcript, with every turn starting with the speaker's name and a colon. "
    "For a verdict on the interview, talk to the valiDate agent."
)
ANALYST_INTRO = (
    "Hi, I'm the valiDate Signal Analyst. I judge each thing a customer said in an interview as a "
    "commitment, past pain, a hypothetical, a compliment or neutral, score the real interest, and "
    "pick a verdict.\n\nFirst, what idea does the interview test? One sentence is enough."
)
STRATEGIST_INTRO = (
    "Hi, I'm the valiDate Strategist. I read a judged customer interview and write what it means "
    "and what to ask next. The Signal Analyst does the judging for me.\n\n"
    "First, what idea does the interview test? One sentence is enough."
)


async def intake_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    candidates = [u.data.decode("utf-8", errors="replace").strip() for u in uploads if u.is_text]
    candidates += [clean(t) for t in texts]
    for text in candidates:
        if text and not is_small_talk(text):
            try:
                transcript, note = prepare_transcript(text)
            except ValueError as ex:
                return str(ex)
            return f"{note or 'The turns were already labelled Founder: and Customer:.'}\n\n{transcript}"
    return TEXT_ONLY if uploads else INTAKE_INTRO


async def _judge_reply(ctx: Context, idea: str, text: str) -> str:
    transcript, note = prepare_transcript(text)
    judged = await pipeline.judge(idea, transcript)
    return (f"_{note}_\n\n" if note else "") + render_judged(judged)


async def analyst_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=ANALYST_INTRO, finish=_judge_reply)


async def _strategy_reply(ctx: Context, idea: str, text: str) -> str:
    transcript, note = prepare_transcript(text)
    try:
        reply = await ask(
            ctx, "Signal Analyst", address_of("analyst"),
            JudgeTranscript(idea=idea, transcript=transcript), Judgement,
        )
        judged = Judged.model_validate(reply.judged)
        source = "_Judged by the valiDate Signal Analyst._"
    except StageFailed as ex:
        ctx.logger.warning(f"Signal Analyst unavailable ({ex}); judging here")
        judged = await pipeline.judge(idea, transcript)
        source = ""
    result = await pipeline.write(idea, transcript, judged)
    return f"{render_written(result)}\n\n{source}".strip()


async def strategist_chat(ctx: Context, sender: str, texts: list[str], uploads: list[Upload]) -> str:
    return await converse(ctx, sender, texts, uploads, intro=STRATEGIST_INTRO, finish=_strategy_reply)


intake_chat_proto = make_chat_protocol(intake_chat)
analyst_chat_proto = make_chat_protocol(analyst_chat)
strategist_chat_proto = make_chat_protocol(strategist_chat)
