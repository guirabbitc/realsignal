"""Step 9: every quoted span in writer text must be verbatim in the transcript (MISSION invariant 2). No AI.

Only normalisation allowed: collapse whitespace and unify quote characters. Paraphrases fail.
"""

import re

MIN_WORDS = 3
_QUOTED = re.compile(r"[\"“]([^\"“”]+)[\"”]")
_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    return " ".join(text.translate(_QUOTE_CHARS).split())


def quoted_spans(text: str) -> list[str]:
    return [m.group(1).strip() for m in _QUOTED.finditer(text)]


def unverifiable_quotes(text: str, transcript: str) -> list[str]:
    haystack = normalize(transcript)
    return [
        span
        for span in quoted_spans(text)
        if len(span.split()) >= MIN_WORDS and normalize(span) not in haystack
    ]


def is_verifiable(text: str, transcript: str) -> bool:
    return not unverifiable_quotes(text, transcript)
