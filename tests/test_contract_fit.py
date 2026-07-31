import pytest

from src.contract_fit import calculate_contract_fit, sprint_to_months
from src.models import SizingResult


def make_sizing(max_sprints: float) -> SizingResult:
    return SizingResult(
        relative_job_size=5,
        tshirt_size="M",
        min_sprints=2,
        max_sprints=max_sprints,
        discovery_review_required=False,
        decomposition_required=False,
    )


def test_sprint_to_months_formula():
    assert sprint_to_months(4) == pytest.approx(4 * 2 / 4.33)


def test_contract_fit_fits_at_exactly_80_percent():
    sizing = make_sizing(4)
    estimated = sprint_to_months(4)
    contract_months = estimated / 0.80
    result = calculate_contract_fit(sizing, "Custom", contract_months)
    assert result.fit_ratio == pytest.approx(0.80)
    assert result.status == "Fits"


def test_contract_fit_below_80_percent():
    sizing = make_sizing(1)
    result = calculate_contract_fit(sizing, "Annual")
    assert result.status == "Fits"
    assert result.fit_ratio < 0.80


def test_contract_fit_at_risk_above_80_percent():
    sizing = make_sizing(4)
    estimated = sprint_to_months(4)
    contract_months = estimated / 0.85
    result = calculate_contract_fit(sizing, "Custom", contract_months)
    assert result.status == "At Risk"


def test_contract_fit_at_risk_at_exactly_100_percent():
    sizing = make_sizing(4)
    estimated = sprint_to_months(4)
    result = calculate_contract_fit(sizing, "Custom", estimated)
    assert result.fit_ratio == pytest.approx(1.00)
    assert result.status == "At Risk"


def test_contract_fit_does_not_fit_above_100_percent():
    sizing = make_sizing(10)
    result = calculate_contract_fit(sizing, "Quarterly")
    assert result.status == "Does Not Fit"
    assert result.fit_ratio > 1.0


def test_contract_fit_definition_required_when_custom_months_missing():
    sizing = make_sizing(4)
    result = calculate_contract_fit(sizing, "Custom", None)
    assert result.status == "Estimate Definition Required"
    assert result.fit_ratio is None
    assert result.contract_months is None
    assert result.estimated_months is not None


def test_contract_fit_uses_standard_term_months():
    sizing = make_sizing(4)
    result = calculate_contract_fit(sizing, "Six months")
    assert result.contract_months == 6


def test_contract_fit_unknown_term_raises():
    sizing = make_sizing(4)
    with pytest.raises(ValueError):
        calculate_contract_fit(sizing, "Not a real term")
