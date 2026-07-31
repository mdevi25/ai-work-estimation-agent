"""Streamlit UI: guided 5-step self-service estimation wizard (EAP.M1.UI1),
plus the preliminary SOW outline action (EAP.M1.UI2).

Collects inputs and displays outputs only -- no business formulas live in
this file. All authoritative calculation happens in
src/complexity_engine.py, src/sizing_engine.py, and src/contract_fit.py,
unchanged since MVP.M1. src/scope_defaults.py, src/assumption_engine.py,
src/running_estimate_preview.py, and src/sow_outline_engine.py are
non-authoritative UI-support helpers (scope defaults/counts, template-based
assumptions, a preliminary display-only complexity preview, and the
preliminary SOW outline generator, respectively).
"""
from datetime import datetime

import pandas as pd
import streamlit as st

from src.assumption_engine import generate_assumptions
from src.complexity_engine import calculate_weighted_complexity, load_complexity_questions
from src.config import ConfigurationError, load_json_config
from src.contract_fit import calculate_contract_fit, sprint_to_months
from src.models import COMPLEXITY_DIMENSION_KEYS, ComplexityDimensionAnswer, EstimateRequest, ResourcePlanRow
from src.phase_planner import build_phase_plan
from src.resource_planner import build_resource_plan, load_resource_rules
from src.running_estimate_preview import compute_preliminary_view
from src.scope_defaults import (
    categories_for_work_type,
    compute_scope_confirmation_percentage,
    compute_scope_counts,
    default_selections_for_work_type,
    systems_involved_options,
    unknown_item_keys,
)
from src.sizing_engine import map_to_size
from src.sow_outline_engine import (
    GATE_SUCCESS_MESSAGE,
    PRELIMINARY_STATEMENT,
    build_preliminary_sow_outline,
    evaluate_pre_generation_gate,
    render_outline_as_markdown,
    render_outline_as_text,
)
from src.validators import find_missing_required_fields

TOTAL_STEPS = 5

SYSTEM_CONTEXT_OPTIONS = ["New system", "Existing system", "Not yet known"]
AUDIENCE_OPTIONS = ["Internal users", "Customers or external users", "Both", "Not yet known"]
CONTRACT_TERM_OPTIONS = ["Quarterly", "Six months", "Nine months", "Annual", "Custom"]
AI_INCLUDED_OPTIONS = ["No", "Yes", "Not sure"]
SCOPE_STATUS_OPTIONS = ["Included", "Not included", "Unknown"]
STAFFING_MODEL_OPTIONS = ["Lean", "Balanced", "Specialized", "Customer-defined"]
SCOPE_STATUS_TO_KEY = {"Included": "included", "Not included": "not_included", "Unknown": "unknown"}
SCOPE_KEY_TO_STATUS = {v: k for k, v in SCOPE_STATUS_TO_KEY.items()}

DEFAULTS = {
    "wizard_step": 1,
    "work_type": None,
    "estimate_name": "",
    "business_objective": "",
    "system_context": None,
    "audience": None,
    "contract_term": None,
    "contract_custom_months": None,
    "requested_deadline": "",
    "customer_or_business_unit": "",
    "other_context": "",
    "known_dependencies": "",
    "description": "",
    "scope_checklist": {},
    "systems_involved_selected": [],
    "systems_involved_other_note": "",
    "complexity_answers": {},
    "ai_included": "No",
    "ai_help": [],
    "ai_data": None,
    "ai_human_review": None,
    "ai_capability_type": "",
    "ai_business_objective": "",
    "ai_workstream_activities": [],
    "ai_assumptions": "",
    "ai_exclusions": "",
    "assumptions": [],
    "new_assumption_text": "",
    "results": None,
    "sow_outline_gate": None,
    "sow_outline_sections": None,
    "sow_outline_generated_at": None,
    "staffing_model": "Balanced",
    "customer_defined_assignments": {},
    "resource_plan_result": None,
    "resource_plan_rows_editable": None,
}


def init_state() -> None:
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def go_to_step(step: int) -> None:
    st.session_state["wizard_step"] = step


def clear_ai_fields() -> None:
    st.session_state["ai_help"] = []
    st.session_state["ai_data"] = None
    st.session_state["ai_human_review"] = None
    st.session_state["ai_capability_type"] = ""
    st.session_state["ai_business_objective"] = ""
    st.session_state["ai_workstream_activities"] = []
    st.session_state["ai_assumptions"] = ""
    st.session_state["ai_exclusions"] = ""


# Streamlit removes a widget's session_state entry whenever that widget is
# not instantiated on a given rerun. Binding a widget's `key=` directly to a
# canonical field name silently wipes that field once the wizard navigates
# away. Every field below uses a separate widget-only key, syncing its
# value back into a plain, Streamlit-untouched canonical session_state
# entry -- this is what makes Back/Continue value persistence work.
def synced_text_input(label: str, state_key: str, **kwargs) -> None:
    value = st.text_input(label, value=st.session_state[state_key], key=f"w_{state_key}", **kwargs)
    st.session_state[state_key] = value


def synced_text_area(label: str, state_key: str, **kwargs) -> None:
    value = st.text_area(label, value=st.session_state[state_key], key=f"w_{state_key}", **kwargs)
    st.session_state[state_key] = value


def work_types_config() -> list[dict]:
    return load_json_config("work_types.json")


def work_type_label(key: str | None) -> str | None:
    if not key:
        return None
    for entry in work_types_config():
        if entry["key"] == key:
            return entry["label"]
    return None


def dimension_display_names() -> dict[str, str]:
    questions = load_complexity_questions()
    return {dimension["key"]: dimension["display_name"] for dimension in questions["dimensions"]}


def apply_work_type(work_type_key: str) -> None:
    st.session_state["work_type"] = work_type_key
    st.session_state["estimate_type"] = work_type_key
    st.session_state["scope_checklist"] = default_selections_for_work_type(work_type_key)


# ---------------------------------------------------------------------------
# Persistent left-side panel (Steps 2-5)
# ---------------------------------------------------------------------------


