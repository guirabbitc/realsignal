"""Run test cases through the real agents, over the Fetch network, and score the answers.

For each case this agent plays a founder:
  1. chats with the valiDate front agent (idea, then transcript) and reads the verdict from the
     reply, which exercises the whole team: front -> Intake -> Signal Analyst -> Strategist;
  2. sends the Signal Analyst a typed JudgeTranscript and gets back every judged sentence.
It scores both against the answer key (tester/scoring.py) and saves the report in tester/results/.

The team must be running. The first time, connect this agent's mailbox from the inspector link it
prints, then run it again.

    uv run --project agents python agents/tester/agent.py                     # all of tester/cases/
    uv run --project agents python agents/tester/agent.py path/to/cases.json
    uv run --project agents python agents/tester/agent.py --local             # no agents: the pipeline
                                                                              # directly, fast, same key
"""
import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import pipeline  # noqa: E402
from app.pipeline.analyze import Judged  # noqa: E402
from common import address_of, make_agent  # noqa: E402
from models import Judgement, JudgeTranscript, StageError  # noqa: E402
from render import VERDICT_TEXT  # noqa: E402
from tester.scoring import CaseResult, load_cases, new_result, report, score_case  # noqa: E402
from uagents import Agent, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

DESCRIPTION = (
    "Test client for the valiDate team: sends test interviews to the valiDate agents and measures how "
    "often their verdicts and judgments match an answer key."
)
CASES_DIR = HERE / "cases"
RESULTS_DIR = HERE / "results"
REPLY_TIMEOUT_SECONDS = 180
VERDICT_IN_REPLY = re.compile(r"\*\*Verdict:\s*(.+?)\*\*")
VERDICT_SLUG = {text: slug for slug, text in VERDICT_TEXT.items()}
TEAM_TRACE = "Handled by the valiDate team"


def chat(*content) -> ChatMessage:
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=list(content))


def failed(case: dict, ex: Exception) -> CaseResult:
    result = new_result(case)
    result.error = f"{type(ex).__name__}: {getattr(ex, 'message', ex)}"[:300]
    return result


def attach_tester(agent: Agent, cases: list[dict], front: str, analyst: str, on_done) -> None:
    """Make `agent` run every case against the agents at `front` and `analyst`, then call on_done(results)."""
    replies: asyncio.Queue[str] = asyncio.Queue()
    proto = Protocol(spec=chat_protocol_spec)

    @proto.on_message(ChatMessage)
    async def on_reply(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
        for item in msg.content:
            if isinstance(item, TextContent) and sender == front:
                await replies.put(item.text)

    @proto.on_message(ChatAcknowledgement)
    async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        pass

    agent.include(proto)

    async def say(ctx: Context, text: str, first: bool = False) -> str:
        """Send one chat message to the front agent and wait for its text reply."""
        while not replies.empty():
            replies.get_nowait()
        content = [TextContent(type="text", text=text)]
        if first:
            content.insert(0, StartSessionContent(type="start-session"))
        await ctx.send(front, chat(*content))
        return await asyncio.wait_for(replies.get(), timeout=REPLY_TIMEOUT_SECONDS)

    async def run_case(ctx: Context, case: dict, first: bool) -> CaseResult:
        await say(ctx, f"new idea: {case['idea']}", first=first)
        reply = await say(ctx, case["transcript"])
        match = VERDICT_IN_REPLY.search(reply)
        if not match or match.group(1).strip() not in VERDICT_SLUG:
            raise RuntimeError(f"No verdict in the front agent's reply: {reply[:160]!r}")

        answer, status = await ctx.send_and_receive(
            analyst,
            JudgeTranscript(idea=case["idea"], transcript=case["transcript"]),
            response_type={Judgement, StageError},
            timeout=REPLY_TIMEOUT_SECONDS,
        )
        if not isinstance(answer, Judgement):
            raise RuntimeError(f"Signal Analyst did not answer: {getattr(answer, 'error', status)}")

        result = score_case(case, Judged.model_validate(answer.judged))
        # The verdict that counts is the one the founder saw in the chat.
        result.verdict = VERDICT_SLUG[match.group(1).strip()]
        result.through_team = TEAM_TRACE in reply
        return result

    @agent.on_event("startup")
    async def run_all(ctx: Context):
        async def work():
            await asyncio.sleep(5)  # let registration and the mailbox client settle
            results = []
            for i, case in enumerate(cases):
                start = time.time()
                try:
                    result = await run_case(ctx, case, first=i == 0)
                except Exception as ex:
                    result = failed(case, ex)
                ctx.logger.info(f"ran {result.id} in {time.time() - start:.0f}s ({i + 1}/{len(cases)})")
                results.append(result)
            on_done(results)

        asyncio.create_task(work())


async def run_local(cases: list[dict]) -> list[CaseResult]:
    """The same scoring without any agent: the judging half of the pipeline, called directly."""
    results = []
    for i, case in enumerate(cases):
        start = time.time()
        try:
            result = score_case(case, await pipeline.judge(case["idea"], case["transcript"]))
        except Exception as ex:
            result = failed(case, ex)
        print(f"  ran {result.id} in {time.time() - start:.1f}s ({i + 1}/{len(cases)})", file=sys.stderr, flush=True)
        results.append(result)
    return results


def save(results: list[CaseResult], tag: str) -> None:
    text = report(results)
    print(text, flush=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}-{tag}"
    (RESULTS_DIR / f"{stamp}.txt").write_text(text + "\n")
    (RESULTS_DIR / f"{stamp}.json").write_text(json.dumps([r.__dict__ for r in results], indent=2))
    print(f"\nSaved to agents/tester/results/{stamp}.txt and .json", flush=True)


if __name__ == "__main__":
    import os

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = [Path(p) for p in args] or sorted(CASES_DIR.glob("*.json"))
    if not paths:
        raise SystemExit("No case files. Save the generator's JSON output in agents/tester/cases/ first.")
    all_cases = [case for path in paths for case in load_cases(path)]

    if "--local" in sys.argv:
        print(f"Judging {len(all_cases)} cases with the pipeline directly (no agents)...", file=sys.stderr)
        save(asyncio.run(run_local(all_cases)), "local")
    else:
        def finish(results: list[CaseResult]) -> None:
            save(results, "agents")
            os._exit(0)

        agent = make_agent("tester", "valiDate Tester", DESCRIPTION)
        attach_tester(agent, all_cases, address_of("front"), address_of("analyst"), finish)
        print(f"Running {len(all_cases)} cases through the agents. Expect roughly a minute per case.", flush=True)
        agent.run()
