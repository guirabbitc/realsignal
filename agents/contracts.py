# GENERATED from packages/contracts/analyze.schema.json. Do not edit: run `pnpm contracts:generate`.

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, constr


class Label(StrEnum):
    real_signal = 'real_signal'
    polite = 'polite'
    neutral = 'neutral'


class Verdict(StrEnum):
    keep_going = 'keep_going'
    narrow_down = 'narrow_down'
    try_new_angle = 'try_new_angle'
    pivot = 'pivot'


class Sentence(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    order: conint(ge=0) = Field(
        ..., description='Position in the transcript, starting at 0.'
    )
    speaker: str
    text: str
    is_interviewee: bool
    label: Label | None = Field(
        ..., description='Null for interviewer sentences, which are not judged.'
    )
    confidence: confloat(ge=0.0, le=1.0) | None = Field(
        ..., description='Confidence in the label, 0 to 1. Null when label is null.'
    )


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    idea: constr(min_length=1) = Field(
        ..., description='The idea this interview tests.'
    )
    transcript: constr(min_length=1) = Field(
        ..., description='Interview text, one `Speaker: words` turn per line.'
    )


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    transcript: str = Field(
        ...,
        description='The transcript that was analyzed (produced by transcription when audio was sent).',
    )
    sentences: list[Sentence]
    score: confloat(ge=0.0, le=100.0) = Field(
        ..., description='Demand score, computed in Python.'
    )
    verdict: Verdict
    summary: str
    next_steps: list[str]


class TranscribeResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    transcript: str = Field(..., description='One `speaker: words` turn per line.')


class JudgeResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    transcript: str = Field(
        ...,
        description='The transcript that was analyzed (produced by transcription when audio was sent).',
    )
    sentences: list[Sentence]
    score: confloat(ge=0.0, le=100.0) = Field(
        ..., description='Demand score, computed in Python.'
    )
    verdict: Verdict


class WriteRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    idea: constr(min_length=1)
    judged: JudgeResponse


class WriteResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    summary: str
    next_steps: list[str]


class AnalyzeContract(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    request: AnalyzeRequest
    response: AnalyzeResponse
    transcribe_response: TranscribeResponse
    judge_response: JudgeResponse
    write_request: WriteRequest
    write_response: WriteResponse
