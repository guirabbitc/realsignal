"""The LLM only writes text: the summary and next steps. All OpenAI calls stay in this module."""
import json
from typing import Protocol

from app.contracts import Label, Sentence, Verdict
from app.pipeline.scoring import count_labels

OPENAI_MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = (
    "You help first-time founders read customer interviews. The judgments are already "
    "made: every sentence has a label, and the score and verdict are final. Do not "
    "re-judge, re-count or change them. Explain the verdict using the quoted sentences "
    "as evidence, then give concrete next steps. We measure evidence of real demand, "
    "never whether someone is lying. Reply with JSON: "
    '{"summary": string, "next_steps": [string, ...]} with 3 to 5 next steps.'
)


class Writer(Protocol):
    def write(
        self, idea: str, sentences: list[Sentence], score: float, verdict: Verdict
    ) -> tuple[str, list[str]]:
        """Return (summary, next_steps)."""
        ...


class OpenAIWriter:
    def __init__(self, api_key: str, model: str = OPENAI_MODEL, client=None):
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client = client
        self._model = model

    def write(
        self, idea: str, sentences: list[Sentence], score: float, verdict: Verdict
    ) -> tuple[str, list[str]]:
        payload = {
            "idea": idea,
            "score": score,
            "verdict": verdict.value,
            "label_counts": count_labels(sentences),
            "sentences": [
                {"speaker": s.speaker, "text": s.text, "label": s.label.value, "confidence": s.confidence}
                for s in sentences
                if s.label is not None
            ],
        }
        completion = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(completion.choices[0].message.content)
        return str(data["summary"]), [str(step) for step in data["next_steps"]]


class FakeWriter:
    """Templated text standing in for OpenAI. Used in tests and in fake mode."""

    def write(
        self, idea: str, sentences: list[Sentence], score: float, verdict: Verdict
    ) -> tuple[str, list[str]]:
        counts = count_labels(sentences)
        strongest = [s.text for s in sentences if s.label == Label.real_signal][:2]
        summary = (
            f"[fake writer] Score {score}/100, verdict {verdict.value}. "
            f"{counts['real_signal']} real-signal, {counts['polite']} polite and "
            f"{counts['neutral']} neutral sentences."
        )
        if strongest:
            summary += " Strongest evidence: " + " | ".join(strongest)
        next_steps = [
            "Ask the next interviewee about the last time the problem happened.",
            "Ask for a concrete commitment: a pre-order, a pilot date or an introduction.",
            "Run two more interviews before changing the idea.",
        ]
        return summary, next_steps
