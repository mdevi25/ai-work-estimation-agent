import json

import pytest

from src.config import DATA_DIR, load_json_config
from src.phase_planner import build_phase_plan
from src.pricing_engine import (
    build_baseline_cost,
    load_rate_card,
    reconcile_rate_state,
    reset_all_rates,
    reset_role_rate,
)
from src.resource_planner import build_resource_plan


def _plan(work_type="enhancement", total_sprints=4, ai_included="No", **kwargs):
    phases = build_phase_plan(work_type, total_sprints, ai_included, **kwargs)
    return build_resource_plan(work_type, phases, ai_included=ai_included, staffing_model="Balanced", **kwargs)


def _cost(plan, scenario_rates=None, override_reasons=None, ai_enabled=False, staffing_model="Balanced", unresolved=False):
    return build_baseline_cost(
        plan,
        scenario_rates=scenario_rates or {},
        override_reasons=override_reasons or {},
        ai_enabled=ai_enabled,
        staffing_model=staffing_model,
        unresolved_items_present=unresolved,
    )


# --- Rate card completeness (EAP.M3-D1 correction 2) ------------------------


def test_rate_card_covers_every_role_m2_can_generate():
    resource_rules = load_json_config("resource_rules.json")
    m2_roles = set()
    for phases in resource_rules["roles_by_work_type"].values():
        for roles in phases.values():
            for entry in roles:
                m2_roles.add(entry["role"])
    for mapping in resource_rules["ai_activity_to_phase_role"].values():
        m2_roles.add(mapping["role"])

    rate_card = load_rate_card()
    missing = m2_roles - set(rate_card.keys())
    assert not missing, f"rate_card.csv is missing distinct rates for: {missing}"


def test_rate_card_has_no_duplicate_generic_rate_reused_for_every_role():
    rate_card = load_rate_card()
    distinct_rates = {entry.default_hourly_rate for entry in rate_card.values()}
    assert len(distinct_rates) > 1  # not a single universal rate


# --- 1-3: role cost, baseline cost, blended rate ----------------------------


def test_role_cost_at_known_hours_and_rate():
    plan = _plan()
    result = _cost(plan)
    dev_row = next(r for r in result.rows if r.role == "Developer")
    assert dev_row.role_cost == pytest.approx(dev_row.total_estimated_hours * dev_row.configured_default_rate)


def test_baseline_cost_is_sum_of_role_costs():
    plan = _plan()
    result = _cost(plan)
    assert result.baseline_delivery_cost == pytest.approx(sum(r.role_cost for r in result.rows))


def test_blended_rate_formula():
    plan = _plan()
    result = _cost(plan)
    # blended_hourly_rate is rounded to 2 decimals for currency display;
    # compare against the same rounding rather than the raw division.
    expected = round(result.baseline_delivery_cost / result.total_estimated_hours, 2)
    assert result.blended_hourly_rate == pytest.approx(expected)


# --- 4: zero-hours handling --------------------------------------------------


def test_zero_total_hours_blended_rate_is_none_not_zero():
    plan = _plan()
    plan.total_hours_by_role = {}
    result = _cost(plan)
    assert result.blended_hourly_rate is None
    assert result.readiness_status == "Calculation Blocked"


# --- 5-6: role-specific and default scenario rates --------------------------


def test_role_specific_rates_are_not_uniform():
    plan = _plan(work_type="new_project", total_sprints=6)
    result = _cost(plan)
    rates = {r.configured_default_rate for r in result.rows}
    assert len(rates) > 1


def test_scenario_rate_defaults_to_configured_rate_when_not_overridden():
    plan = _plan()
    result = _cost(plan)
    for row in result.rows:
        assert row.scenario_rate == row.configured_default_rate


# --- 7-10: overrides and resets ----------------------------------------------


def test_single_role_override_with_reason_is_accepted():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": 130}, override_reasons={"Developer": "Negotiated rate"})
    dev_row = next(r for r in result.rows if r.role == "Developer")
    assert dev_row.scenario_rate == 130
    assert dev_row.override_reason == "Negotiated rate"


def test_override_without_reason_blocks():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": 130})
    assert result.readiness_status == "Calculation Blocked"
    assert any("override reason" in r.lower() for r in result.readiness_reasons)


def test_reset_one_role_restores_default_and_clears_reason():
    rates = {"Developer": 130}
    reasons = {"Developer": "Negotiated rate"}
    reset_role_rate("Developer", rates, reasons)
    assert "Developer" not in rates
    assert "Developer" not in reasons


def test_reset_all_restores_every_active_role():
    rates = {"Developer": 130, "QA": 80}
    reasons = {"Developer": "x", "QA": "y"}
    reset_all_rates(["Developer", "QA"], rates, reasons)
    assert rates == {}
    assert reasons == {}


# --- 11-13: below-default, above-default, zero-rate warnings ---------------


def test_below_default_rate_shows_commercial_warning():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": 100}, override_reasons={"Developer": "discount"})
    assert any("Commercial risk" in w for w in result.commercial_warnings)
    assert any("Gross profit and margin will be calculated in a later milestone" in w for w in result.commercial_warnings)
    assert result.readiness_status == "Human Review Required"


def test_above_default_rate_is_informational_not_blocking():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": 200}, override_reasons={"Developer": "premium"})
    assert not result.commercial_warnings
    assert result.readiness_status == "Human Review Required"  # override still requires review, not blocked


