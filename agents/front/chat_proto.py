# Adapted from fetchai/uAgent-Examples:
# 6-deployed-agents/knowledge-base/openai-agent/chat_proto.py
# Change from the template: instead of calling an LLM, the content is handed to flow.py,
# which gets the interview analyzed by the analyzer service.
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

from front.flow import Upload, handle_founder_input

STORAGE_URL = os.getenv("AGENTVERSE_URL", "https://agentverse.ai") + "/v1/storage"


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
        reply = await handle_founder_input(ctx, sender, texts, uploads)
        await ctx.send(sender, create_text_chat(reply))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )
