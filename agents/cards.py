"""ASI:One interactive cards: what the front agent shows under its text, and reading the click back.

Presentation only, like render.py. A card never replaces the text: ASI:One falls back to the text
when it cannot show a card, and the web chat only reads the text.
"""
import json
import re

from app.models import AnalyzeResult
from render import CATEGORY_TEXT, VERDICT_TEXT, _percent, _real_quotes

# What a button sends back. The prefix keeps them from matching ordinary words in a message.
BREAKDOWN = "validate_breakdown"
ANOTHER = "validate_another"
NEW_IDEA = "validate_new_idea"
UNLOCK = "validate_unlock"
CANCEL = "validate_cancel"
ACTIONS = (BREAKDOWN, ANOTHER, NEW_IDEA, UNLOCK, CANCEL)

ACTION_IN_PROSE = re.compile(r"\b(" + "|".join(ACTIONS) + r")\b")
MAX_SELECTION_CHARS = 600  # a click arrives as a short message; anything longer is the founder writing
VERDICT_BADGE = {
    "keep_going": "success",
    "narrow_down": "info",
    "new_angle": "info",
    "pivot": "warning",
    "need_more_evidence": "warning",
}


def _button(label: str, action: str, primary: bool = False) -> dict:
    return {"type": "button", "label": label, "primary": primary, "action": {"selection": {"action": action}}}


def result_card(result: AnalyzeResult) -> dict:
    """A `custom` card: the verdict at a glance and what the founder can do next."""
    badges = [{"type": "badge", "label": VERDICT_TEXT[result.verdict], "variant": VERDICT_BADGE[result.verdict]}]
    if result.score is not None:
        badges.append({"type": "badge", "label": f"Signal score {result.score} / 100", "variant": "info"})
    children: list[dict] = [
        {"type": "group", "direction": "row", "gap": 8, "children": badges},
        {"type": "text", "value": result.summary, "style": "body"},
    ]
    quotes = _real_quotes(result.statements)
    if quotes:
        best = quotes[0]
        children += [
            {"type": "text", "value": f"“{best.quote}”", "style": "emphasis"},
            {"type": "text", "value": f"{CATEGORY_TEXT[best.category]}, {_percent(best.p_real)} real", "style": "muted"},
        ]
    children += [
        {"type": "divider"},
        {
            "type": "group",
            "direction": "column",
            "gap": 8,
            "children": [
                _button(f"Every sentence, judged ({len(result.statements)})", BREAKDOWN, primary=True),
                _button("Analyze another interview", ANOTHER),
                _button("Test a new idea", NEW_IDEA),
            ],
        },
    ]
    return {"root": {"type": "section", "title": f"Verdict: {VERDICT_TEXT[result.verdict]}", "children": children}}


def unlock_card(price: str, sentences: int) -> dict:
    """A `review` card: what the paid breakdown is and what it costs, before any payment request."""
    return {
        "title": "Unlock the sentence-by-sentence breakdown",
        "summary_rows": [
            {"label": "You get", "value": "Every customer sentence with its category and how likely it is a real signal"},
            {"label": "Sentences", "value": str(sentences)},
            {"label": "Price", "value": f"{price} FET (Fetch testnet)"},
        ],
        "approve_cta": {"label": "Pay and unlock", "selection": {"action": UNLOCK}, "primary": True},
        "reject_cta": {"label": "Not now", "selection": {"action": CANCEL}},
    }


def read_action(texts: list[str]) -> str | None:
    """The button the founder clicked, if this message is a click.

    ASI:One sends the selection as JSON when the founder talks to the agent directly, and as a
    sentence that mentions the action when its planner is in between.
    """
    if len(texts) != 1:
        return None
    text = texts[0].strip()
    if len(text) > MAX_SELECTION_CHARS:
        return None
    if text.lower() == "breakdown":  # the same action typed, for chats with no cards (the web app)
        return BREAKDOWN
    try:
        selection = json.loads(text)
    except ValueError:
        selection = None
    if isinstance(selection, dict):
        action = selection.get("action")
        return action if action in ACTIONS else None
    found = ACTION_IN_PROSE.search(text)
    return found.group(1) if found else None
