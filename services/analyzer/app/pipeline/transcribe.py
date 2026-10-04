"""Step 1 (audio only): ElevenLabs Scribe speech to text with speaker separation. No AI judgment here.

Returns voices and turns, never roles: only the founder knows which voice is theirs, and a wrong guess would
judge their own pitch as customer evidence. Turn text is Scribe's text with whitespace collapsed and audio
events dropped, never rewritten, so every later quote is verbatim (MISSION invariant 2).
Never logs transcript text.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from app.errors import EmptyAudio, NoSpeech, TranscriptionFailed
from app.models import TranscribeResult, TranscribeSpeaker, TranscribeTurn

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_MODEL = "scribe_v2"
# Best-effort determinism from Scribe: same audio, same transcript, same verdict.
SEED = 20261004
# One total budget so the timeouts nest under the web call (285 s) and Node fetch's 300 s header timeout.
BUDGET_S = 270.0
# A retry only makes sense if it can still finish.
MIN_RETRY_S = 60.0
RETRY_DELAY_S = 1.0
SAMPLE_TURNS = 2
SAMPLE_CHARS = 200
# Before the first labelled word (should not happen with diarize=true). Never merged into a real voice.
UNKNOWN_SPEAKER = "speaker_unknown"
_RETRYABLE = ("rate_limited", "upstream_error", "timeout")
_BAD_AUDIO_HINTS = ("audio", "file", "decode", "duration", "corrupt")

log = logging.getLogger("analyzer")
_WHITESPACE = re.compile(r"\s+")


class _AttemptFailed(Exception):
    def __init__(self, reason: str, status: int | None):
        self.reason = reason
        self.status = status


def make_client() -> httpx.AsyncClient:
    """Patched in tests with an httpx.MockTransport."""
    return httpx.AsyncClient()


def scribe_fields(model: str, num_speakers: int) -> dict[str, str]:
    # tag_audio_events=false: otherwise "(laughter)" lands inside quotes. No detect_speaker_roles (the founder
    # chooses), no no_verbatim (receipts are what was actually said), no keyterms/entities/edits/webhook.
    return {
        "model_id": model,
        "diarize": "true",
        "num_speakers": str(num_speakers),
        "tag_audio_events": "false",
        "language_code": "en",
        "timestamps_granularity": "word",
        "seed": str(SEED),
    }


async def call_scribe(
    path: Path,
    filename: str,
    content_type: str,
    num_speakers: int,
    *,
    api_key: str,
    model: str,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """The raw Scribe response. Retries once on 429, 5xx or timeout; never returns a partial result."""
    deadline = time.monotonic() + BUDGET_S
    for attempt in (1, 2):
        try:
            return await _attempt(path, filename, content_type, num_speakers, api_key, model, client,
                                  deadline - time.monotonic())
        except _AttemptFailed as failed:
            log.warning("scribe attempt=%d failed reason=%s status=%s", attempt, failed.reason, failed.status)
            last = failed
            can_retry = deadline - time.monotonic() - RETRY_DELAY_S >= MIN_RETRY_S
            if attempt == 1 and failed.reason in _RETRYABLE and can_retry:
                await asyncio.sleep(RETRY_DELAY_S)
                continue
            break
    if last.reason == "empty_audio":
        raise EmptyAudio("We could not read any audio in this file.")
    raise TranscriptionFailed(last.reason)


async def _attempt(path, filename, content_type, num_speakers, api_key, model, client, remaining) -> dict[str, Any]:
    try:
        async with asyncio.timeout(max(remaining, 0.001)):
            with path.open("rb") as audio:
                response = await client.post(
                    SCRIBE_URL,
                    headers={"xi-api-key": api_key},
                    data=scribe_fields(model, num_speakers),
                    files={"file": (filename, audio, content_type)},
                    timeout=httpx.Timeout(max(remaining, 0.001), connect=10.0),
                )
    except (TimeoutError, httpx.TimeoutException):
        raise _AttemptFailed("timeout", None) from None
    except httpx.HTTPError:
        raise _AttemptFailed("upstream_error", None) from None

    status = response.status_code
    if status == 200:
        try:
            body = response.json()
        except ValueError:
            raise _AttemptFailed("upstream_error", status) from None
        if not isinstance(body, dict):
            raise _AttemptFailed("upstream_error", status)
        return body
    if status == 429:
        raise _AttemptFailed("rate_limited", status)
    if status >= 500:
        raise _AttemptFailed("upstream_error", status)
    # Scribe answers 400/422 for audio it cannot decode. Only the detail's wording is checked; the provider
    # message is never logged or returned.
    if status in (400, 422) and any(hint in response.text.lower() for hint in _BAD_AUDIO_HINTS):
        raise _AttemptFailed("empty_audio", status)
    raise _AttemptFailed("rejected", status)


@dataclass
class _OpenTurn:
    speaker_id: str
    parts: list[str] = field(default_factory=list)
    start: float | None = None
    end: float | None = None


def _clean(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def build_turns(words: list[dict[str, Any]]) -> list[TranscribeTurn]:
    """Consecutive words with the same speaker_id form one turn. Spacing belongs to the turn it falls in;
    a word with no speaker_id continues the current turn (we never invent a voice)."""
    open_turns: list[_OpenTurn] = []
    for item in words:
        kind = item.get("type")
        if kind not in ("word", "spacing"):
            continue  # audio_event, and anything unknown
        text = item.get("text") or ""
        if kind == "spacing":
            if open_turns:
                open_turns[-1].parts.append(text)
            continue
        speaker = item.get("speaker_id") or (open_turns[-1].speaker_id if open_turns else UNKNOWN_SPEAKER)
        if not open_turns or open_turns[-1].speaker_id != speaker:
            open_turns.append(_OpenTurn(speaker_id=speaker))
        turn = open_turns[-1]
        turn.parts.append(text)
        if turn.start is None and item.get("start") is not None:
            turn.start = float(item["start"])
        if item.get("end") is not None:
            turn.end = float(item["end"])

    turns: list[TranscribeTurn] = []
    for turn in open_turns:
        text = _clean("".join(turn.parts))
        if not text:
            continue
        if turns and turns[-1].speaker_id == turn.speaker_id:  # the turn between them was empty and dropped
            before = turns[-1]
            turns[-1] = TranscribeTurn(speaker_id=before.speaker_id, text=f"{before.text} {text}",
                                       start=before.start, end=turn.end if turn.end is not None else before.end)
            continue
        turns.append(TranscribeTurn(speaker_id=turn.speaker_id, text=text, start=turn.start, end=turn.end))
    return turns


def summarize_speakers(turns: list[TranscribeTurn]) -> list[TranscribeSpeaker]:
    """One entry per voice, in the order they first speak."""
    by_id: dict[str, list[TranscribeTurn]] = {}
    for turn in turns:
        by_id.setdefault(turn.speaker_id, []).append(turn)

    speakers = []
    for speaker_id, own in by_id.items():
        seconds = sum(t.end - t.start for t in own if t.start is not None and t.end is not None and t.end >= t.start)
        speakers.append(TranscribeSpeaker(
            id=speaker_id,
            turns=len(own),
            words=sum(len(t.text.split()) for t in own),
            seconds=round(seconds, 1),
            sample=[t.text[:SAMPLE_CHARS].rstrip() for t in own[:SAMPLE_TURNS]],
        ))
    return speakers


def suggest_founder(turns: list[TranscribeTurn], speakers: list[TranscribeSpeaker]) -> str:
    """The voice with the most turns ending in "?"; a tie goes to whoever spoke first. A suggestion only."""
    questions = {s.id: 0 for s in speakers}
    for turn in turns:
        if turn.text.endswith("?"):
            questions[turn.speaker_id] += 1
    return max(speakers, key=lambda s: questions[s.id]).id  # max() keeps the first on ties


def to_result(scribe: dict[str, Any], model: str) -> TranscribeResult:
    turns = build_turns(scribe.get("words") or [])
    if not turns:
        raise NoSpeech("We could not hear any speech in this audio.")
    speakers = summarize_speakers(turns)
    duration = scribe.get("audio_duration_secs")
    if duration is None:
        duration = next((t.end for t in reversed(turns) if t.end is not None), None)
    return TranscribeResult(
        duration_s=round(float(duration), 1) if duration is not None else None,
        language_code=scribe.get("language_code"),
        model=model,
        speakers=speakers,
        turns=turns,
        suggested_founder_id=suggest_founder(turns, speakers),
    )
