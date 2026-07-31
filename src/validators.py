"""Reusable validation shared across engines.

Every function here raises on invalid input rather than silently coercing
or falling back to a hard-coded default -- see the Change-Impact Gate
correction requiring controlled errors for invalid configuration.
"""
from __future__ import annotations

import math
from typing import Optional

from src.config import ConfigurationError
from src.models import COMPLEXITY_DIMENSION_KEYS

FIBONACCI_RELATIVE_JOB_SIZES = (1, 2, 3, 5, 8, 13, 20)
TSHIRT_SIZES = ("XS", "S", "M", "L", "XL", "Epic")


def validate_dimension_score(score: object) -> int:
    if not isinstance(score, int) or isinstance(score, bool):
        raise ValueError("Complexity dimension score must be an integer")
    if not 0 <= score <= 5:
        raise ValueError(f"Complexity dimension score must be between 0 and 5, got {score}")
    return score


def validate_weight_total(weights: dict) -> None:
    if set(weights.keys()) != set(COMPLEXITY_DIMENSION_KEYS):
        raise ConfigurationError(
            "Complexity weights must define exactly these dimensions: "
            f"{sorted(COMPLEXITY_DIMENSION_KEYS)}"
        )
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ConfigurationError(f"Complexity weights must total 1.00, got {total:.4f}")


def validate_sizing_bands(bands: list[dict]) -> None:
    if not bands:
        raise ConfigurationError("Sizing bands configuration is empty")

    sorted_bands = sorted(bands, key=lambda band: band.get("min_score", -1))

    if sorted_bands[0].get("min_score") != 0.0:
        raise ConfigurationError("Sizing bands must start at a minimum score of 0.00")
    if sorted_bands[-1].get("max_score") != 5.0:
        raise ConfigurationError("Sizing bands must end at a maximum score of 5.00")

    previous_max = None
    for band in sorted_bands:
        rjs = band.get("relative_job_size")
        tshirt = band.get("tshirt_size")
        min_score = band.get("min_score")
        max_score = band.get("max_score")
        min_sprints = band.get("min_sprints")
        max_sprints = band.get("max_sprints")

        if rjs not in FIBONACCI_RELATIVE_JOB_SIZES:
            raise ConfigurationError(f"Invalid Relative Job Size in sizing bands: {rjs}")
        if tshirt not in TSHIRT_SIZES:
            raise ConfigurationError(f"Invalid T-shirt size in sizing bands: {tshirt}")
        if min_score is None or max_score is None or min_score > max_score:
            raise ConfigurationError(f"Invalid score range in sizing band for size {rjs}")
        if (
            min_sprints is None
            or max_sprints is None
            or min_sprints <= 0
            or min_sprints > max_sprints
        ):
            raise ConfigurationError(f"Invalid sprint range in sizing band for size {rjs}")

        if previous_max is not None:
            gap = round(min_score - previous_max, 2)
            if gap != 0.01:
                raise ConfigurationError(
                    "Sizing bands must have no gaps or overlaps between score ranges "
                    f"(band for size {rjs} starts at {min_score}, previous band ended at "
                    f"{previous_max})"
                )
        previous_max = max_score


def validate_contract_terms(terms: dict) -> None:
    if not terms:
        raise ConfigurationError("Contract terms configuration is empty")
    for term, months in terms.items():
        if not isinstance(months, (int, float)) or isinstance(months, bool) or months <= 0:
            raise ConfigurationError(
                f"Contract term '{term}' must map to a positive number of months"
            )


def validate_contract_duration(months: object) -> float:
    if months is None or isinstance(months, bool) or not isinstance(months, (int, float)):
        raise ValueError("Contract duration must be a positive number of months")
    if months <= 0:
        raise ValueError("Contract duration must be a positive number of months")
    return float(months)


def validate_ai_capability(value: str, allowed_values: tuple[str, ...]) -> str:
    if value not in allowed_values:
        raise ValueError(f"Invalid AI capability value: {value}")
    return value


def validate_scope_item_status(value: str) -> str:
    allowed = ("included", "not_included", "unknown")
    if value not in allowed:
        raise ValueError(f"Invalid scope item status: {value}")
    return value


def validate_ai_workstream_activities(selected: list[str], catalog: list[str]) -> list[str]:
    invalid = [item for item in selected if item not in catalog]
    if invalid:
        raise ValueError(f"Unknown AI workstream activities selected: {invalid}")
    return list(selected)


VALID_WORK_TYPES = ("new_project", "enhancement", "production_support")


