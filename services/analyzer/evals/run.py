"""Score the analyzer against test cases with an answer key.

Cases come from another LLM, using the prompt in evals/generate_cases_prompt.md, saved as
JSON files in evals/cases/. Each case has an idea, a transcript, the expected verdict and the
expected label of every interviewee sentence.

    uv run python -m evals.run                       # every file in evals/cases/, real Jev (paid, small)
    uv run python -m evals.run evals/cases/a.json    # chosen files
    uv run python -m evals.run --fake                # keyword rules instead of Jev: free, tests the script only

Only the judging is run (labels, score, verdict). The writer is skipped, so no OpenAI cost.
"""
import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = ("real_signal", "polite", "neutral")
VERDICTS = ("keep_going", "narrow_down", "try_new_angle", "pivot")
VERDICT_ALIASES = {"try_a_new_angle": "try_new_angle"}
REQUIRED = ("idea", "transcript", "expected_verdict", "interviewee_sentences")


@dataclass
class CaseResult:
    id: str
    persona: str
    difficulty: str
    expected_verdict: str
    verdict: str
    score: float
    labels_total: int = 0
    labels_right: int = 0
    unmatched: int = 0
    disagreements: list[dict] = field(default_factory=list)
    error: str | None = None

    @property
    def verdict_right(self) -> bool:
        return self.error is None and self.verdict == self.expected_verdict


def slug(value: str) -> str:
    value = re.sub(r"[^a-z]+", "_", str(value).strip().lower()).strip("_")
    return VERDICT_ALIASES.get(value, value)