def render_sidebar() -> None:
    step = st.session_state["wizard_step"]

    with st.sidebar:
        st.markdown("### Estimate progress")
        step_labels = ["Work type", "Quick facts", "Scope checklist", "Complexity and AI", "Review and estimate"]
        for index, label in enumerate(step_labels, start=1):
            if index < step:
                st.markdown(f"✅ Step {index}: {label}")
            elif index == step:
                st.markdown(f"**➡️ Step {index}: {label} (current)**")
            else:
                st.markdown(f"⬜ Step {index}: {label}")

        st.divider()
        st.markdown("### Current estimate")
        st.markdown(f"**Work type:** {work_type_label(st.session_state['work_type']) or '_Not selected_'}")
        st.markdown(f"**System context:** {st.session_state['system_context'] or '_Not selected_'}")
        st.markdown(f"**AI included:** {st.session_state['ai_included']}")
        st.markdown(f"**Delivery term:** {st.session_state['contract_term'] or '_Not selected_'}")

        st.divider()
        st.markdown("### Running estimate")
        _render_running_estimate()

        st.divider()
        st.markdown("### Status")
        _render_warning_status()


def _render_running_estimate() -> None:
    results = st.session_state["results"]
    scope_checklist = st.session_state["scope_checklist"]
    confirmation_pct = compute_scope_confirmation_percentage(scope_checklist) if scope_checklist else 0.0
    st.markdown(f"Scope confirmed: **{confirmation_pct:.0f}%**")

    if results is not None:
        sizing = results["sizing_result"]
        contract_fit = results["contract_fit_result"]
        st.markdown("**Governed estimate (reviewed and generated):**")
        st.markdown(f"- Size: {sizing.tshirt_size}")
        st.markdown(f"- Sprint range: {sizing.min_sprints:g}–{sizing.max_sprints:g}")
        if contract_fit.estimated_months is not None:
            st.markdown(f"- Duration: {contract_fit.estimated_months:.1f} months")
        st.markdown(f"- Contract fit: {contract_fit.status}")
        return

    answered_scores = {
        key: value["score"] for key, value in st.session_state["complexity_answers"].items() if value
    }
    preview = compute_preliminary_view(answered_scores)
    answered = preview["answered_count"]
    total = preview["total_dimensions"]

    if preview["preliminary_score"] is None:
        st.info("Complete complexity questions to see your preliminary estimate here.")
        st.caption("Pricing available after team and rate planning.")
        return

    sizing = preview["preliminary_sizing"]
    if answered < total:
        st.warning(
            f"Preliminary planning view based on {answered} of {total} complexity questions. "
            "Complete the remaining questions for the governed estimate."
        )
    else:
        st.warning(
            "Preliminary planning view based on all 7 complexity questions. Confirm and "
            "generate the estimate at Step 5 for the governed result."
        )
    if sizing is not None:
        low = sprint_to_months(sizing.min_sprints)
        high = sprint_to_months(sizing.max_sprints)
        likely = sprint_to_months((sizing.min_sprints + sizing.max_sprints) / 2)
        st.markdown(f"- Preliminary low: {low:.1f} months")
        st.markdown(f"- Likely: {likely:.1f} months")
        st.markdown(f"- Preliminary high: {high:.1f} months")
        st.markdown(f"- Current estimated size: {sizing.tshirt_size}")
    st.caption("Pricing available after team and rate planning.")


def _render_warning_status() -> None:
    scope_checklist = st.session_state["scope_checklist"]
    unknowns = unknown_item_keys(scope_checklist) if scope_checklist else []
    results = st.session_state["results"]

    shown_any = False
    if results is not None and results["contract_fit_result"].status == "Estimate Definition Required":
        st.error("Estimate Definition Required: there is not yet enough defined scope to responsibly estimate duration.")
        shown_any = True

    if unknowns:
        st.warning(
            "Delivery risk: some scope items are marked Unknown. Reducing effort or scope "
            "without resolving these may affect testing, deployment readiness, "
            "documentation, or timeline reliability. Review the affected items before "
            "finalizing this scenario."
        )
        shown_any = True

    if not shown_any:
        st.caption("No warnings at this time.")


# ---------------------------------------------------------------------------
# Step 1: Work type
# ---------------------------------------------------------------------------


def render_step_1_work_type() -> None:
    st.subheader("Step 1 of 5: Work type")
    st.caption("What kind of work is this? Choose the option that best matches this request.")

    work_types = work_types_config()
    labels = [entry["label"] for entry in work_types]
    key_by_label = {entry["label"]: entry["key"] for entry in work_types}
    label_by_key = {entry["key"]: entry["label"] for entry in work_types}

    current_label = label_by_key.get(st.session_state["work_type"])
    index = labels.index(current_label) if current_label in labels else None

    selected_label = st.radio(
        "Work type (required)",
        labels,
        index=index,
        key="w_work_type",
        help="This determines the suggested scope checklist and assumptions.",
    )
    with st.expander("What do these mean?", expanded=True):
        for entry in work_types:
            st.markdown(f"- **{entry['label']}** — {entry['description']}")

    if not selected_label:
        return

    selected_key = key_by_label[selected_label]
    current_key = st.session_state["work_type"]

    if current_key == selected_key:
        return

    if current_key is None or not st.session_state["scope_checklist"]:
        apply_work_type(selected_key)
        return

    st.warning(
        "Changing work type will reset your scope checklist to new suggested defaults for "
        "the new work type. Your complexity, contact, and other answers are kept."
    )
    cols = st.columns(2)
    with cols[0]:
        if st.button("Apply new work type (resets scope defaults)", key="confirm_work_type_change"):
            apply_work_type(selected_key)
            st.rerun()
    with cols[1]:
        if st.button("Cancel -- keep current work type", key="cancel_work_type_change"):
            st.rerun()


# ---------------------------------------------------------------------------
# Step 2: Quick facts
# ---------------------------------------------------------------------------


