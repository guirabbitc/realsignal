"""The tester's scoring, on cases built from the analyzer's reference fixtures and their human labels."""
import asyncio
import json

import pytest

import pipeline
from app.pipeline.split import split_transcript
from tester.scoring import load_cases, report, score_case
from tests.doubles import ANALYZER, IDEA, fake_services


def fixture_case(name: str) -> dict:
    """One case in the generator's JSON format, from a fixture and its .labels.json."""
    transcript = (ANALYZER / "fixtures" / f"{name}.txt").read_text()
    labels = json.loads((ANALYZER / "fixtures" / f"{name}.labels.json").read_text())
    split = split_transcript(transcript, 80000)
    return {
        "id": name,
        "idea": IDEA,
        "persona": "fixture",
        "difficulty": "easy",
        "expected_verdict": labels["allowed_verdicts"][0],
        "allowed_verdicts": labels["allowed_verdicts"],
        "transcript": transcript,
        "customer_sentences": [
            {"text": cs.text, "category": labels["expected_categories"][str(cs.position)]}
            for cs in split.customer_sentences
        ],
        "founder": {"pitched_early": False, "leading_questions": False},
    }


@pytest.fixture
def cases(tmp_path):
    path = tmp_path / "fixtures.json"
    path.write_text("```json\n" + json.dumps([fixture_case("real_pain"), fixture_case("mixed")]) + "\n```")
    return load_cases(path)


def test_cases_load_and_an_ideal_judge_scores_full_marks(cases, monkeypatch):
    case = cases[0]
    assert case["id"] == "fixtures/real_pain" and not case["warnings"]
    monkeypatch.setattr(pipeline, "services", lambda: fake_services("real_pain"))
    result = score_case(case, asyncio.run(pipeline.judge(case["idea"], case["transcript"])))
    assert result.unmatched == 0 and result.categories_right == result.categories_total > 0
    assert result.verdict_allowed and result.flags_right == result.flags_total == 2


def test_a_wrong_key_shows_up_as_a_disagreement(cases, monkeypatch):
    case = cases[0]
    wrong = case["customer_sentences"][0]
    wrong["category"] = "compliment" if wrong["category"] != "compliment" else "neutral"
    monkeypatch.setattr(pipeline, "services", lambda: fake_services("real_pain"))
    result = score_case(case, asyncio.run(pipeline.judge(case["idea"], case["transcript"])))
    assert [d["text"] for d in result.disagreements] == [wrong["text"]]
    assert wrong["text"] in report([result])


def test_a_key_that_ignores_the_gate_is_flagged_as_a_broken_case(tmp_path):
    case = {
        "idea": "x", "expected_verdict": "Keep going",
        "transcript": "Founder: Would you pay?\nCustomer: I paid 60 dollars last month.",
        "customer_sentences": [{"text": "I paid 60 dollars last month.", "category": "Past pain"}],
    }
    path = tmp_path / "thin.json"
    path.write_text(json.dumps([case]))
    loaded = load_cases(path)[0]
    assert loaded["expected_verdict"] == "keep_going" and loaded["customer_sentences"][0]["category"] == "past_pain"
    assert "under the gate" in loaded["warnings"][0]


def test_a_case_without_an_answer_key_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"idea": "x", "transcript": "Founder: a\nCustomer: b"}]))
    with pytest.raises(ValueError, match="missing"):
        load_cases(path)
