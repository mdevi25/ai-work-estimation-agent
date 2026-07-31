"""Contract-duration fit assessment.

Owns: sprint-to-month conversion, fit ratio, and fit status. For MVP.M1,
uses the maximum estimated sprint count from the approved sizing result as
the duration source, per CONTRACT-FIT.md section 3.

Must not: model PTO, holidays, ceremonies, meetings, or personal
availability.
"""
from __future__ import annotations

from typing import Optional

from src.config import load_json_config
from src.models import ContractFitResult, ContractFitStatus, SizingResult
from src.validators import validate_contract_duration, validate_contract_terms

STATUS_EXPLANATIONS: dict[ContractFitStatus, str] = {
    "Fits": "The estimated delivery duration comfortably fits within the proposed contract term.",
    "At Risk": (
        "The estimated delivery duration is close to the proposed contract term's limit. "
        "Scope, phasing, or duration may need review to ensure a comfortable fit."
    ),
    "Does Not Fit": (
        "The estimated delivery duration exceeds the proposed contract term. Scope "
        "reduction, phased delivery, or an extended contract term is recommended before "
        "proceeding."
    ),
    "Estimate Definition Required": (
        "There is not yet enough defined scope to responsibly estimate a delivery "
        "duration. Additional discovery or requirements definition is recommended before "
        "a duration or contract term can be proposed."
    ),
}


def load_contract_terms() -> dict[str, float]:
    terms = load_json_config("contract_terms.json")
    validate_contract_terms(terms)
    return terms


def sprint_to_months(sprint_count: float) -> float:
    """estimated_months = sprint_count * 2 / 4.33, for two-week sprints."""
    return sprint_count * 2 / 4.33


def _definition_required(estimated_months: float) -> ContractFitResult:
    status: ContractFitStatus = "Estimate Definition Required"
    return ContractFitResult(
        estimated_months=estimated_months,
        contract_months=None,
        fit_ratio=None,
        status=status,
        status_explanation=STATUS_EXPLANATIONS[status],
    )


def calculate_contract_fit(
    sizing_result: SizingResult,
    contract_term: str,
    contract_custom_months: Optional[float] = None,
) -> ContractFitResult:
    estimated_months = sprint_to_months(sizing_result.max_sprints)

    if contract_term == "Custom":
        contract_months: Optional[float] = contract_custom_months
    else:
        terms = load_contract_terms()
        if contract_term not in terms:
            raise ValueError(f"Unknown contract term: {contract_term}")
        contract_months = terms[contract_term]

    if contract_months is None:
        return _definition_required(estimated_months)

    try:
        contract_months = validate_contract_duration(contract_months)
    except ValueError:
        return _definition_required(estimated_months)

    fit_ratio = estimated_months / contract_months

    status: ContractFitStatus
    if fit_ratio <= 0.80:
        status = "Fits"
    elif fit_ratio <= 1.00:
        status = "At Risk"
    else:
        status = "Does Not Fit"

    return ContractFitResult(
        estimated_months=estimated_months,
        contract_months=contract_months,
        fit_ratio=fit_ratio,
        status=status,
        status_explanation=STATUS_EXPLANATIONS[status],
    )
