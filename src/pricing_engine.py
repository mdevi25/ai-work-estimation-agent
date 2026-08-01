"""Baseline delivery cost (MVP.M3) and commercial scenario pricing (MVP.M4).

MVP.M3 section owns: loading/validating the configured rate card
(data/rate_card.csv), computing role cost, baseline delivery cost, the
read-only blended hourly rate, and pricing-readiness status.

MVP.M4 section owns: loading/validating governed commercial scenario
defaults (data/commercial_pricing_defaults.json), computing contingency
through equivalent markup per scenario, commercial-readiness and
approval-status derivation, baseline-drift detection, and the
approval gate. No discount, rounding, or management-adjustment lever
exists in this milestone (EAP.M4-D1) -- customer_price is the direct
output of contingency and target margin only.

Rates in data/rate_card.csv and defaults in
data/commercial_pricing_defaults.json are fictional/illustrative
demonstration values only, per GUARDRAILS.md section 3 and
PRICING-RULES.md section 9. Both are read-only from the application's
perspective: scenario overrides live only in the caller's session state
and are never written back to either file.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.config import load_csv_config, load_json_config
from src.models import (
    SCENARIO_IDS,
    BaselineCostResult,
    CommercialReadinessStatus,
    PricingScenario,
    RateCardEntry,
    ResourcePlanResult,
    RoleCostRow,
    ScenarioApprovalStatus,
)
from src.validators import (
    detect_commercial_loss,
    validate_baseline_delivery_cost,
    validate_commercial_pricing_defaults,
    validate_contingency_percentage,
    validate_override_reason,
    validate_rate_card,
    validate_scenario_rate_value,
    validate_target_margin_percentage,
)

COMMERCIAL_BELOW_DEFAULT_WARNING = (
    "Commercial risk: The proposed scenario rate is below the configured default and may "
    "reduce expected margin. Review the resulting gross profit and margin before approving "
    "this quote.\n\nGross profit and margin will be calculated in a later milestone."
)

DELIVERY_RISK_WARNING = (
    "Delivery risk: The proposed hours may be insufficient for the selected scope and "
    "required delivery activities. Reducing effort without changing scope may affect "
    "testing, deployment readiness, documentation, support coverage, or timeline "
    "reliability. Review the affected roles and phases before approving this scenario."
)

HIGH_DELIVERY_RISK_WARNING = (
    "High delivery risk: One or more required phases have insufficient allocated hours. "
    "This scenario should not be treated as equivalent to the recommended delivery plan "
    "unless scope, responsibilities, or controls are explicitly reduced and documented."
)

COMMERCIAL_LOSS_WARNING = (
    "Commercial loss warning: The proposed customer price is below the calculated delivery "
    "cost. Approving this scenario would create an expected loss unless an authorized "
    "subsidy, strategic exception, or scope adjustment is documented."
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


# =============================================================================
# MVP.M4 -- commercial scenario pricing and approval
# =============================================================================


def load_commercial_pricing_defaults() -> dict:
    data = load_json_config("commercial_pricing_defaults.json")
    validate_commercial_pricing_defaults(data)
    return data


def build_default_scenarios(defaults: dict) -> dict[str, PricingScenario]:
    """Builds the four governed scenarios fresh from configured defaults.
    Not yet calculated against a baseline -- `needs_recalculation=True`
    until the caller runs `recalculate_scenario` against a live
    `BaselineCostResult`.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    scenarios: dict[str, PricingScenario] = {}
    for scenario_id in SCENARIO_IDS:
        entry = defaults["scenarios"][scenario_id]
        scenarios[scenario_id] = PricingScenario(
            scenario_id=scenario_id,
            scenario_name=entry["scenario_name"],
            scenario_description=entry["scenario_description"],
            contingency_percentage=entry["contingency_percentage"],
            target_margin_percentage=entry["target_margin_percentage"],
            created_at=now,
            needs_recalculation=True,
        )
    return scenarios


def reset_scenario_to_default(scenario: PricingScenario, defaults: dict) -> PricingScenario:
    """Restores one scenario's name, description, contingency, and target
    margin to its governed configured default. Does not touch approval
    state directly -- the next recalculation resolves readiness/approval.
    """
    entry = defaults["scenarios"][scenario.scenario_id]
    return scenario.model_copy(
        update={
            "scenario_name": entry["scenario_name"],
            "scenario_description": entry["scenario_description"],
            "contingency_percentage": entry["contingency_percentage"],
            "target_margin_percentage": entry["target_margin_percentage"],
            "needs_recalculation": True,
            "stale_reason": None,
        }
    )


