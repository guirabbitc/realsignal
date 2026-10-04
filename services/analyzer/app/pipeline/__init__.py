"""The analysis pipeline: split -> judge (Jev) -> score (Python) -> verdict (Jev) -> write (OpenAI)."""
from dataclasses import dataclass

from app.contracts import AnalyzeResponse, Sentence
from app.pipeline.jev import Judge
from app.pipeline.scoring import compute_score
from app.pipeline.split import split_transcript
from app.pipeline.transcribe import Transcriber
from app.pipeline.writer import Writer


@dataclass
class Clients:
    transcriber: Transcriber
    judge: Judge
    writer: Writer


def run_analysis(idea: str, transcript: str, clients: Clients) -> AnalyzeResponse:
    drafts = split_transcript(transcript)
    to_judge = [d for d in drafts if d.is_interviewee]
    judgments = clients.judge.label_sentences(idea, transcript, [d.text for d in to_judge])
    if len(judgments) != len(to_judge):
        raise RuntimeError(
            f"Judge returned {len(judgments)} judgments for {len(to_judge)} sentences"
        )
    by_order = {d.order: j for d, j in zip(to_judge, judgments)}

    sentences = []
    for d in drafts:
        j = by_order.get(d.order)
        sentences.append(
            Sentence(
                order=d.order,
                speaker=d.speaker,
                text=d.text,
                is_interviewee=d.is_interviewee,
                label=j.label if j else None,
                confidence=j.confidence if j else None,
            )
        )

    score = compute_score(sentences)
    verdict = clients.judge.pick_verdict(idea, sentences, score)
    summary, next_steps = clients.writer.write(idea, sentences, score, verdict)

    return AnalyzeResponse(
        transcript=transcript,
        sentences=sentences,
        score=score,
        verdict=verdict,
        summary=summary,
        next_steps=next_steps,
    )
