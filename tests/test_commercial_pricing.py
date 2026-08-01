import pytest

from src.models import BaselineCostResult
from src.pricing_engine import (
    COMMERCIAL_LOSS_WARNING,
    approve_scenario,
    build_default_scenarios,
    calculate_scenario_financials,
    compute_approval_status,
    compute_commercial_readiness,
    derive_delivery_risk_warnings,
    detect_baseline_drift,
    load_commercial_pricing_defaults,
    recalculate_scenario,
    refresh_scenario_staleness,
    reset_scenario_to_default,
)
from src.validators import (
    detect_commercial_loss,
    validate_baseline_delivery_cost,
    validate_contingency_percentage,
    validate_target_margin_percentage,
)

DEFAULTS = load_commercial_pricing_defaults()
MAX_CONTINGENCY = DEFAULTS["max_contingency_percentage"]


def _baseline(cost=80000.0, status="Ready for Baseline Review", commercial_warnings=None):
    return BaselineCostResult(
        rows=[],
        total_estimated_hours=100.0,
        baseline_delivery_cost=cost,
        readiness_status=status,
        commercial_warnings=commercial_warnings or [],
    )


def _recalc(scenario, baseline, **overrides):
    kwargs = dict(
        baseline_cost_result=baseline,
        defaults=DEFAULTS,
        rates_overridden=False,
        delivery_warnings_present=False,
        ai_enabled=False,
        staffing_model="Balanced",
        unresolved_items_present=False,
        recommended_contingency_percentage=DEFAULTS["scenarios"]["recommended"]["contingency_percentage"],
        recommended_target_margin_percentage=DEFAULTS["scenarios"]["recommended"]["target_margin_percentage"],
        is_currently_approved=False,
    )
    kwargs.update(overrides)
    return recalculate_scenario(scenario, **kwargs)


# --- 1-6: formulas at known inputs -------------------------------------------


def test_contingency_amount_at_known_inputs():
    fin = calculate_scenario_financials(80000, 0.10, 0.30, MAX_CONTINGENCY)
    assert fin["contingency_amount"] == pytest.approx(8000.0)


def test_risk_adjusted_cost():
    fin = calculate_scenario_financials(80000, 0.10, 0.30, MAX_CONTINGENCY)
    assert fin["risk_adjusted_delivery_cost"] == pytest.approx(88000.0)


def test_customer_price_formula():
    fin = calculate_scenario_financials(80000, 0.0, 0.30, MAX_CONTINGENCY)
    # Matches PRICING-RULES.md section 3's worked example exactly.
    assert fin["customer_price"] == pytest.approx(114285.7142857, rel=1e-6)


def test_gross_profit_formula():
    fin = calculate_scenario_financials(80000, 0.0, 0.30, MAX_CONTINGENCY)
    assert fin["gross_profit"] == pytest.approx(34285.7142857, rel=1e-6)


def test_achieved_margin_formula():
    fin = calculate_scenario_financials(80000, 0.0, 0.30, MAX_CONTINGENCY)
    assert fin["achieved_margin"] == pytest.approx(0.30, rel=1e-6)


def test_equivalent_markup_formula():
    fin = calculate_scenario_financials(80000, 0.0, 0.30, MAX_CONTINGENCY)
    # PRICING-RULES.md section 3: markup (42.86%) differs from margin (30%)
    # at the same dollar profit -- never interchangeable.
    assert fin["equivalent_markup"] == pytest.approx(0.428571, rel=1e-5)
    assert fin["equivalent_markup"] != pytest.approx(fin["achieved_margin"])


# --- 7-8: full precision internally, two-decimal display only ----------------


def test_full_precision_retained_internally_not_rounded():
    fin = calculate_scenario_financials(80000, 0.10, 0.30, MAX_CONTINGENCY)
    # 88000 / 0.7 is not a round number -- confirms no internal rounding
    # to 2 decimals happened inside the engine (display-only concern).
    assert fin["customer_price"] != round(fin["customer_price"], 2)


# --- 9-11: contingency bounds --------------------------------------------------


def test_zero_contingency_is_valid_not_blocking():
    fin = calculate_scenario_financials(80000, 0.0, 0.30, MAX_CONTINGENCY)
    assert fin["blocking_conditions"] == []