def render_step_2_quick_facts() -> None:
    st.subheader("Step 2 of 5: Quick facts")
    st.info(f"Work type: {work_type_label(st.session_state['work_type'])}")

    if not st.session_state["estimate_name"] and st.session_state["work_type"]:
        st.session_state["estimate_name"] = f"{work_type_label(st.session_state['work_type'])} estimate"

    synced_text_input(
        "Estimate name (required)",
        "estimate_name",
        help="Auto-suggested from the work type -- edit to make it specific.",
    )
    synced_text_area(
        "Business objective in one sentence (required)",
        "business_objective",
        help="Example: Reduce manual invoice processing time by 50%.",
    )

    current_context = st.session_state["system_context"]
    context_index = SYSTEM_CONTEXT_OPTIONS.index(current_context) if current_context in SYSTEM_CONTEXT_OPTIONS else None
    selected_context = st.radio(
        "System context (required)",
        SYSTEM_CONTEXT_OPTIONS,
        index=context_index,
        key="w_system_context",
        horizontal=True,
    )
    if selected_context:
        st.session_state["system_context"] = selected_context

    current_audience = st.session_state["audience"]
    audience_index = AUDIENCE_OPTIONS.index(current_audience) if current_audience in AUDIENCE_OPTIONS else None
    selected_audience = st.radio(
        "Audience (required)",
        AUDIENCE_OPTIONS,
        index=audience_index,
        key="w_audience",
        horizontal=True,
    )
    if selected_audience:
        st.session_state["audience"] = selected_audience

    current_term = st.session_state["contract_term"]
    term_index = CONTRACT_TERM_OPTIONS.index(current_term) if current_term in CONTRACT_TERM_OPTIONS else None
    selected_term = st.radio(
        "Requested delivery term (required)",
        CONTRACT_TERM_OPTIONS,
        index=term_index,
        key="w_contract_term",
        horizontal=True,
        help="This is a planning and commercial boundary only -- no holiday, PTO, or meeting deductions.",
    )
    if selected_term:
        st.session_state["contract_term"] = selected_term

    if st.session_state.get("contract_term") == "Custom":
        custom_months = st.number_input(
            "Custom delivery term in months (required)",
            min_value=0.0,
            step=0.5,
            value=st.session_state["contract_custom_months"],
            key="w_contract_custom_months",
        )
        st.session_state["contract_custom_months"] = custom_months or None
    else:
        st.session_state["contract_custom_months"] = None

    current_ai = st.session_state["ai_included"]
    ai_index = AI_INCLUDED_OPTIONS.index(current_ai) if current_ai in AI_INCLUDED_OPTIONS else 0
    selected_ai = st.radio(
        "AI included? (required)",
        AI_INCLUDED_OPTIONS,
        index=ai_index,
        key="w_ai_included",
        horizontal=True,
        help="Choose 'No' unless this project includes an AI capability. AI is never assumed.",
    )
    if selected_ai == "No" and st.session_state["ai_included"] != "No":
        clear_ai_fields()
    st.session_state["ai_included"] = selected_ai

    with st.expander("Additional details (optional)"):
        synced_text_input("Known deadline", "requested_deadline")
        synced_text_input("Customer or business unit", "customer_or_business_unit")
        synced_text_area("Known dependencies", "known_dependencies")
        synced_text_area("Other context", "other_context")
        synced_text_area("Short notes", "description")


# ---------------------------------------------------------------------------
# Step 3: Scope checklist
# ---------------------------------------------------------------------------


def render_step_3_scope_checklist() -> None:
    st.subheader("Step 3 of 5: Scope checklist")
    st.caption("Suggested assumptions based on the selected work type. Correct any that don't apply.")

    work_type = st.session_state["work_type"]
    scope_checklist = st.session_state["scope_checklist"]

    for category in categories_for_work_type(work_type):
        st.markdown(f"**{category['label']}**")
        for item in category["items"]:
            item_key = item["key"]
            current_status = scope_checklist.get(item_key, item["defaults"][work_type])
            current_display = SCOPE_KEY_TO_STATUS[current_status]
            selected_display = st.segmented_control(
                item["label"],
                SCOPE_STATUS_OPTIONS,
                default=current_display,
                required=True,
                key=f"w_scope_{item_key}",
            )
            scope_checklist[item_key] = SCOPE_STATUS_TO_KEY[selected_display]
        st.divider()

    st.session_state["scope_checklist"] = scope_checklist

    counts = compute_scope_counts(scope_checklist)
    cols = st.columns(3)
    cols[0].metric("Included", counts["included"])
    cols[1].metric("Not included", counts["not_included"])
    cols[2].metric("Unknown", counts["unknown"])
    if counts["unknown"]:
        st.caption("Unknown items may proceed but are flagged for review at the Review step.")

    st.markdown("**Systems involved**")
    selected_systems = st.multiselect(
        "Systems involved",
        systems_involved_options(),
        default=st.session_state["systems_involved_selected"],
        key="w_systems_involved_selected",
        label_visibility="collapsed",
    )
    st.session_state["systems_involved_selected"] = selected_systems
    if "Other" in selected_systems:
        synced_text_input("Other system (short note, optional)", "systems_involved_other_note")


# ---------------------------------------------------------------------------
# Step 4: Complexity and AI
# ---------------------------------------------------------------------------


def render_step_4_complexity_and_ai() -> None:
    st.subheader("Step 4 of 5: Complexity and AI")
    st.caption(
        "This 0-5 scale is the product's approved estimation convention, not a universal "
        "industry standard."
    )

    questions = load_complexity_questions()
    answers = st.session_state["complexity_answers"]

    for dimension in questions["dimensions"]:
        dim_key = dimension["key"]
        level_labels = [level["label"] for level in dimension["levels"]]
        current = answers.get(dim_key)
        current_index = level_labels.index(current["label"]) if current else None
        selected = st.selectbox(
            f"{dimension['display_name']} (required)",
            level_labels,
            index=current_index,
            key=f"w_complexity_{dim_key}",
            help=dimension["question"],
            placeholder="Select a level...",
        )
        with st.expander("Level descriptions and examples"):
            for level in dimension["levels"]:
                st.markdown(f"- **{level['label']}** — {level['description']} _Example: {level['example']}_")
        if selected:
            matched = next(level for level in dimension["levels"] if level["label"] == selected)
            answers[dim_key] = {"label": matched["label"], "score": matched["score"]}

    st.session_state["complexity_answers"] = answers

    st.divider()
    st.markdown(f"**AI included:** {st.session_state['ai_included']}")

    if st.session_state["ai_included"] == "No":
        st.info("No AI-specific questions apply for this estimate.")
        return

    help_options_config = load_json_config("ai_help_options.json")
    selected_help = st.multiselect(
        "What should AI help with? (required)",
        help_options_config["help_options"],
        default=st.session_state["ai_help"],
        key="w_ai_help",
    )
    st.session_state["ai_help"] = selected_help

    data_index = (
        help_options_config["data_options"].index(st.session_state["ai_data"])
        if st.session_state["ai_data"] in help_options_config["data_options"]
        else None
    )
    selected_data = st.selectbox(
        "What data will AI use? (required)",
        help_options_config["data_options"],
        index=data_index,
        key="w_ai_data",
        placeholder="Select...",
    )
    if selected_data:
        st.session_state["ai_data"] = selected_data

    review_index = (
        help_options_config["human_review_options"].index(st.session_state["ai_human_review"])
        if st.session_state["ai_human_review"] in help_options_config["human_review_options"]
        else None
    )
    selected_review = st.selectbox(
        "Will a person review AI output? (required)",
        help_options_config["human_review_options"],
        index=review_index,
        key="w_ai_human_review",
        placeholder="Select...",
    )
    if selected_review:
        st.session_state["ai_human_review"] = selected_review

    with st.expander("Advanced AI details (optional)"):
        synced_text_input("AI capability type", "ai_capability_type")
        synced_text_area("AI business objective", "ai_business_objective")
        catalog = load_json_config("ai_workstream_activities.json")
        selected_activities = st.multiselect(
            "Potential AI activities",
            catalog,
            default=st.session_state["ai_workstream_activities"],
            key="w_ai_workstream_activities",
        )
        st.session_state["ai_workstream_activities"] = selected_activities
        synced_text_area("AI assumptions", "ai_assumptions")
        synced_text_area("AI exclusions", "ai_exclusions")


