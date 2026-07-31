"""Baseline delivery cost from role-specific hourly rates (MVP.M3).

Owns: loading/validating the configured rate card (data/rate_card.csv),
computing role cost, baseline delivery cost, the read-only blended hourly
rate, and pricing-readiness status. No contingency, margin, markup,
discount, or customer price exists anywhere in this file -- that is
MVP.M4 scope.

Rates in data/rate_card.csv are fictional/illustrative demonstration
values only, per GUARDRAILS.md section 3 and PRICING-RULES.md section 9.
The rate card is read-only from the application's perspective: scenario
overrides live only in the caller's session state and are never written
back to the CSV file.
"""
from __future__ import annotations

from typing import Optional

from src.config import load_csv_config
from src.models import BaselineCostResult, RateCardEntry, ResourcePlanResult, RoleCostRow
from src.validators import validate_override_reason, validate_rate_card, validate_scenario_rate_value

COMMERCIAL_BELOW_DEFAULT_WARNING = (
    "Commercial risk: The proposed scenario rate is below the configured default and may "
    "reduce expected margin. Review the resulting gross profit and margin before approving "
    "this quote.\n\nGross profit and margin will be calculated in a later milestone."
)


def load_rate_card() -> dict[str, RateCardEntry]:
    records = load_csv_config("rate_card.csv")
    validate_rate_card(records)
    return {
        record["Role"].strip(): RateCardEntry(
            role=record["Role"].strip(),
            default_hourly_rate=float(record["Default Hourly Rate"]),
            currency=record["Currency"].strip(),
            active=str(record.get("Active", "")).strip().lower() in ("yes", "true", "1"),
        )
        for record in records
    }


def reset_role_rate(role: str, scenario_rates: dict[str, float], override_reasons: dict[str, str]) -> None:
    """Restores the configured default (by removing the override), clearing
    both the scenario rate and its override reason for this role.
    """
    scenario_rates.pop(role, None)
    override_reasons.pop(role, None)


def reset_all_rates(
    active_roles: list[str], scenario_rates: dict[str, float], override_reasons: dict[str, str]
) -> None:
    for role in active_roles:
        reset_role_rate(role, scenario_rates, override_reasons)


def reconcile_rate_state(
    active_roles: set[str], scenario_rates: dict[str, float], override_reasons: dict[str, str]
) -> None:
    """Drops stale scenario rates/reasons for roles no longer present in the
    resource plan. Newly introduced roles need no action -- they simply
    have no entry yet and default to the configured rate.
    """
    for role in list(scenario_rates.keys()):
        if role not in active_roles:
            scenario_rates.pop(role, None)
            override_reasons.pop(role, None)
    for role in list(override_reasons.keys()):
        if role not in active_roles:
            override_reasons.pop(role, None)


def build_baseline_cost(
    resource_plan: Optional[ResourcePlanResult],
    scenario_rates: dict[str, float],
    override_reasons: dict[str, str],
    ai_enabled: bool,
    staffing_model: str,
    unresolved_items_present: bool,
) -> BaselineCostResult:
    """Builds the baseline-cost view for the current scenario.

    role_cost = estimated_role_hours * effective_hourly_rate
    baseline_delivery_cost = sum(role_cost)
    blended_hourly_rate = baseline_delivery_cost / total_estimated_hours
        (None when total_estimated_hours is 0 -- never a fabricated 0.00)

    Readiness precedence: Calculation Blocked > Human Review Required >
    Ready for Baseline Review (EAP.M3-D1 correction 4).
    """
    if resource_plan is None or not resource_plan.rows:
        return BaselineCostResult(
            rows=[],
            total_estimated_hours=0.0,
            baseline_delivery_cost=0.0,
            blended_hourly_rate=None,
            readiness_status="Calculation Blocked",
            readiness_reasons=["Resource plan is missing or has no role hours."],
        )

    rate_card = load_rate_card()

    # True if ANY row for that role is AI-tagged (a role could in principle
    # appear in both core IT and AI phases).
    is_ai_by_role: dict[str, bool] = {}
    for row in resource_plan.rows:
        is_ai_by_role[row.role] = is_ai_by_role.get(row.role, False) or row.is_ai_workstream

    blocking_reasons: list[str] = []
    review_reasons: list[str] = []
    commercial_warnings: list[str] = []
    missing_rate_roles: list[str] = []
    rows: list[RoleCostRow] = []

    total_estimated_hours = 0.0
    baseline_delivery_cost = 0.0
    total_cost_core_it = 0.0
    total_cost_ai_workstream = 0.0

    for role, hours in resource_plan.total_hours_by_role.items():
        total_estimated_hours += hours
        entry = rate_card.get(role)

        if entry is None or not entry.active:
            missing_rate_roles.append(role)
            blocking_reasons.append(f"No active configured rate is available for \"{role}\".")
            rows.append(
                RoleCostRow(
                    role=role,
                    total_estimated_hours=hours,
                    is_ai_workstream=is_ai_by_role.get(role, False),
                    has_missing_rate=True,
                )
            )
            continue

        default_rate = entry.default_hourly_rate
        reason = override_reasons.get(role)
        raw_scenario_rate = scenario_rates.get(role, default_rate)

        try:
            scenario_rate = validate_scenario_rate_value(raw_scenario_rate)
        except ValueError as exc:
            blocking_reasons.append(f"{role}: {exc}")
            rows.append(
                RoleCostRow(
                    role=role,
                    total_estimated_hours=hours,
                    configured_default_rate=default_rate,
                    override_reason=reason,
                    currency=entry.currency,
                    is_ai_workstream=is_ai_by_role.get(role, False),
                    has_missing_rate=True,
                )
            )
            continue

        try:
            validate_override_reason(scenario_rate, default_rate, reason)
        except ValueError as exc:
            blocking_reasons.append(f"{role}: {exc}")

        role_cost = round(hours * scenario_rate, 2)
        difference_dollars = round(scenario_rate - default_rate, 2)
        difference_percent = round((difference_dollars / default_rate) * 100, 2) if default_rate else None

        if scenario_rate < default_rate:
            commercial_warnings.append(f"{role}: {COMMERCIAL_BELOW_DEFAULT_WARNING}")
            review_reasons.append(f"\"{role}\"'s scenario rate is below the configured default.")
        elif scenario_rate > default_rate:
            review_reasons.append(f"\"{role}\"'s scenario rate is above the configured default.")

        if scenario_rate == 0:
            review_reasons.append(f"\"{role}\" has a zero rate -- confirm this is intentional.")

        rows.append(
            RoleCostRow(
                role=role,
                total_estimated_hours=hours,
                configured_default_rate=default_rate,
                scenario_rate=scenario_rate,
                override_reason=reason,
                currency=entry.currency,
                role_cost=role_cost,
                difference_dollars=difference_dollars,
                difference_percent=difference_percent,
                is_ai_workstream=is_ai_by_role.get(role, False),
                has_missing_rate=False,
            )
        )

        baseline_delivery_cost += role_cost
        if is_ai_by_role.get(role, False):
            total_cost_ai_workstream += role_cost
        else:
            total_cost_core_it += role_cost

    if total_estimated_hours <= 0:
        blocking_reasons.append("Total estimated hours are invalid (zero or negative).")

    blended_hourly_rate = (
        round(baseline_delivery_cost / total_estimated_hours, 2) if total_estimated_hours > 0 else None
    )

    if ai_enabled:
        review_reasons.append("The AI workstream is present in this estimate.")
    if staffing_model == "Customer-defined":
        review_reasons.append("Customer-defined staffing is in use.")
    if resource_plan.warnings:
        review_reasons.append("Delivery-risk warnings remain from the resource plan -- see the resource plan section.")
    if unresolved_items_present:
        review_reasons.append("Material assumptions or unknown scope items remain unresolved.")

    if blocking_reasons:
        status = "Calculation Blocked"
        readiness_reasons = blocking_reasons
    elif review_reasons:
        status = "Human Review Required"
        readiness_reasons = review_reasons
    else:
        status = "Ready for Baseline Review"
        readiness_reasons = []

    return BaselineCostResult(
        rows=rows,
        total_estimated_hours=round(total_estimated_hours, 2),
        baseline_delivery_cost=round(baseline_delivery_cost, 2),
        blended_hourly_rate=blended_hourly_rate,
        total_cost_core_it=round(total_cost_core_it, 2),
        total_cost_ai_workstream=round(total_cost_ai_workstream, 2),
        missing_rate_roles=missing_rate_roles,
        readiness_status=status,
        readiness_reasons=readiness_reasons,
        commercial_warnings=commercial_warnings,
    )
