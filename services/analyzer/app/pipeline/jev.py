"""Every judgment comes from Jev. All Jev calls stay in this module so the provider can be swapped.

Uses TypeSafe's HTTP API (https://docs.typesafe.ai/api): POST {base}/v1/systemone with
`state`, `model` and a map of typed `questions`; each answer comes back under the same key.
"""
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.contracts import Label, Sentence, Verdict
from app.pipeline.scoring import count_labels

JEV_BASE_URL = "https://api.typesafe.ai"
JEV_MODEL = "jev-latest"
# Keeps each request well inside Jev's ~32k token limit for state + questions.
SENTENCES_PER_REQUEST = 20

LABEL_CRITERIA = {
    Label.real_signal.value: (
        "Evidence of real demand: something the person already did, paid, lost or tried, "
        "or a concrete commitment of money, time or reputation."
    ),
    Label.polite.value: (
        "Politeness without evidence: compliments, enthusiasm, or hypothetical "
        "statements about what they would or might do."
    ),
    Label.neutral.value: "Neither: facts, small talk, questions or statements unrelated to demand.",
}

VERDICT_CRITERIA = {
    Verdict.keep_going.value: "Strong evidence of demand from this interview. Continue with the idea as it is.",
    Verdict.narrow_down.value: "Real evidence, but only for part of the idea or one kind of customer. Focus there.",
    Verdict.try_new_angle.value: "A real problem shows up, but not the one this idea solves. Reframe the idea around it.",
    Verdict.pivot.value: "Little or no evidence of demand beyond politeness. Change the idea.",
}


@dataclass
class Judgment:
    label: Label
    confidence: float


class Judge(Protocol):
    def label_sentences(self, idea: str, transcript: str, sentences: list[str]) -> list[Judgment]:
        """One judgment per sentence, in the same order."""
        ...

    def pick_verdict(self, idea: str, sentences: list[Sentence], score: float) -> Verdict: ...


class JevJudge:
    def __init__(
        self,
        api_key: str,
        base_url: str = JEV_BASE_URL,
        model: str = JEV_MODEL,
        http: httpx.Client | None = None,
    ):
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/v1/systemone"
        self._model = model
        self._http = http or httpx.Client(timeout=60)

    def _ask(self, state: dict, questions: dict) -> dict:
        response = self._http.post(
            self._url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"state": state, "model": self._model, "questions": questions},
        )
        response.raise_for_status()
        return response.json()["answers"]

    def label_sentences(self, idea: str, transcript: str, sentences: list[str]) -> list[Judgment]:
        judgments: list[Judgment] = []
        state = {"idea": idea, "transcript": transcript}
        for start in range(0, len(sentences), SENTENCES_PER_REQUEST):
            batch = sentences[start : start + SENTENCES_PER_REQUEST]
            questions = {
                f"s{start + i}": {
                    "type": "choice",
                    "instructions": (
                        "Classify this sentence said by the interviewee, as evidence of "
                        f"demand for the idea: {sentence!r}"
                    ),
                    "criteria": LABEL_CRITERIA,
                }
                for i, sentence in enumerate(batch)
            }
            answers = self._ask(state, questions)
            for i in range(len(batch)):
                answer = answers[f"s{start + i}"]
                judgments.append(
                    Judgment(label=Label(answer["choice"]), confidence=float(answer["confidence"]))
                )
        return judgments

    def pick_verdict(self, idea: str, sentences: list[Sentence], score: float) -> Verdict:
        state = {
            "idea": idea,
            "demand_score_0_to_100": score,
            "label_counts": count_labels(sentences),
            "interviewee_sentences": [
                {"text": s.text, "label": s.label.value, "confidence": s.confidence}
                for s in sentences
                if s.label is not None
            ],
        }
        questions = {
            "verdict": {
                "type": "choice",
                "instructions": "Given the labelled sentences and the demand score, what should the founder do next?",
                "criteria": VERDICT_CRITERIA,
            }
        }
        return Verdict(self._ask(state, questions)["verdict"]["choice"])


REAL_SIGNAL_CUES = (
    "last week", "last month", "last year", "i paid", "i spent", "cost us", "i tried",
    "i already", "i still use", "i stopped", "i cancelled", "threw away", "we ordered",
    "i will pay", "sign me up", "i booked", "introduce you", "i'll send",
)
POLITE_CUES = (
    "love it", "cool idea", "great", "awesome", "sounds nice", "sounds perfect", "i like it",
    "i would", "i'd ", "i could see", "would love", "good luck", "maybe",
)


class FakeJudge:
    """Keyword rules standing in for Jev. Used in tests and in fake mode; makes no network calls."""

    def label_sentences(self, idea: str, transcript: str, sentences: list[str]) -> list[Judgment]:
        judgments = []
        for sentence in sentences:
            text = sentence.lower()
            if any(cue in text for cue in REAL_SIGNAL_CUES):
                judgments.append(Judgment(Label.real_signal, 0.9))
            elif any(cue in text for cue in POLITE_CUES):
                judgments.append(Judgment(Label.polite, 0.85))
            else:
                judgments.append(Judgment(Label.neutral, 0.6))
        return judgments

    def pick_verdict(self, idea: str, sentences: list[Sentence], score: float) -> Verdict:
        if score >= 70:
            return Verdict.keep_going
        if score >= 45:
            return Verdict.narrow_down
        if score >= 20:
            return Verdict.try_new_angle
        return Verdict.pivot
