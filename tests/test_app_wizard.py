"""Streamlit AppTest-driven usability and transparency tests (EAP.M1.UI1).

See the note in this module's previous version (still true here): Streamlit
1.60.0's AppTest cannot reliably drive more than ~2 script reruns past an
abandoned st.radio/st.selectbox/st.segmented_control widget -- a framework
limitation reproduced with a five-line vanilla Streamlit script, unrelated
to this application's code. Deep-flow tests pre-seed session_state and
render straight to the target step rather than clicking through every
earlier selection widget. Tests confined to steps 1-2 (at most one such
widget touched) use natural click-driven navigation.

st.data_editor (used by the future pricing preview) has no AppTest
interaction wrapper in this Streamlit version, so that section is verified
by confirming it renders without exception and its static/initial content
displays -- not by driving cell edits through AppTest. Manual browser
verification covers the live edit/recalculation behavior.
"""
from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from src.scope_defaults import compute_scope_confirmation_percentage, default_selections_for_work_type

COMPLETE_COMPLEXITY_ANSWERS = {
    "functional": {"label": "High", "score": 4},
    "technical": {"label": "Moderate", "score": 3},
    "integration": {"label": "Low", "score": 2},
    "data": {"label": "Very High", "score": 5},
    "testing": {"label": "Very Low", "score": 1},
    "dependency": {"label": "None or Not Applicable", "score": 0},
    "operational_risk": {"label": "Moderate", "score": 3},
}


def _seed_complete_state(at: AppTest, step: int) -> None:
    at.session_state["wizard_step"] = step
    at.session_state["work_type"] = "enhancement"
    at.session_state["estimate_name"] = "Test Estimate"
    at.session_state["business_objective"] = "Reduce processing time by half"
    at.session_state["system_context"] = "Existing system"
    at.session_state["audience"] = "Internal users"
    at.session_state["contract_term"] = "Six months"
    at.session_state["ai_included"] = "No"
    at.session_state["scope_checklist"] = default_selections_for_work_type("enhancement")
    at.session_state["systems_involved_selected"] = ["Web application"]
    at.session_state["complexity_answers"] = dict(COMPLETE_COMPLEXITY_ANSWERS)


def _generate_results(at: AppTest) -> dict:
    at.run()
    at.button(key="generate_estimate").click()
    at.run()
    return at.session_state["results"]


# --- Item 1: only three work types -----------------------------------------


def test_only_three_work_types_appear():
    at = AppTest.from_file("app.py")
    at.run()
    work_type_radio = at.radio(key="w_work_type")
    assert work_type_radio.options == ["New Project", "Enhancement", "Production Support"]


# --- Item 2: five-step flow --------------------------------------------------


def test_five_step_flow_is_used():
    at = AppTest.from_file("app.py")
    at.run()
    assert any("Step 1 of 5" in caption.value for caption in at.caption)


# --- Item 3: persistent sidebar on Steps 2-5, not required on Step 1 --------


def test_sidebar_absent_on_step_1_present_on_step_2():
    at = AppTest.from_file("app.py")
    at.run()
    assert len(at.sidebar.markdown) == 0

    at.session_state["wizard_step"] = 2
    at.session_state["work_type"] = "new_project"
    at.run()
    sidebar_text = "\n".join(m.value for m in at.sidebar.markdown)
    assert "Current estimate" in sidebar_text
    assert "Running estimate" in sidebar_text


def test_sidebar_present_on_steps_3_4_5():
    for step in (3, 4, 5):
        at = AppTest.from_file("app.py")
        at.session_state["wizard_step"] = step
        at.session_state["work_type"] = "new_project"
        at.run()
        assert len(at.sidebar.markdown) > 0, f"sidebar missing on step {step}"


# --- Item 6/19: Back/Continue preserve values (text fields, steps 1-2) -----


def test_back_and_continue_preserve_values():
    # Deliberately never renders Step 3 (segmented_control shares the same
    # AppTest multi-rerun limitation documented above) -- confined to
    # Steps 1-2, which is sufficient to prove the persistence mechanism.
    at = AppTest.from_file("app.py")
    at.run()
    at.radio(key="w_work_type").set_value("New Project")
    at.button(key="continue_1").click()
    at.run()
    assert at.session_state["wizard_step"] == 2

    at.text_area(key="w_business_objective").set_value("Persisted objective")
    at.run()
    at.button(key="back_2").click()
    at.run()
    assert at.session_state["wizard_step"] == 1
    assert at.session_state["business_objective"] == "Persisted objective"


