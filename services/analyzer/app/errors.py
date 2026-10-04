"""Analyzer errors. Each maps to one contract error code and HTTP status (SPEC §6)."""


class AnalyzerError(Exception):
    code: str = "invalid_request"
    status: int = 422

    def __init__(self, message: str, code: str | None = None, status: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status = status


class UnlabelledTranscript(AnalyzerError):
    code, status = "unlabelled_transcript", 422


class TranscriptTooLong(AnalyzerError):
    code, status = "transcript_too_long", 422


class JevFailed(AnalyzerError):
    code, status = "jev_failed", 502


class OpenAIFailed(AnalyzerError):
    code, status = "openai_failed", 502


class WriterUnverifiable(AnalyzerError):
    code, status = "writer_unverifiable", 502


class AnalysisTimeout(AnalyzerError):
    code, status = "timeout", 504
