"""Steps 3, 4 and 6: every judgment comes from Jev (MISSION invariant 4: Jev judges).

The backend is a protocol so unit tests can replay recorded answers without the network.
A Jev failure raises JevFailed; there is never a default answer (MISSION invariant 5).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from app.errors import JevFailed

QuestionSpec = dict[str, Any]  # {"type": "choice", "instructions": str, "criteria": {...}} | {"type": "noul", ...}


@dataclass(frozen=True)
class ChoiceResult:
    choice: str
    probabilities: dict[str, float]
    confidence: float


@dataclass(frozen=True)
class JevAnswers:
    choices: dict[str, ChoiceResult]
    nouls: dict[str, float]


class JevBackend(Protocol):
    model: str

    async def ask(self, state: Mapping[str, Any], questions: Mapping[str, QuestionSpec]) -> JevAnswers: ...


class SdkJevBackend:
    """Real backend: typesafe-sdk's AsyncTypeSafeClient (SDK retries 429s twice by default)."""

    def __init__(self, api_key: str, model: str, timeout: float = 10.0):
        from typesafe_sdk import AsyncTypeSafeClient

        self.model = model
        self._client = AsyncTypeSafeClient(api_key=api_key, model=model, timeout=timeout)

    async def ask(self, state: Mapping[str, Any], questions: Mapping[str, QuestionSpec]) -> JevAnswers:
        from typesafe_sdk import TypeSafeError

        try:
            response = await self._client.system_one(dict(state), dict(questions))
        except TypeSafeError as error:
            raise JevFailed(f"Jev request failed: {type(error).__name__}") from error
        return JevAnswers(
            choices={
                name: ChoiceResult(a.choice, dict(a.probabilities), float(a.confidence))
                for name, a in response.choices.items()
            },
            nouls={name: float(a.noul) for name, a in response.nouls.items()},
        )


@dataclass(frozen=True)
class SentenceJudgment:
    category: str
    category_probs: dict[str, float]
    confidence: float
    p_real: float


@dataclass(frozen=True)
class VerdictJudgment:
    verdict: str
    probabilities: dict[str, float]
    confidence: float


def _require_choice(answers: JevAnswers, key: str) -> ChoiceResult:
    if key not in answers.choices:
        raise JevFailed(f"Jev returned no answer for '{key}'.")
    return answers.choices[key]


def _require_noul(answers: JevAnswers, key: str) -> float:
    if key not in answers.nouls:
        raise JevFailed(f"Jev returned no answer for '{key}'.")
    return answers.nouls[key]


class Judge:
    def __init__(self, backend: JevBackend, rubric: Mapping[str, Any]):
        self.backend = backend
        self.rubric = rubric
        q = rubric["questions"]
        self._sentence_questions: dict[str, QuestionSpec] = {
            "category": {
                "type": "choice",
                "instructions": q["category"],
                "criteria": {name: c["description"] for name, c in rubric["categories"].items()},
            },
            "is_real_signal": {"type": "noul", "instructions": q["is_real_signal"]},
        }
        self._founder_questions: dict[str, QuestionSpec] = {
            "pitched_early": {"type": "noul", "instructions": q["pitched_early"]},
            "leading_questions": {"type": "noul", "instructions": q["leading_questions"]},
        }
        self._verdict_question: dict[str, QuestionSpec] = {
            "verdict": {"type": "choice", "instructions": q["verdict"], "criteria": dict(rubric["verdicts"])},
        }

    async def judge_sentence(self, idea: str, founder_question: str | None, sentence: str) -> SentenceJudgment:
        state = {
            "startup_idea": idea,
            "founder_question": founder_question or "(no founder question before this)",
            "customer_statement": sentence,
        }
        answers = await self.backend.ask(state, self._sentence_questions)
        category = _require_choice(answers, "category")
        return SentenceJudgment(
            category=category.choice,
            category_probs=category.probabilities,
            confidence=category.confidence,
            p_real=_require_noul(answers, "is_real_signal"),
        )

    async def judge_founder(self, idea: str, founder_turns: Sequence[str]) -> tuple[float | None, float | None]:
        if not founder_turns:
            return None, None
        state = {
            "startup_idea": idea,
            "founder_turns_in_order": [f"{i}. {turn}" for i, turn in enumerate(founder_turns, start=1)],
        }
        answers = await self.backend.ask(state, self._founder_questions)
        return _require_noul(answers, "pitched_early"), _require_noul(answers, "leading_questions")

    async def judge_verdict(self, idea: str, labelled_statements: Sequence[str], score: int | None) -> VerdictJudgment:
        """The mean of N identical calls (SPEC §0.2): Jev is self-consistent, not deterministic."""
        import asyncio

        state = {"startup_idea": idea, "signal_score_0_to_100": score, "customer_statements": list(labelled_statements)}
        samples = self.rubric["verdict_samples"]
        results = await asyncio.gather(*(self.backend.ask(state, self._verdict_question) for _ in range(samples)))
        choices = [_require_choice(r, "verdict") for r in results]
        options = list(self.rubric["verdicts"].keys())
        mean = {opt: sum(c.probabilities.get(opt, 0.0) for c in choices) / len(choices) for opt in options}
        best = max(options, key=lambda opt: (mean[opt], -options.index(opt)))  # ties: rubric order
        confidence = sum(c.confidence for c in choices) / len(choices)
        return VerdictJudgment(verdict=best, probabilities=mean, confidence=confidence)