# --- Item 9/10: scope defaults pre-populated by work type, and editable ----


def test_scope_defaults_prepopulated_by_work_type():
    at = AppTest.from_file("app.py")
    at.session_state["wizard_step"] = 3
    at.session_state["work_type"] = "production_support"
    at.session_state["scope_checklist"] = {}
    at.run()
    # Production Support gets its own additional category.
    assert "investigation_diagnosis" in at.session_state["scope_checklist"]
    assert at.session_state["scope_checklist"]["investigation_diagnosis"] == "included"


def test_scope_item_is_editable():
    at = AppTest.from_file("app.py")
    at.session_state["wizard_step"] = 3
    at.session_state["work_type"] = "new_project"
    at.session_state["scope_checklist"] = default_selections_for_work_type("new_project")
    at.run()
    at.segmented_control(key="w_scope_configuration_only").set_value("Included")
    at.run()
    assert at.session_state["scope_checklist"]["configuration_only"] == "included"


# --- Item 12/13: AI intake simplicity and clean toggle-off -----------------


def test_ai_questions_are_exactly_three_when_enabled():
    at = AppTest.from_file("app.py")
    at.session_state["wizard_step"] = 4
    at.session_state["work_type"] = "new_project"
    at.session_state["ai_included"] = "Yes"
    at.run()
    primary_ai_widgets = [
        w for w in list(at.multiselect) + list(at.selectbox)
        if w.label
        in (
            "What should AI help with? (required)",
            "What data will AI use? (required)",
            "Will a person review AI output? (required)",
        )
    ]
    assert len(primary_ai_widgets) == 3


def test_ai_fields_disappear_and_clear_when_set_to_no():
    at = AppTest.from_file("app.py")
    at.session_state["wizard_step"] = 4
    at.session_state["work_type"] = "new_project"
    at.session_state["ai_included"] = "Yes"
    at.session_state["ai_help"] = ["Generate content"]
    at.session_state["ai_data"] = "Public information"
    at.session_state["ai_human_review"] = "Always"
    at.run()
    assert at.session_state["ai_help"] == ["Generate content"]

    at.session_state["wizard_step"] = 2
    at.run()
    at.radio(key="w_ai_included").set_value("No")
    at.run()
    assert at.session_state["ai_included"] == "No"
    assert at.session_state["ai_help"] == []
    assert at.session_state["ai_data"] is None
    assert at.session_state["ai_human_review"] is None


# --- Item 14/24/25/26/27/28: sidebar + review content ----------------------


def test_review_step_shows_all_selected_values():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.run()
    body = "\n".join(m.value for m in at.markdown)
    assert "Test Estimate" in body
    assert "Reduce processing time by half" in body
    assert "Six months" in body


def test_sidebar_step_status_and_current_estimate_update():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=3)
    at.run()
    sidebar_text = "\n".join(m.value for m in at.sidebar.markdown)
    assert "Step 1: Work type" in sidebar_text
    assert "Step 2: Quick facts" in sidebar_text
    assert "current" in sidebar_text.lower()
    assert "Enhancement" in sidebar_text
    assert "Six months" in sidebar_text


def test_sidebar_scope_confirmation_percentage_correct():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=3)
    at.run()
    expected = compute_scope_confirmation_percentage(at.session_state["scope_checklist"])
    sidebar_text = "\n".join(m.value for m in at.sidebar.markdown)
    assert f"{expected:.0f}%" in sidebar_text


def test_sidebar_running_estimate_updates_and_labels_preliminary():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.run()
    sidebar_warnings = "\n".join(w.value for w in at.sidebar.warning)
    assert "Preliminary" in sidebar_warnings
    assert "7 of 7" not in sidebar_warnings or "all 7" in sidebar_warnings.lower() or "Preliminary" in sidebar_warnings

    results = _generate_results(at)
    sidebar_text = "\n".join(m.value for m in at.sidebar.markdown)
    assert "Governed estimate" in sidebar_text
    assert results["sizing_result"].tshirt_size in sidebar_text


