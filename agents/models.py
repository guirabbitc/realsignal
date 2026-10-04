"""Messages the agents send each other. Every agent imports its messages from here.

Analysis payloads travel as plain dicts and are validated with the analyzer's own models
(app.pipeline.analyze.Judged, app.models.AnalyzeResult), so those shapes are defined in one place.
"""
from uagents import Model


class IntakeRequest(Model):
    text: str


class TranscriptReady(Model):
    transcript: str  # every turn labelled Founder: or Customer:
    note: str  # how the speakers were mapped, to show the founder; empty when nothing was changed


class JudgeTranscript(Model):
    idea: str
    transcript: str


class Judgement(Model):
    judged: dict  # app.pipeline.analyze.Judged


class WriteUp(Model):
    idea: str
    transcript: str
    judged: dict  # app.pipeline.analyze.Judged


class Written(Model):
    result: dict  # app.models.AnalyzeResult


class StageError(Model):
    stage: str
    error: str
