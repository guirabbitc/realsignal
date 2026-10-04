"""Speech to text with speaker labels. All ElevenLabs calls stay in this module."""
from typing import Protocol

import httpx

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/speech-to-text"
ELEVENLABS_MODEL = "scribe_v2"


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        """Return the transcript as `speaker: words` lines."""
        ...


def words_to_transcript(words: list[dict]) -> str:
    """Group ElevenLabs words into one line per speaker turn."""
    turns: list[tuple[str, str]] = []
    for word in words:
        if word.get("type") == "audio_event":
            continue
        speaker = word.get("speaker_id") or "speaker_0"
        if turns and turns[-1][0] == speaker:
            turns[-1] = (speaker, turns[-1][1] + word["text"])
        else:
            turns.append((speaker, word["text"]))
    return "\n".join(f"{speaker}: {text.strip()}" for speaker, text in turns if text.strip())


class ElevenLabsTranscriber:
    def __init__(self, api_key: str, http: httpx.Client | None = None):
        self._api_key = api_key
        self._http = http or httpx.Client(timeout=300)

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        response = self._http.post(
            ELEVENLABS_URL,
            headers={"xi-api-key": self._api_key},
            data={"model_id": ELEVENLABS_MODEL, "diarize": "true"},
            files={"file": (filename, audio, content_type)},
        )
        response.raise_for_status()
        return words_to_transcript(response.json()["words"])


class FakeTranscriber:
    """Returns a fixed transcript. Used in tests and in fake mode."""

    def __init__(self, transcript: str = "speaker_0: How do you plan dinner?\nspeaker_1: Last week I paid for a meal kit."):
        self._transcript = transcript

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        return self._transcript