def test_negative_contingency_blocks():
    with pytest.raises(ValueError):
        validate_contingency_percentage(-0.01, MAX_CONTINGENCY)
    fin = calculate_scenario_financials(80000, -0.01, 0.30, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


def test_excessive_contingency_blocks():
    with pytest.raises(ValueError):
        validate_contingency_percentage(MAX_CONTINGENCY + 0.01, MAX_CONTINGENCY)
    fin = calculate_scenario_financials(80000, MAX_CONTINGENCY + 0.01, 0.30, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


# --- 12-15: margin bounds ------------------------------------------------------


def test_zero_margin_is_valid_not_blocking():
    fin = calculate_scenario_financials(80000, 0.10, 0.0, MAX_CONTINGENCY)
    assert fin["blocking_conditions"] == []
    assert fin["customer_price"] == pytest.approx(fin["risk_adjusted_delivery_cost"])


def test_negative_margin_blocks():
    with pytest.raises(ValueError):
        validate_target_margin_percentage(-0.01)
    fin = calculate_scenario_financials(80000, 0.10, -0.01, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


def test_margin_at_100_percent_blocks():
    with pytest.raises(ValueError):
        validate_target_margin_percentage(1.0)
    fin = calculate_scenario_financials(80000, 0.10, 1.0, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


def test_margin_above_100_percent_blocks():
    with pytest.raises(ValueError):
        validate_target_margin_percentage(1.5)
    fin = calculate_scenario_financials(80000, 0.10, 1.5, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


# --- 16-18: baseline cost handling ---------------------------------------------


def test_missing_baseline_blocks():
    with pytest.raises(ValueError):
        validate_baseline_delivery_cost(None)
    fin = calculate_scenario_financials(None, 0.10, 0.30, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]
    assert fin["customer_price"] is None


def test_invalid_baseline_blocks():
    with pytest.raises(ValueError):
        validate_baseline_delivery_cost(-500)
    fin = calculate_scenario_financials(-500, 0.10, 0.30, MAX_CONTINGENCY)
    assert fin["blocking_conditions"]


def test_zero_baseline_requires_review_not_blocked_and_not_silently_ready():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline(cost=0.0)
    result = _recalc(scenarios["recommended"], baseline)
    assert result.readiness_status == "Human Review Required"
    assert any("zero" in reason.lower() for reason in result.validation_warnings)
    assert result.customer_price == 0.0
    assert result.achieved_margin is None  # never a fabricated 0/0 value


# --- 19-21: default scenarios ---------------------------------------------------


def test_recommended_scenario_defaults():
    scenarios = build_default_scenarios(DEFAULTS)
    rec = scenarios["recommended"]
    assert rec.contingency_percentage == DEFAULTS["scenarios"]["recommended"]["contingency_percentage"]
    assert rec.target_margin_percentage == DEFAULTS["scenarios"]["recommended"]["target_margin_percentage"]


def test_competitive_scenario_defaults_lower_and_always_human_review():
    scenarios = build_default_scenarios(DEFAULTS)
    comp = scenarios["competitive"]
    rec = scenarios["recommended"]
    assert comp.contingency_percentage <= rec.contingency_percentage
    assert comp.target_margin_percentage <= rec.target_margin_percentage

    baseline = _baseline()
    result = _recalc(comp, baseline)
    assert result.readiness_status == "Human Review Required"
    assert any("competitive" in reason.lower() for reason in result.validation_warnings)


def test_conservative_scenario_defaults_higher():
    scenarios = build_default_scenarios(DEFAULTS)
    cons = scenarios["conservative"]
    rec = scenarios["recommended"]
    assert cons.contingency_percentage >= rec.contingency_percentage
    assert cons.target_margin_percentage >= rec.target_margin_percentage


# --- 22-23: custom editing and reset --------------------------------------------


def test_custom_scenario_editing():
    scenarios = build_default_scenarios(DEFAULTS)
    custom = scenarios["custom"].model_copy(
        update={"contingency_percentage": 0.25, "target_margin_percentage": 0.40, "scenario_name": "Special Deal"}
    )
    assert custom.contingency_percentage == 0.25
    assert custom.scenario_name == "Special Deal"


def test_scenario_reset_restores_governed_defaults():
    scenarios = build_default_scenarios(DEFAULTS)
    edited = scenarios["custom"].model_copy(
        update={"contingency_percentage": 0.99 if 0.99 <= MAX_CONTINGENCY else 0.3, "scenario_name": "Edited"}
    )
    reset = reset_scenario_to_default(edited, DEFAULTS)
    assert reset.contingency_percentage == DEFAULTS["scenarios"]["custom"]["contingency_percentage"]
    assert reset.scenario_name == DEFAULTS["scenarios"]["custom"]["scenario_name"]
    assert reset.needs_recalculation is True


# --- 24-25: comparison isolation and difference from Recommended ---------------


def test_scenario_comparison_isolation_changing_one_does_not_affect_another():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    rec_before = _recalc(scenarios["recommended"], baseline)
    edited_competitive = scenarios["competitive"].model_copy(update={"contingency_percentage": 0.01})
    _recalc(edited_competitive, baseline)
    # Recommended's own fields are untouched by editing/recalculating Competitive.
    rec_after = _recalc(scenarios["recommended"], baseline)
    assert rec_before.customer_price == pytest.approx(rec_after.customer_price)


def test_difference_from_recommended_triggers_material_review():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    threshold = DEFAULTS["material_difference_threshold_contingency"]
    custom = scenarios["custom"].model_copy(
        update={
            "contingency_percentage": DEFAULTS["scenarios"]["recommended"]["contingency_percentage"] + threshold + 0.01
        }
    )
    result = _recalc(custom, baseline)
    assert any("materially" in reason.lower() for reason in result.validation_warnings)


# --- 26-27: approval note and acknowledgement requirements ---------------------


def test_approval_note_required_but_does_not_invalidate_calculation():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    result = _recalc(scenarios["recommended"], baseline)
    assert result.readiness_status == "Ready for Commercial Review"  # valid calc, no note yet
    can_approve, reasons = approve_scenario(result, delivery_warnings_present=False, commercial_warnings_present=False)
    assert not can_approve
    assert any("approval note" in r.lower() for r in reasons)


def test_warning_acknowledgement_required_only_at_approval():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    result = _recalc(scenarios["recommended"], baseline, delivery_warnings_present=True)
    # Calculation and comparison succeed without acknowledgement.
    assert result.customer_price is not None
    result = result.model_copy(update={"approval_reason": "Reviewed"})
    can_approve, reasons = approve_scenario(result, delivery_warnings_present=True, commercial_warnings_present=False)
    assert not can_approve
    assert any("delivery-risk" in r.lower() for r in reasons)
    acknowledged = result.model_copy(update={"delivery_warnings_acknowledged": True})
    can_approve2, reasons2 = approve_scenario(acknowledged, delivery_warnings_present=True, commercial_warnings_present=False)
    assert can_approve2
    assert reasons2 == []


# --- 28-29: exactly one approved scenario, changing approval -------------------


def test_exactly_one_scenario_approved_at_a_time():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    rec = _recalc(scenarios["recommended"], baseline, is_currently_approved=True)
    comp = _recalc(scenarios["competitive"], baseline, is_currently_approved=False)
    assert rec.approval_status == "Approved"
    assert comp.approval_status != "Approved"


def test_changing_approved_scenario_reverts_previous_without_deleting_it():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    rec_approved = _recalc(scenarios["recommended"], baseline, is_currently_approved=True)
    assert rec_approved.approval_status == "Approved"
    # Switching approval to a different scenario: the previous one is
    # recalculated with is_currently_approved=False -- its inputs and
    # calculations survive, only its approval status changes.
    rec_after_switch = _recalc(rec_approved, baseline, is_currently_approved=False)
    assert rec_after_switch.approval_status != "Approved"
    assert rec_after_switch.customer_price == pytest.approx(rec_approved.customer_price)
    assert rec_after_switch.contingency_percentage == rec_approved.contingency_percentage


# --- 30-32: approval invalidation after upstream changes -----------------------


def test_approval_invalidated_after_baseline_change():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline(cost=80000.0)
    rec = _recalc(scenarios["recommended"], baseline, is_currently_approved=True)
    all_scenarios = {**scenarios, "recommended": rec}

    new_baseline = _baseline(cost=95000.0)  # e.g. from a rate or hours edit
    updated, new_approved_id = refresh_scenario_staleness(all_scenarios, new_baseline, approved_scenario_id="recommended")
    assert new_approved_id is None
    assert updated["recommended"].needs_recalculation is True
    assert updated["recommended"].stale_reason is not None


def test_approval_invalidated_after_rate_change_via_baseline_drift():
    # A role-rate override changes baseline_delivery_cost -- the same
    # generic drift-detection path as any other baseline change.
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline(cost=80000.0)
    rec = _recalc(scenarios["recommended"], baseline, is_currently_approved=True)
    rate_changed_baseline = _baseline(cost=82500.0)
    drift = detect_baseline_drift(rec, rate_changed_baseline)
    assert drift is not None


def test_approval_invalidated_after_hours_change_via_baseline_drift():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline(cost=80000.0)
    rec = _recalc(scenarios["recommended"], baseline, is_currently_approved=True)
    hours_changed_baseline = _baseline(cost=76000.0)
    drift = detect_baseline_drift(rec, hours_changed_baseline)
    assert drift is not None


# --- 33-34: AI on/off ------------------------------------------------------------


def test_ai_on_triggers_human_review():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    result = _recalc(scenarios["recommended"], baseline, ai_enabled=True)
    assert result.readiness_status == "Human Review Required"
    assert any("ai workstream" in reason.lower() for reason in result.validation_warnings)


def test_ai_off_no_ai_related_review_trigger():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline()
    result = _recalc(scenarios["recommended"], baseline, ai_enabled=False)
    assert not any("ai workstream" in reason.lower() for reason in result.validation_warnings)


# --- 35-36: commercial loss ------------------------------------------------------


def test_commercial_loss_detected_standalone():
    assert detect_commercial_loss(100.0, 200.0) is True
    assert detect_commercial_loss(200.0, 100.0) is False
    assert detect_commercial_loss(None, 100.0) is False


def test_commercial_loss_blocks_approval_with_no_override_pathway():
    # Constructed directly against calculate_scenario_financials's internal
    # loss check (the fixed formula makes this unreachable through normal
    # contingency/margin ranges alone -- see calculate_scenario_financials's
    # docstring and detect_commercial_loss's docstring for why this is
    # still tested as a standalone defensive guard).
    fin = {
        "contingency_amount": 0.0,
        "risk_adjusted_delivery_cost": 100.0,
        "customer_price": 50.0,
        "gross_profit": -50.0,
        "achieved_margin": -1.0,
        "equivalent_markup": -0.5,
        "blocking_conditions": [COMMERCIAL_LOSS_WARNING] if detect_commercial_loss(50.0, 100.0) else [],
    }
    status, reasons = compute_commercial_readiness(
        financials=fin,
        baseline_cost_result=_baseline(),
        scenario_id="recommended",
        contingency_percentage=0.0,
        target_margin_percentage=0.0,
        recommended_contingency_percentage=0.0,
        recommended_target_margin_percentage=0.0,
        material_threshold_contingency=0.05,
        material_threshold_margin=0.05,
        rates_overridden=False,
        delivery_warnings_present=False,
        ai_enabled=False,
        staffing_model="Balanced",
        unresolved_items_present=False,
    )
    assert status == "Approval Blocked"
    assert COMMERCIAL_LOSS_WARNING in reasons
    scenario = build_default_scenarios(DEFAULTS)["recommended"].model_copy(
        update={
            "blocking_conditions": reasons,
            "approval_reason": "I approve anyway",
            "delivery_warnings_acknowledged": True,
            "commercial_warnings_acknowledged": True,
        }
    )
    can_approve, _ = approve_scenario(scenario, delivery_warnings_present=False, commercial_warnings_present=False)
    assert not can_approve  # no note or acknowledgement can override a commercial-loss block


# --- 37-38: delivery-risk and M3 rate-warning propagation ----------------------


def test_delivery_risk_warnings_propagate_without_altering_wording():
    resource_plan_warnings = ["Delivery risk: some scope items are marked Unknown."]
    warnings = derive_delivery_risk_warnings(resource_plan_warnings)
    assert warnings
    assert "Delivery risk:" in warnings[0]
    # Original M2 warning text is untouched by this mapping.
    assert resource_plan_warnings == ["Delivery risk: some scope items are marked Unknown."]


def test_high_delivery_risk_fires_on_missing_coverage_warnings():
    resource_plan_warnings = ["Missing independent AI evaluation coverage for the AI workstream."]
    warnings = derive_delivery_risk_warnings(resource_plan_warnings)
    assert any(w.startswith("High delivery risk:") for w in warnings)


def test_m3_rate_warning_propagation_triggers_human_review():
    scenarios = build_default_scenarios(DEFAULTS)
    baseline = _baseline(commercial_warnings=["Commercial risk: ..."])
    result = _recalc(scenarios["recommended"], baseline, rates_overridden=True)
    assert result.readiness_status == "Human Review Required"
    assert any("rate" in reason.lower() for reason in result.validation_warnings)


# --- Config governance -----------------------------------------------------------


def test_commercial_pricing_defaults_are_flagged_as_prototype():
    assert "_prototype_warning" in DEFAULTS
    assert "review" in DEFAULTS["_prototype_warning"].lower()


def test_no_discount_or_management_adjustment_fields_on_scenario_model():
    scenario = build_default_scenarios(DEFAULTS)["custom"]
    dumped = scenario.model_dump()
    for forbidden in ("discount", "rounding", "management_adjustment"):
        assert forbidden not in dumped
