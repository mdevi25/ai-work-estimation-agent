"""Suggested scope-checklist defaults by work type, and scope-confirmation math.

Owns: loading and validating the scope-checklist configuration, selecting
applicable categories/items for a work type, applying suggested defaults,
and computing the scope-confirmation percentage and included/not-included/
unknown counts shown in the wizard and the persistent sidebar.

Must not: feed into or alter the complexity, sizing, or contract-fit
engines -- scope-checklist answers are descriptive intake, not a
calculation input, per EAP.M1.UI1.
"""
from __future__ import annotations

from src.config import load_json_config
from src.validators import validate_scope_checklist_schema


def load_scope_checklist_config() -> dict:
    config = load_json_config("scope_checklist_items.json")
    validate_scope_checklist_schema(config)
    return config


def categories_for_work_type(work_type: str) -> list[dict]:
    config = load_scope_checklist_config()
    return [
        category
        for category in config["categories"]
        if work_type in category["applies_to_work_types"]
    ]


def default_selections_for_work_type(work_type: str) -> dict[str, str]:
    """Every applicable item's suggested default status for this work type."""
    selections: dict[str, str] = {}
    for category in categories_for_work_type(work_type):
        for item in category["items"]:
            selections[item["key"]] = item["defaults"][work_type]
    return selections


def systems_involved_options() -> list[str]:
    return load_scope_checklist_config()["systems_involved_options"]


def compute_scope_counts(selections: dict[str, str]) -> dict[str, int]:
    counts = {"included": 0, "not_included": 0, "unknown": 0}
    for status in selections.values():
        counts[status] = counts.get(status, 0) + 1
    return counts


def compute_scope_confirmation_percentage(selections: dict[str, str]) -> float:
    """Share of applicable items resolved (included or not included), not left unknown."""
    if not selections:
        return 0.0
    counts = compute_scope_counts(selections)
    resolved = counts["included"] + counts["not_included"]
    return round(100.0 * resolved / len(selections), 1)


def unknown_item_keys(selections: dict[str, str]) -> list[str]:
    return [key for key, status in selections.items() if status == "unknown"]


def included_item_keys(selections: dict[str, str]) -> list[str]:
    return [key for key, status in selections.items() if status == "included"]


def not_included_item_keys(selections: dict[str, str]) -> list[str]:
    return [key for key, status in selections.items() if status == "not_included"]
