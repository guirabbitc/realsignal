"""Run the accuracy cases through the real agents, over the Fetch network.

For each case this agent plays a founder:
  1. chats with the ValiDate front agent (idea, then transcript) and reads the verdict from the
     reply, which exercises the whole team: front -> Intake -> Signal Analyst -> Strategist;
  2. sends the Signal Analyst a typed JudgeTranscript and gets back the label of every sentence.
It then scores both against the answer key, like services/analyzer/evals/run.py.

The team and the analyzer must be running. The first time, connect this agent's mailbox
from the inspector link it prints, then run it again.

    uv run --project agents python agents/tester/agent.py                    # all of evals/cases/
    uv run --project agents python agents/tester/agent.py path/to/cases.json
"""
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents"))
sys.path.insert(0, str(ROOT / "services" / "analyzer"))

from common import make_agent  # noqa: E402
from contracts import JudgeResponse  # noqa: E402
from evals.run import CaseResult, load_cases, report, score_case, slug  # noqa: E402
from models import Judged, JudgeTranscript, StageError  # noqa: E402
from uagents import Agent, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

DESCRIPTION = "Test client for the ValiDate team: sends test interviews to the ValiDate agents and measures how often their verdicts and labels match an answer key."
CASES_DIR = ROOT / "services" / "analyzer" / "evals" / "cases"
RESULTS_DIR = ROOT / "services" / "analyzer" / "evals" / "results"
REPLY_TIMEOUT_SECONDS = 180
VERDICT_IN_REPLY = re.compile(r"Verdict:\s*([A-Za-z ]+?)\*\*")
SCORE_IN_REPLY = re.compile(r"Demand score:\s*([0-9.]+)")


def chat(*content) -> ChatMessage:
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=list(content))


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
        if not match:
            raise RuntimeError(f"No verdict in the front agent's reply: {reply[:200]!r}")
        through_team = "Handled by the ValiDate team" in reply

        answer, status = await ctx.send_and_receive(
            analyst,
            JudgeTranscript(idea=case["idea"], transcript=case["transcript"]),
            response_type={Judged, StageError},
            timeout=REPLY_TIMEOUT_SECONDS,
        )
        if not isinstance(answer, Judged):
            raise RuntimeError(f"Signal Analyst did not answer: {getattr(answer, 'error', status)}")

        result = score_case(case, JudgeResponse.model_validate(answer.judged))
        # The verdict that counts is the one the founder saw in the chat.
        result.verdict = slug(match.group(1))
        score = SCORE_IN_REPLY.search(reply)
        result.score = float(score.group(1)) if score else result.score
        if not through_team:
            ctx.logger.warning(f"{case['id']}: the front agent answered without its specialists (fallback)")
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
                    result = CaseResult(
                        id=case["id"], persona=case.get("persona", "?"), difficulty=case.get("difficulty", "?"),
                        expected_verdict=case["expected_verdict"], verdict="", score=0,
                        error=f"{type(ex).__name__}: {ex}"[:300],
                    )
                ctx.logger.info(f"ran {result.id} in {time.time() - start:.0f}s ({i + 1}/{len(cases)})")
                results.append(result)
            on_done(results)

        asyncio.create_task(work())


def finish(results: list[CaseResult]) -> None:
    text = report(results)
    print(text, flush=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + "-agents"
    (RESULTS_DIR / f"{stamp}.txt").write_text(text + "\n")
    (RESULTS_DIR / f"{stamp}.json").write_text(json.dumps([r.__dict__ for r in results], indent=2))
    print(f"\nSaved to services/analyzer/evals/results/{stamp}.txt and .json", flush=True)
    os._exit(0)


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or sorted(CASES_DIR.glob("*.json"))
    if not paths:
        raise SystemExit("No case files. Save the generator's JSON output in services/analyzer/evals/cases/ first.")
    all_cases = [case for path in paths for case in load_cases(path)]
    agent = make_agent("TESTER", "ValiDate Tester", DESCRIPTION)
    attach_tester(
        agent, all_cases, os.environ["FRONT_AGENT_ADDRESS"], os.environ["ANALYST_AGENT_ADDRESS"], finish
    )
    print(f"Running {len(all_cases)} cases through the agents. Expect roughly a minute per case.", flush=True)
    agent.run()
