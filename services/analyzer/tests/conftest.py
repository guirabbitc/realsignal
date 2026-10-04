"""Unit-test doubles. These replace Jev and OpenAI in UNIT tests only; the E2E always uses the real APIs
(FACTORY_RULES.md §2 rule 4)."""

import json
from pathlib import Path

import pytest

from app.errors import JevFailed
from app.pipeline.jev import ChoiceResult, JevAnswers, Judge
from app.pipeline.writer import WriterOutput
from app.rubric import load_rubric

FIXTURES = Path(__file__).parent.parent / "fixtures"
P_REAL_BY_GROUP = {"real": 0.9, "polite": 0.15, "none": 0.3}


def load_fixture(name: str) -> tuple[str, dict]:
    return (FIXTURES / f"{name}.txt").read_text(), json.loads((FIXTURES / f"{name}.labels.json").read_text())


class LabelledJev:
    """Answers each customer sentence with the human label from the fixtures; a stand-in for an ideal Jev."""

    model = "fake-jev"

    def __init__(self, categories_by_text: dict[str, str] | None = None, verdict_probs=None, verdict_conf=0.8,
                 fail=False):
        self.categories_by_text = categories_by_text or {}
        self.verdict_probs = verdict_probs or {"keep_going": 0.7, "narrow_down": 0.1, "new_angle": 0.1, "pivot": 0.1}
        self.verdict_conf = verdict_conf
        self.fail = fail
        self.calls: list[set[str]] = []

    async def ask(self, state, questions):
        self.calls.append(set(questions))
        if self.fail:
            raise JevFailed("simulated Jev outage")
        if "category" in questions:
            category = self.categories_by_text.get(state["customer_statement"], "neutral")
            group = load_rubric()["categories"][category]["group"]
            probs = {c: (0.8 if c == category else 0.05) for c in load_rubric()["categories"]}
            return JevAnswers({"category": ChoiceResult(category, probs, 0.8)},
                              {"is_real_signal": P_REAL_BY_GROUP[group]})
        if "pitched_early" in questions:
            return JevAnswers({}, {"pitched_early": 0.2, "leading_questions": 0.3})
        best = max(self.verdict_probs, key=self.verdict_probs.get)
        return JevAnswers({"verdict": ChoiceResult(best, dict(self.verdict_probs), self.verdict_conf)}, {})


class ScriptedWriter:
    model = "fake-writer"

    def __init__(self, outputs: list[WriterOutput] | None = None):
        self.outputs = outputs or []
        self.calls = 0

    async def write(self, payload):
        self.calls += 1
        if self.outputs:
            return self.outputs.pop(0)
        return WriterOutput(
            summary="The customer described real costs [#9].",
            reasons=["They pay for a manual workaround today [#9]."],
            next_questions=["What did you do last weekend?", "Who else handles bookings?", "What did it cost?"],
        )


def labelled_jev_for(name: str, **kwargs) -> LabelledJev:
    from app.pipeline.split import split_transcript

    transcript, labels = load_fixture(name)
    split = split_transcript(transcript, 80000)
    by_text = {cs.text: labels["expected_categories"][str(cs.position)] for cs in split.customer_sentences}
    return LabelledJev(by_text, **kwargs)


@pytest.fixture
def rubric():
    return load_rubric()


@pytest.fixture
def make_judge(rubric):
    return lambda backend: Judge(backend, rubric)
