"""Step 7: the confidence gate. Thin evidence always becomes need_more_evidence (MISSION invariant 3). No AI."""

from collections.abc import Mapping
from typing import Any


def pre_gate_failures(non_neutral: int, customer_words: int, gate: Mapping[str, Any]) -> list[str]:
    """Checked before the verdict calls; any failure skips them."""
    failures = []
    if non_neutral < gate["min_non_neutral"]:
        failures.append(f"Only {non_neutral} statements carried a signal (need {gate['min_non_neutral']}).")
    if customer_words < gate["min_customer_words"]:
        failures.append(f"Only {customer_words} customer words (need {gate['min_customer_words']}).")
    return failures


def post_gate_failure(verdict_confidence: float, gate: Mapping[str, Any]) -> str | None:
    """Checked after the verdict calls."""
    minimum = gate["min_verdict_confidence"]
    if verdict_confidence < minimum:
        return f"The verdict confidence was {verdict_confidence:.2f} (need {minimum})."
    return None


def missing_evidence_text(failures: list[str]) -> str | None:
    return " ".join(failures) if failures else None