def calculate_scenario_financials(
    baseline_delivery_cost: object,
    contingency_percentage: object,
    target_margin_percentage: object,
    max_contingency_percentage: float,
) -> dict:
    """Computes contingency through equivalent markup at full precision --
    display-only rounding to two decimals happens in the UI, never here
    (EAP.M4-D1: "use full precision internally").

    Never raises: invalid input becomes a blocking condition in the
    returned dict rather than an exception, so a scenario with bad input
    still renders (as Approval Blocked) instead of crashing the page.
    """
    blocking: list[str] = []
    empty_result = {
        "contingency_amount": None,
        "risk_adjusted_delivery_cost": None,
        "customer_price": None,
        "gross_profit": None,
        "achieved_margin": None,
        "equivalent_markup": None,
    }

    try:
        cost = validate_baseline_delivery_cost(baseline_delivery_cost)
    except ValueError as exc:
        blocking.append(f"Baseline delivery cost: {exc}")
        return {**empty_result, "blocking_conditions": blocking}

    try:
        contingency = validate_contingency_percentage(contingency_percentage, max_contingency_percentage)
    except ValueError as exc:
        blocking.append(f"Contingency percentage: {exc}")
        contingency = None

    try:
        margin = validate_target_margin_percentage(target_margin_percentage)
    except ValueError as exc:
        blocking.append(f"Target margin percentage: {exc}")
        margin = None

    if contingency is None or margin is None:
        return {**empty_result, "blocking_conditions": blocking}

    contingency_amount = cost * contingency
    risk_adjusted_delivery_cost = cost + contingency_amount
    customer_price = risk_adjusted_delivery_cost / (1 - margin)
    gross_profit = customer_price - risk_adjusted_delivery_cost
    achieved_margin = (gross_profit / customer_price) if customer_price else None
    equivalent_markup = (
        (customer_price - risk_adjusted_delivery_cost) / risk_adjusted_delivery_cost
        if risk_adjusted_delivery_cost
        else None
    )

    if detect_commercial_loss(customer_price, risk_adjusted_delivery_cost):
        blocking.append(COMMERCIAL_LOSS_WARNING)

    return {
        "contingency_amount": contingency_amount,
        "risk_adjusted_delivery_cost": risk_adjusted_delivery_cost,
        "customer_price": customer_price,
        "gross_profit": gross_profit,
        "achieved_margin": achieved_margin,
        "equivalent_markup": equivalent_markup,
        "blocking_conditions": blocking,
    }


def derive_delivery_risk_warnings(resource_plan_warnings: list[str]) -> list[str]:
    """Maps M2's resource-plan warnings to the two governed EAP.M4 delivery-
    risk warning levels for display in the Commercial Pricing section.
    "High delivery risk" fires when any underlying M2 warning indicates a
    required phase has literally missing coverage (a simple keyword check,
    the same lightweight-safeguard pattern already used in
    sow_outline_engine.py's risky-language scan -- not a numeric threshold
    invented for this milestone).
    """
    if not resource_plan_warnings:
        return []
    warnings = [DELIVERY_RISK_WARNING]
    if any("missing" in warning.lower() for warning in resource_plan_warnings):
        warnings.append(HIGH_DELIVERY_RISK_WARNING)
    return warnings


def compute_commercial_readiness(
    financials: dict,
    baseline_cost_result: Optional[BaselineCostResult],
    scenario_id: str,
    contingency_percentage: float,
    target_margin_percentage: float,
    recommended_contingency_percentage: float,
    recommended_target_margin_percentage: float,
    material_threshold_contingency: float,
    material_threshold_margin: float,
    rates_overridden: bool,
    delivery_warnings_present: bool,
    ai_enabled: bool,
    staffing_model: str,
    unresolved_items_present: bool,
) -> tuple[CommercialReadinessStatus, list[str]]:
    """Readiness precedence: Approval Blocked > Human Review Required >
    Ready for Commercial Review (EAP.M4-D1 item 5). Readiness and approval
    status are independent axes -- this function never looks at whether the
    scenario is currently approved.
    """
    blocking_conditions = list(financials.get("blocking_conditions", []))

    if baseline_cost_result is None or baseline_cost_result.readiness_status == "Calculation Blocked":
        blocking_conditions.append("The M3 baseline delivery cost calculation is blocked.")

    if blocking_conditions:
        return "Approval Blocked", blocking_conditions

    review_reasons: list[str] = []

    if baseline_cost_result.baseline_delivery_cost == 0:
        review_reasons.append(
            "Baseline delivery cost is zero -- requires human review before this can be "
            "treated as commercially ready."
        )
    if rates_overridden:
        review_reasons.append("One or more role rates differ from the configured defaults.")
    if scenario_id != "recommended":
        if abs(contingency_percentage - recommended_contingency_percentage) >= material_threshold_contingency:
            review_reasons.append("Contingency differs materially from the Recommended scenario.")
        if abs(target_margin_percentage - recommended_target_margin_percentage) >= material_threshold_margin:
            review_reasons.append("Target margin differs materially from the Recommended scenario.")
    if delivery_warnings_present:
        review_reasons.append("Delivery-risk warnings remain from the resource plan -- see the Resource Plan section.")
    if ai_enabled:
        review_reasons.append("The AI workstream is included in this estimate.")
    if staffing_model == "Customer-defined":
        review_reasons.append("Customer-defined staffing is in use.")
    if unresolved_items_present:
        review_reasons.append("Material assumptions or unknown scope items remain unresolved.")
    if scenario_id == "competitive":
        review_reasons.append("The Competitive scenario always requires human review before approval.")
    if contingency_percentage == 0:
        review_reasons.append("This scenario has zero contingency -- confirm this is intentional.")
    if target_margin_percentage == 0:
        review_reasons.append("This scenario has zero target margin -- confirm this is intentional.")

    if review_reasons:
        return "Human Review Required", review_reasons
    return "Ready for Commercial Review", []


def compute_approval_status(
    readiness_status: CommercialReadinessStatus, is_currently_approved: bool
) -> ScenarioApprovalStatus:
    """Readiness (calculation cleanliness) and approval (human decision
    state) are independent axes: a scenario may be "Ready for Commercial
    Review" and still "Draft" (EAP.M4-D1 item 5).
    """
    if readiness_status == "Approval Blocked":
        return "Approval Blocked"
    if is_currently_approved:
        return "Approved"
    if readiness_status == "Human Review Required":
        return "Review Required"
    return "Draft"


def recalculate_scenario(
    scenario: PricingScenario,
    baseline_cost_result: Optional[BaselineCostResult],
    defaults: dict,
    rates_overridden: bool,
    delivery_warnings_present: bool,
    ai_enabled: bool,
    staffing_model: str,
    unresolved_items_present: bool,
    recommended_contingency_percentage: float,
    recommended_target_margin_percentage: float,
    is_currently_approved: bool,
) -> PricingScenario:
    """Recomputes one scenario's financials, readiness, and approval status
    against the CURRENT baseline, snapshotting that baseline onto the
    scenario. Does not alter another scenario's values (EAP.M4-D1 item 6 /
    PRICING-RULES.md section 14).
    """
    max_contingency = defaults["max_contingency_percentage"]
    baseline_cost = baseline_cost_result.baseline_delivery_cost if baseline_cost_result is not None else None
    baseline_status = baseline_cost_result.readiness_status if baseline_cost_result is not None else None

    financials = calculate_scenario_financials(
        baseline_cost, scenario.contingency_percentage, scenario.target_margin_percentage, max_contingency
    )
    readiness_status, reasons = compute_commercial_readiness(
        financials=financials,
        baseline_cost_result=baseline_cost_result,
        scenario_id=scenario.scenario_id,
        contingency_percentage=scenario.contingency_percentage,
        target_margin_percentage=scenario.target_margin_percentage,
        recommended_contingency_percentage=recommended_contingency_percentage,
        recommended_target_margin_percentage=recommended_target_margin_percentage,
        material_threshold_contingency=defaults["material_difference_threshold_contingency"],
        material_threshold_margin=defaults["material_difference_threshold_margin"],
        rates_overridden=rates_overridden,
        delivery_warnings_present=delivery_warnings_present,
        ai_enabled=ai_enabled,
        staffing_model=staffing_model,
        unresolved_items_present=unresolved_items_present,
    )
    approval_status = compute_approval_status(readiness_status, is_currently_approved)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return scenario.model_copy(
        update={
            "baseline_delivery_cost_used": baseline_cost,
            "baseline_readiness_status_used": baseline_status,
            "contingency_amount": financials["contingency_amount"],
            "risk_adjusted_delivery_cost": financials["risk_adjusted_delivery_cost"],
            "customer_price": financials["customer_price"],
            "gross_profit": financials["gross_profit"],
            "achieved_margin": financials["achieved_margin"],
            "equivalent_markup": financials["equivalent_markup"],
            "readiness_status": readiness_status,
            "approval_status": approval_status,
            "blocking_conditions": reasons if readiness_status == "Approval Blocked" else [],
            "validation_warnings": reasons if readiness_status == "Human Review Required" else [],
            "needs_recalculation": False,
            "stale_reason": None,
            "recalculated_at": now,
            "created_at": scenario.created_at or now,
        }
    )