def validate_scope_checklist_schema(data: dict) -> None:
    categories = data.get("categories")
    if not categories:
        raise ConfigurationError("Scope checklist configuration has no categories")

    for category in categories:
        applies_to = category.get("applies_to_work_types")
        if not applies_to or any(work_type not in VALID_WORK_TYPES for work_type in applies_to):
            raise ConfigurationError(
                f"Scope checklist category '{category.get('key')}' has an invalid or empty "
                "applies_to_work_types list"
            )
        items = category.get("items")
        if not items:
            raise ConfigurationError(
                f"Scope checklist category '{category.get('key')}' has no items"
            )
        for item in items:
            if not item.get("key") or not item.get("label"):
                raise ConfigurationError(
                    f"Scope checklist item in category '{category.get('key')}' is missing a "
                    "key or label"
                )
            defaults = item.get("defaults", {})
            if not defaults or set(defaults.keys()) - set(applies_to):
                raise ConfigurationError(
                    f"Scope checklist item '{item.get('key')}' must define a default for each "
                    "applicable work type and no others"
                )
            for status in defaults.values():
                try:
                    validate_scope_item_status(status)
                except ValueError as exc:
                    raise ConfigurationError(
                        f"Scope checklist item '{item.get('key')}' has an invalid default "
                        f"status: {exc}"
                    ) from exc

    if not data.get("systems_involved_options"):
        raise ConfigurationError("Scope checklist configuration has no systems_involved_options")


def validate_complexity_questions_schema(data: dict) -> None:
    dimensions = data.get("dimensions")
    if not dimensions:
        raise ConfigurationError("Complexity questions configuration has no dimensions")

    keys = [dimension.get("key") for dimension in dimensions]
    if set(keys) != set(COMPLEXITY_DIMENSION_KEYS) or len(keys) != len(COMPLEXITY_DIMENSION_KEYS):
        raise ConfigurationError(
            "Complexity questions configuration must define exactly the 7 approved dimensions"
        )

    for dimension in dimensions:
        if not dimension.get("question") or not dimension.get("display_name"):
            raise ConfigurationError(
                f"Complexity dimension '{dimension.get('key')}' is missing a question or "
                "display name"
            )
        levels = dimension.get("levels", [])
        scores = sorted(level.get("score") for level in levels)
        if scores != [0, 1, 2, 3, 4, 5]:
            raise ConfigurationError(
                f"Complexity dimension '{dimension.get('key')}' must define exactly one "
                "level for each score from 0 through 5"
            )
        for level in levels:
            if not level.get("label") or not level.get("description") or not level.get("example"):
                raise ConfigurationError(
                    f"Complexity dimension '{dimension.get('key')}' level "
                    f"{level.get('score')} is missing a label, description, or example"
                )


REQUIRED_FIELD_LABELS = {
    "estimate_name": "Estimate name",
    "work_type": "Work type",
    "business_objective": "Business objective",
    "system_context": "System context",
    "audience": "Audience",
    "contract_term": "Delivery term",
}


def find_missing_required_fields(
    state: dict, dimension_display_names: dict[str, str] | None = None
) -> list[str]:
    """Return human-readable labels for every required field not yet answered.

    Operates on raw wizard session-state (not an EstimateRequest) so it can
    report gaps before the structured model is assembled.
    """
    missing: list[str] = []

    for key, label in REQUIRED_FIELD_LABELS.items():
        if not state.get(key):
            missing.append(label)

    if state.get("contract_term") == "Custom" and not state.get("contract_custom_months"):
        missing.append("Custom delivery term (months)")

    complexity_answers = state.get("complexity_answers", {}) or {}
    for dimension_key in COMPLEXITY_DIMENSION_KEYS:
        if complexity_answers.get(dimension_key) is None:
            display = (dimension_display_names or {}).get(dimension_key, dimension_key)
            missing.append(f"Complexity answer: {display}")

    if state.get("ai_included", "No") != "No":
        if not state.get("ai_help"):
            missing.append("What should AI help with?")
        if not state.get("ai_data"):
            missing.append("What data will AI use?")
        if not state.get("ai_human_review"):
            missing.append("Will a person review AI output?")

    return missing


