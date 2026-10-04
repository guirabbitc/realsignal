from app.pipeline.gate import missing_evidence_text, post_gate_failure, pre_gate_failures


def test_pre_gate_thresholds(rubric):
    g = rubric["gate"]
    assert pre_gate_failures(4, 150, g) == []
    assert len(pre_gate_failures(3, 150, g)) == 1
    assert len(pre_gate_failures(4, 149, g)) == 1
    assert len(pre_gate_failures(0, 0, g)) == 2


def test_post_gate_threshold(rubric):
    g = rubric["gate"]
    assert post_gate_failure(0.6, g) is None
    assert post_gate_failure(0.59, g) is not None


def test_missing_evidence_text():
    assert missing_evidence_text([]) is None
    assert missing_evidence_text(["A.", "B."]) == "A. B."
