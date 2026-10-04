# Adapted from fetchai/uAgent-Examples:
# 6-deployed-agents/knowledge-base/openai-agent/chat_proto.py
# Phase 0 change: the LLM call is replaced by a hello-world reply.
import base64
import os
from datetime import datetime
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
PREVIEW_CHARS = 200


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


def describe_resource(data: dict) -> str:
    # ExternalStorage returns the file contents base64-encoded
    raw = base64.b64decode(data["contents"])
    mime_type = data.get("mime_type", "unknown")
    summary = f"Received a file: {mime_type}, {len(raw)} bytes."
    if mime_type.startswith("text/"):
        preview = raw.decode("utf-8", errors="replace")[:PREVIEW_CHARS]
        summary += f"\nIt starts with:\n{preview}"
    return summary


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

    replies = []
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            await ctx.send(sender, create_metadata({"attachments": "true"}))
        elif isinstance(item, TextContent):
            replies.append(f'Real Signal is alive. You said: "{item.text}"')
        elif isinstance(item, ResourceContent):
            try:
                external_storage = ExternalStorage(
                    identity=ctx.agent.identity,
                    storage_url=STORAGE_URL,
                )
                data = external_storage.download(str(item.resource_id))
                replies.append(describe_resource(data))

            except Exception as ex:
                ctx.logger.error(f"Failed to download resource: {ex}")
                await ctx.send(sender, create_text_chat("Failed to download resource."))
        else:
            ctx.logger.warning(f"Got unexpected content from {sender}")

    if replies:
        await ctx.send(sender, create_text_chat("\n\n".join(replies)))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )
