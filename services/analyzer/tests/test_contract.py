"""The Pydantic models must match packages/contracts/analyze.schema.json and transcribe.schema.json
(SPEC §4 rule 3)."""

import json
from pathlib import Path
from typing import get_args

import jsonschema
import pytest

from app.models import (
    AnalyzeRequest,
    AnalyzeResult,
    ErrorResponse,
    Statement,
    TranscribeErrorCode,
    TranscribeErrorDetail,
    TranscribeErrorResponse,
    TranscribeFailureReason,
    TranscribeResult,
    TranscribeSpeaker,
    TranscribeTurn,
)

CONTRACTS = Path(__file__).parents[3] / "packages/contracts"
CONTRACT = json.loads((CONTRACTS / "analyze.schema.json").read_text())
DEFS = CONTRACT["$defs"]
TRANSCRIBE = json.loads((CONTRACTS / "transcribe.schema.json").read_text())
T_DEFS = TRANSCRIBE["$defs"]
T_ERROR = T_DEFS["TranscribeErrorResponse"]["properties"]["error"]


@pytest.mark.parametrize("model,name", [(AnalyzeRequest, "AnalyzeRequest"), (AnalyzeResult, "AnalyzeResult"),
                                        (Statement, "Statement"), (ErrorResponse, "ErrorResponse")])
def test_fields_and_required_match(model, name):
    schema = model.model_json_schema()
    assert set(schema["properties"]) == set(DEFS[name]["properties"])
    pyd_required = {k for k, f in model.model_fields.items() if f.is_required()}
    contract_required = set(DEFS[name]["required"])
    # Fields with defaults in Pydantic may be required in the contract (always present in output).
    assert pyd_required <= contract_required


def test_enums_match():
    from typing import get_args

    from app.models import Category, ErrorCode, Kind, Verdict

    assert set(get_args(Kind)) == set(DEFS["Kind"]["enum"])
    assert set(get_args(Category)) == set(DEFS["Category"]["enum"])
    assert set(get_args(Verdict)) == set(DEFS["Verdict"]["enum"])
    assert set(get_args(ErrorCode)) == set(DEFS["ErrorResponse"]["properties"]["error"]["properties"]["code"]["enum"])


async def test_a_real_result_validates_against_the_contract(make_judge, rubric):
    from tests.test_pipeline import analyze_fixture

    result = await analyze_fixture("real_pain", make_judge, rubric)
    schema = {"$schema": CONTRACT["$schema"], "$defs": DEFS, "$ref": "#/$defs/AnalyzeResult"}
    jsonschema.validate(result.model_dump(mode="json"), schema)


@pytest.mark.parametrize("model,props", [
    (TranscribeTurn, T_DEFS["TranscribeTurn"]),
    (TranscribeSpeaker, T_DEFS["TranscribeSpeaker"]),
    (TranscribeResult, T_DEFS["TranscribeResult"]),
    (TranscribeErrorResponse, T_DEFS["TranscribeErrorResponse"]),
    (TranscribeErrorDetail, T_ERROR),
])
def test_transcribe_fields_and_required_match(model, props):
    assert set(model.model_json_schema()["properties"]) == set(props["properties"])
    assert {k for k, f in model.model_fields.items() if f.is_required()} <= set(props["required"])


def test_transcribe_enums_match():
    assert set(get_args(TranscribeErrorCode)) == set(T_ERROR["properties"]["code"]["enum"])
    assert set(get_args(TranscribeFailureReason)) | {None} == set(T_ERROR["properties"]["reason"]["enum"])


def test_a_transcribe_result_and_error_validate_against_the_contract():
    from app.errors import TranscriptionFailed
    from app.pipeline.transcribe import to_result

    scribe = json.loads((Path(__file__).parent / "recordings/audio/synthetic.scribe.json").read_text())
    for name, value in [
        ("TranscribeResult", to_result(scribe, "scribe_v2").model_dump(mode="json")),
        ("TranscribeErrorResponse", {"error": {"code": "transcription_failed",
                                               "message": TranscriptionFailed("timeout").message, "reason": "timeout"}}),
        ("TranscribeErrorResponse", {"error": {"code": "no_speech", "message": "No speech."}}),
    ]:
        jsonschema.validate(value, {"$schema": TRANSCRIBE["$schema"], "$defs": T_DEFS, "$ref": f"#/$defs/{name}"})