# --- Item 29: warning status ------------------------------------------------


def test_sidebar_shows_delivery_risk_for_unknown_scope_items():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=3)
    at.session_state["scope_checklist"]["documentation"] = "unknown"
    at.run()
    sidebar_warnings = "\n".join(w.value for w in at.sidebar.warning)
    assert "Delivery risk" in sidebar_warnings


def test_no_delivery_warning_when_scope_fully_resolved():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=3)
    at.session_state["scope_checklist"] = {
        key: ("unknown" if False else "included") for key in at.session_state["scope_checklist"]
    }
    at.run()
    sidebar_warnings = "\n".join(w.value for w in at.sidebar.warning)
    assert "Delivery risk" not in sidebar_warnings


# --- Transparency (unchanged engine, same reconciliation checks as MVP.M1) --


def test_transparency_reconciles_with_governed_result():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    results = _generate_results(at)
    complexity = results["complexity_result"]
    sizing = results["sizing_result"]
    body = "\n".join(m.value for m in at.markdown)
    assert f"Relative Job Size {sizing.relative_job_size}, T-shirt size {sizing.tshirt_size}" in body
    assert f"stored at full precision: {complexity.weighted_complexity_score}" in body


# --- Assumptions (item 44-50, generation already unit-tested; UI wiring here) --


def test_assumptions_generated_and_editable_at_review():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.run()
    assert at.session_state["assumptions"]
    assert any("Assumption" in ti.label for ti in at.text_input if ti.label)


# --- Future pricing preview: renders without error, illustrative only ------


def test_future_pricing_preview_renders_without_error_and_is_illustrative():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.run()
    assert list(at.exception) == []
    expander_labels = [e.label for e in at.expander]
    assert any("Future pricing interaction preview" in label for label in expander_labels)
    caption_text = "\n".join(c.value for c in at.caption)
    assert "illustrative" in caption_text.lower()
    assert len(at.dataframe) > 0


# --- EAP.M1.UI2: action navigation and preliminary SOW outline --------------


def test_action_navigation_shows_five_differentiated_actions():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    labels = [b.label for b in at.button]
    assert "Generate Preliminary SOW Outline" in labels
    assert "Generate Final SOW" in labels
    assert "Export to Excel" in labels
    assert "Export to PowerPoint" in labels
    assert "Build Resource Plan" in labels
    assert "Generate SOW" not in labels  # never a bare, active "Generate SOW"


def test_locked_actions_are_disabled_with_correct_labels():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    assert at.button(key="final_sow_locked").disabled is True
    assert at.button(key="final_sow_locked").help == "Requires approved resource plan and pricing"
    assert at.button(key="export_excel_locked").disabled is True
    assert at.button(key="export_excel_locked").help == "Coming in a later milestone"
    assert at.button(key="export_ppt_locked").disabled is True
    # Build Resource Plan is intentionally NOT locked in EAP.M2 -- it's the
    # active action this milestone introduces.
    assert at.button(key="build_resource_plan").disabled is False


def test_generate_preliminary_sow_outline_produces_outline():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    gate = at.session_state["sow_outline_gate"]
    assert gate.status == "Human Review Required"
    sections = at.session_state["sow_outline_sections"]
    assert len(sections) >= 20
    body = "\n".join(m.value for m in at.markdown)
    assert "Preliminary Draft" in body


def test_outline_shows_mandatory_disclaimer_and_no_pricing_leakage():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    body = "\n".join(m.value for m in at.markdown)
    assert (
        "Draft for business and legal review. This language is not binding until approved "
        "and incorporated into an executed agreement." in body
    )
    for forbidden in ("Configured default rate", "Scenario rate", "blended rate", "$"):
        assert forbidden not in body.split("Future pricing interaction preview")[0]


def test_outline_shows_edit_and_regenerate_actions_and_download():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    button_labels = [b.label for b in at.button]
    assert "Edit inputs" in button_labels
    assert "Regenerate outline" in button_labels
    assert len(at.download_button) > 0