def test_zero_rate_with_reason_warns_but_does_not_block():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": 0}, override_reasons={"Developer": "pro bono"})
    assert result.readiness_status == "Human Review Required"
    assert any("zero rate" in r.lower() for r in result.readiness_reasons)


# --- 14-17: invalid/negative/missing/unknown rate blocking ------------------


def test_negative_rate_blocks():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": -5}, override_reasons={"Developer": "typo"})
    assert result.readiness_status == "Calculation Blocked"


def test_non_numeric_rate_blocks():
    plan = _plan()
    result = _cost(plan, scenario_rates={"Developer": "abc"}, override_reasons={"Developer": "bad input"})
    assert result.readiness_status == "Calculation Blocked"


def test_missing_rate_for_active_role_blocks():
    plan = _plan()
    plan.total_hours_by_role = dict(plan.total_hours_by_role)
    plan.total_hours_by_role["Nonexistent Role"] = 20.0
    result = _cost(plan)
    assert result.readiness_status == "Calculation Blocked"
    assert "Nonexistent Role" in result.missing_rate_roles


def test_unknown_role_never_gets_a_fabricated_rate():
    plan = _plan()
    plan.total_hours_by_role = dict(plan.total_hours_by_role)
    plan.total_hours_by_role["Totally Unknown Role"] = 10.0
    result = _cost(plan)
    unknown_row = next(r for r in result.rows if r.role == "Totally Unknown Role")
    assert unknown_row.role_cost is None
    assert unknown_row.has_missing_rate is True


# --- 18: multiple role overrides --------------------------------------------


def test_multiple_role_overrides_each_tracked_independently():
    plan = _plan(work_type="new_project", total_sprints=6)
    result = _cost(
        plan,
        scenario_rates={"Developer": 100, "Senior Developer": 200},
        override_reasons={"Developer": "discount", "Senior Developer": "premium"},
    )
    dev = next(r for r in result.rows if r.role == "Developer")
    senior = next(r for r in result.rows if r.role == "Senior Developer")
    assert dev.scenario_rate == 100
    assert senior.scenario_rate == 200
    assert dev.override_reason == "discount"
    assert senior.override_reason == "premium"


# --- 19-21: resource-plan change reconciliation ------------------------------


def test_reconcile_removes_stale_roles_not_in_current_plan():
    rates = {"Developer": 100, "Ghost Role": 999}
    reasons = {"Developer": "x", "Ghost Role": "y"}
    reconcile_rate_state({"Developer", "QA"}, rates, reasons)
    assert "Ghost Role" not in rates
    assert "Ghost Role" not in reasons
    assert rates["Developer"] == 100


def test_reconcile_leaves_newly_added_roles_to_default_naturally():
    rates: dict[str, float] = {}
    reasons: dict[str, str] = {}
    reconcile_rate_state({"Developer", "QA", "Brand New Role"}, rates, reasons)
    # No entry means "use configured default" -- nothing to add explicitly.
    assert "Brand New Role" not in rates


# --- 22-23: AI on/off ---------------------------------------------------------


def test_ai_on_rate_behavior_costs_ai_rows_separately():
    plan = _plan(ai_included="Yes", ai_help=["Generate content"])
    result = _cost(plan, ai_enabled=True)
    ai_rows = [r for r in result.rows if r.is_ai_workstream]
    assert ai_rows
    assert result.total_cost_ai_workstream > 0
    assert result.total_cost_ai_workstream == pytest.approx(sum(r.role_cost for r in ai_rows))


def test_ai_off_has_no_ai_cost_at_all():
    plan = _plan(ai_included="No")
    result = _cost(plan, ai_enabled=False)
    assert not any(r.is_ai_workstream for r in result.rows)
    assert result.total_cost_ai_workstream == 0.0


# --- 24: customer-defined staffing triggers review --------------------------


def test_customer_defined_staffing_triggers_human_review():
    plan = _plan()
    result = _cost(plan, staffing_model="Customer-defined")
    assert result.readiness_status == "Human Review Required"
    assert any("Customer-defined" in r for r in result.readiness_reasons)


# --- 25: delivery-risk propagation ------------------------------------------


def test_delivery_risk_warnings_from_resource_plan_trigger_review_without_altering_wording():
    plan = _plan()
    plan.warnings = ["Delivery risk: some scope items are marked Unknown."]
    result = _cost(plan)
    assert result.readiness_status == "Human Review Required"
    # The original warning text is untouched on the resource plan itself.
    assert plan.warnings == ["Delivery risk: some scope items are marked Unknown."]


# --- Readiness precedence (EAP.M3-D1 correction 4) --------------------------


def test_blocked_takes_precedence_over_human_review_conditions():
    plan = _plan()
    # AI enabled (a Human Review trigger) AND a negative rate (a Blocked trigger).
    result = _cost(
        plan,
        scenario_rates={"Developer": -10},
        override_reasons={"Developer": "bad"},
        ai_enabled=True,
    )
    assert result.readiness_status == "Calculation Blocked"


def test_ready_status_when_no_blocking_or_review_conditions():
    plan = _plan()
    plan.warnings = []
    result = _cost(plan, ai_enabled=False, staffing_model="Balanced", unresolved=False)
    assert result.readiness_status == "Ready for Baseline Review"
    assert result.readiness_reasons == []
