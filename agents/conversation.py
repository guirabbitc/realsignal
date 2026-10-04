"""The two-step conversation every ValiDate agent uses: ask for the idea, then for the interview.

Either can arrive first. An interview sent before the idea is kept until the idea arrives.
What happens once both are known is up to the agent (`finish`).
"""
import base64
import re
from typing import Awaitable, Callable

from uagents import Context

from chat import Upload

SPEAKER_LINE = re.compile(r"^\s*[^:\n]{1,40}:\s+\S", re.MULTILINE)
# A file sent before the idea is kept in agent storage only if it is small.
MAX_PENDING_FILE_BYTES = 2_000_000

ASK_TRANSCRIPT = (
    "Now send me the interview: paste the transcript, or upload it as a PDF. "
    "One `Speaker: words` turn per line works best."
)

# A leading @mention, quotes or brackets around the message, and an optional "idea:" label.
MENTION = re.compile(r"^(?:@\S+\s+)+")
WRAPPERS = "[](){}\"'`“” "
IDEA_LABEL = re.compile(r"^(?:my\s+|the\s+)?(new\s+)?idea\s*(?:is\b|[:\-])\s*", re.IGNORECASE)
GREETING = re.compile(
    r"^(hi|hello|hey|yo|help|start|test|ok|okay|thanks|thank you|good (morning|afternoon|evening)|"
    r"what (can|do) you do|who are you|how does (this|it) work)\b[\s!?.]*$",
    re.IGNORECASE,
)

Finish = Callable[[Context, str, str | None, Upload | None], Awaitable[str]]


def looks_like_transcript(text: str) -> bool:
    return len(SPEAKER_LINE.findall(text)) >= 2 or len(text) > 400


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


async def converse(
    ctx: Context, sender: str, texts: list[str], uploads: list[Upload], *, intro: str, finish: Finish
) -> str:
    """Collect the idea and the interview from the founder, then call `finish(ctx, idea, transcript, file)`."""
    idea_key, pending_key, pending_file_key = f"idea:{sender}", f"pending:{sender}", f"pending_file:{sender}"
    transcript: str | None = None
    file: Upload | None = None
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
            file = upload

    if new_idea:
        ctx.storage.set(idea_key, new_idea)
    idea = ctx.storage.get(idea_key)
    if not transcript and not file and new_idea:
        transcript = ctx.storage.get(pending_key)
        kept = ctx.storage.get(pending_file_key)
        if not transcript and kept:
            file = Upload(mime_type=kept["mime_type"], data=base64.b64decode(kept["b64"]))

    if transcript or file:
        if not idea:
            if transcript:
                ctx.storage.set(pending_key, transcript)
                return "Got the interview. Before I read it: what idea does it test? One sentence is enough."
            if len(file.data) <= MAX_PENDING_FILE_BYTES:
                ctx.storage.set(pending_file_key, {"mime_type": file.mime_type, "b64": base64.b64encode(file.data).decode()})
                return "Got the file. Before I read it: what idea does it test? One sentence is enough."
            return "Got the file. Before I read it: what idea does it test? Tell me in one sentence, then upload the file again."
        ctx.storage.set(pending_key, None)
        ctx.storage.set(pending_file_key, None)
        try:
            return await finish(ctx, idea, transcript, None if transcript else file)
        except Exception as ex:
            ctx.logger.error(f"Analysis failed: {ex}")
            return f"I could not analyze this interview. {ex}"

    if new_idea:
        return f'Got it. The idea: "{idea}"\n\n{ASK_TRANSCRIPT}'
    if idea and small_talk:
        return f'I have your idea: "{idea}"\n\n{ASK_TRANSCRIPT}\n\nTo test a different idea, write `new idea: ...`.'
    return intro
