"""Messages the agents send each other. Every agent imports its messages from here.

Payloads that the analyzer defines (judged sentences, score, verdict) travel as plain
dicts and are validated with the generated models in contracts.py, so the contract in
packages/contracts stays the only place those shapes are defined.
"""
from typing import Optional

from uagents import Model


class IntakeRequest(Model):
    """Either pasted/uploaded text, or a recording as base64."""
    text: Optional[str] = None
    audio_b64: Optional[str] = None
    filename: str = "audio"
    mime_type: str = "application/octet-stream"


class TranscriptReady(Model):
    transcript: str


class JudgeTranscript(Model):
    idea: str
    transcript: str


class Judged(Model):
    judged: dict  # contracts.JudgeResponse


class WriteUp(Model):
    idea: str
    judged: dict  # contracts.JudgeResponse


class Written(Model):
    written: dict  # contracts.WriteResponse


class StageError(Model):
    stage: str
    error: str
