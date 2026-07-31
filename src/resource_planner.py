"""Role and resource planning.

Owns: required roles by phase, person-sprint and hour calculations,
staffing-model combined-assignment views, and resource warnings, per
PHASE-RESOURCE-PLANNING.md sections 3-8 and 12 (optional AI workstream).

Must not: apply internal rates or calculate cost or price.
"""
from __future__ import annotations

from typing import Optional

from src.config import load_json_config
from src.models import PhasePlanEntry, ResourcePlanResult, ResourcePlanRow, StaffingModel
from src.phase_planner import resolve_ai_activities
from src.validators import validate_resource_rules, validate_role_combinations


def load_resource_rules() -> dict:
    rules = load_json_config("resource_rules.json")
    validate_resource_rules(rules)
    return rules


def load_role_combinations() -> dict:
    combos = load_json_config("role_combinations.json")
    validate_role_combinations(combos)
    return combos


def build_required_effort_rows(
    work_type: str,
    phases: list[PhasePlanEntry],
    ai_activities: list[str],
) -> list[ResourcePlanRow]:
    """The required-effort table: independent of staffing model. Person-
    sprints and hours use the exact governed formulas:

        person_sprints = phase_duration_in_sprints * (allocation_percent / 100)
        estimated_hours = person_sprints * hours_per_sprint
    """
    resource_rules = load_resource_rules()
    hours_per_sprint = resource_rules["hours_per_sprint"]
    rows: list[ResourcePlanRow] = []

    core_roles_by_phase = resource_rules["roles_by_work_type"][work_type]
    for phase in phases:
        if phase.is_ai_workstream:
            continue
        for role_entry in core_roles_by_phase.get(phase.phase_key, []):
            allocation = float(role_entry["allocation_percent"])
            person_sprints = round(phase.duration_sprints * allocation / 100, 4)
            rows.append(
                ResourcePlanRow(
                    phase_key=phase.phase_key,
                    phase_label=phase.phase_label,
                    role=role_entry["role"],
                    allocation_percent=allocation,
                    person_sprints=person_sprints,
                    estimated_hours=round(person_sprints * hours_per_sprint, 2),
                    is_ai_workstream=False,
                )
            )

    if ai_activities:
        default_allocation = float(resource_rules["ai_default_allocation_percent"])
        phase_roles: dict[str, set[str]] = {}
        for activity in ai_activities:
            mapping = resource_rules["ai_activity_to_phase_role"].get(activity)
            if mapping:
                phase_roles.setdefault(mapping["phase"], set()).add(mapping["role"])

        for phase in phases:
            if not phase.is_ai_workstream:
                continue
            for role in sorted(phase_roles.get(phase.phase_key, [])):
                person_sprints = round(phase.duration_sprints * default_allocation / 100, 4)
                rows.append(
                    ResourcePlanRow(
                        phase_key=phase.phase_key,
                        phase_label=phase.phase_label,
                        role=role,
                        allocation_percent=default_allocation,
                        person_sprints=person_sprints,
                        estimated_hours=round(person_sprints * hours_per_sprint, 2),
                        is_ai_workstream=True,
                    )
                )

    return rows


def apply_staffing_model(
    rows: list[ResourcePlanRow],
    staffing_model: StaffingModel,
    customer_defined_assignments: Optional[dict[str, str]] = None,
) -> list[ResourcePlanRow]:
    """Sets `assigned_to` per row. Never changes allocation_percent,
    person_sprints, or estimated_hours -- required effort is constant
    regardless of staffing model (PHASE-RESOURCE-PLANNING.md section 5).
    """
    combos = load_role_combinations()
    compatible = combos["compatible_combinations"]

    def combined_group_for(role: str) -> Optional[str]:
        for combo in compatible:
            if staffing_model in combo["staffing_models"] and role in combo["roles"]:
                return " / ".join(combo["roles"])
        return None

    updated: list[ResourcePlanRow] = []
    for row in rows:
        row = row.model_copy()
        if staffing_model == "Customer-defined":
            row.assigned_to = (customer_defined_assignments or {}).get(row.role, row.role)
        elif staffing_model == "Specialized":
            row.assigned_to = row.role
        else:
            row.assigned_to = combined_group_for(row.role) or row.role
        updated.append(row)
    return updated