# ---------------------------------------------------------------------------
# Step 5: Review and estimate
# ---------------------------------------------------------------------------


def _derive_scope_labels() -> tuple[list[str], list[str], list[str]]:
    """Returns (included, excluded, unknown) as raw display-label lists."""
    work_type = st.session_state["work_type"]
    scope_checklist = st.session_state["scope_checklist"]
    display_names: dict[str, str] = {}
    for category in categories_for_work_type(work_type):
        for item in category["items"]:
            display_names[item["key"]] = item["label"]

    included = [display_names[k] for k, v in scope_checklist.items() if v == "included" and k in display_names]
    excluded = [display_names[k] for k, v in scope_checklist.items() if v == "not_included" and k in display_names]
    unknown = [display_names[k] for k, v in scope_checklist.items() if v == "unknown" and k in display_names]
    return included, excluded, unknown


def _ensure_assumptions_generated() -> None:
    if st.session_state["assumptions"]:
        return
    _, excluded_labels, unknown_labels = _derive_scope_labels()
    st.session_state["assumptions"] = generate_assumptions(
        work_type=st.session_state["work_type"],
        unknown_item_labels=unknown_labels,
        systems_involved=st.session_state["systems_involved_selected"],
        ai_included=st.session_state["ai_included"],
        ai_human_review=st.session_state["ai_human_review"],
        excluded_item_labels=excluded_labels,
        system_context=st.session_state["system_context"],
        ai_data=st.session_state["ai_data"],
        contract_term=st.session_state["contract_term"],
        known_dependencies=st.session_state["known_dependencies"] or None,
    )


def build_estimate_request() -> EstimateRequest:
    complexity_answers = [
        ComplexityDimensionAnswer(
            dimension_key=key,
            selected_label=st.session_state["complexity_answers"][key]["label"],
            score=st.session_state["complexity_answers"][key]["score"],
        )
        for key in COMPLEXITY_DIMENSION_KEYS
    ]
    ai_on = st.session_state["ai_included"] != "No"
    included_labels, excluded_labels, _ = _derive_scope_labels()
    systems_selected = st.session_state["systems_involved_selected"]

    return EstimateRequest(
        estimate_name=st.session_state["estimate_name"],
        work_type=st.session_state["work_type"],
        estimate_type=st.session_state["work_type"],
        business_objective=st.session_state["business_objective"],
        system_context=st.session_state["system_context"],
        audience=st.session_state["audience"],
        description=st.session_state["description"] or None,
        included_scope=", ".join(included_labels) or None,
        known_exclusions=", ".join(excluded_labels) or None,
        systems_involved=", ".join(systems_selected) or None,
        systems_involved_list=systems_selected,
        requested_deadline=st.session_state["requested_deadline"] or None,
        customer_or_business_unit=st.session_state["customer_or_business_unit"] or None,
        other_context=st.session_state["other_context"] or None,
        known_dependencies=st.session_state["known_dependencies"] or None,
        scope_checklist=dict(st.session_state["scope_checklist"]),
        assumptions=list(st.session_state["assumptions"]),
        items_needing_review=unknown_item_keys(st.session_state["scope_checklist"]),
        contract_term=st.session_state["contract_term"],
        contract_custom_months=st.session_state["contract_custom_months"],
        ai_included=st.session_state["ai_included"],
        ai_help=st.session_state["ai_help"] if ai_on else [],
        ai_data=st.session_state["ai_data"] if ai_on else None,
        ai_human_review=st.session_state["ai_human_review"] if ai_on else None,
        ai_capability=("Yes - Other AI capability" if ai_on else "No"),
        ai_capability_type=(st.session_state["ai_capability_type"] or None) if ai_on else None,
        ai_business_objective=(st.session_state["ai_business_objective"] or None) if ai_on else None,
        ai_workstream_activities=st.session_state["ai_workstream_activities"] if ai_on else [],
        ai_assumptions=(st.session_state["ai_assumptions"] or None) if ai_on else None,
        ai_exclusions=(st.session_state["ai_exclusions"] or None) if ai_on else None,
        complexity_answers=complexity_answers,
    )


def run_calculation(estimate_request: EstimateRequest) -> dict:
    complexity_result = calculate_weighted_complexity(
        {answer.dimension_key: answer.score for answer in estimate_request.complexity_answers}
    )
    sizing_result = map_to_size(complexity_result.weighted_complexity_score)
    contract_fit_result = calculate_contract_fit(
        sizing_result, estimate_request.contract_term, estimate_request.contract_custom_months
    )
    return {
        "estimate_request": estimate_request,
        "complexity_result": complexity_result,
        "sizing_result": sizing_result,
        "contract_fit_result": contract_fit_result,
    }


