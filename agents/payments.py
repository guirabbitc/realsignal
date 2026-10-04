"""The Agent Payment Protocol for the front agent: it sells the sentence-by-sentence breakdown.

The verdict and the read-out are free. The breakdown costs PAYMENT_FET_AMOUNT in FET, paid directly
on the Fetch testnet. With PAYMENT_FET_AMOUNT unset, payments are off and the breakdown is free.

A payment is never completed on the buyer's word: the transfer is read from the ledger first.
"""
import asyncio
import os
import time
from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation

from chat import create_text_chat
from uagents import Context, Protocol
from uagents_core.contrib.protocols.payment import (
    CancelPayment,
    CommitPayment,
    CompletePayment,
    Funds,
    RejectPayment,
    RequestPayment,
    payment_protocol_spec,
)

NETWORK = "stable-testnet"
DENOM = "atestfet"
ATTO = 10**18
METHOD = "fet_direct"
DEADLINE_SECONDS = 300
# A transfer can take a few seconds to show up on the ledger after the wallet reports it.
VERIFY_ATTEMPTS = 4
VERIFY_WAIT_SECONDS = 4
VERIFY_TIMEOUT_SECONDS = 20

# Called once a payment is verified: (ctx, buyer, reference) -> the text to deliver, or None.
Fulfil = Callable[[Context, str, str], Awaitable[str | None]]

_recipient: str | None = None
_fulfil: Fulfil | None = None

payment_proto = Protocol(spec=payment_protocol_spec, role="seller")


class TransferNotFound(Exception):
    pass


def setup(recipient: str, fulfil: Fulfil) -> None:
    """`recipient` is the agent's own wallet address. It is never taken from a message."""
    global _recipient, _fulfil
    _recipient, _fulfil = recipient, fulfil


def price() -> str | None:
    """The price in FET, or None when payments are off."""
    raw = os.getenv("PAYMENT_FET_AMOUNT", "").strip()
    try:
        return raw if raw and Decimal(raw) > 0 else None
    except InvalidOperation:
        return None


def enabled() -> bool:
    return price() is not None and _recipient is not None


def to_atto(amount: str) -> int:
    return int(Decimal(amount) * ATTO)


def received(tx, recipient: str) -> int:
    """How much testnet FET a ledger transaction sent to `recipient`, in atestfet.

    Read from the transaction's own bank messages, not from its events: fee payments also emit
    transfer events.
    """
    from cosmpy.protos.cosmos.bank.v1beta1.tx_pb2 import MsgSend

    total = 0
    for message in tx.body.messages:
        send = MsgSend()
        if not message.Is(MsgSend.DESCRIPTOR) or not message.Unpack(send):
            continue
        if send.to_address == recipient:
            total += sum(int(coin.amount) for coin in send.amount if coin.denom == DENOM)
    return total


def paid_on_ledger(tx_hash: str, recipient: str) -> int:
    """Blocking. The amount a successful testnet transaction sent to `recipient`."""
    from cosmpy.aerial.client import LedgerClient, NetworkConfig
    from cosmpy.protos.cosmos.tx.v1beta1.service_pb2 import GetTxRequest

    ledger = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    try:
        found = ledger.txs.GetTx(GetTxRequest(hash=tx_hash))
    except Exception as ex:
        detail = ex.details() if hasattr(ex, "details") else str(ex)
        if "not found" in str(detail).lower():
            raise TransferNotFound() from ex
        raise
    if found.tx_response.code != 0:
        return 0
    return received(found.tx, recipient)


async def verify(tx_hash: str, recipient: str) -> int:
    for attempt in range(VERIFY_ATTEMPTS):
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(paid_on_ledger, tx_hash, recipient), timeout=VERIFY_TIMEOUT_SECONDS
            )
        except TransferNotFound:
            if attempt == VERIFY_ATTEMPTS - 1:
                raise
            await asyncio.sleep(VERIFY_WAIT_SECONDS)
    raise TransferNotFound()


async def request(ctx: Context, buyer: str, reference: str, description: str) -> None:
    """Ask `buyer` to pay for the item `reference`. One open request per buyer."""
    amount = price()
    if amount is None or _recipient is None:
        raise RuntimeError("payments are off")
    ctx.storage.set(f"payment:{buyer}", {"reference": reference, "amount": amount, "at": int(time.time())})
    await ctx.send(
        buyer,
        RequestPayment(
            accepted_funds=[Funds(currency="FET", amount=amount, payment_method=METHOD)],
            recipient=_recipient,
            deadline_seconds=DEADLINE_SECONDS,
            reference=reference,
            description=description,
            metadata={"fet_network": NETWORK, "provider_agent_wallet": _recipient},
        ),
    )
    ctx.logger.info(f"RequestPayment sent: {amount} FET, reference {reference}")


async def _cancel(ctx: Context, buyer: str, tx_hash: str, reason: str) -> None:
    ctx.logger.warning(f"Payment not accepted (tx {tx_hash[:12]}): {reason}")
    await ctx.send(buyer, CancelPayment(transaction_id=tx_hash, reason=reason))


@payment_proto.on_message(CommitPayment)
async def on_commit(ctx: Context, sender: str, msg: CommitPayment):
    tx_hash = (msg.transaction_id or "").strip()
    ctx.logger.info(f"CommitPayment: method {msg.funds.payment_method}, tx {tx_hash[:12]}")

    # One transaction pays for one thing, once.
    used_by = ctx.storage.get(f"tx:{tx_hash}")
    if used_by == sender:
        await ctx.send(sender, CompletePayment(transaction_id=tx_hash))
        return
    if used_by:
        return await _cancel(ctx, sender, tx_hash, "This transaction was already used for another payment.")

    pending = ctx.storage.get(f"payment:{sender}")
    if not pending or _recipient is None or _fulfil is None:
        return await _cancel(ctx, sender, tx_hash, "There is no open payment request.")
    if msg.funds.payment_method != METHOD or not tx_hash:
        return await _cancel(ctx, sender, tx_hash, "Only a direct FET transfer on the Fetch testnet is accepted.")

    try:
        paid = await verify(tx_hash, _recipient)
    except TransferNotFound:
        return await _cancel(ctx, sender, tx_hash, "I could not find this transaction on the Fetch testnet.")
    except Exception as ex:
        ctx.logger.error(f"Ledger check failed: {type(ex).__name__}")
        return await _cancel(ctx, sender, tx_hash, "I could not check the payment on the Fetch testnet. Nothing was unlocked.")
    if paid < to_atto(pending["amount"]):
        return await _cancel(
            ctx, sender, tx_hash,
            f"The transaction did not send {pending['amount']} FET to this agent on the Fetch testnet.",
        )

    ctx.storage.set(f"tx:{tx_hash}", sender)
    ctx.storage.set(f"payment:{sender}", None)
    await ctx.send(sender, CompletePayment(transaction_id=tx_hash))
    ctx.logger.info(f"Payment verified: {pending['amount']} FET, reference {pending['reference']}")
    text = await _fulfil(ctx, sender, pending["reference"])
    await ctx.send(sender, create_text_chat(text or "Payment received. Send the interview again and I'll include the breakdown."))


@payment_proto.on_message(RejectPayment)
async def on_reject(ctx: Context, sender: str, msg: RejectPayment):
    ctx.logger.info("Payment request rejected by the buyer")
    ctx.storage.set(f"payment:{sender}", None)