def compute_warnings(rows: list[ResourcePlanRow], phases: list[PhasePlanEntry], ai_enabled: bool) -> list[str]:
    warnings: list[str] = []
    combos = load_role_combinations()

    for row in rows:
        if row.allocation_percent > 100:
            warnings.append(
                f'{row.role} is allocated {row.allocation_percent:.0f}% in "{row.phase_label}" -- '
                "allocation above 100% in a single phase is not realistic for one person and should "
                "be reviewed."
            )

    by_phase_person: dict[tuple[str, str], float] = {}
    phase_label_by_key = {row.phase_key: row.phase_label for row in rows}
    for row in rows:
        if not row.assigned_to:
            continue
        key = (row.phase_key, row.assigned_to)
        by_phase_person[key] = by_phase_person.get(key, 0.0) + row.allocation_percent
    for (phase_key, assigned_to), total in by_phase_person.items():
        if total > 100:
            warnings.append(
                f'"{assigned_to}" is allocated a combined {total:.0f}% in '
                f'"{phase_label_by_key[phase_key]}" under the selected staffing model -- this person '
                "may be over-committed in that phase."
            )

    assigned_roles: dict[str, set[str]] = {}
    for row in rows:
        if row.assigned_to:
            assigned_roles.setdefault(row.assigned_to, set()).add(row.role)
    for combo in combos["incompatible_combinations"]:
        combo_roles = set(combo["roles"])
        for assigned_to, roles in assigned_roles.items():
            if combo_roles.issubset(roles):
                warnings.append(f'{combo["reason"]} (currently combined under "{assigned_to}").')

    core_phase_keys = {p.phase_key for p in phases if not p.is_ai_workstream}
    covered_phase_keys = {row.phase_key for row in rows if not row.is_ai_workstream}
    for expected in ("deployment", "stabilization"):
        if expected in core_phase_keys and expected not in covered_phase_keys:
            warnings.append(
                f'No role effort is assigned to the "{expected}" phase -- this is a resource-plan gap, '
                "not an accepted simplification."
            )

    if ai_enabled:
        resource_rules = load_resource_rules()
        required_eval_activities = set(resource_rules["ai_independent_evaluation_activities"])
        ai_roles_present = {row.role for row in rows if row.is_ai_workstream}
        eval_roles = {
            mapping["role"]
            for activity, mapping in resource_rules["ai_activity_to_phase_role"].items()
            if activity in required_eval_activities
        }
        if not (ai_roles_present & eval_roles):
            warnings.append(
                "No independent AI evaluation or Responsible AI review coverage is present in the AI "
                "workstream -- this is a resource-plan gap, not an accepted simplification."
            )

    return warnings


def compute_totals(rows: list[ResourcePlanRow]) -> dict:
    total_hours_by_role: dict[str, float] = {}
    total_hours_by_phase: dict[str, float] = {}
    total_core = 0.0
    total_ai = 0.0
    for row in rows:
        total_hours_by_role[row.role] = total_hours_by_role.get(row.role, 0.0) + row.estimated_hours
        total_hours_by_phase[row.phase_label] = total_hours_by_phase.get(row.phase_label, 0.0) + row.estimated_hours
        if row.is_ai_workstream:
            total_ai += row.estimated_hours
        else:
            total_core += row.estimated_hours
    return {
        "total_hours_by_role": {role: round(hours, 2) for role, hours in total_hours_by_role.items()},
        "total_hours_by_phase": {phase: round(hours, 2) for phase, hours in total_hours_by_phase.items()},
        "total_hours_core_it": round(total_core, 2),
        "total_hours_ai_workstream": round(total_ai, 2),
    }


def build_resource_plan(
    work_type: str,
    phases: list[PhasePlanEntry],
    ai_included: str,
    staffing_model: StaffingModel,
    ai_workstream_activities: Optional[list[str]] = None,
    ai_help: Optional[list[str]] = None,
    customer_defined_assignments: Optional[dict[str, str]] = None,
) -> ResourcePlanResult:
    ai_enabled = ai_included != "No"
    ai_activities = (
        resolve_ai_activities(ai_workstream_activities or [], ai_help or []) if ai_enabled else []
    )

    rows = build_required_effort_rows(work_type, phases, ai_activities)
    rows = apply_staffing_model(rows, staffing_model, customer_defined_assignments)
    warnings = compute_warnings(rows, phases, ai_enabled)
    totals = compute_totals(rows)

    return ResourcePlanResult(
        phases=phases,
        rows=rows,
        staffing_model=staffing_model,
        warnings=warnings,
        **totals,
    )
