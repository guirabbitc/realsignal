"""Step 2: split a speaker-labelled transcript into turns and sentences. No AI.

Every sentence keeps its exact substring of the transcript, so quotes are verbatim by construction
(MISSION invariant 2).
"""

import re
from dataclasses import dataclass
from typing import Literal

import pysbd

from app.errors import TranscriptTooLong, UnlabelledTranscript

Speaker = Literal["founder", "customer"]

_LABEL = re.compile(r"^[ \t]*(founder|customer)[ \t]*:[ \t]*", re.IGNORECASE)
_segmenter = pysbd.Segmenter(language="en", clean=False)


@dataclass(frozen=True)
class Turn:
    speaker: Speaker
    text: str


@dataclass(frozen=True)
class Sentence:
    position: int
    speaker: Speaker
    text: str
    turn_index: int


@dataclass(frozen=True)
class CustomerSentence:
    position: int
    text: str
    founder_question: str | None


@dataclass(frozen=True)
class SplitResult:
    turns: list[Turn]
    sentences: list[Sentence]
    customer_sentences: list[CustomerSentence]
    founder_words: int
    customer_words: int

    @property
    def founder_talk_ratio(self) -> float | None:
        total = self.founder_words + self.customer_words
        return self.founder_words / total if total else None

    @property
    def founder_turns(self) -> list[str]:
        return [t.text for t in self.turns if t.speaker == "founder"]


def _word_count(text: str) -> int:
    return len(text.split())


def _turn_spans(transcript: str) -> list[tuple[Speaker, int, int]]:
    """(speaker, start, end) offsets into the transcript. Unlabelled lines continue the previous turn."""
    spans: list[list] = []
    offset = 0
    for line in transcript.splitlines(keepends=True):
        content_end = offset + len(line.rstrip("\r\n"))
        match = _LABEL.match(line)
        if match:
            spans.append([match.group(1).lower(), offset + match.end(), content_end])
        elif spans and line.strip():
            spans[-1][2] = content_end
        offset += len(line)
    return [(s, a, b) for s, a, b in spans]


def _sentences_in(turn_text: str) -> list[str]:
    """Sentences of one turn, each an exact substring of turn_text."""
    out: list[str] = []
    cursor = 0
    for segment in _segmenter.segment(turn_text):
        sentence = segment.strip()
        if not sentence:
            continue
        index = turn_text.find(sentence, cursor)
        if index == -1:
            index = turn_text.find(sentence)
        if index == -1:  # pysbd with clean=False never rewrites text; fail loudly if it ever does
            raise RuntimeError("sentence splitter produced text that is not in the transcript")
        out.append(turn_text[index : index + len(sentence)])
        cursor = index + len(sentence)
    return out


def split_transcript(transcript: str, max_chars: int) -> SplitResult:
    if len(transcript) > max_chars:
        raise TranscriptTooLong(f"Transcript has {len(transcript)} characters; the limit is {max_chars}.")

    spans = _turn_spans(transcript)
    if not spans:
        raise UnlabelledTranscript('Label every turn with "Founder:" or "Customer:".')

    turns: list[Turn] = []
    sentences: list[Sentence] = []
    customer_sentences: list[CustomerSentence] = []
    founder_words = customer_words = 0
    last_founder_turn: str | None = None
    position = 0

    for speaker, start, end in spans:
        text = transcript[start:end].strip()
        if not text:
            continue
        turn_index = len(turns)
        turns.append(Turn(speaker=speaker, text=text))
        if speaker == "founder":
            founder_words += _word_count(text)
        else:
            customer_words += _word_count(text)

        for sentence in _sentences_in(text):
            position += 1
            sentences.append(Sentence(position, speaker, sentence, turn_index))
            if speaker == "customer":
                customer_sentences.append(CustomerSentence(position, sentence, last_founder_turn))

        if speaker == "founder":
            last_founder_turn = text

    return SplitResult(turns, sentences, customer_sentences, founder_words, customer_words)