def render_step_5_review_and_estimate() -> None:
    st.subheader("Step 5 of 5: Review and estimate")

    review_state = dict(st.session_state)
    review_state["complexity_answers"] = {
        key: (value["score"] if value else None)
        for key, value in st.session_state["complexity_answers"].items()
    }
    missing = find_missing_required_fields(review_state)

    display_names = dimension_display_names()
    included_labels, excluded_labels, unknown_labels = _derive_scope_labels()
    included_scope, excluded_scope = ", ".join(included_labels), ", ".join(excluded_labels)
    _ensure_assumptions_generated()

    def _edit_button(label: str, step: int, key: str) -> None:
        if st.button(f"Edit {label}", key=key):
            go_to_step(step)
            st.rerun()

    st.markdown(f"**Work type:** {work_type_label(st.session_state['work_type'])}")
    _edit_button("work type", 1, "edit_work_type")
    st.markdown(f"**Estimate name:** {st.session_state['estimate_name']}")
    st.markdown(f"**Business objective:** {st.session_state['business_objective']}")
    st.markdown(f"**System context:** {st.session_state['system_context']}")
    st.markdown(f"**Audience:** {st.session_state['audience']}")
    st.markdown(f"**Delivery term:** {st.session_state['contract_term']}")
    st.markdown(f"**AI included:** {st.session_state['ai_included']}")
    _edit_button("quick facts", 2, "edit_quick_facts")

    st.markdown(f"**Included scope:** {included_scope or '_None marked included_'}")
    st.markdown(f"**Excluded scope:** {excluded_scope or '_None marked excluded_'}")
    st.markdown(f"**Unknown items:** {', '.join(unknown_labels) or '_None_'}")
    st.markdown(
        f"**Systems involved:** {', '.join(st.session_state['systems_involved_selected']) or '_None selected_'}"
    )
    _edit_button("scope checklist", 3, "edit_scope")

    st.markdown("**Complexity answers:**")
    for dim_key in COMPLEXITY_DIMENSION_KEYS:
        answer = st.session_state["complexity_answers"].get(dim_key)
        st.markdown(f"- {display_names[dim_key]}: {answer['label'] if answer else '_Not answered_'}")
    _edit_button("complexity and AI", 4, "edit_complexity")

    st.markdown("**Suggested assumptions (editable):**")
    for index, assumption in enumerate(list(st.session_state["assumptions"])):
        cols = st.columns([5, 1])
        with cols[0]:
            updated = st.text_input(
                f"Assumption {index + 1}", value=assumption, key=f"assumption_{index}", label_visibility="collapsed"
            )
            st.session_state["assumptions"][index] = updated
        with cols[1]:
            if st.button("Remove", key=f"remove_assumption_{index}"):
                st.session_state["assumptions"].pop(index)
                st.rerun()
    new_assumption = st.text_input("Add another assumption", key="new_assumption_input")
    if st.button("Add assumption", key="add_assumption") and new_assumption:
        st.session_state["assumptions"].append(new_assumption)
        st.rerun()
    st.caption("Assumptions are suggestions until you confirm them here -- they are not approved facts.")

    st.markdown(f"**Known dependencies:** {st.session_state['known_dependencies'] or '_None documented_'}")

    if unknown_labels:
        st.markdown(f"**Items needing review:** {', '.join(unknown_labels)}")

    if missing:
        st.warning("Missing required information:\n" + "\n".join(f"- {item}" for item in missing))
    else:
        st.success("All required information is complete.")

    if st.button("Confirm and generate estimate", key="generate_estimate", disabled=bool(missing)):
        estimate_request = build_estimate_request()
        st.session_state["results"] = run_calculation(estimate_request)
        st.session_state["sow_outline_gate"] = None
        st.session_state["sow_outline_sections"] = None
        st.rerun()

    if st.session_state["results"] is not None:
        _render_executive_results()
        _render_calculation_transparency()
        _render_action_navigation()

    _render_future_pricing_preview()


def _render_executive_results() -> None:
    results = st.session_state["results"]
    complexity = results["complexity_result"]
    sizing = results["sizing_result"]
    contract_fit = results["contract_fit_result"]

    st.divider()
    st.markdown("## Estimate results")
    st.markdown(f"### T-shirt size: {sizing.tshirt_size}")
    st.markdown(f"**Sprint range:** {sizing.min_sprints:g}–{sizing.max_sprints:g} sprints")
    if contract_fit.estimated_months is not None:
        st.markdown(f"**Estimated duration:** {contract_fit.estimated_months:.1f} months")
    st.markdown(f"**Contract-fit status:** {contract_fit.status}")
    st.info(contract_fit.status_explanation)

    if complexity.higher_scoring_dimensions:
        display_names = dimension_display_names()
        higher = ", ".join(display_names[k] for k in complexity.higher_scoring_dimensions)
        st.markdown(f"**Higher-scoring complexity dimensions:** {higher}")

    if sizing.discovery_review_required:
        st.warning(
            "This work is large enough to require a discovery or phasing review before a "
            "firm commitment is made."
        )
    if sizing.decomposition_required:
        st.warning(
            "This work must be decomposed into smaller estimates before a final commercial "
            "commitment is made."
        )


