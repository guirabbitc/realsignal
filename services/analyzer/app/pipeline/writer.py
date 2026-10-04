"""Step 8: OpenAI writes the read-out from Jev's structured output only (MISSION invariant 4: OpenAI writes).

The writer's schema has no field for a verdict, label or score, so it cannot change them.
"""

import json
from collections.abc import Mapping
from typing import Any, Protocol

from pydantic import BaseModel

from app.errors import OpenAIFailed

INSTRUCTIONS = """You write the read-out for validate.ai, a coach that tells first-time founders whether a \
customer interview showed real interest or just politeness.

You do NOT judge anything. The verdict, the score and every statement's label were already decided and \
are given to you. Explain them in plain, direct English for a first-time founder.

Rules:
- Never state or suggest a verdict or score different from the ones given.
- Refer to customer statements by their position, like [#3]. If you quote, copy the words exactly.
- If the verdict is need_more_evidence, explain what evidence is missing; the next questions must target it.
- Mention a founder mistake only when its value is at or above its threshold (talk ratio, pitched early, \
leading questions).
- Next questions: exactly 3, open-ended, about the customer's past behaviour and real commitments, never \
hypotheticals ("would you use...").
- Judge statements about the product, never the person. Never infer emotions, personality or traits.
- summary: 2-4 sentences. reasons: 2-4 short bullet sentences."""


class WriterOutput(BaseModel):
    summary: str
    reasons: list[str]
    next_questions: list[str]


class WriterBackend(Protocol):
    model: str

    async def write(self, payload: Mapping[str, Any]) -> WriterOutput: ...


class OpenAIWriter:
    def __init__(self, api_key: str, model: str, timeout: float = 60.0):
        from openai import AsyncOpenAI

        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=2)

    async def write(self, payload: Mapping[str, Any]) -> WriterOutput:
        from openai import OpenAIError

        try:
            response = await self._client.responses.parse(
                model=self.model,
                instructions=INSTRUCTIONS,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=WriterOutput,
                store=False,  # founders' transcripts are not stored at OpenAI (MISSION out-of-scope: data use)
            )
        except OpenAIError as error:
            raise OpenAIFailed(f"OpenAI request failed: {type(error).__name__}") from error
        if response.output_parsed is None:
            raise OpenAIFailed("OpenAI returned no structured output.")
        return response.output_parsed
