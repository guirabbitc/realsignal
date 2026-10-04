"""Load test cases with an answer key and score the agents' answers against it.

A case is written by another LLM with tester/generate_cases_prompt.md: an idea, a transcript, the
expected verdict, and the expected category of every customer sentence. Cases are synthetic; real
interview transcripts never go in the repo.
"""
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from app.pipeline.analyze import Judged
from app.rubric import load_rubric

VERDICTS = ("keep_going", "narrow_down", "new_angle", "pivot", "need_more_evidence")
VERDICT_ALIASES = {
    "try_a_new_angle": "new_angle",
    "try_new_angle": "new_angle",
    "not_enough_evidence_yet": "need_more_evidence",
    "not_enough_evidence": "need_more_evidence",
}
FLAGS = ("pitched_early", "leading_questions", "talked_too_much")
REQUIRED = ("idea", "transcript", "expected_verdict", "customer_sentences")
CUSTOMER_LINE = re.compile(r"^[ \t]*customer[ \t]*:[ \t]*(.*)$", re.IGNORECASE | re.MULTILINE)


@dataclass
class CaseResult:
    id: str
    persona: str
    difficulty: str
    expected_verdict: str
    allowed_verdicts: list[str]
    verdict: str = ""
    score: int | None = None
    categories_total: int = 0
    categories_right: int = 0
    groups_right: int = 0
    unmatched: int = 0
    flags_total: int = 0
    flags_right: int = 0
    disagreements: list[dict] = field(default_factory=list)
    flag_misses: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    through_team: bool | None = None
    error: str | None = None

    @property
    def ran(self) -> bool:
        return self.error is None

    @property
    def verdict_exact(self) -> bool:
        return self.ran and self.verdict == self.expected_verdict

    @property
    def verdict_allowed(self) -> bool:
        return self.ran and self.verdict in self.allowed_verdicts


def slug(value: str) -> str:
    value = re.sub(r"[^a-z]+", "_", str(value).strip().lower()).strip("_")
    return VERDICT_ALIASES.get(value, value)


