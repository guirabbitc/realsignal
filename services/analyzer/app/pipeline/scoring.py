"""All the math lives here. Jev is unreliable at counting, so totals are never asked of a model."""
from app.contracts import Label, Sentence

# How much one sentence of each label counts as evidence, before its confidence.
NEUTRAL_WEIGHT = 0.5


def compute_score(sentences: list[Sentence]) -> float:
    """Demand score from 0 to 100.

    The share of confidence-weighted evidence that is real signal. Polite
    sentences count fully against it, neutral ones count half.
    """
    real = polite = neutral = 0.0
    for s in sentences:
        if s.label is None or s.confidence is None:
            continue
        if s.label == Label.real_signal:
            real += s.confidence
        elif s.label == Label.polite:
            polite += s.confidence
        else:
            neutral += s.confidence

    total = real + polite + NEUTRAL_WEIGHT * neutral
    if total == 0:
        return 0.0
    return round(100 * real / total, 1)


def count_labels(sentences: list[Sentence]) -> dict[str, int]:
    counts = {label.value: 0 for label in Label}
    for s in sentences:
        if s.label is not None:
            counts[s.label.value] += 1
    return counts
