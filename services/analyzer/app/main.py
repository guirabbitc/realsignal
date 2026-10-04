"""Real Signal analyzer. Private service: receives data, returns JSON, never touches a database."""
import hmac
import logging
import os
from functools import lru_cache

import certifi
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import ValidationError

load_dotenv(find_dotenv())
# python.org builds of Python on macOS ship without root certificates
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from app.contracts import AnalyzeRequest, AnalyzeResponse  # noqa: E402
from app.pipeline import Clients, run_analysis  # noqa: E402
from app.pipeline.jev import JEV_BASE_URL, JEV_MODEL, FakeJudge, JevJudge  # noqa: E402
from app.pipeline.transcribe import ElevenLabsTranscriber, FakeTranscriber  # noqa: E402
from app.pipeline.writer import OPENAI_MODEL, FakeWriter, OpenAIWriter  # noqa: E402

logger = logging.getLogger("analyzer")
app = FastAPI(title="Real Signal analyzer")


def fake_mode() -> bool:
    return os.getenv("ANALYZER_FAKE_CLIENTS", "") == "1"


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=503, detail=f"{name} is not set")
    return value


@lru_cache
def _fake_clients() -> Clients:
    logger.warning("ANALYZER_FAKE_CLIENTS=1: using fake transcriber, judge and writer")
    return Clients(transcriber=FakeTranscriber(), judge=FakeJudge(), writer=FakeWriter())


def get_clients() -> Clients:
    if fake_mode():
        return _fake_clients()
    return Clients(
        transcriber=ElevenLabsTranscriber(_required("ELEVENLABS_API_KEY")),
        judge=JevJudge(
            _required("JEV_API_KEY"),
            base_url=os.getenv("JEV_BASE_URL", JEV_BASE_URL),
            model=os.getenv("JEV_MODEL", JEV_MODEL),
        ),
        writer=OpenAIWriter(_required("OPENAI_API_KEY"), model=os.getenv("OPENAI_MODEL", OPENAI_MODEL)),
    )


def require_key(x_analyzer_key: str | None = Header(default=None)) -> None:
    secret = os.getenv("ANALYZER_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="ANALYZER_SECRET is not set")
    if not x_analyzer_key or not hmac.compare_digest(x_analyzer_key, secret):
        raise HTTPException(status_code=401, detail="Missing or wrong X-Analyzer-Key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "fake" if fake_mode() else "live"}


@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(require_key)])
async def analyze(request: Request, clients: Clients = Depends(get_clients)) -> AnalyzeResponse:
    """JSON body (AnalyzeRequest), or multipart/form-data with `idea` and an audio `file`."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        idea = str(form.get("idea") or "").strip()
        file = form.get("file")
        if not idea or file is None or isinstance(file, str):
            raise HTTPException(status_code=422, detail="multipart needs `idea` and `file`")
        transcript = clients.transcriber.transcribe(
            await file.read(), file.filename or "audio", file.content_type or "application/octet-stream"
        )
    else:
        try:
            body = AnalyzeRequest.model_validate(await request.json())
        except (ValidationError, ValueError) as ex:
            raise HTTPException(status_code=422, detail=str(ex)) from ex
        idea, transcript = body.idea, body.transcript

    return run_analysis(idea, transcript, clients)
