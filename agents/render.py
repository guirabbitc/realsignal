"""Turn analyzer results into chat text. Presentation only: nothing here judges or counts evidence."""
from app.models import AnalyzeResult
from app.pipeline.analyze import Judged
from app.rubric import load_rubric

TOP_QUOTES = 3
MAX_STATEMENTS_SHOWN = 30

VERDICT_TEXT = {
    "keep_going": "Keep going",
    "narrow_down": "Narrow down",
    "new_angle": "Try a new angle",
    "pivot": "Pivot",
    "need_more_evidence": "Not enough evidence yet",
}
CATEGORY_TEXT = {
    "commitment": "Commitment",
    "past_pain": "Past pain",
    "hypothetical": "Hypothetical",
    "compliment": "Compliment",
    "neutral": "Neutral",
}


def _percent(value: float) -> str:
    return f"{round(value * 100)}%"


def verdict_lines(judged: Judged | AnalyzeResult) -> list[str]:
    lines = [f"**Verdict: {VERDICT_TEXT[judged.verdict]}**"]
    if judged.score is not None:
        # a blank line: chat clients render a single newline as a space
        lines += ["", f"Signal score: {judged.score} / 100"]
    if judged.missing_evidence:
        lines += ["", judged.missing_evidence]
    return lines


def _real_quotes(statements) -> list:
    categories = load_rubric()["categories"]
    real = [s for s in statements if categories[s.category]["group"] == "real"]
    return sorted(real, key=lambda s: s.p_real, reverse=True)[:TOP_QUOTES]


def _founder_lines(result: AnalyzeResult) -> list[str]:
    """The founder's own interviewing mistakes, shown only when a value passes its threshold."""
    limits = result.model_versions.founder_flags
    lines = []
    if result.founder_talk_ratio is not None and result.founder_talk_ratio > limits.talk_ratio:
        lines.append(f"- You did {_percent(result.founder_talk_ratio)} of the talking.")
    if result.pitched_early is not None and result.pitched_early > limits.pitched_early:
        lines.append("- You pitched the idea before asking about their problem.")
    if result.leading_questions is not None and result.leading_questions > limits.leading_questions:
        lines.append("- Some of your questions led the customer to the answer.")
    return lines


def render_analysis(result: AnalyzeResult) -> str:
    """The front agent's full read-out."""
    lines = verdict_lines(result) + ["", result.summary]
    if result.reasons:
        lines += ["", "**Why**"] + [f"- {reason}" for reason in result.reasons]
    quotes = _real_quotes(result.statements)
    if quotes:
        lines += ["", "**Strongest evidence**"]
        lines += [f'- "{s.quote}" ({CATEGORY_TEXT[s.category]}, {_percent(s.p_real)} real)' for s in quotes]
    founder = _founder_lines(result)
    if founder:
        lines += ["", "**Your interviewing**"] + founder
    lines += ["", "**Ask next**"] + [f"{i}. {q}" for i, q in enumerate(result.next_questions, 1)]
    return "\n".join(lines)


def render_judged(judged: Judged | AnalyzeResult) -> str:
    """Verdict, score and every customer sentence with its judgment: the Signal Analyst's reply, and
    the front agent's breakdown."""
    lines = verdict_lines(judged) + ["", "**Each customer sentence**"]
    lines += [
        f'- {CATEGORY_TEXT[s.category]} ({_percent(s.p_real)} real): "{s.quote}"'
        for s in judged.statements[:MAX_STATEMENTS_SHOWN]
    ]
    hidden = len(judged.statements) - MAX_STATEMENTS_SHOWN
    if hidden > 0:
        lines.append(f"- ...and {hidden} more.")
    return "\n".join(lines)


def render_written(result: AnalyzeResult) -> str:
    """The Strategist's reply: the text only."""
    lines = [result.summary]
    if result.reasons:
        lines += ["", "**Why**"] + [f"- {reason}" for reason in result.reasons]
    lines += ["", "**Ask next**"] + [f"{i}. {q}" for i, q in enumerate(result.next_questions, 1)]
    return "\n".join(lines)
