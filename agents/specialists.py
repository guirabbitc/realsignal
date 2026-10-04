"""The three specialist protocols. Each wraps one analyzer stage and holds no analysis logic."""
import base64

from uagents import Context, Protocol

import analyzer_client
from contracts import JudgeResponse
from models import (
    IntakeRequest,
    Judged,
    JudgeTranscript,
    StageError,
    TranscriptReady,
    WriteUp,
    Written,
)

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
