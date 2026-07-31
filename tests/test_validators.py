import pytest

from src.config import ConfigurationError
from src.models import COMPLEXITY_DIMENSION_KEYS
from src.validators import (
    find_missing_required_fields,
    validate_ai_capability,
    validate_ai_workstream_activities,
    validate_complexity_questions_schema,
    validate_contract_duration,
    validate_contract_terms,
    validate_dimension_score,
    validate_sizing_bands,
    validate_weight_total,
)

VALID_WEIGHTS = {
    "functional": 0.20,
    "technical": 0.20,
    "integration": 0.15,
    "data": 0.10,
    "testing": 0.15,
    "dependency": 0.10,
    "operational_risk": 0.10,
}

VALID_BANDS = [
    {"relative_job_size": 1, "tshirt_size": "XS", "min_score": 0.00, "max_score": 0.75, "min_sprints": 0.5, "max_sprints": 1, "discovery_review_required": False, "decomposition_required": False},
    {"relative_job_size": 2, "tshirt_size": "S", "min_score": 0.76, "max_score": 1.50, "min_sprints": 1, "max_sprints": 1.5, "discovery_review_required": False, "decomposition_required": False},
    {"relative_job_size": 3, "tshirt_size": "S", "min_score": 1.51, "max_score": 2.00, "min_sprints": 1, "max_sprints": 2, "discovery_review_required": False, "decomposition_required": False},
    {"relative_job_size": 5, "tshirt_size": "M", "min_score": 2.01, "max_score": 3.00, "min_sprints": 2, "max_sprints": 4, "discovery_review_required": False, "decomposition_required": False},
    {"relative_job_size": 8, "tshirt_size": "L", "min_score": 3.01, "max_score": 4.00, "min_sprints": 4, "max_sprints": 6, "discovery_review_required": False, "decomposition_required": False},
    {"relative_job_size": 13, "tshirt_size": "XL", "min_score": 4.01, "max_score": 4.60, "min_sprints": 6, "max_sprints": 10, "discovery_review_required": True, "decomposition_required": False},
    {"relative_job_size": 20, "tshirt_size": "Epic", "min_score": 4.61, "max_score": 5.00, "min_sprints": 10, "max_sprints": 16, "discovery_review_required": False, "decomposition_required": True},
]


def test_validate_dimension_score_accepts_boundaries():
    assert validate_dimension_score(0) == 0
    assert validate_dimension_score(5) == 5


@pytest.mark.parametrize("bad", [-1, 6, 2.5, "3", True])
def test_validate_dimension_score_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_dimension_score(bad)


def test_validate_weight_total_accepts_approved_weights():
    validate_weight_total(VALID_WEIGHTS)  # must not raise


def test_validate_weight_total_rejects_wrong_sum():
    weights = dict(VALID_WEIGHTS)
    weights["operational_risk"] = 0.05
    with pytest.raises(ConfigurationError):
        validate_weight_total(weights)


def test_validate_weight_total_rejects_missing_dimension():
    with pytest.raises(ConfigurationError):
        validate_weight_total({"functional": 1.0})


def test_validate_sizing_bands_accepts_approved_table():
    validate_sizing_bands(VALID_BANDS)  # must not raise


def test_validate_sizing_bands_rejects_gap():
    bands = [dict(band) for band in VALID_BANDS]
    bands[1]["min_score"] = 0.80
    with pytest.raises(ConfigurationError):
        validate_sizing_bands(bands)


def test_validate_sizing_bands_rejects_overlap():
    bands = [dict(band) for band in VALID_BANDS]
    bands[1]["min_score"] = 0.70
    with pytest.raises(ConfigurationError):
        validate_sizing_bands(bands)


def test_validate_sizing_bands_rejects_invalid_relative_job_size():
    bands = [dict(band) for band in VALID_BANDS]
    bands[0]["relative_job_size"] = 4
    with pytest.raises(ConfigurationError):
        validate_sizing_bands(bands)


def test_validate_sizing_bands_rejects_invalid_tshirt():
    bands = [dict(band) for band in VALID_BANDS]
    bands[0]["tshirt_size"] = "XXL"
    with pytest.raises(ConfigurationError):
        validate_sizing_bands(bands)


def test_validate_sizing_bands_rejects_empty():
    with pytest.raises(ConfigurationError):
        validate_sizing_bands([])


def test_validate_contract_terms_rejects_non_positive():
    with pytest.raises(ConfigurationError):
        validate_contract_terms({"Quarterly": 0})


def test_validate_contract_terms_rejects_empty():
    with pytest.raises(ConfigurationError):
        validate_contract_terms({})


def test_validate_contract_duration_rejects_non_positive():
    with pytest.raises(ValueError):
        validate_contract_duration(0)
    with pytest.raises(ValueError):
        validate_contract_duration(-1)
    with pytest.raises(ValueError):
        validate_contract_duration(None)


def test_validate_contract_duration_accepts_positive():
    assert validate_contract_duration(6) == 6.0


def test_validate_ai_capability_rejects_unknown_value():
    with pytest.raises(ValueError):
        validate_ai_capability("Maybe", ("No", "Yes - AI-assisted feature"))


def test_validate_ai_capability_accepts_known_value():
    assert validate_ai_capability("No", ("No", "Yes - AI-assisted feature")) == "No"


def test_validate_ai_workstream_activities_rejects_unknown_activity():
    with pytest.raises(ValueError):
        validate_ai_workstream_activities(["Not a real activity"], ["AI use-case definition"])


def test_validate_ai_workstream_activities_accepts_known_activities():
    result = validate_ai_workstream_activities(
        ["AI use-case definition"], ["AI use-case definition", "AI monitoring"]
    )
    assert result == ["AI use-case definition"]


def test_validate_complexity_questions_schema_rejects_missing_level():
    data = {
        "dimensions": [
            {
                "key": key,
                "display_name": "Display",
                "question": "Q?",
                "levels": [
                    {"score": score, "label": "L", "description": "D", "example": "E"}
                    for score in range(5)  # missing score 5
                ],
            }
            for key in COMPLEXITY_DIMENSION_KEYS
        ]
    }
    with pytest.raises(ConfigurationError):
        validate_complexity_questions_schema(data)


def test_validate_complexity_questions_schema_rejects_missing_dimension():
    with pytest.raises(ConfigurationError):
        validate_complexity_questions_schema({"dimensions": []})


def test_find_missing_required_fields_reports_gaps():
    missing = find_missing_required_fields({})
    assert "Estimate name" in missing
    assert "Work type" in missing
    assert any("Complexity answer" in item for item in missing)


def test_find_missing_required_fields_empty_when_complete():
    state = {
        "estimate_name": "Name",
        "work_type": "new_project",
        "business_objective": "Obj",
        "system_context": "New system",
        "audience": "Internal users",
        "contract_term": "Quarterly",
        "complexity_answers": {key: 3 for key in COMPLEXITY_DIMENSION_KEYS},
        "ai_included": "No",
    }
    assert find_missing_required_fields(state) == []


def test_find_missing_required_fields_requires_ai_fields_when_ai_on():
    state = {
        "estimate_name": "Name",
        "work_type": "new_project",
        "business_objective": "Obj",
        "system_context": "New system",
        "audience": "Internal users",
        "contract_term": "Quarterly",
        "complexity_answers": {key: 3 for key in COMPLEXITY_DIMENSION_KEYS},
        "ai_included": "Yes",
    }
    missing = find_missing_required_fields(state)
    assert "What should AI help with?" in missing
    assert "What data will AI use?" in missing
    assert "Will a person review AI output?" in missing