def validate_allocation_percent(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Allocation percent must be numeric")
    if value < 0:
        raise ValueError(f"Allocation percent cannot be negative, got {value}")
    return float(value)


def validate_phase_rules(data: dict) -> None:
    phases_by_work_type = data.get("phases_by_work_type")
    if not phases_by_work_type or set(phases_by_work_type.keys()) != set(VALID_WORK_TYPES):
        raise ConfigurationError(
            f"phase_rules.json must define phases_by_work_type for exactly: {sorted(VALID_WORK_TYPES)}"
        )
    for work_type, phases in phases_by_work_type.items():
        if not phases:
            raise ConfigurationError(f"phase_rules.json has no phases for work type '{work_type}'")
        weight_total = 0.0
        for phase in phases:
            if not phase.get("key") or not phase.get("label"):
                raise ConfigurationError(f"A phase for '{work_type}' is missing a key or label")
            weight = phase.get("weight")
            if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
                raise ConfigurationError(f"Phase '{phase.get('key')}' for '{work_type}' has an invalid weight")
            weight_total += weight
        if abs(weight_total - 1.0) > 1e-6:
            raise ConfigurationError(
                f"Phase weights for work type '{work_type}' must total 1.00, got {weight_total:.4f}"
            )

    ai_phases = data.get("ai_phases")
    if not ai_phases:
        raise ConfigurationError("phase_rules.json is missing ai_phases")
    for phase in ai_phases:
        if not phase.get("key") or not phase.get("label"):
            raise ConfigurationError("An AI phase is missing a key or label")

    ai_weight = data.get("ai_phase_weight_of_core_duration")
    if not isinstance(ai_weight, (int, float)) or isinstance(ai_weight, bool) or not 0 <= ai_weight <= 1:
        raise ConfigurationError("phase_rules.json's ai_phase_weight_of_core_duration must be between 0 and 1")


def validate_resource_rules(data: dict) -> None:
    hours_per_sprint = data.get("hours_per_sprint")
    if not isinstance(hours_per_sprint, (int, float)) or isinstance(hours_per_sprint, bool) or hours_per_sprint <= 0:
        raise ConfigurationError("resource_rules.json's hours_per_sprint must be a positive number")

    roles_by_work_type = data.get("roles_by_work_type")
    if not roles_by_work_type or set(roles_by_work_type.keys()) != set(VALID_WORK_TYPES):
        raise ConfigurationError(
            f"resource_rules.json must define roles_by_work_type for exactly: {sorted(VALID_WORK_TYPES)}"
        )
    for work_type, phases in roles_by_work_type.items():
        if not phases:
            raise ConfigurationError(f"resource_rules.json has no phase/role entries for '{work_type}'")
        for phase_key, roles in phases.items():
            if not roles:
                raise ConfigurationError(f"Phase '{phase_key}' for '{work_type}' has no roles defined")
            for role_entry in roles:
                if not role_entry.get("role"):
                    raise ConfigurationError(f"A role entry in phase '{phase_key}' for '{work_type}' has no role name")
                validate_allocation_percent(role_entry.get("allocation_percent"))

    for key in (
        "ai_activity_to_phase_role",
        "ai_help_fallback_activities",
        "ai_baseline_activities",
        "ai_independent_evaluation_activities",
    ):
        if not data.get(key):
            raise ConfigurationError(f"resource_rules.json is missing {key}")


def validate_role_combinations(data: dict) -> None:
    if not data.get("compatible_combinations"):
        raise ConfigurationError("role_combinations.json is missing compatible_combinations")
    if not data.get("incompatible_combinations"):
        raise ConfigurationError("role_combinations.json is missing incompatible_combinations")
    for combo in data["incompatible_combinations"]:
        if not combo.get("roles") or len(combo["roles"]) < 2 or not combo.get("reason"):
            raise ConfigurationError("Each incompatible combination needs at least two roles and a reason")


def validate_rate_card(records: list[dict]) -> None:
    if not records:
        raise ConfigurationError("rate_card.csv has no rows")

    seen_roles: set[str] = set()
    for record in records:
        role = (record.get("Role") or "").strip()
        if not role:
            raise ConfigurationError("rate_card.csv has a row with no Role")
        if role in seen_roles:
            raise ConfigurationError(f"rate_card.csv has a duplicate Role: '{role}'")
        seen_roles.add(role)

        raw_rate = record.get("Default Hourly Rate")
        try:
            rate = float(raw_rate)
        except (TypeError, ValueError):
            raise ConfigurationError(
                f"rate_card.csv has a non-numeric Default Hourly Rate for '{role}': {raw_rate!r}"
            ) from None
        if rate < 0:
            raise ConfigurationError(f"rate_card.csv has a negative Default Hourly Rate for '{role}'")

        if not (record.get("Currency") or "").strip():
            raise ConfigurationError(f"rate_card.csv is missing a Currency for '{role}'")

        active_raw = str(record.get("Active", "")).strip().lower()
        if active_raw not in ("yes", "no", "true", "false", "1", "0"):
            raise ConfigurationError(f"rate_card.csv has an unrecognized Active value for '{role}': {active_raw!r}")


def validate_scenario_rate_value(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Scenario rate must be numeric")
    if math.isnan(value):
        raise ValueError("Scenario rate must be numeric")
    if value < 0:
        raise ValueError(f"Scenario rate cannot be negative, got {value}")
    return float(value)


def validate_override_reason(scenario_rate: float, default_rate: float, override_reason: Optional[str]) -> None:
    if scenario_rate != default_rate and not (override_reason or "").strip():
        raise ValueError(
            "An override reason is required when the scenario rate differs from the "
            "configured default rate"
        )
