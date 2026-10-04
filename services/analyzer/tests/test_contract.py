"""The Pydantic models must match packages/contracts/analyze.schema.json (SPEC §4 rule 3)."""

import json
from pathlib import Path

import jsonschema
import pytest

from app.models import AnalyzeRequest, AnalyzeResult, ErrorResponse, Statement

CONTRACT = json.loads((Path(__file__).parents[3] / "packages/contracts/analyze.schema.json").read_text())
DEFS = CONTRACT["$defs"]


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
