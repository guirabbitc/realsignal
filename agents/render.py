"""Turn analyzer results into chat text. Presentation only: nothing here judges or counts evidence."""
from contracts import AnalyzeResponse, JudgeResponse, Label, WriteResponse

TOP_QUOTES = 3
MAX_SENTENCES_SHOWN = 30

VERDICT_TEXT = {
    "keep_going": "Keep going",
    "narrow_down": "Narrow down",
    "try_new_angle": "Try a new angle",
    "pivot": "Pivot",
}
LABEL_TEXT = {"real_signal": "Real signal", "polite": "Polite", "neutral": "Neutral"}


def verdict_lines(judged: JudgeResponse | AnalyzeResponse) -> list[str]:
    return [
        f"**Verdict: {VERDICT_TEXT[judged.verdict.value]}**",
        "",  # a blank line: chat clients render a single newline as a space
        f"Demand score: {judged.score:g} / 100",
    ]


def written_lines(written: WriteResponse | AnalyzeResponse) -> list[str]:
    return [written.summary, "", "**Next steps**"] + [
        f"{i}. {step}" for i, step in enumerate(written.next_steps, 1)
    ]


def render_analysis(result: AnalyzeResponse) -> str:
    """The front agent's full reply: verdict, summary, strongest quotes, next steps."""
    quotes = sorted(
        (s for s in result.sentences if s.label == Label.real_signal),
        key=lambda s: s.confidence or 0,
        reverse=True,
    )[:TOP_QUOTES]
    lines = verdict_lines(result) + ["", result.summary, ""]
    if quotes:
        lines.append("**Strongest evidence**")
        lines += [f'- "{s.text}" ({s.speaker}, {round((s.confidence or 0) * 100)}%)' for s in quotes]
        lines.append("")
    lines.append("**Next steps**")
    lines += [f"{i}. {step}" for i, step in enumerate(result.next_steps, 1)]
    return "\n".join(lines)


def render_judged(judged: JudgeResponse) -> str:
    """The Signal Analyst's reply: verdict, score and every judged sentence with its label."""
    judged_sentences = [s for s in judged.sentences if s.label is not None]
    lines = verdict_lines(judged) + ["", "**Each interviewee sentence**"]
    lines += [
        f'- {LABEL_TEXT[s.label.value]} ({round((s.confidence or 0) * 100)}%): "{s.text}"'
        for s in judged_sentences[:MAX_SENTENCES_SHOWN]
    ]
    hidden = len(judged_sentences) - MAX_SENTENCES_SHOWN
    if hidden > 0:
        lines.append(f"- ...and {hidden} more.")
    return "\n".join(lines)


def render_written(written: WriteResponse) -> str:
    return "\n".join(written_lines(written))
