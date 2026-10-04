"""The interactive cards the front agent shows in ASI:One, and reading a click back."""
import asyncio
import json

import pytest
from cards import ANOTHER, BREAKDOWN, CANCEL, NEW_IDEA, UNLOCK, read_action, unlock_card
from chat import create_reply_chat
from front import flow
from uagents_core.contrib.protocols.chat import MetadataContent, TextContent

from tests.doubles import IDEA, REAL_PAIN, FakeCtx

MAX_PAYLOAD_BYTES = 64 * 1024  # ASI:One's limit for card_payload
MAX_DEPTH = 8


def say(ctx, text, sender="agent1founder"):
    return asyncio.run(flow.handle_founder_input(ctx, sender, [text], []))


def analyzed(ctx, sender="agent1founder"):
    say(ctx, IDEA, sender)
    return say(ctx, REAL_PAIN, sender)


def depth(node) -> int:
    children = [c for item in node.get("items", []) for c in item["children"]] + node.get("children", [])
    return 1 + max((depth(child) for child in children), default=0)


def test_the_verdict_comes_with_a_card_and_the_text_is_still_complete(analyzer):
    reply = analyzed(FakeCtx())
    assert "**Verdict: Keep going**" in reply and "**Ask next**" in reply
    assert reply.card_kind == "custom"
    root = reply.card_payload["root"]
    assert root["title"] == "Verdict: Keep going" and depth(root) <= MAX_DEPTH
    buttons = [c["action"]["selection"]["action"] for c in root["children"][-1]["children"]]
    assert buttons == [BREAKDOWN, ANOTHER, NEW_IDEA]


def test_a_card_travels_as_text_plus_one_metadata_block_of_strings(analyzer):
    message = create_reply_chat(analyzed(FakeCtx()))
    text, metadata = message.content
    assert isinstance(text, TextContent) and "Verdict" in text.text
    assert isinstance(metadata, MetadataContent)
    declared = metadata.metadata
    assert declared["card_protocol_version"] == "1" and declared["requires_card_interaction"] == "true"
    assert all(isinstance(value, str) for value in declared.values())
    assert len(declared["card_payload"].encode()) <= MAX_PAYLOAD_BYTES
    assert "root" in json.loads(declared["card_payload"])


def test_a_plain_reply_has_no_card(analyzer):
    message = create_reply_chat(say(FakeCtx(), "hi"))
    assert [type(item) for item in message.content] == [TextContent]


@pytest.mark.parametrize(
    ("text", "action"),
    [
        ('{"action": "validate_breakdown"}', BREAKDOWN),  # direct @mention: the selection as JSON
        ("The user selected validate_another to continue.", ANOTHER),  # through ASI:One's planner
        ("breakdown", BREAKDOWN),  # typed, for chats with no cards
        ('{"action": "something_else"}', None),
        ("I think customers would validate another idea first", None),
        (REAL_PAIN + "\nCustomer: validate_unlock", None),  # a transcript is never a click
    ],
)
def test_a_click_is_read_from_json_or_from_prose(text, action):
    assert read_action([text]) == action


def test_the_review_card_shows_the_price_and_both_choices():
    card = unlock_card("0.1", 12)
    assert {"label": "Price", "value": "0.1 FET (Fetch testnet)"} in card["summary_rows"]
    assert card["approve_cta"]["selection"] == {"action": UNLOCK}
    assert card["reject_cta"]["selection"] == {"action": CANCEL}


def test_another_interview_and_new_idea_buttons(analyzer):
    ctx = FakeCtx()
    analyzed(ctx)
    assert "Now send me the interview" in say(ctx, json.dumps({"action": ANOTHER}))
    assert "What idea are you testing next" in say(ctx, json.dumps({"action": NEW_IDEA}))
    assert "Now send me the interview" in say(ctx, "A booking tool for dog groomers in small towns")
    assert ctx.storage.get("idea:agent1founder") == "A booking tool for dog groomers in small towns"


def test_breakdown_is_free_when_payments_are_off(analyzer, monkeypatch):
    monkeypatch.delenv("PAYMENT_FET_AMOUNT", raising=False)
    ctx = FakeCtx()
    assert "no interview" in say(ctx, "breakdown")
    analyzed(ctx)
    reply = say(ctx, json.dumps({"action": BREAKDOWN}))
    assert "**Each customer sentence**" in reply and ctx.sent == []