def _render_calculation_transparency() -> None:
    results = st.session_state["results"]
    complexity = results["complexity_result"]
    sizing = results["sizing_result"]
    contract_fit = results["contract_fit_result"]
    display_names = dimension_display_names()

    with st.expander("How was this calculated?"):
        st.markdown(
            "_The mappings shown below are the product's approved estimation convention, not "
            "a universal SAFe or Agile standard._"
        )

        st.markdown("**Complexity dimensions**")
        for dim_key in COMPLEXITY_DIMENSION_KEYS:
            answer = next(
                a for a in results["estimate_request"].complexity_answers if a.dimension_key == dim_key
            )
            weight = complexity.dimension_weights[dim_key]
            contribution = complexity.dimension_contributions[dim_key]
            st.markdown(
                f"- **{display_names[dim_key]}** — Selected answer: {answer.selected_label}; "
                f"Internal score: {answer.score}; Weight: {weight:.0%}; "
                f"Contribution: {answer.score} × {weight:.2f} = {contribution:.2f}"
            )

        st.markdown("**Weighted complexity formula**")
        st.markdown(
            "Weighted complexity = (Functional × 0.20) + (Technical × 0.20) + "
            "(Integration × 0.15) + (Data × 0.10) + (Testing × 0.15) + "
            "(Dependency × 0.10) + (Operational risk × 0.10)"
        )
        substituted = " + ".join(
            f"({complexity.dimension_scores[k]} × {complexity.dimension_weights[k]:.2f})"
            for k in COMPLEXITY_DIMENSION_KEYS
        )
        st.markdown(f"Substituted: {substituted} = {complexity.weighted_complexity_display}")
        st.markdown(
            f"**Weighted complexity result:** {complexity.weighted_complexity_display} "
            f"(stored at full precision: {complexity.weighted_complexity_score})"
        )

        st.markdown("**Relative Job Size, T-shirt, and sprint-range mapping**")
        st.markdown(
            f"A weighted complexity score of {complexity.weighted_complexity_display} falls in "
            f"the approved band mapping to Relative Job Size {sizing.relative_job_size}, "
            f"T-shirt size {sizing.tshirt_size}, and a sprint range of {sizing.min_sprints:g}–"
            f"{sizing.max_sprints:g} sprints."
        )

        st.markdown("**Duration formula**")
        st.markdown("Estimated months = maximum sprint estimate × 2 weeks ÷ 4.33 weeks per month")
        if contract_fit.estimated_months is not None:
            st.markdown(
                f"Substituted: {sizing.max_sprints:g} × 2 ÷ 4.33 = "
                f"{contract_fit.estimated_months:.2f} months"
            )

        st.markdown("**Contract-fit formula**")
        st.markdown("Contract utilization = estimated months ÷ delivery-term months")
        if contract_fit.fit_ratio is not None:
            st.markdown(
                f"Substituted: {contract_fit.estimated_months:.2f} ÷ "
                f"{contract_fit.contract_months:g} = {contract_fit.fit_ratio:.0%}"
            )
            st.markdown("**Threshold used:** Fits ≤ 80%, At Risk 80%–100%, Does Not Fit > 100%.")


# ---------------------------------------------------------------------------
# Action navigation and preliminary SOW outline (EAP.M1.UI2)
# ---------------------------------------------------------------------------


def _generate_sow_outline() -> None:
    results = st.session_state["results"]
    estimate_request = results["estimate_request"]
    contract_fit = results["contract_fit_result"]

    gate = evaluate_pre_generation_gate(estimate_request, contract_fit.status)
    st.session_state["sow_outline_gate"] = gate

    if gate.status == "Generation Blocked":
        st.session_state["sow_outline_sections"] = None
        return

    included_labels, excluded_labels, unknown_labels = _derive_scope_labels()
    st.session_state["sow_outline_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state["sow_outline_sections"] = build_preliminary_sow_outline(
        estimate_request=estimate_request,
        complexity_result=results["complexity_result"],
        sizing_result=results["sizing_result"],
        contract_fit_result=contract_fit,
        work_type_label=work_type_label(estimate_request.work_type),
        included_scope_labels=included_labels,
        excluded_scope_labels=excluded_labels,
        unknown_scope_labels=unknown_labels,
        dimension_display_names=dimension_display_names(),
        generated_at=st.session_state["sow_outline_generated_at"],
        resource_plan=st.session_state["resource_plan_result"],
    )


def _render_action_navigation() -> None:
    st.divider()
    st.markdown("### Actions")
    cols = st.columns(5)
    with cols[0]:
        if st.button("Generate Preliminary SOW Outline", key="generate_sow_outline"):
            _generate_sow_outline()
    with cols[1]:
        st.button(
            "Generate Final SOW",
            disabled=True,
            help="Requires approved resource plan and pricing",
            key="final_sow_locked",
        )
    with cols[2]:
        st.button(
            "Export to Excel",
            disabled=True,
            help="Coming in a later milestone",
            key="export_excel_locked",
        )
    with cols[3]:
        st.button(
            "Export to PowerPoint",
            disabled=True,
            help="Coming in a later milestone",
            key="export_ppt_locked",
        )
    with cols[4]:
        if st.button("Build Resource Plan", key="build_resource_plan"):
            _generate_resource_plan()

    if st.session_state["resource_plan_rows_editable"] is not None:
        _render_resource_plan_section()

    if st.session_state["sow_outline_gate"] is not None:
        _render_sow_outline_section()


# ---------------------------------------------------------------------------
# Phase and resource planning (EAP.M2)
# ---------------------------------------------------------------------------


def _generate_resource_plan() -> None:
    results = st.session_state["results"]
    estimate_request = results["estimate_request"]
    sizing = results["sizing_result"]

    phases = build_phase_plan(
        work_type=estimate_request.work_type,
        total_sprints=sizing.max_sprints,
        ai_included=estimate_request.ai_included,
        ai_workstream_activities=estimate_request.ai_workstream_activities,
        ai_help=estimate_request.ai_help,
    )
    plan = build_resource_plan(
        work_type=estimate_request.work_type,
        phases=phases,
        ai_included=estimate_request.ai_included,
        staffing_model=st.session_state["staffing_model"],
        ai_workstream_activities=estimate_request.ai_workstream_activities,
        ai_help=estimate_request.ai_help,
        customer_defined_assignments=st.session_state["customer_defined_assignments"] or None,
    )
    st.session_state["resource_plan_result"] = plan
    duration_by_phase = {p.phase_key: p.duration_sprints for p in plan.phases}
    st.session_state["resource_plan_rows_editable"] = [
        {
            "Phase": row.phase_label,
            "Role": row.role,
            "AI workstream": row.is_ai_workstream,
            "Duration (sprints)": duration_by_phase[row.phase_key],
            "Allocation %": row.allocation_percent,
            "Person-sprints": row.person_sprints,
            "Estimated hours": row.estimated_hours,
            "_phase_key": row.phase_key,
            "_role": row.role,
            "_assigned_to": row.assigned_to,
        }
        for row in plan.rows
    ]