def detect_baseline_drift(scenario: PricingScenario, baseline_cost_result: Optional[BaselineCostResult]) -> Optional[str]:
    """Compares a scenario's baseline snapshot to the live BaselineCostResult.
    Returns None when they match; otherwise a human-readable reason. Covers
    role-rate, hours, resource-plan, and AI-toggle changes generically --
    all of them change `baseline_delivery_cost` or `readiness_status` on the
    live BaselineCostResult, which is what this function actually compares.
    """
    current_cost = baseline_cost_result.baseline_delivery_cost if baseline_cost_result is not None else None
    current_status = baseline_cost_result.readiness_status if baseline_cost_result is not None else None
    if current_cost == scenario.baseline_delivery_cost_used and current_status == scenario.baseline_readiness_status_used:
        return None
    return (
        "The baseline delivery cost has changed since this scenario was last calculated "
        f"(was {scenario.baseline_delivery_cost_used}, now {current_cost}). Recalculate this "
        "scenario before it can be approved."
    )


def refresh_scenario_staleness(
    scenarios: dict[str, PricingScenario],
    baseline_cost_result: Optional[BaselineCostResult],
    approved_scenario_id: Optional[str],
) -> tuple[dict[str, PricingScenario], Optional[str]]:
    """Marks any scenario whose baseline has drifted as needing
    recalculation and immediately removes its approval if it was the
    approved scenario -- without recomputing its stored dollar fields
    (EAP.M4-D1 item 8: "do not leave a stale approved price," but
    recalculation itself still requires an explicit user action). Valid
    scenario inputs (contingency/margin/name/description/notes) are always
    preserved.
    """
    updated: dict[str, PricingScenario] = {}
    new_approved_id = approved_scenario_id
    for scenario_id, scenario in scenarios.items():
        if scenario.needs_recalculation:
            updated[scenario_id] = scenario
            continue
        drift_reason = detect_baseline_drift(scenario, baseline_cost_result)
        if drift_reason is None:
            updated[scenario_id] = scenario
            continue
        updated[scenario_id] = scenario.model_copy(
            update={
                "needs_recalculation": True,
                "stale_reason": drift_reason,
                "approval_status": "Approval Blocked" if scenario.blocking_conditions else "Draft",
            }
        )
        if approved_scenario_id == scenario_id:
            new_approved_id = None
    return updated, new_approved_id


def approve_scenario(
    scenario: PricingScenario,
    delivery_warnings_present: bool,
    commercial_warnings_present: bool,
) -> tuple[bool, list[str]]:
    """Gate checked only at the moment of an approval attempt -- never at
    plain calculation or comparison time (EAP.M4-D1 items 3-4). A missing
    approval note or unacknowledged warning blocks approval but never
    invalidates the scenario's own calculated numbers.
    """
    reasons: list[str] = []

    if scenario.needs_recalculation:
        reasons.append("This scenario must be recalculated against the current baseline before it can be approved.")
    if scenario.blocking_conditions:
        reasons.append(
            "This scenario has a blocking condition and cannot be approved: "
            + "; ".join(scenario.blocking_conditions)
        )
    if not (scenario.approval_reason or "").strip():
        reasons.append("An approval note is required before this scenario can be approved.")
    if delivery_warnings_present and not scenario.delivery_warnings_acknowledged:
        reasons.append("Delivery-risk warnings must be acknowledged before this scenario can be approved.")
    if commercial_warnings_present and not scenario.commercial_warnings_acknowledged:
        reasons.append("Commercial-risk warnings must be acknowledged before this scenario can be approved.")

    return (not reasons, reasons)
