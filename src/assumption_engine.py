"""Deterministic, template-based assumption generation.

Owns: combining the assumption templates in data/assumption_templates.json
with the user's actual selections (work type, scope, systems, AI) into a
concrete, editable assumption list. Never invents assumptions unrelated to
what the user actually selected, and never calls an AI model -- this is
plain template substitution, not generation in the AI sense.

Generated assumptions are suggestions, not approved facts, until the user
confirms them at the Review step (EAP.M1.UI1 correction 6).
"""
from __future__ import annotations

from typing import Optional

from src.config import ConfigurationError, load_json_config

_REQUIRED_WORK_TYPES = ("new_project", "enhancement", "production_support")


def load_assumption_templates() -> dict:
    templates = load_json_config("assumption_templates.json")
    by_work_type = templates.get("by_work_type", {})
    if any(work_type not in by_work_type for work_type in _REQUIRED_WORK_TYPES):
        raise ConfigurationError(
            "Assumption templates must define by_work_type entries for all three work types"
        )
    if not templates.get("ai_enabled"):
        raise ConfigurationError("Assumption templates are missing the ai_enabled list")
    if not templates.get("human_review_templates"):
        raise ConfigurationError("Assumption templates are missing human_review_templates")
    if not templates.get("unknown_scope_item_template"):
        raise ConfigurationError("Assumption templates are missing unknown_scope_item_template")
    if not templates.get("systems_involved_template"):
        raise ConfigurationError("Assumption templates are missing systems_involved_template")
    if not templates.get("excluded_scope_item_template"):
        raise ConfigurationError("Assumption templates are missing excluded_scope_item_template")
    if not templates.get("system_context_templates"):
        raise ConfigurationError("Assumption templates are missing system_context_templates")
    if not templates.get("ai_data_template"):
        raise ConfigurationError("Assumption templates are missing ai_data_template")
    if not templates.get("contract_term_template"):
        raise ConfigurationError("Assumption templates are missing contract_term_template")
    if not templates.get("dependency_provided_template"):
        raise ConfigurationError("Assumption templates are missing dependency_provided_template")
    return templates


def generate_assumptions(
    work_type: str,
    unknown_item_labels: list[str],
    systems_involved: list[str],
    ai_included: str,
    ai_human_review: Optional[str] = None,
    *,
    excluded_item_labels: Optional[list[str]] = None,
    system_context: Optional[str] = None,
    ai_data: Optional[str] = None,
    contract_term: Optional[str] = None,
    known_dependencies: Optional[str] = None,
) -> list[str]:
    """Generate a suggested, editable assumption list from actual selections.

    Order: work-type assumptions, then scope-driven (unknown, then
    excluded), then systems-driven, then context-driven (system context,
    delivery term, known dependencies), then AI-driven. De-duplicated
    while preserving first occurrence -- never mutates a previously
    returned/approved list, this always builds a fresh one from current
    inputs (EAP.M1.UI2-D1 correction 5).
    """
    templates = load_assumption_templates()
    generated: list[str] = list(templates["by_work_type"].get(work_type, []))

    unknown_template = templates["unknown_scope_item_template"]
    for label in unknown_item_labels:
        generated.append(unknown_template.format(item=label))

    excluded_template = templates["excluded_scope_item_template"]
    for label in excluded_item_labels or []:
        generated.append(excluded_template.format(item=label))

    systems_template = templates["systems_involved_template"]
    excluded_system_labels = {"Not yet known", "Other"}
    for system in systems_involved:
        if system in excluded_system_labels:
            continue
        generated.append(systems_template.format(system=system))

    if system_context:
        context_text = templates["system_context_templates"].get(system_context)
        if context_text:
            generated.append(context_text)

    if contract_term:
        generated.append(templates["contract_term_template"].format(term=contract_term))

    if known_dependencies:
        generated.append(templates["dependency_provided_template"].format(dependency=known_dependencies))

    if ai_included != "No":
        generated.extend(templates["ai_enabled"])
        if ai_data:
            generated.append(templates["ai_data_template"].format(data_type=ai_data))
        if ai_human_review:
            review_text = templates["human_review_templates"].get(ai_human_review)
            if review_text:
                generated.append(review_text)

    seen: set[str] = set()
    deduplicated: list[str] = []
    for assumption in generated:
        if assumption not in seen:
            seen.add(assumption)
            deduplicated.append(assumption)
    return deduplicated
