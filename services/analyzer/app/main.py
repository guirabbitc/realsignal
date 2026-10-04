"""validate.ai analyzer: POST /analyze, GET /health. Stateless; never touches the database.

Logs ids, timings, model ids, rubric version and error codes only. Never transcript text (MISSION invariant 6).
"""

import asyncio
import hmac
import logging
import os
import time
import uuid
from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.errors import AnalysisTimeout, AnalyzerError, TranscriptTooLong
from app.models import AnalyzeRequest
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


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


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
