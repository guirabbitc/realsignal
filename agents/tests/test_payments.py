"""The Payment Protocol: the breakdown is delivered only after the transfer is found on the ledger."""
import asyncio
import json

import payments
import pytest
from cards import BREAKDOWN, CANCEL, UNLOCK
from cosmpy.protos.cosmos.bank.v1beta1.tx_pb2 import MsgSend
from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin
from cosmpy.protos.cosmos.tx.v1beta1.tx_pb2 import Tx
from front import flow
from uagents_core.contrib.protocols.chat import ChatMessage
from uagents_core.contrib.protocols.payment import (
    CancelPayment,
    CommitPayment,
    CompletePayment,
    Funds,
    RejectPayment,
    RequestPayment,
)

from tests.doubles import IDEA, REAL_PAIN, FakeCtx

BUYER = "agent1buyer"
WALLET = "fetch1seller"
PRICE = "0.1"


@pytest.fixture
def shop(analyzer, monkeypatch):
    """Payments on, with a ledger that knows one good transfer and one that is too small."""
    ledger = {"TXGOOD": payments.to_atto(PRICE), "TXSMALL": payments.to_atto("0.01")}

    async def verify(tx_hash, recipient):
        assert recipient == WALLET
        if tx_hash not in ledger:
            raise payments.TransferNotFound()
        return ledger[tx_hash]

    monkeypatch.setenv("PAYMENT_FET_AMOUNT", PRICE)
    monkeypatch.setattr(payments, "verify", verify)
    monkeypatch.setattr(payments, "_recipient", WALLET)
    monkeypatch.setattr(payments, "_fulfil", flow.paid_breakdown)
    ctx = FakeCtx()
    say(ctx, IDEA)
    say(ctx, REAL_PAIN)
    return ctx


def say(ctx, text, sender=BUYER):
    return asyncio.run(flow.handle_founder_input(ctx, sender, [text], []))


def click(ctx, action, sender=BUYER):
    return say(ctx, json.dumps({"action": action}), sender)


def commit(ctx, tx_hash, sender=BUYER, method="fet_direct"):
    message = CommitPayment(
        funds=Funds(currency="FET", amount=PRICE, payment_method=method), recipient=WALLET, transaction_id=tx_hash
    )
    ctx.sent.clear()
    asyncio.run(payments.on_commit(ctx, sender, message))
    return [message for _, message in ctx.sent]


def test_breakdown_shows_the_price_first_and_charges_nothing(shop):
    reply = click(shop, BREAKDOWN)
    assert reply.card_kind == "review" and "0.1 FET" in reply
    assert "Each customer sentence" not in reply and shop.sent == []
    assert "nothing was charged" in click(shop, CANCEL) and shop.sent == []


def test_confirming_sends_one_payment_request_to_the_agents_own_wallet(shop):
    click(shop, BREAKDOWN)
    reply = click(shop, UNLOCK)
    assert "payment request" in reply and "Each customer sentence" not in reply
    [(destination, request)] = shop.sent
    assert destination == BUYER and isinstance(request, RequestPayment)
    assert request.recipient == WALLET
    assert request.accepted_funds == [Funds(currency="FET", amount=PRICE, payment_method="fet_direct")]
    assert request.metadata == {"fet_network": "stable-testnet", "provider_agent_wallet": WALLET}


def test_a_verified_transfer_completes_the_payment_and_delivers_the_breakdown(shop):
    click(shop, UNLOCK)
    complete, delivered = commit(shop, "TXGOOD")
    assert complete == CompletePayment(transaction_id="TXGOOD")
    assert isinstance(delivered, ChatMessage) and "**Each customer sentence**" in delivered.content[0].text
    # paid once: the breakdown is now free to read again
    assert "**Each customer sentence**" in click(shop, BREAKDOWN)


@pytest.mark.parametrize(
    ("tx_hash", "method", "reason"),
    [
        ("TXUNKNOWN", "fet_direct", "could not find"),
        ("TXSMALL", "fet_direct", "did not send 0.1 FET"),
        ("TXGOOD", "stripe", "Only a direct FET transfer"),
    ],
)
def test_an_unverified_payment_is_cancelled_and_nothing_is_delivered(shop, tx_hash, method, reason):
    click(shop, UNLOCK)
    [cancelled] = commit(shop, tx_hash, method=method)
    assert isinstance(cancelled, CancelPayment) and reason in cancelled.reason
    assert click(shop, BREAKDOWN).card_kind == "review"  # still locked


def test_a_commit_with_no_open_request_is_cancelled(shop):
    [cancelled] = commit(shop, "TXGOOD")
    assert isinstance(cancelled, CancelPayment) and "no open payment request" in cancelled.reason


def test_one_transaction_unlocks_once(shop):
    click(shop, UNLOCK)
    commit(shop, "TXGOOD")
    # the same buyer repeats the commit: acknowledged, not delivered again
    assert commit(shop, "TXGOOD") == [CompletePayment(transaction_id="TXGOOD")]
    # another buyer tries the same transaction for their own interview
    say(shop, IDEA, "agent1other")
    say(shop, REAL_PAIN, "agent1other")
    click(shop, UNLOCK, "agent1other")
    [cancelled] = commit(shop, "TXGOOD", sender="agent1other")
    assert isinstance(cancelled, CancelPayment) and "already used" in cancelled.reason


def test_a_rejected_request_closes_it(shop):
    click(shop, UNLOCK)
    asyncio.run(payments.on_reject(shop, BUYER, RejectPayment(reason="no")))
    [cancelled] = commit(shop, "TXGOOD")
    assert "no open payment request" in cancelled.reason


def test_the_web_chat_cannot_be_asked_to_pay(shop):
    say(shop, IDEA, "web:abc")
    say(shop, REAL_PAIN, "web:abc")
    shop.sent.clear()
    reply = say(shop, "breakdown", "web:abc")
    assert "ASI:One" in reply and "Each customer sentence" not in reply and shop.sent == []


def test_only_bank_transfers_of_testnet_fet_to_the_recipient_count():
    def send(to, amount, denom):
        return MsgSend(from_address="fetch1buyer", to_address=to, amount=[Coin(denom=denom, amount=str(amount))])

    tx = Tx()
    for message in (send(WALLET, 70, "atestfet"), send(WALLET, 30, "atestfet"), send("fetch1other", 500, "atestfet"), send(WALLET, 900, "afet")):
        tx.body.messages.add().Pack(message)
    assert payments.received(tx, WALLET) == 100


def test_price_is_off_unless_it_is_a_positive_number(monkeypatch):
    for raw, expected in (("", None), ("abc", None), ("0", None), ("0.25", "0.25")):
        monkeypatch.setenv("PAYMENT_FET_AMOUNT", raw)
        assert payments.price() == expected
    assert payments.to_atto("0.1") == 10**17