def test_outline_reflects_unknown_items_as_items_requiring_confirmation():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.session_state["scope_checklist"]["documentation"] = "unknown"
    _generate_results(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    body = "\n".join(m.value for m in at.markdown)
    assert "Documentation" in body
    gate = at.session_state["sow_outline_gate"]
    assert any("Unknown" in warning for warning in gate.warnings)


def test_state_preserved_and_sidebar_intact_after_generating_outline():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    assert at.session_state["estimate_name"] == "Test Estimate"
    assert at.session_state["business_objective"] == "Reduce processing time by half"
    sidebar_text = "\n".join(m.value for m in at.sidebar.markdown)
    assert "Governed estimate" in sidebar_text


# --- EAP.M2: phase and resource planning ------------------------------------


def _build_resource_plan(at: AppTest):
    at.button(key="build_resource_plan").click()
    at.run()
    return at.session_state["resource_plan_result"]


def test_build_resource_plan_active_only_after_governed_estimate():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.run()
    # Before "Confirm and generate estimate," no action row (and therefore no
    # Build Resource Plan button) is rendered at all -- results is None.
    assert at.session_state["results"] is None
    assert "build_resource_plan" not in [b.key for b in at.button]


def test_build_resource_plan_produces_rows_with_no_ai_when_off():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    plan = _build_resource_plan(at)
    assert plan is not None
    assert plan.rows
    assert not any(r.is_ai_workstream for r in plan.rows)
    assert plan.total_hours_ai_workstream == 0.0


def test_build_resource_plan_includes_ai_rows_when_enabled():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    at.session_state["ai_included"] = "Yes"
    at.session_state["ai_help"] = ["Generate content"]
    at.session_state["ai_data"] = "Internal business information"
    at.session_state["ai_human_review"] = "Always"
    _generate_results(at)
    plan = _build_resource_plan(at)
    assert any(r.is_ai_workstream for r in plan.rows)
    assert plan.total_hours_ai_workstream > 0


def test_staffing_model_switch_preserves_total_required_hours():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    balanced_plan = _build_resource_plan(at)
    balanced_total = sum(r.estimated_hours for r in balanced_plan.rows)

    at.radio(key="w_staffing_model").set_value("Specialized")
    at.run()
    specialized_plan = at.session_state["resource_plan_result"]
    specialized_total = sum(r.estimated_hours for r in specialized_plan.rows)

    assert specialized_total == pytest.approx(balanced_total)
    assert all(r.assigned_to == r.role for r in specialized_plan.rows)


def test_customer_defined_shows_assignment_inputs():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    _build_resource_plan(at)
    at.radio(key="w_staffing_model").set_value("Customer-defined")
    at.run()
    assignment_labels = [t.label for t in at.text_input if t.label and "Assigned person" in t.label]
    assert assignment_labels


def test_resource_plan_totals_render_in_plain_language():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    _build_resource_plan(at)
    body = "\n".join(m.value for m in at.markdown)
    assert "Core IT workstream" in body
    assert "By role" in body
    assert "By phase" in body


def test_resource_plan_transparency_expander_present():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    _build_resource_plan(at)
    expander_labels = [e.label for e in at.expander]
    assert any("How was resource effort calculated?" in label for label in expander_labels)


def test_resource_plan_feeds_into_sow_outline_as_preliminary():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    _build_resource_plan(at)
    at.button(key="generate_sow_outline").click()
    at.run()
    sections = at.session_state["sow_outline_sections"]
    section_map = dict(sections)
    assert "Preliminary phase and resource plan" in section_map
    resource_section = section_map["Preliminary phase and resource plan"]
    assert "preliminary planning information only" in resource_section
    for forbidden in ("$", "hourly rate", "blended rate", "role cost", "margin", "contingency"):
        assert forbidden not in resource_section.lower()


def test_no_pricing_or_rate_functionality_introduced_in_resource_plan_ui():
    at = AppTest.from_file("app.py")
    _seed_complete_state(at, step=5)
    _generate_results(at)
    _build_resource_plan(at)
    body = "\n".join(m.value for m in at.markdown).lower()
    resource_plan_body = body.split("## resource plan", 1)[-1].split("future pricing interaction preview", 1)[0]
    for forbidden in ("hourly rate", "blended rate", "role cost", "margin", "contingency", "customer price"):
        assert forbidden not in resource_plan_body
