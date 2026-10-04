"""The two-step conversation every agent uses: ask for the idea, then for the interview.

Either can arrive first. An interview sent before the idea is kept until the idea arrives.
What happens once both are known is up to the agent (`finish`).

Transcript text is never logged (MISSION invariant 6): only lengths and types are.
"""
import re
from collections.abc import Awaitable, Callable

from chat import Upload
from labels import restore_turns
from uagents import Context

SPEAKER_LINE = re.compile(r"^\s*[^:\n]{1,40}:\s+\S", re.MULTILINE)

ASK_TRANSCRIPT = (
    "Now send me the interview: paste the transcript, with every turn starting with the speaker's "
    "name and a colon, for example `Founder: ...` and `Customer: ...`."
)
TEXT_ONLY = "I can only read text for now. Paste the transcript, or upload it as a .txt file."

# A leading @mention, quotes or brackets around the message, and an optional "idea:" label.
MENTION = re.compile(r"^(?:@\S+\s+)+")
WRAPPERS = "[](){}\"'`“” "
IDEA_LABEL = re.compile(r"^(?:my\s+|the\s+)?(new\s+)?idea\s*(?:is\b|[:\-])\s*", re.IGNORECASE)
GREETING = re.compile(
    r"^(hi|hello|hey|yo|help|start|test|ok|okay|thanks|thank you|good (morning|afternoon|evening)|"
    r"what (can|do) you do|who are you|how does (this|it) work)\b[\s!?.]*$",
    re.IGNORECASE,
)
MAX_IDEA_CHARS = 500  # the analyzer's limit

Finish = Callable[[Context, str, str], Awaitable[str]]


def idea_key(sender: str) -> str:
    return f"idea:{sender}"


def looks_like_transcript(text: str) -> bool:
    return len(SPEAKER_LINE.findall(restore_turns(text))) >= 2 or len(text) > MAX_IDEA_CHARS


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
    """Collect the idea and the interview from the founder, then call `finish(ctx, idea, transcript)`."""
    pending_key = f"pending:{sender}"
    transcript: str | None = None
    new_idea: str | None = None
    small_talk = False
    refused_file = False

    for raw in texts:
        text = clean(raw)
        ctx.logger.info(f"Text from founder: {len(text)} characters")
        if not text:
            continue
        candidate, labelled = read_idea(text)
        if labelled and candidate:
            new_idea = candidate
        elif looks_like_transcript(text):
            transcript = text
        elif is_small_talk(text):
            small_talk = True
        elif not ctx.storage.get(idea_key(sender)):
            new_idea = candidate
        else:
            small_talk = True
    for upload in uploads:
        ctx.logger.info(f"Upload from founder: {upload.mime_type}, {len(upload.data)} bytes")
        if upload.is_text:
            transcript = upload.data.decode("utf-8", errors="replace").strip()
        else:
            refused_file = True

    if new_idea:
        ctx.storage.set(idea_key(sender), new_idea[:MAX_IDEA_CHARS])
    idea = ctx.storage.get(idea_key(sender))
    if not transcript and new_idea:
        transcript = ctx.storage.get(pending_key)

    if transcript:
        if not idea:
            ctx.storage.set(pending_key, transcript)
            return "Got the interview. Before I read it: what idea does it test? One sentence is enough."
        ctx.storage.set(pending_key, None)
        try:
            return await finish(ctx, idea, transcript)
        except Exception as ex:
            ctx.logger.error(f"Analysis failed: {type(ex).__name__}")
            return f"I could not analyze this interview. {getattr(ex, 'message', ex)}"

    if refused_file:
        return TEXT_ONLY
    if new_idea:
        return f'Got it. The idea: "{idea}"\n\n{ASK_TRANSCRIPT}'
    if idea and small_talk:
        return f'I have your idea: "{idea}"\n\n{ASK_TRANSCRIPT}\n\nTo test a different idea, write `new idea: ...`.'
    return intro
