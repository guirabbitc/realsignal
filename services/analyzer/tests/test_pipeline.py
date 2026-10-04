import pytest

from app.errors import JevFailed, WriterUnverifiable
from app.models import AnalyzeRequest
from app.pipeline.analyze import Judged, judge_interview, run_analysis, write_readout
from app.pipeline.writer import WriterOutput
from tests.conftest import LabelledJev, ScriptedWriter, labelled_jev_for, load_fixture

IDEA = "WhatsApp bot that takes restaurant reservations"


def request(transcript: str) -> AnalyzeRequest:
    return AnalyzeRequest(idea=IDEA, transcript=transcript, kind="interview")


async def analyze_fixture(name, make_judge, rubric, **jev_kwargs):
    transcript, _ = load_fixture(name)
    return await run_analysis(request(transcript), make_judge(labelled_jev_for(name, **jev_kwargs)),
                              ScriptedWriter(), rubric)


async def test_fixture_order_polite_lt_mixed_lt_real_pain(make_judge, rubric):
    scores = {n: (await analyze_fixture(n, make_judge, rubric)).score for n in ["polite", "mixed", "real_pain"]}
    assert scores["polite"] < scores["mixed"] < scores["real_pain"]


@pytest.mark.parametrize("name", ["polite", "mixed", "real_pain"])
async def test_fixture_scores_land_in_their_human_bands(name, make_judge, rubric):
    _, labels = load_fixture(name)
    score = (await analyze_fixture(name, make_judge, rubric)).score
    band = labels["score_band"]
    assert score > band.get("min_exclusive", -1) and score >= band.get("min_inclusive", 0)
    assert score < band.get("max_exclusive", 101) and score <= band.get("max_inclusive", 100)


async def test_statement_quotes_are_verbatim(make_judge, rubric):
    transcript, _ = load_fixture("real_pain")
    result = await analyze_fixture("real_pain", make_judge, rubric)
    assert result.statements and all(s.quote in transcript for s in result.statements)


async def test_founder_only_transcript_needs_more_evidence(make_judge, rubric):
    jev = LabelledJev()
    result = await run_analysis(request("Founder: Hello? Is anyone there? I will pitch now."),
                                make_judge(jev), ScriptedWriter(), rubric)
    assert result.verdict == "need_more_evidence"
    assert result.verdict_confidence is None
    assert result.missing_evidence
    assert not any("verdict" in c for c in jev.calls)  # pre-gate skips the verdict calls


async def test_low_verdict_confidence_trips_the_gate(make_judge, rubric):
    result = await analyze_fixture("real_pain", make_judge, rubric, verdict_conf=0.4)
    assert result.verdict == "need_more_evidence"
    assert "confidence" in result.missing_evidence


async def test_verdict_uses_three_samples(make_judge, rubric):
    jev = labelled_jev_for("real_pain")
    transcript, _ = load_fixture("real_pain")
    await run_analysis(request(transcript), make_judge(jev), ScriptedWriter(), rubric)
    assert sum(1 for c in jev.calls if "verdict" in c) == rubric["verdict_samples"]


async def test_jev_failure_fails_the_analysis_never_defaults(make_judge, rubric):
    transcript, _ = load_fixture("real_pain")
    with pytest.raises(JevFailed):
        await run_analysis(request(transcript), make_judge(LabelledJev(fail=True)), ScriptedWriter(), rubric)


async def test_writer_paraphrase_retries_once_then_fails(make_judge, rubric):
    transcript, _ = load_fixture("real_pain")
    bad = WriterOutput(summary='They said "we lose a fortune every weekend".', reasons=[],
                       next_questions=["a?", "b?", "c?"])
    writer = ScriptedWriter([bad, bad])
    with pytest.raises(WriterUnverifiable):
        await run_analysis(request(transcript), make_judge(labelled_jev_for("real_pain")), writer, rubric)
    assert writer.calls == 2


async def test_unverifiable_reason_is_dropped(make_judge, rubric):
    transcript, _ = load_fixture("real_pain")
    out = WriterOutput(summary="Real pain [#9].",
                       reasons=['Good: "I pay someone 300 dollars a month"', 'Bad: "they love our brand a lot"'],
                       next_questions=["a?", "b?", "c?"])
    result = await run_analysis(request(transcript), make_judge(labelled_jev_for("real_pain")),
                                ScriptedWriter([out]), rubric)
    assert result.reasons == ['Good: "I pay someone 300 dollars a month"']


async def test_writer_cannot_change_the_verdict(make_judge, rubric):
    result = await analyze_fixture(
        "real_pain", make_judge, rubric,
        verdict_probs={"keep_going": 0.1, "narrow_down": 0.1, "new_angle": 0.1, "pivot": 0.7},
    )
    assert result.verdict == "pivot"  # whatever the writer says, the verdict is Jev's


async def test_the_two_halves_give_the_same_result_as_one_run_even_across_a_json_hop(make_judge, rubric):
    transcript, _ = load_fixture("real_pain")
    whole = await analyze_fixture("real_pain", make_judge, rubric)

    judged = await judge_interview(request(transcript), make_judge(labelled_jev_for("real_pain")), rubric)
    carried = Judged.model_validate_json(judged.model_dump_json())  # as sent between two agents
    halves = await write_readout(request(transcript), carried, ScriptedWriter(), rubric)

    assert halves == whole
