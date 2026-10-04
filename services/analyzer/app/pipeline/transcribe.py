"""Turn an uploaded file into a transcript: text and PDF are read, audio is transcribed.

All ElevenLabs calls stay in this module.
"""
import io
from typing import Protocol

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

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


def is_pdf(data: bytes, content_type: str) -> bool:
    return content_type == "application/pdf" or data[:5] == b"%PDF-"


def pdf_to_text(data: bytes) -> str:
    """Text of every page. A wrapped line has no speaker label, so split.py joins it to its turn."""
    lines = []
    try:
        for page in PdfReader(io.BytesIO(data)).pages:
            lines += [line.strip() for line in (page.extract_text() or "").splitlines()]
    except PdfReadError as ex:
        raise ValueError(f"Could not read the PDF: {ex}") from ex
    text = "\n".join(line for line in lines if line)
    if not text:
        raise ValueError("No text found in the PDF. A scanned PDF has only images; export it as text first.")
    return text


def file_to_transcript(data: bytes, filename: str, content_type: str, transcriber: Transcriber) -> str:
    """Read the transcript out of an upload, whatever kind of file it is."""
    if is_pdf(data, content_type):
        return pdf_to_text(data)
    if content_type.startswith("text/") or filename.lower().endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace").strip()
    return transcriber.transcribe(data, filename, content_type)
