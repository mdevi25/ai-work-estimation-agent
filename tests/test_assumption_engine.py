import pytest

from src.assumption_engine import generate_assumptions, load_assumption_templates
from src.config import ConfigurationError


def test_load_assumption_templates_has_all_work_types():
    templates = load_assumption_templates()
    for work_type in ("new_project", "enhancement", "production_support"):
        assert templates["by_work_type"][work_type]


def test_generate_assumptions_includes_work_type_baseline():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
    )
    assert "Existing source code and environments are accessible." in assumptions


def test_generate_assumptions_includes_unknown_scope_items():
    assumptions = generate_assumptions(
        work_type="new_project",
        unknown_item_labels=["Database or data model"],
        systems_involved=[],
        ai_included="No",
    )
    assert any("Database or data model" in a for a in assumptions)


def test_generate_assumptions_includes_systems_involved():
    assumptions = generate_assumptions(
        work_type="new_project",
        unknown_item_labels=[],
        systems_involved=["Cloud platform"],
        ai_included="No",
    )
    assert any("Cloud platform" in a for a in assumptions)


def test_generate_assumptions_excludes_not_yet_known_and_other_systems():
    assumptions = generate_assumptions(
        work_type="new_project",
        unknown_item_labels=[],
        systems_involved=["Not yet known", "Other"],
        ai_included="No",
    )
    assert not any("Not yet known" in a for a in assumptions)
    assert not any(a.startswith("Work involving Other") for a in assumptions)


def test_generate_assumptions_no_ai_content_when_ai_off():
    assumptions = generate_assumptions(
        work_type="production_support",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
    )
    assert not any("AI output" in a or "Model-provider" in a for a in assumptions)


def test_generate_assumptions_includes_ai_content_and_human_review_when_on():
    assumptions = generate_assumptions(
        work_type="production_support",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="Yes",
        ai_human_review="Always",
    )
    assert any("Model-provider charges" in a for a in assumptions)
    assert "AI output will always be reviewed by a person before use." in assumptions


def test_generate_assumptions_deduplicates_preserving_order():
    assumptions = generate_assumptions(
        work_type="new_project",
        unknown_item_labels=["Same item", "Same item"],
        systems_involved=[],
        ai_included="No",
    )
    unknown_related = [a for a in assumptions if "Same item" in a]
    assert len(unknown_related) == 1


def test_generate_assumptions_includes_excluded_scope_items():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
        excluded_item_labels=["Reporting or analytics"],
    )
    assert any("Reporting or analytics" in a and "excluded" in a for a in assumptions)


def test_generate_assumptions_includes_system_context():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
        system_context="Existing system",
    )
    assert "Existing system behavior and interfaces are assumed stable unless a change is identified in scope." in assumptions


def test_generate_assumptions_includes_contract_term():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
        contract_term="Six months",
    )
    assert any("Six months" in a and "planning and commercial boundary" in a for a in assumptions)


def test_generate_assumptions_includes_known_dependencies():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
        known_dependencies="Vendor API access must be granted",
    )
    assert any("Vendor API access must be granted" in a for a in assumptions)


def test_generate_assumptions_includes_ai_data_type_when_ai_on():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="Yes",
        ai_data="Customer information",
    )
    assert any("Customer information" in a for a in assumptions)


def test_generate_assumptions_no_context_content_when_not_provided():
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=[],
        systems_involved=[],
        ai_included="No",
    )
    assert not any("planning and commercial boundary" in a for a in assumptions)
    assert not any("must be resolved before or during delivery" in a for a in assumptions)


def test_generate_assumptions_new_context_params_do_not_duplicate_existing():
    # Calling with every new parameter populated must not repeat any
    # assumption that a different driver already produced verbatim.
    assumptions = generate_assumptions(
        work_type="enhancement",
        unknown_item_labels=["Database or data model"],
        systems_involved=["Cloud platform"],
        ai_included="Yes",
        ai_human_review="Always",
        excluded_item_labels=["Reporting or analytics"],
        system_context="Existing system",
        ai_data="Internal business information",
        contract_term="Quarterly",
        known_dependencies="Third-party vendor sign-off",
    )
    assert len(assumptions) == len(set(assumptions))
