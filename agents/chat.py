"""The Chat Protocol, which makes an agent usable from ASI:One.

Adapted from fetchai/uAgent-Examples:
6-deployed-agents/knowledge-base/openai-agent/chat_proto.py
Change from the template: instead of calling an LLM, the texts and files of a message are
handed to the agent's own `respond` function.
"""
import base64
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable
from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    MetadataContent,
    ResourceContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.storage import ExternalStorage

STORAGE_URL = os.getenv("AGENTVERSE_URL", "https://agentverse.ai") + "/v1/storage"


@dataclass
class Upload:
    """A file from the founder. Text is read by the agent; PDFs and recordings go to the analyzer as they are."""

    mime_type: str
    data: bytes

    @property
    def is_text(self) -> bool:
        return self.mime_type.startswith("text/")


Respond = Callable[[Context, str, list[str], list[Upload]], Awaitable[str]]


def create_text_chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )


def create_metadata(metadata: dict[str, str]) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[MetadataContent(
            type="metadata",
            metadata=metadata,
        )],
    )


def make_chat_protocol(respond: Respond) -> Protocol:
    """A Chat Protocol whose replies come from `respond(ctx, sender, texts, uploads)`."""
    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(ChatMessage)
    async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
        ctx.logger.info(f"Got a message from {sender}")
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id
            ),
        )

        texts: list[str] = []
        uploads: list[Upload] = []
        for item in msg.content:
            if isinstance(item, StartSessionContent):
                await ctx.send(sender, create_metadata({"attachments": "true"}))
            elif isinstance(item, TextContent):
                texts.append(item.text)
            elif isinstance(item, ResourceContent):
                ctx.logger.info(f"Resource received: {item.resource_id}")
                try:
                    external_storage = ExternalStorage(
                        identity=ctx.agent.identity,
                        storage_url=STORAGE_URL,
                    )
                    data = external_storage.download(str(item.resource_id))
                    # ExternalStorage returns the file contents base64-encoded
                    uploads.append(Upload(
                        mime_type=data.get("mime_type", "application/octet-stream"),
                        data=base64.b64decode(data["contents"]),
                    ))

                except Exception as ex:
                    ctx.logger.error(f"Failed to download resource: {ex}")
                    await ctx.send(sender, create_text_chat("Failed to download resource."))
            else:
                ctx.logger.warning(f"Got unexpected content from {sender}")

        if texts or uploads:
            reply = await respond(ctx, sender, texts, uploads)
            await ctx.send(sender, create_text_chat(reply))

    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.info(
            f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
        )

    return chat_proto