def _render_resource_plan_section() -> None:
    from src.resource_planner import compute_totals, compute_warnings

    st.divider()
    st.markdown("## Resource plan")
    st.caption(
        "Preliminary planning information only -- not a final staffing commitment. Duration and "
        "allocation are editable below; person-sprints and hours recalculate immediately."
    )

    current_model = st.session_state["staffing_model"]
    model_index = STAFFING_MODEL_OPTIONS.index(current_model) if current_model in STAFFING_MODEL_OPTIONS else 1
    selected_model = st.radio(
        "Staffing model",
        STAFFING_MODEL_OPTIONS,
        index=model_index,
        key="w_staffing_model",
        horizontal=True,
        help="Changes only who is assigned to combined roles -- required effort per role never changes.",
    )
    if selected_model != st.session_state["staffing_model"]:
        st.session_state["staffing_model"] = selected_model
        _generate_resource_plan()
        st.rerun()

    if selected_model == "Customer-defined":
        with st.expander("Customer-defined role assignments", expanded=True):
            unique_roles = sorted({row["_role"] for row in st.session_state["resource_plan_rows_editable"]})
            assignments = dict(st.session_state["customer_defined_assignments"])
            for role in unique_roles:
                assignments[role] = st.text_input(
                    f"Assigned person for {role}",
                    value=assignments.get(role, role),
                    key=f"w_assign_{role}",
                )
            if st.button("Apply assignments", key="apply_customer_assignments"):
                st.session_state["customer_defined_assignments"] = assignments
                _generate_resource_plan()
                st.rerun()

    editable_rows = st.session_state["resource_plan_rows_editable"]
    display_df = pd.DataFrame(editable_rows).drop(columns=["_phase_key", "_role", "_assigned_to"])
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Phase": st.column_config.TextColumn("Phase", disabled=True),
            "Role": st.column_config.TextColumn("Role", disabled=True),
            "AI workstream": st.column_config.CheckboxColumn("AI workstream", disabled=True),
            "Duration (sprints)": st.column_config.NumberColumn("Duration (sprints)", min_value=0.0, step=0.25),
            "Allocation %": st.column_config.NumberColumn("Allocation %", min_value=0.0, step=5.0),
            "Person-sprints": st.column_config.NumberColumn("Person-sprints", disabled=True),
            "Estimated hours": st.column_config.NumberColumn("Estimated hours", disabled=True),
        },
        hide_index=True,
        key="resource_plan_editor",
    )
    st.caption(
        "Tip: if you change a phase's duration, update it on every row for that phase to keep "
        "totals consistent."
    )

    resource_rules = load_resource_rules()
    hours_per_sprint = resource_rules["hours_per_sprint"]

    recalculated_rows: list[ResourcePlanRow] = []
    updated_editable: list[dict] = []
    for index, row in edited_df.iterrows():
        duration = float(row["Duration (sprints)"])
        allocation = float(row["Allocation %"])
        person_sprints = round(duration * allocation / 100, 4)
        estimated_hours = round(person_sprints * hours_per_sprint, 2)
        original = editable_rows[index]
        recalculated_rows.append(
            ResourcePlanRow(
                phase_key=original["_phase_key"],
                phase_label=row["Phase"],
                role=row["Role"],
                allocation_percent=allocation,
                person_sprints=person_sprints,
                estimated_hours=estimated_hours,
                is_ai_workstream=bool(row["AI workstream"]),
                assigned_to=original["_assigned_to"],
            )
        )
        updated_editable.append(
            {
                "Phase": row["Phase"],
                "Role": row["Role"],
                "AI workstream": row["AI workstream"],
                "Duration (sprints)": duration,
                "Allocation %": allocation,
                "Person-sprints": person_sprints,
                "Estimated hours": estimated_hours,
                "_phase_key": original["_phase_key"],
                "_role": original["_role"],
                "_assigned_to": original["_assigned_to"],
            }
        )
    st.session_state["resource_plan_rows_editable"] = updated_editable

    plan = st.session_state["resource_plan_result"]
    phases_for_warnings = [
        p.model_copy(update={"duration_sprints": next(
            (r["Duration (sprints)"] for r in updated_editable if r["_phase_key"] == p.phase_key), p.duration_sprints
        )})
        for p in plan.phases
    ]
    warnings = compute_warnings(recalculated_rows, phases_for_warnings, ai_enabled=estimate_request_ai_enabled())
    totals = compute_totals(recalculated_rows)
    st.session_state["resource_plan_result"] = plan.model_copy(
        update={"rows": recalculated_rows, "warnings": warnings, **totals}
    )

    st.markdown("### Totals")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**By role**")
        for role, hours in totals["total_hours_by_role"].items():
            st.markdown(f"- {role}: {hours:g} hours")
    with cols[1]:
        st.markdown("**By phase**")
        for phase, hours in totals["total_hours_by_phase"].items():
            st.markdown(f"- {phase}: {hours:g} hours")
    st.markdown(f"**Core IT workstream:** {totals['total_hours_core_it']:g} hours")
    if totals["total_hours_ai_workstream"]:
        st.markdown(f"**Optional AI workstream:** {totals['total_hours_ai_workstream']:g} hours")

    if warnings:
        st.markdown("### Resource warnings")
        for warning in warnings:
            st.warning(warning)

    with st.expander("How was resource effort calculated?"):
        st.markdown("Person-sprints = phase duration in sprints × (allocation % ÷ 100)")
        st.markdown(f"Estimated hours = person-sprints × {hours_per_sprint:g} hours per sprint")
        for row in recalculated_rows:
            st.markdown(
                f"- **{row.role}** in *{row.phase_label}*: "
                f"{next((r['Duration (sprints)'] for r in updated_editable if r['_phase_key'] == row.phase_key and r['_role'] == row.role), 0):g} "
                f"sprints × {row.allocation_percent:.0f}% = {row.person_sprints:g} person-sprints; "
                f"{row.person_sprints:g} × {hours_per_sprint:g} = {row.estimated_hours:g} hours"
            )


def estimate_request_ai_enabled() -> bool:
    results = st.session_state["results"]
    return results is not None and results["estimate_request"].ai_included != "No"


