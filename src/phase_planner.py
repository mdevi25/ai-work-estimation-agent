"""Phase-based estimation.

Owns: selecting applicable phases by work type and deriving each phase's
duration in sprints from the governed sizing result (the caller passes in
`SizingResult.max_sprints` as `total_sprints`, the same MVP.M1 duration
source `contract_fit.py` already uses -- see docs/architecture.md for why
this milestone does not change contract_fit.py itself), per
PHASE-RESOURCE-PLANNING.md sections 1-3, plus the optional AI workstream's
phases per section 12.

Must not: assign roles, calculate person-sprints or hours, or calculate
cost.
"""
from __future__ import annotations

from typing import Optional

from src.config import load_json_config
from src.models import PhasePlanEntry
from src.validators import validate_phase_rules


def load_phase_rules() -> dict:
    rules = load_json_config("phase_rules.json")
    validate_phase_rules(rules)
    return rules


def build_core_phases(work_type: str, total_sprints: float) -> list[PhasePlanEntry]:
    rules = load_phase_rules()
    phases = rules["phases_by_work_type"][work_type]
    return [
        PhasePlanEntry(
            phase_key=phase["key"],
            phase_label=phase["label"],
            duration_sprints=round(total_sprints * phase["weight"], 2),
            is_ai_workstream=False,
        )
        for phase in phases
    ]


def resolve_ai_activities(ai_workstream_activities: list[str], ai_help: list[str]) -> list[str]:
    """The effective set of detailed AI activities driving the AI workstream.

    Uses the user's own detailed selections (the optional/advanced section)
    when provided; otherwise falls back to activities implied by the
    simplified "AI help" answers. Always includes the baseline activities
    (use-case definition, Responsible AI review) per ESTIMATE-TYPES.md
    section 11.5 -- materially required oversight is never a simplification
    to drop.
    """
    resource_rules = load_json_config("resource_rules.json")

    activities: set[str] = set(ai_workstream_activities or [])
    if not activities:
        for help_option in ai_help or []:
            activities.update(resource_rules["ai_help_fallback_activities"].get(help_option, []))
    activities.update(resource_rules["ai_baseline_activities"])
    return sorted(activities)


def build_ai_phases(activities: list[str], total_sprints: float) -> list[PhasePlanEntry]:
    if not activities:
        return []

    rules = load_phase_rules()
    resource_rules = load_json_config("resource_rules.json")
    ai_phase_defs = {phase["key"]: phase["label"] for phase in rules["ai_phases"]}

    triggered_phase_keys: set[str] = set()
    for activity in activities:
        mapping = resource_rules["ai_activity_to_phase_role"].get(activity)
        if mapping:
            triggered_phase_keys.add(mapping["phase"])

    if not triggered_phase_keys:
        return []

    ai_total_sprints = round(total_sprints * rules["ai_phase_weight_of_core_duration"], 2)
    per_phase_sprints = round(ai_total_sprints / len(triggered_phase_keys), 2)

    # Preserve the ai_phases config order for deterministic, readable output.
    ordered_keys = [phase["key"] for phase in rules["ai_phases"] if phase["key"] in triggered_phase_keys]
    return [
        PhasePlanEntry(
            phase_key=key,
            phase_label=ai_phase_defs[key],
            duration_sprints=per_phase_sprints,
            is_ai_workstream=True,
        )
        for key in ordered_keys
    ]


def build_phase_plan(
    work_type: str,
    total_sprints: float,
    ai_included: str,
    ai_workstream_activities: Optional[list[str]] = None,
    ai_help: Optional[list[str]] = None,
) -> list[PhasePlanEntry]:
    """Builds the full phase plan: core IT phases always; AI phases only
    when `ai_included != "No"` -- entirely absent (not zeroed) otherwise.
    """
    core_phases = build_core_phases(work_type, total_sprints)
    if ai_included == "No":
        return core_phases

    activities = resolve_ai_activities(ai_workstream_activities or [], ai_help or [])
    ai_phases = build_ai_phases(activities, total_sprints)
    return core_phases + ai_phases
