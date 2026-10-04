"""The only place the agents touch the analysis. They import the analyzer's pipeline directly
(SPEC §11): no HTTP call, and no analysis logic of their own."""
import os
from functools import lru_cache

from app.models import AnalyzeRequest, AnalyzeResult
from app.pipeline.analyze import Judged, judge_interview, run_analysis, write_readout
from app.pipeline.jev import Judge, SdkJevBackend
from app.pipeline.writer import OpenAIWriter, WriterBackend
from app.rubric import load_rubric


@lru_cache(maxsize=1)
def services() -> tuple[Judge, WriterBackend]:
    rubric = load_rubric()
    judge = Judge(SdkJevBackend(os.environ["TYPESAFE_API_KEY"], rubric["models"]["jev"]), rubric)
    writer = OpenAIWriter(os.environ["OPENAI_API_KEY"], os.environ["OPENAI_MODEL"])
    return judge, writer


def _request(idea: str, transcript: str) -> AnalyzeRequest:
    return AnalyzeRequest(idea=idea, transcript=transcript, kind="interview")


async def analyze(idea: str, transcript: str) -> AnalyzeResult:
    judge, writer = services()
    return await run_analysis(_request(idea, transcript), judge, writer, load_rubric())


async def judge(idea: str, transcript: str) -> Judged:
    return await judge_interview(_request(idea, transcript), services()[0], load_rubric())


async def write(idea: str, transcript: str, judged: Judged) -> AnalyzeResult:
    return await write_readout(_request(idea, transcript), judged, services()[1], load_rubric())
