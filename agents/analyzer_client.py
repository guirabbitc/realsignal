"""The only place the agents talk to the analyzer. Same contract and secret as the web app."""
import os

import httpx

from contracts import (
    AnalyzeRequest,
    AnalyzeResponse,
    JudgeResponse,
    TranscribeResponse,
    WriteRequest,
    WriteResponse,
)

TIMEOUT_SECONDS = 300


async def _post(path: str, **kwargs) -> dict:
    url = os.environ["ANALYZER_URL"].rstrip("/") + path
    headers = {"X-Analyzer-Key": os.environ["ANALYZER_SECRET"]}
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
        response = await http.post(url, headers=headers, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"Analyzer {path} returned {response.status_code}: {response.text[:300]}")
    return response.json()


async def analyze(idea: str, transcript: str) -> AnalyzeResponse:
    body = AnalyzeRequest(idea=idea, transcript=transcript)
    return AnalyzeResponse.model_validate(await _post("/analyze", json=body.model_dump()))


async def analyze_audio(idea: str, audio: bytes, filename: str, mime_type: str) -> AnalyzeResponse:
    data = await _post("/analyze", data={"idea": idea}, files={"file": (filename, audio, mime_type)})
    return AnalyzeResponse.model_validate(data)


async def transcribe(audio: bytes, filename: str, mime_type: str) -> TranscribeResponse:
    data = await _post("/transcribe", files={"file": (filename, audio, mime_type)})
    return TranscribeResponse.model_validate(data)


async def judge(idea: str, transcript: str) -> JudgeResponse:
    body = AnalyzeRequest(idea=idea, transcript=transcript)
    return JudgeResponse.model_validate(await _post("/judge", json=body.model_dump()))


async def write(idea: str, judged: JudgeResponse) -> WriteResponse:
    body = WriteRequest(idea=idea, judged=judged)
    return WriteResponse.model_validate(await _post("/write", json=body.model_dump(mode="json")))