def norm(text: str) -> str:
    """Compare sentences by their words only, so quotes and spacing do not matter."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def gate_warnings(case: dict) -> list[str]:
    """The analyzer answers need_more_evidence when the evidence is thin, whatever the interview says.
    A key that expects another verdict from an interview under the gate is a broken case, not a miss."""
    rubric = load_rubric()
    gate, categories = rubric["gate"], rubric["categories"]
    words = sum(len(text.split()) for text in CUSTOMER_LINE.findall(case["transcript"]))
    signals = sum(1 for s in case["customer_sentences"] if categories[s["category"]]["group"] != "none")
    under = []
    if words < gate["min_customer_words"]:
        under.append(f"{words} customer words (the gate needs {gate['min_customer_words']})")
    if signals < gate["min_non_neutral"]:
        under.append(f"{signals} non-neutral sentences in the key (the gate needs {gate['min_non_neutral']})")
    expects_gate = "need_more_evidence" in case["allowed_verdicts"]
    if under and not expects_gate:
        return [f"key expects {case['expected_verdict']} but the interview is under the gate: " + ", ".join(under)]
    if not under and case["expected_verdict"] == "need_more_evidence":
        return ["key expects need_more_evidence but the interview passes the word and sentence gates"]
    return []


def load_cases(path: Path) -> list[dict]:
    """Read one file of cases. Tolerates the ```json fence models often wrap around their answer."""
    text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", path.read_text().strip())
    data = json.loads(text)
    cases = data["cases"] if isinstance(data, dict) else data
    categories = load_rubric()["categories"]
    for i, case in enumerate(cases):
        missing = [key for key in REQUIRED if not case.get(key)]
        if missing:
            raise ValueError(f"{path.name}, case {i + 1}: missing {', '.join(missing)}")
        case["id"] = f"{path.stem}/{case.get('id') or i + 1}"
        case["expected_verdict"] = slug(case["expected_verdict"])
        allowed = [slug(v) for v in case.get("allowed_verdicts") or []]
        case["allowed_verdicts"] = sorted({case["expected_verdict"], *allowed})
        for verdict in case["allowed_verdicts"]:
            if verdict not in VERDICTS:
                raise ValueError(f"{case['id']}: unknown verdict {verdict!r}")
        for sentence in case["customer_sentences"]:
            sentence["category"] = slug(sentence["category"])
            if sentence["category"] not in categories:
                raise ValueError(f"{case['id']}: unknown category {sentence['category']!r}")
        case["warnings"] = gate_warnings(case)
    return cases


def new_result(case: dict) -> CaseResult:
    return CaseResult(
        id=case["id"],
        persona=case.get("persona", "?"),
        difficulty=case.get("difficulty", "?"),
        expected_verdict=case["expected_verdict"],
        allowed_verdicts=case["allowed_verdicts"],
        warnings=list(case.get("warnings", [])),
    )


def score_case(case: dict, judged: Judged) -> CaseResult:
    """Line the judged statements up with the answer key by their text."""
    rubric = load_rubric()
    categories, limits = rubric["categories"], rubric["founder_flags"]
    result = new_result(case)
    result.verdict, result.score = judged.verdict, judged.score

    got = defaultdict(list)
    for statement in judged.statements:
        got[norm(statement.quote)].append(statement)
    for expected in case["customer_sentences"]:
        matches = got.get(norm(expected["text"]))
        statement = matches.pop(0) if matches else None
        if statement is None:
            result.unmatched += 1
            continue
        result.categories_total += 1
        same_group = categories[statement.category]["group"] == categories[expected["category"]]["group"]
        result.groups_right += same_group
        if statement.category == expected["category"]:
            result.categories_right += 1
        else:
            result.disagreements.append(
                {
                    "text": expected["text"],
                    "expected": expected["category"],
                    "got": statement.category,
                    "p_real": statement.p_real,
                    "same_group": same_group,
                }
            )

    measured = {
        "pitched_early": (judged.pitched_early, limits["pitched_early"]),
        "leading_questions": (judged.leading_questions, limits["leading_questions"]),
        "talked_too_much": (judged.founder_talk_ratio, limits["talk_ratio"]),
    }
    for flag, expected in (case.get("founder") or {}).items():
        value, limit = measured.get(flag, (None, None))
        if value is None or not isinstance(expected, bool):
            continue
        result.flags_total += 1
        if (value > limit) == expected:
            result.flags_right += 1
        else:
            result.flag_misses.append(f"{flag}: key says {expected}, measured {value:.2f} (limit {limit})")
    return result


def pct(right: int, total: int) -> str:
    return f"{right}/{total} ({100 * right / total:.0f}%)" if total else "n/a"


def breakdown(results: list[CaseResult], key: str) -> list[str]:
    groups = defaultdict(list)
    for r in results:
        groups[getattr(r, key)].append(r)
    return [
        f"  {name:<26} verdict {pct(sum(r.verdict_allowed for r in group), len(group)):<14}"
        f" categories {pct(sum(r.categories_right for r in group), sum(r.categories_total for r in group))}"
        for name, group in sorted(groups.items())
    ]


def report(results: list[CaseResult]) -> str:
    ok = [r for r in results if r.ran]
    lines = ["", "=== Cases ==="]
    for r in results:
        if not r.ran:
            lines.append(f"  ERROR {r.id}: {r.error}")
            continue
        mark = "ok  " if r.verdict_exact else ("ok~ " if r.verdict_allowed else "MISS")
        lines.append(
            f"  {mark} {r.id:<24} expected {r.expected_verdict:<18} got {r.verdict:<18}"
            f" score {str(r.score):>4}  categories {pct(r.categories_right, r.categories_total)}"
            + (f"  ({r.unmatched} unmatched)" if r.unmatched else "")
            + ("  [fallback]" if r.through_team is False else "")
        )

    total_categories = sum(r.categories_total for r in ok)
    lines += ["", "=== Accuracy ==="]
    lines.append(f"  Verdict, exact:        {pct(sum(r.verdict_exact for r in ok), len(ok))}")
    lines.append(f"  Verdict, allowed set:  {pct(sum(r.verdict_allowed for r in ok), len(ok))}   (ok~ above)")
    lines.append(f"  Category, exact:       {pct(sum(r.categories_right for r in ok), total_categories)}")
    lines.append(f"  Category, same group:  {pct(sum(r.groups_right for r in ok), total_categories)}   (real / polite / none)")
    lines.append(f"  Founder flags:         {pct(sum(r.flags_right for r in ok), sum(r.flags_total for r in ok))}")
    gated = [r for r in ok if r.verdict == "need_more_evidence" and r.expected_verdict != "need_more_evidence"]
    if gated:
        lines.append(f"  {len(gated)} cases got need_more_evidence when the key expected a verdict (the confidence gate).")
    unmatched = sum(r.unmatched for r in ok)
    if unmatched:
        lines.append(f"  {unmatched} answer-key sentences could not be lined up and were left out.")
    fallbacks = sum(1 for r in ok if r.through_team is False)
    if fallbacks:
        lines.append(f"  {fallbacks} cases were answered by the front agent alone (a specialist did not answer).")

    lines += ["", "By persona (verdict in allowed set):"] + breakdown(ok, "persona")
    lines += ["", "By difficulty (verdict in allowed set):"] + breakdown(ok, "difficulty")

    confusion = Counter((d["expected"], d["got"]) for r in ok for d in r.disagreements)
    if confusion:
        lines += ["", "Category mix-ups (answer key -> agents):"]
        lines += [f"  {exp:<13} -> {got:<13} {n}" for (exp, got), n in confusion.most_common()]

    warned = [r for r in results if r.warnings]
    if warned:
        lines += ["", "=== Broken cases (fix or drop these before trusting the numbers) ==="]
        lines += [f"  {r.id}: {w}" for r in warned for w in r.warnings]

    misses = [r for r in ok if not r.verdict_allowed or r.disagreements or r.flag_misses]
    if misses:
        lines += ["", "=== Disagreements (read these: the answer key can be wrong too) ==="]
        for r in misses:
            lines.append(f"  {r.id} [{r.persona}, {r.difficulty}]")
            if not r.verdict_allowed:
                allowed = ", ".join(r.allowed_verdicts)
                lines.append(f"    verdict: expected {allowed}; got {r.verdict} (score {r.score})")
            for d in r.disagreements:
                lines.append(f"    {d['expected']} -> {d['got']} (p_real {d['p_real']:.2f}): {d['text']}")
            lines += [f"    founder: {miss}" for miss in r.flag_misses]
    return "\n".join(lines)