def _render_sow_outline_section() -> None:
    gate = st.session_state["sow_outline_gate"]
    st.divider()
    st.markdown("## Preliminary SOW Outline")

    if gate.status == "Generation Blocked":
        st.error(
            "Generation Blocked -- the preliminary outline could not be generated:\n"
            + "\n".join(f"- {reason}" for reason in gate.blocking_reasons)
        )
        return

    st.markdown("**Status: Preliminary Draft**")
    st.success(GATE_SUCCESS_MESSAGE)
    if gate.warnings:
        with st.expander("Human review notes", expanded=False):
            for warning in gate.warnings:
                st.markdown(f"- {warning}")

    sections = st.session_state["sow_outline_sections"]
    st.info(PRELIMINARY_STATEMENT)

    for index, (title, body) in enumerate(sections, start=1):
        st.markdown(f"**{index}. {title}**")
        st.markdown(body)

    cols = st.columns(3)
    with cols[0]:
        if st.button("Edit inputs", key="sow_edit_inputs"):
            go_to_step(1)
            st.rerun()
    with cols[1]:
        if st.button("Regenerate outline", key="sow_regenerate"):
            _generate_sow_outline()
            st.rerun()
    with cols[2]:
        estimate_name = st.session_state["estimate_name"]
        generated_at = st.session_state["sow_outline_generated_at"]
        download_format = st.selectbox(
            "Download format", ["Markdown (.md)", "Plain text (.txt)"], key="sow_download_format"
        )
        if download_format == "Markdown (.md)":
            content = render_outline_as_markdown(sections, estimate_name, generated_at)
            st.download_button(
                "Download outline",
                data=content,
                file_name=f"{estimate_name}_preliminary_sow_outline.md",
                mime="text/markdown",
                key="sow_download_md",
            )
        else:
            content = render_outline_as_text(sections, estimate_name, generated_at)
            st.download_button(
                "Download outline",
                data=content,
                file_name=f"{estimate_name}_preliminary_sow_outline.txt",
                mime="text/plain",
                key="sow_download_txt",
            )


# ---------------------------------------------------------------------------
# Future pricing interaction preview -- illustrative values only
# ---------------------------------------------------------------------------


def _default_rate_preview_rows() -> list[dict]:
    return [
        {"Role": "Developer", "Actual hours": 100.0, "Configured default rate": 125.0, "Scenario rate": 125.0, "Override reason": ""},
        {"Role": "QA", "Actual hours": 40.0, "Configured default rate": 95.0, "Scenario rate": 95.0, "Override reason": ""},
        {"Role": "Business Analyst", "Actual hours": 30.0, "Configured default rate": 110.0, "Scenario rate": 110.0, "Override reason": ""},
    ]


def _render_future_pricing_preview() -> None:
    st.divider()
    with st.expander("Future pricing interaction preview — illustrative values only", expanded=False):
        st.caption(
            "This section demonstrates a future role/hours/rate interaction pattern "
            "(MVP.M3/M4 scaffolding). Values here are illustrative examples only -- they are "
            "not connected to this estimate and are not a customer quote."
        )

        if "rate_preview_rows" not in st.session_state:
            st.session_state["rate_preview_rows"] = _default_rate_preview_rows()

        df = pd.DataFrame(st.session_state["rate_preview_rows"])
        edited_df = st.data_editor(
            df,
            column_config={
                "Role": st.column_config.TextColumn("Role"),
                "Actual hours": st.column_config.NumberColumn("Actual hours", min_value=0.0, step=1.0),
                "Configured default rate": st.column_config.NumberColumn(
                    "Configured default rate", min_value=0.0, step=1.0, disabled=True
                ),
                "Scenario rate": st.column_config.NumberColumn("Scenario rate", min_value=0.0, step=1.0),
                "Override reason": st.column_config.TextColumn("Override reason (required if rate differs)"),
            },
            hide_index=True,
            key="rate_preview_editor",
        )
        st.session_state["rate_preview_rows"] = edited_df.to_dict("records")

        edited_df = edited_df.copy()
        edited_df["Estimated cost"] = edited_df["Actual hours"] * edited_df["Scenario rate"]
        st.dataframe(
            edited_df[["Role", "Actual hours", "Configured default rate", "Scenario rate", "Estimated cost"]],
            hide_index=True,
        )

        total_hours = edited_df["Actual hours"].sum()
        total_cost = edited_df["Estimated cost"].sum()
        blended_rate = (total_cost / total_hours) if total_hours else None
        if blended_rate is not None:
            st.metric("Calculated blended rate (illustrative, read-only)", f"{blended_rate:,.2f}")

        missing_reasons = edited_df[
            (edited_df["Scenario rate"] != edited_df["Configured default rate"])
            & (edited_df["Override reason"].fillna("") == "")
        ]
        if not missing_reasons.empty:
            st.warning(
                "Override reason required for: " + ", ".join(missing_reasons["Role"].tolist())
            )

        below_default = edited_df[edited_df["Scenario rate"] < edited_df["Configured default rate"]]
        if not below_default.empty:
            st.warning(
                "Illustrative example only -- Commercial risk: the proposed scenario rate is "
                "below the configured default for " + ", ".join(below_default["Role"].tolist()) + "."
            )


# ---------------------------------------------------------------------------
# Navigation and main
# ---------------------------------------------------------------------------


def render_navigation() -> None:
    step = st.session_state["wizard_step"]
    if step == 5:
        cols = st.columns(2)
        with cols[0]:
            if st.button("Back", key="back_5"):
                go_to_step(4)
                st.rerun()
        return

    cols = st.columns(3)
    with cols[0]:
        if step > 1 and st.button("Back", key=f"back_{step}"):
            go_to_step(step - 1)
            st.rerun()
    with cols[1]:
        if st.button("Continue", key=f"continue_{step}"):
            go_to_step(step + 1)
            st.rerun()
    with cols[2]:
        if st.button("Review estimate", key=f"review_shortcut_{step}"):
            go_to_step(5)
            st.rerun()


STEP_RENDERERS = {
    1: render_step_1_work_type,
    2: render_step_2_quick_facts,
    3: render_step_3_scope_checklist,
    4: render_step_4_complexity_and_ai,
    5: render_step_5_review_and_estimate,
}


def main() -> None:
    st.set_page_config(page_title="AI Work Estimation and Pricing Assistant", layout="wide")
    init_state()

    st.title("AI Work Estimation and Pricing Assistant")
    step = st.session_state["wizard_step"]
    st.caption(f"Step {step} of {TOTAL_STEPS}")
    st.progress(step / TOTAL_STEPS)

    if step > 1:
        render_sidebar()

    STEP_RENDERERS[step]()
    render_navigation()


try:
    main()
except ConfigurationError as exc:
    st.error(f"This application's configuration is invalid and cannot proceed: {exc}")
