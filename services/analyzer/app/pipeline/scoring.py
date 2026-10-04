"""Step 5: the signal score. Plain arithmetic anyone can check (SPEC §5 "Score"). No AI."""

import math
from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class Scorable(Protocol):
    category: str
    p_real: float


def round_half_up(value: float) -> int:
    """Python's round() is banker's rounding (round(82.5) == 82); the spec says half up."""
    return math.floor(value + 0.5)


def group_of(category: str, categories: Mapping[str, Any]) -> str:
    return categories[category]["group"]


def count_non_neutral(statements: Iterable[Scorable], categories: Mapping[str, Any]) -> int:
    return sum(1 for s in statements if group_of(s.category, categories) in ("real", "polite"))


def compute_score(statements: Iterable[Scorable], categories: Mapping[str, Any]) -> int | None:
    """score = round_half_up(100 * R / (R + P)); null with no non-neutral sentences or R + P == 0.

    R = sum(w * p) over "real" sentences; P = sum(w * (1 - p)) over "polite" sentences.
    Neutral sentences count toward neither.
    """
    real = polite = 0.0
    counted = 0
    for s in statements:
        group = group_of(s.category, categories)
        weight = categories[s.category]["weight"]
        if group == "real":
            real += weight * s.p_real
            counted += 1
        elif group == "polite":
            polite += weight * (1 - s.p_real)
            counted += 1
    if counted == 0 or real + polite == 0:
        return None
    return round_half_up(100 * real / (real + polite))