def norm(text: str) -> str:
    """Compare sentences by their words only, so quotes and spacing do not matter."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_cases(path: Path) -> list[dict]:
    """Read one file of cases. Tolerates the ```json fence models often wrap around their answer."""
    text = path.read_text().strip()
    text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text)
    data = json.loads(text)
    cases = data["cases"] if isinstance(data, dict) else data
    for i, case in enumerate(cases):
        missing = [key for key in REQUIRED if not case.get(key)]
        if missing:
            raise ValueError(f"{path.name}, case {i + 1}: missing {', '.join(missing)}")
        case["id"] = f"{path.stem}/{case.get('id') or i + 1}"
        case["expected_verdict"] = slug(case["expected_verdict"])
        if case["expected_verdict"] not in VERDICTS:
            raise ValueError(f"{case['id']}: unknown verdict {case['expected_verdict']!r}")
        for sentence in case["interviewee_sentences"]:
            sentence["label"] = slug(sentence["label"])
            if sentence["label"] not in LABELS:
                raise ValueError(f"{case['id']}: unknown label {sentence['label']!r}")
    return cases


def score_case(case: dict, judged) -> CaseResult:
    """Line the analyzer's sentences up with the answer key by their text."""
    result = CaseResult(
        id=case["id"],
        persona=case.get("persona", "?"),
        difficulty=case.get("difficulty", "?"),
        expected_verdict=case["expected_verdict"],
        verdict=judged.verdict.value,
        score=judged.score,
    )
    got = defaultdict(list)
    for s in judged.sentences:
        got[norm(s.text)].append(s)
    for expected in case["interviewee_sentences"]:
        matches = got.get(norm(expected["text"]))
        sentence = matches.pop(0) if matches else None
        if sentence is None or sentence.label is None:
            # Not found, or the analyzer took this speaker for the interviewer.
            result.unmatched += 1
            continue
        result.labels_total += 1
        if sentence.label.value == expected["label"]:
            result.labels_right += 1
        else:
            result.disagreements.append(
                {
                    "text": expected["text"],
                    "expected": expected["label"],
                    "got": sentence.label.value,
                    "confidence": sentence.confidence,
                }
            )
    return result


def pct(right: int, total: int) -> str:
    return f"{right}/{total} ({100 * right / total:.0f}%)" if total else "n/a"


def breakdown(results: list[CaseResult], key: str) -> list[str]:
    groups = defaultdict(list)
    for r in results:
        groups[getattr(r, key)].append(r)
    lines = []
    for name, group in sorted(groups.items()):
        lines.append(
            f"  {name:<26} verdict {pct(sum(r.verdict_right for r in group), len(group)):<14}"
            f" labels {pct(sum(r.labels_right for r in group), sum(r.labels_total for r in group))}"
        )
    return lines


def report(results: list[CaseResult]) -> str:
    ok = [r for r in results if r.error is None]
    lines = ["", "=== Cases ==="]
    for r in results:
        if r.error:
            lines.append(f"  ERROR {r.id}: {r.error}")
            continue
        mark = "ok  " if r.verdict_right else "MISS"
        lines.append(
            f"  {mark} {r.id:<28} expected {r.expected_verdict:<14} got {r.verdict:<14}"
            f" score {r.score:>5.1f}  labels {pct(r.labels_right, r.labels_total)}"
            + (f"  ({r.unmatched} unmatched)" if r.unmatched else "")
        )

    lines += ["", "=== Accuracy ==="]
    lines.append(f"  Verdict: {pct(sum(r.verdict_right for r in ok), len(ok))}")
    lines.append(f"  Labels:  {pct(sum(r.labels_right for r in ok), sum(r.labels_total for r in ok))}")
    unmatched = sum(r.unmatched for r in ok)
    if unmatched:
        lines.append(f"  {unmatched} answer-key sentences could not be lined up and were left out.")
    lines += ["", "By persona:"] + breakdown(ok, "persona")
    lines += ["", "By difficulty:"] + breakdown(ok, "difficulty")

    confusion = Counter((d["expected"], d["got"]) for r in ok for d in r.disagreements)
    if confusion:
        lines += ["", "Label mix-ups (answer key -> analyzer):"]
        lines += [f"  {exp:<12} -> {got:<12} {n}" for (exp, got), n in confusion.most_common()]

    misses = [r for r in ok if not r.verdict_right or r.disagreements]
    if misses:
        lines += ["", "=== Disagreements (read these: the answer key can be wrong too) ==="]
        for r in misses:
            lines.append(f"  {r.id} [{r.persona}, {r.difficulty}]")
            if not r.verdict_right:
                lines.append(f"    verdict: expected {r.expected_verdict}, got {r.verdict} (score {r.score})")
            for d in r.disagreements:
                lines.append(f"    {d['expected']} -> {d['got']} ({d['confidence']:.2f}): {d['text']}")
    return "\n".join(lines)


def build_clients(fake: bool):
    from app.pipeline import Clients
    from app.pipeline.jev import FakeJudge
    from app.pipeline.transcribe import FakeTranscriber
    from app.pipeline.writer import FakeWriter

    if fake:
        return Clients(transcriber=FakeTranscriber(), judge=FakeJudge(), writer=FakeWriter())
    os.environ["ANALYZER_FAKE_CLIENTS"] = ""
    from app.main import get_clients

    clients = get_clients()
    clients.writer = FakeWriter()  # the eval never writes, so never pay for it
    return clients


def run(paths: list[Path], fake: bool) -> list[CaseResult]:
    from app.pipeline import judge

    clients = build_clients(fake)
    results = []
    for path in paths:
        for case in load_cases(path):
            start = time.time()
            try:
                judged = judge(case["idea"], case["transcript"], clients)
                result = score_case(case, judged)
            except Exception as ex:
                result = CaseResult(
                    id=case["id"], persona=case.get("persona", "?"), difficulty=case.get("difficulty", "?"),
                    expected_verdict=case["expected_verdict"], verdict="", score=0, error=str(ex)[:300],
                )
            print(f"  ran {result.id} in {time.time() - start:.1f}s", file=sys.stderr, flush=True)
            results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("files", nargs="*", type=Path, help="case files (default: evals/cases/*.json)")
    parser.add_argument("--fake", action="store_true", help="use keyword rules instead of Jev (free)")
    args = parser.parse_args()

    paths = args.files or sorted((HERE / "cases").glob("*.json"))
    if not paths:
        raise SystemExit("No case files. Save the generator's JSON output in evals/cases/ first.")
    print(f"Judging with {'FAKE keyword rules' if args.fake else 'real Jev'}...", file=sys.stderr)
    results = run(paths, args.fake)
    text = report(results)
    print(text)

    out = HERE / "results"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + ("-fake" if args.fake else "")
    (out / f"{stamp}.txt").write_text(text + "\n")
    (out / f"{stamp}.json").write_text(json.dumps([r.__dict__ for r in results], indent=2))
    print(f"\nSaved to evals/results/{stamp}.txt and .json")


if __name__ == "__main__":
    main()
