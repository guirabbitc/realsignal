import json

import pytest

from app.pipeline import judge
from evals.run import HERE, load_cases, report, score_case, slug


def test_sample_cases_load_and_line_up_with_the_analyzer(fakes):
    cases = load_cases(HERE / "cases" / "sample.json")
    assert [c["expected_verdict"] for c in cases] == ["keep_going", "pivot"]
    for case in cases:
        result = score_case(case, judge(case["idea"], case["transcript"], fakes))
        assert result.unmatched == 0
        assert result.labels_total == len(case["interviewee_sentences"])


def test_disagreements_are_reported(fakes):
    case = load_cases(HERE / "cases" / "sample.json")[1]
    case["interviewee_sentences"][3]["label"] = "real_signal"  # wrong on purpose: "That is a neat idea."
    result = score_case(case, judge(case["idea"], case["transcript"], fakes))
    assert any(d["text"] == "That is a neat idea." and d["expected"] == "real_signal" for d in result.disagreements)
    assert "That is a neat idea." in report([result])


def test_loader_accepts_fenced_json_and_human_verdicts(tmp_path):
    case = {
        "idea": "x", "transcript": "Interviewer: Why?\nAna: I paid for it.", "expected_verdict": "Try a new angle",
        "interviewee_sentences": [{"text": "I paid for it.", "label": "Real signal"}],
    }
    path = tmp_path / "batch.json"
    path.write_text("```json\n" + json.dumps([case]) + "\n```")
    loaded = load_cases(path)[0]
    assert loaded["expected_verdict"] == "try_new_angle" and loaded["interviewee_sentences"][0]["label"] == "real_signal"
    assert slug("Keep going") == "keep_going"


def test_loader_rejects_a_case_without_an_answer_key(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"idea": "x", "transcript": "A: b"}]))
    with pytest.raises(ValueError, match="missing"):
        load_cases(path)
