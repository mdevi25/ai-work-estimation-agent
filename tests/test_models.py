import pytest
from pydantic import ValidationError

from src.models import COMPLEXITY_DIMENSION_KEYS, ComplexityDimensionAnswer, EstimateRequest


def _complete_complexity_answers():
    return [
        ComplexityDimensionAnswer(dimension_key=key, selected_label="Moderate", score=3)
        for key in COMPLEXITY_DIMENSION_KEYS
    ]


def _base_kwargs(**overrides):
    kwargs = dict(
        estimate_name="Test estimate",
        work_type="new_project",
        estimate_type="new_project",
        business_objective="Objective",
        system_context="New system",
        audience="Internal users",
        contract_term="Quarterly",
        complexity_answers=_complete_complexity_answers(),
    )
    kwargs.update(overrides)
    return kwargs


def test_estimate_request_minimal_required_fields():
    request = EstimateRequest(**_base_kwargs())
    assert request.ai_included == "No"
    assert request.ai_capability == "No"
    assert request.description is None
    assert request.included_scope is None


def test_estimate_request_rejects_stale_ai_fields_when_off():
    with pytest.raises(ValidationError):
        EstimateRequest(**_base_kwargs(ai_included="No", ai_capability_type="Chatbot"))


def test_estimate_request_rejects_ai_capability_set_without_ai_included():
    with pytest.raises(ValidationError):
        EstimateRequest(**_base_kwargs(ai_capability="Yes - Other AI capability"))


def test_estimate_request_accepts_ai_fields_when_on():
    request = EstimateRequest(
        **_base_kwargs(
            ai_included="Yes",
            ai_capability="Yes - Other AI capability",
            ai_help=["Generate content"],
            ai_data="Internal business information",
            ai_human_review="Always",
        )
    )
    assert request.ai_help == ["Generate content"]
    assert request.ai_human_review == "Always"


def test_complexity_dimension_answer_rejects_unknown_dimension():
    with pytest.raises(ValidationError):
        ComplexityDimensionAnswer(dimension_key="unknown", selected_label="Low", score=2)


def test_complexity_dimension_answer_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        ComplexityDimensionAnswer(dimension_key="functional", selected_label="Low", score=6)


def test_estimate_request_rejects_incomplete_complexity_answers():
    with pytest.raises(ValidationError):
        EstimateRequest(
            **_base_kwargs(
                complexity_answers=[
                    ComplexityDimensionAnswer(dimension_key="functional", selected_label="Low", score=2)
                ]
            )
        )
