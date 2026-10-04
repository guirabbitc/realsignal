"""validate.ai analyzer: POST /analyze, POST /transcribe, GET /health. Stateless; never touches the database.

Logs ids, timings, model ids, rubric version and error codes only. Never transcript text (MISSION invariant 6).
"""

import asyncio
import hmac
import logging
import os
import tempfile
import time
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException

from app.errors import (
    AnalysisTimeout,
    AnalyzerError,
    AudioTooLarge,
    EmptyAudio,
    TranscriptionFailed,
    TranscriptionNotConfigured,
    TranscriptTooLong,
)
from app.models import AnalyzeRequest
from app.pipeline import transcribe as scribe
from app.pipeline.analyze import run_analysis
from app.pipeline.jev import Judge, SdkJevBackend
from app.pipeline.writer import OpenAIWriter, WriterBackend
from app.rubric import load_rubric

TIMEOUT_SECONDS = 120
log = logging.getLogger("analyzer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="validate.ai analyzer", docs_url=None, redoc_url=None, openapi_url=None)


@lru_cache(maxsize=1)
def get_services() -> tuple[Judge, WriterBackend]:
    rubric = load_rubric()
    judge = Judge(SdkJevBackend(os.environ["TYPESAFE_API_KEY"], rubric["models"]["jev"]), rubric)
    writer = OpenAIWriter(os.environ["OPENAI_API_KEY"], os.environ["OPENAI_MODEL"])
    return judge, writer


def _error(code: str, message: str, status: int, reason: str | None = None) -> JSONResponse:
    error = {"code": code, "message": message} | ({"reason": reason} if reason else {})
    return JSONResponse({"error": error}, status_code=status)


def _key_ok(given: str | None) -> bool:
    expected = os.environ.get("ANALYZER_KEY", "")
    return bool(expected) and bool(given) and hmac.compare_digest(given.encode(), expected.encode())


REQUIRED_ENV = ("ANALYZER_KEY", "TYPESAFE_API_KEY", "OPENAI_API_KEY", "OPENAI_MODEL")


@app.get("/health")
async def health() -> JSONResponse:
    """ok only when the analyzer can actually run an analysis. Reports missing variable NAMES, never values."""
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        return JSONResponse({"status": "error", "missing_config": missing}, status_code=503)
    return JSONResponse({"status": "ok"})


@app.post("/analyze")
async def analyze(request: Request) -> JSONResponse:
    request_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    if not _key_ok(request.headers.get("x-analyzer-key")):
        log.warning("analyze rejected request_id=%s code=bad_key", request_id)
        return _error("bad_key", "Missing or wrong X-Analyzer-Key.", 401)

    rubric = load_rubric()
    try:
        body = await request.json()
        max_chars = rubric["limits"]["max_transcript_chars"]
        if isinstance(body, dict) and isinstance(body.get("transcript"), str) and len(body["transcript"]) > max_chars:
            raise TranscriptTooLong(f"Transcript is longer than {max_chars} characters.")
        req = AnalyzeRequest.model_validate(body)
    except AnalyzerError as error:
        return _error(error.code, error.message, error.status)
    except (ValidationError, ValueError):
        return _error("invalid_request", "The request body does not match the contract.", 422)

    try:
        judge, writer = get_services()
        async with asyncio.timeout(TIMEOUT_SECONDS):
            result = await run_analysis(req, judge, writer, rubric)
    except TimeoutError:
        error = AnalysisTimeout(f"Analysis took longer than {TIMEOUT_SECONDS}s.")
        log.warning("analyze failed request_id=%s code=%s", request_id, error.code)
        return _error(error.code, error.message, error.status)
    except AnalyzerError as error:
        log.warning("analyze failed request_id=%s code=%s", request_id, error.code)
        return _error(error.code, error.message, error.status)

    log.info(
        "analyze ok request_id=%s ms=%d statements=%d verdict=%s jev=%s openai=%s rubric=%s",
        request_id,
        (time.monotonic() - started) * 1000,
        len(result.statements),
        result.verdict,
        result.model_versions.jev,
        result.model_versions.openai,
        result.model_versions.rubric,
    )
    return JSONResponse(result.model_dump())


AUDIO_EXTENSIONS = frozenset({".mp3", ".m4a", ".wav", ".webm", ".ogg", ".mp4"})
# Multipart boundaries and the num_speakers field on top of the file itself.
MULTIPART_OVERHEAD_BYTES = 64 * 1024
CHUNK_BYTES = 1024 * 1024


def _audio_max_bytes() -> int:
    return int(os.environ.get("AUDIO_MAX_MB") or 100) * 1024 * 1024


def _num_speakers(raw: object) -> int:
    if raw is None or raw == "":
        return 2
    if not isinstance(raw, str) or not raw.isdigit() or not 1 <= int(raw) <= 4:
        raise AnalyzerError("num_speakers must be an integer from 1 to 4.")
    return int(raw)


async def _spool(upload: UploadFile, suffix: str, max_bytes: int) -> tuple[Path, int]:
    """Copies the upload to a temp file that only lives for this request (the caller deletes it)."""
    tmp_dir = os.environ.get("AUDIO_TMP_DIR") or None
    with tempfile.NamedTemporaryFile(prefix="transcribe-", suffix=suffix, delete=False, dir=tmp_dir) as handle:
        path, size = Path(handle.name), 0
        try:
            while chunk := await upload.read(CHUNK_BYTES):
                size += len(chunk)
                if size > max_bytes:
                    raise AudioTooLarge(f"The audio is larger than {max_bytes // (1024 * 1024)} MB.")
                handle.write(chunk)
        except BaseException:
            handle.close()
            path.unlink(missing_ok=True)
            raise
    return path, size


@app.post("/transcribe")
async def transcribe(request: Request) -> JSONResponse:
    """Audio in, voices and turns out. The audio is never stored: one temp file, deleted in `finally`."""
    request_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    if not _key_ok(request.headers.get("x-analyzer-key")):
        log.warning("transcribe rejected request_id=%s code=bad_key", request_id)
        return _error("bad_key", "Missing or wrong X-Analyzer-Key.", 401)

    model = os.environ.get("ELEVENLABS_STT_MODEL") or scribe.DEFAULT_MODEL
    max_bytes = _audio_max_bytes()
    path: Path | None = None
    size = 0
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise TranscriptionNotConfigured("Transcription is not configured.")
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > max_bytes + MULTIPART_OVERHEAD_BYTES:
            raise AudioTooLarge(f"The audio is larger than {max_bytes // (1024 * 1024)} MB.")
        try:
            form = await request.form(max_files=1, max_fields=4)
        except (HTTPException, MultiPartException):
            raise AnalyzerError("Send multipart/form-data with the audio in a field named file.") from None
        try:
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                raise AnalyzerError("Send the audio in a field named file.")
            num_speakers = _num_speakers(form.get("num_speakers"))
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in AUDIO_EXTENSIONS:
                raise AnalyzerError(f"Send one of: {', '.join(sorted(AUDIO_EXTENSIONS))}.")
            path, size = await _spool(upload, suffix, max_bytes)
            content_type = upload.content_type or "application/octet-stream"
        finally:
            await form.close()
        if size == 0:
            raise EmptyAudio("The audio file is empty.")

        async with scribe.make_client() as client:
            # A neutral name: the founder's file name never leaves this service.
            raw = await scribe.call_scribe(path, f"audio{suffix}", content_type, num_speakers,
                                           api_key=api_key, model=model, client=client)
        result = scribe.to_result(raw, model)
    except TranscriptionFailed as error:
        log.warning("transcribe failed request_id=%s bytes=%d ms=%d code=%s reason=%s", request_id, size,
                    (time.monotonic() - started) * 1000, error.code, error.reason)
        return _error(error.code, error.message, error.status, error.reason)
    except AnalyzerError as error:
        log.warning("transcribe failed request_id=%s bytes=%d ms=%d code=%s", request_id, size,
                    (time.monotonic() - started) * 1000, error.code)
        return _error(error.code, error.message, error.status)
    finally:
        if path is not None:
            path.unlink(missing_ok=True)

    log.info(
        "transcribe ok request_id=%s bytes=%d ms=%d model=%s duration_s=%s speakers=%d turns=%d",
        request_id, size, (time.monotonic() - started) * 1000, model, result.duration_s, len(result.speakers),
        len(result.turns),
    )
    return JSONResponse(result.model_dump())
