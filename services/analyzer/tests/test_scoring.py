from dataclasses import dataclass

from app.pipeline.scoring import compute_score, count_non_neutral, round_half_up


@dataclass
class S:
    category: str
    p_real: float


def test_round_half_up_not_bankers():
    assert round_half_up(82.5) == 83
    assert round_half_up(2.5) == 3
    assert round_half_up(2.4999) == 2


def test_formula(rubric):
    # R = 2*0.9 = 1.8 ; P = 1*(1-0.2) = 0.8 ; 100*1.8/2.6 = 69.23 -> 69
    assert compute_score([S("past_pain", 0.9), S("compliment", 0.2)], rubric["categories"]) == 69


def test_neutral_counts_toward_neither(rubric):
    base = [S("commitment", 0.8), S("hypothetical", 0.4)]
    assert compute_score(base, rubric["categories"]) == compute_score(
        base + [S("neutral", 0.0), S("neutral", 1.0)], rubric["categories"]
    )
    assert count_non_neutral(base + [S("neutral", 0.5)], rubric["categories"]) == 2


def test_polite_lowers_score_and_real_raises_it(rubric):
    c = rubric["categories"]
    assert compute_score([S("past_pain", 0.9)], c) == 100
    assert compute_score([S("compliment", 0.1)], c) == 0


def test_null_cases(rubric):
    c = rubric["categories"]
    assert compute_score([], c) is None
    assert compute_score([S("neutral", 0.9)], c) is None
    assert compute_score([S("past_pain", 0.0), S("compliment", 1.0)], c) is None  # R + P == 0
