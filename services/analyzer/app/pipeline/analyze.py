"""Orchestrates the pipeline: split -> Jev -> score -> gate -> verdict -> OpenAI -> verify.

It runs as two halves, judge_interview (everything decided) and write_readout (the text), so they can be
called one after the other (run_analysis) or from separate processes.

Jev judges, OpenAI writes, Python counts.
"""

import asyncio
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from app.errors import WriterUnverifiable
from app.models import AnalyzeRequest, AnalyzeResult, FounderFlags, ModelVersions, Statement, Verdict
from app.pipeline.gate import missing_evidence_text, post_gate_failure, pre_gate_failures
from app.pipeline.jev import Judge
from app.pipeline.scoring import compute_score, count_non_neutral, group_of
from app.pipeline.split import split_transcript
from app.pipeline.verify import is_verifiable
from app.pipeline.writer import WriterBackend, WriterOutput

NEED_MORE_EVIDENCE = "need_more_evidence"


async def _judge_customer_sentences(judge: Judge, idea: str, split, concurrency: int) -> list[Statement]:
    semaphore = asyncio.Semaphore(concurrency)

    async def one(cs):
        async with semaphore:
            j = await judge.judge_sentence(idea, cs.founder_question, cs.text)
        return Statement(
            position=cs.position,
            quote=cs.text,
            founder_question=cs.founder_question,
            category=j.category,
            category_probs=j.category_probs,
            p_real=j.p_real,
            confidence=j.confidence,
        )

    return list(await asyncio.gather(*(one(cs) for cs in split.customer_sentences)))


def _writer_payload(req: AnalyzeRequest, rubric, statements, score, verdict, confidence, missing, founder):
    categories = rubric["categories"]
    signal = [s for s in statements if group_of(s.category, categories) != "none"]
    return {
        "idea": req.idea,
        "kind": req.kind,
        "verdict": verdict,
        "score": score,
        "verdict_confidence": confidence,
        "missing_evidence": missing,
        "founder": founder,
        "statements": [
            {"position": s.position, "quote": s.quote, "category": s.category, "p_real": round(s.p_real, 2)}
            for s in signal
        ],
    }


def _verified(output: WriterOutput, transcript: str) -> WriterOutput | None:
    """Drop unverifiable reasons; reject the whole output if summary or next questions fail."""
    if not is_verifiable(output.summary, transcript):
        return None
    if len(output.next_questions) != 3 or not all(is_verifiable(q, transcript) for q in output.next_questions):
        return None
    reasons = [r for r in output.reasons if is_verifiable(r, transcript)]
    return WriterOutput(summary=output.summary, reasons=reasons, next_questions=output.next_questions)


class Judged(BaseModel):
    """Everything decided before any text is written: the output of the judging half of the pipeline.

    It is plain data, so the judging and the writing can run in different processes (the Fetch.ai
    specialist agents pass it between them). The writer never changes any of it (MISSION invariant 4).
    """

    statements: list[Statement]
    score: int | None
    verdict: Verdict
    verdict_confidence: float | None
    founder_talk_ratio: float | None
    pitched_early: float | None
    leading_questions: float | None
    missing_evidence: str | None
    jev_model: str


async def judge_interview(req: AnalyzeRequest, judge: Judge, rubric: Mapping[str, Any]) -> Judged:
    """Steps split -> Jev -> score -> gate -> verdict."""
    split = split_transcript(req.transcript, rubric["limits"]["max_transcript_chars"])

    statements, (pitched_early, leading_questions) = await asyncio.gather(
        _judge_customer_sentences(judge, req.idea, split, rubric["concurrency"]),
        judge.judge_founder(req.idea, split.founder_turns),
    )

    categories = rubric["categories"]
    score = compute_score(statements, categories)
    failures = pre_gate_failures(count_non_neutral(statements, categories), split.customer_words, rubric["gate"])

    verdict, verdict_confidence = NEED_MORE_EVIDENCE, None
    if not failures:
        labelled = [
            f'[#{s.position}] ({s.category}, p_real {s.p_real:.2f}) "{s.quote}"'
            for s in statements
            if group_of(s.category, categories) != "none"
        ]
        judged = await judge.judge_verdict(req.idea, labelled, score)
        verdict_confidence = judged.confidence
        failure = post_gate_failure(judged.confidence, rubric["gate"])
        if failure:
            failures.append(failure)
        else:
            verdict = judged.verdict

    return Judged(
        statements=statements,
        score=score,
        verdict=verdict,
        verdict_confidence=verdict_confidence,
        founder_talk_ratio=split.founder_talk_ratio,
        pitched_early=pitched_early,
        leading_questions=leading_questions,
        missing_evidence=missing_evidence_text(failures),
        jev_model=judge.backend.model,
    )


async def write_readout(
    req: AnalyzeRequest, judged: Judged, writer: WriterBackend, rubric: Mapping[str, Any]
) -> AnalyzeResult:
    """Steps OpenAI -> verify. Returns the full result; every judged value is passed through unchanged."""
    flags = rubric["founder_flags"]
    founder = {
        "talk_ratio": judged.founder_talk_ratio,
        "pitched_early": judged.pitched_early,
        "leading_questions": judged.leading_questions,
        "thresholds": flags,
    }
    payload = _writer_payload(
        req, rubric, judged.statements, judged.score, judged.verdict, judged.verdict_confidence,
        judged.missing_evidence, founder,
    )

    written = None
    for _ in range(2):  # one retry (SPEC §5 step 9)
        written = _verified(await writer.write(payload), req.transcript)
        if written:
            break
    if written is None:
        raise WriterUnverifiable("The read-out quoted words that are not in the transcript.")

    return AnalyzeResult(
        score=judged.score,
        verdict=judged.verdict,
        verdict_confidence=judged.verdict_confidence,
        founder_talk_ratio=judged.founder_talk_ratio,
        pitched_early=judged.pitched_early,
        leading_questions=judged.leading_questions,
        statements=judged.statements,
        summary=written.summary,
        reasons=written.reasons,
        next_questions=written.next_questions,
        missing_evidence=judged.missing_evidence,
        model_versions=ModelVersions(
            jev=judged.jev_model,
            openai=writer.model,
            rubric=rubric["version"],
            founder_flags=FounderFlags(**flags),
        ),
    )


async def run_analysis(
    req: AnalyzeRequest, judge: Judge, writer: WriterBackend, rubric: Mapping[str, Any]
) -> AnalyzeResult:
    return await write_readout(req, await judge_interview(req, judge, rubric), writer, rubric)
