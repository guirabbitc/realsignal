"""Pydantic models for POST /analyze. Must match packages/contracts/analyze.schema.json (tested)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Kind = Literal["interview", "demo"]
Category = Literal["commitment", "past_pain", "hypothetical", "compliment", "neutral"]
Verdict = Literal["keep_going", "narrow_down", "new_angle", "pivot", "need_more_evidence"]
ErrorCode = Literal[
    "bad_key",
    "unlabelled_transcript",
    "transcript_too_long",
    "invalid_request",
    "jev_failed",
    "openai_failed",
    "writer_unverifiable",
    "timeout",
]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idea: str = Field(min_length=1, max_length=500)
    transcript: str = Field(min_length=1, max_length=80000)
    kind: Kind
    interviewee_label: str | None = Field(default=None, max_length=200)
    audio_url: None = None


class Statement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=1)
    speaker: Literal["customer"] = "customer"
    quote: str = Field(min_length=1)
    founder_question: str | None
    category: Category
    category_probs: dict[str, float]
    p_real: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class FounderFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    talk_ratio: float
    pitched_early: float
    leading_questions: float


class ModelVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jev: str
    openai: str
    rubric: str
    founder_flags: FounderFlags


class AnalyzeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int | None = Field(ge=0, le=100)
    verdict: Verdict
    verdict_confidence: float | None
    founder_talk_ratio: float | None
    pitched_early: float | None
    leading_questions: float | None
    statements: list[Statement]
    summary: str
    reasons: list[str]
    next_questions: list[str] = Field(min_length=3, max_length=3)
    missing_evidence: str | None
    model_versions: ModelVersions


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


# POST /transcribe. Must match packages/contracts/transcribe.schema.json (tested).

TranscribeErrorCode = Literal[
    "bad_key",
    "invalid_request",
    "audio_too_large",
    "empty_audio",
    "no_speech",
    "transcription_failed",
    "transcription_not_configured",
]
TranscribeFailureReason = Literal["rate_limited", "upstream_error", "timeout", "rejected"]


class TranscribeTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    start: float | None = Field(ge=0)
    end: float | None = Field(ge=0)


class TranscribeSpeaker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    turns: int = Field(ge=1)
    words: int = Field(ge=0)
    seconds: float = Field(ge=0)
    sample: list[str] = Field(min_length=1, max_length=2)


class TranscribeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_s: float | None = Field(ge=0)
    language_code: str | None
    model: str = Field(min_length=1)
    speakers: list[TranscribeSpeaker] = Field(min_length=1)
    turns: list[TranscribeTurn] = Field(min_length=1)
    suggested_founder_id: str = Field(min_length=1)


class TranscribeErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: TranscribeErrorCode
    message: str
    reason: TranscribeFailureReason | None = None


class TranscribeErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: TranscribeErrorDetail
