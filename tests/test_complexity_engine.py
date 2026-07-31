import pytest

from src.complexity_engine import (
    calculate_weighted_complexity,
    load_complexity_questions,
    load_complexity_weights,
)
from src.models import COMPLEXITY_DIMENSION_KEYS


def test_load_complexity_weights_totals_one():
    weights = load_complexity_weights()
    assert set(weights.keys()) == set(COMPLEXITY_DIMENSION_KEYS)
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_load_complexity_questions_has_all_dimensions_with_six_levels():
    questions = load_complexity_questions()
    keys = {dimension["key"] for dimension in questions["dimensions"]}
    assert keys == set(COMPLEXITY_DIMENSION_KEYS)
    for dimension in questions["dimensions"]:
        assert len(dimension["levels"]) == 6
        assert sorted(level["score"] for level in dimension["levels"]) == [0, 1, 2, 3, 4, 5]


def test_weighted_complexity_full_precision_and_display():
    scores = {
        "functional": 3,
        "technical": 2,
        "integration": 1,
        "data": 4,
        "testing": 3,
        "dependency": 0,
        "operational_risk": 5,
    }
    result = calculate_weighted_complexity(scores)
    expected = 3 * 0.20 + 2 * 0.20 + 1 * 0.15 + 4 * 0.10 + 3 * 0.15 + 0 * 0.10 + 5 * 0.10
    assert result.weighted_complexity_score == pytest.approx(expected)
    assert result.weighted_complexity_display == f"{expected:.2f}"


def test_weighted_complexity_rejects_missing_dimension():
    with pytest.raises(ValueError):
        calculate_weighted_complexity({"functional": 3})


def test_weighted_complexity_rejects_out_of_range_score():
    scores = {key: 3 for key in COMPLEXITY_DIMENSION_KEYS}
    scores["functional"] = 6
    with pytest.raises(ValueError):
        calculate_weighted_complexity(scores)


def test_higher_scoring_dimensions_only_include_four_and_five():
    scores = {key: 3 for key in COMPLEXITY_DIMENSION_KEYS}
    scores["functional"] = 4
    scores["technical"] = 5
    result = calculate_weighted_complexity(scores)
    assert set(result.higher_scoring_dimensions) == {"functional", "technical"}


def test_no_higher_scoring_dimensions_when_all_below_four():
    scores = {key: 2 for key in COMPLEXITY_DIMENSION_KEYS}
    result = calculate_weighted_complexity(scores)
    assert result.higher_scoring_dimensions == []


def test_below_four_scores_still_present_in_full_detail():
    scores = {key: 3 for key in COMPLEXITY_DIMENSION_KEYS}
    result = calculate_weighted_complexity(scores)
    assert result.dimension_scores == scores
    assert set(result.dimension_contributions.keys()) == set(COMPLEXITY_DIMENSION_KEYS)


def test_weighted_complexity_all_zero():
    scores = {key: 0 for key in COMPLEXITY_DIMENSION_KEYS}
    result = calculate_weighted_complexity(scores)
    assert result.weighted_complexity_score == 0.0
    assert result.weighted_complexity_display == "0.00"


def test_weighted_complexity_all_five():
    scores = {key: 5 for key in COMPLEXITY_DIMENSION_KEYS}
    result = calculate_weighted_complexity(scores)
    assert result.weighted_complexity_score == pytest.approx(5.0)
    assert result.weighted_complexity_display == "5.00"
