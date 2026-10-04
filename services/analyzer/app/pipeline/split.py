"""Turn a transcript into ordered sentences and decide who the interviewee is."""
import re
from dataclasses import dataclass

TURN = re.compile(r"^\s*([^:\n]{1,40}):\s*(.*)$")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
UNKNOWN_SPEAKER = "Speaker"


@dataclass
class SentenceDraft:
    order: int
    speaker: str
    text: str
    is_interviewee: bool


def parse_turns(transcript: str) -> list[tuple[str, str]]:
    """Read `Speaker: words` lines. A line without a speaker continues the previous turn."""
    turns: list[tuple[str, str]] = []
    for line in transcript.splitlines():
        if not line.strip():
            continue
        match = TURN.match(line)
        if match:
            turns.append((match.group(1).strip(), match.group(2).strip()))
        elif turns:
            speaker, text = turns[-1]
            turns[-1] = (speaker, f"{text} {line.strip()}".strip())
        else:
            turns.append((UNKNOWN_SPEAKER, line.strip()))
    return turns


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_END.split(text) if s.strip()]


def identify_interviewer(turns: list[tuple[str, str]]) -> str | None:
    """The interviewer is the speaker who asks the most questions.

    With a single speaker there is no interviewer: every sentence is judged.
    """
    speakers = list(dict.fromkeys(speaker for speaker, _ in turns))
    if len(speakers) < 2:
        return None
    questions = {speaker: 0 for speaker in speakers}
    for speaker, text in turns:
        questions[speaker] += sum(1 for s in split_sentences(text) if s.endswith("?"))
    # ties go to whoever spoke first
    return max(speakers, key=lambda s: questions[s])


def split_transcript(transcript: str) -> list[SentenceDraft]:
    turns = parse_turns(transcript)
    interviewer = identify_interviewer(turns)
    drafts: list[SentenceDraft] = []
    for speaker, text in turns:
        for sentence in split_sentences(text):
            drafts.append(
                SentenceDraft(
                    order=len(drafts),
                    speaker=speaker,
                    text=sentence,
                    is_interviewee=speaker != interviewer,
                )
            )
    return drafts
