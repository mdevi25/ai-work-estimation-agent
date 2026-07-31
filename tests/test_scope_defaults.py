import pytest

from src.config import ConfigurationError
from src.scope_defaults import (
    categories_for_work_type,
    compute_scope_confirmation_percentage,
    compute_scope_counts,
    default_selections_for_work_type,
    included_item_keys,
    not_included_item_keys,
    systems_involved_options,
    unknown_item_keys,
)
from src.validators import validate_scope_checklist_schema


def test_categories_for_work_type_filters_production_support_only_items():
    new_project_categories = {c["key"] for c in categories_for_work_type("new_project")}
    production_support_categories = {c["key"] for c in categories_for_work_type("production_support")}
    assert "production_support_activities" not in new_project_categories
    assert "production_support_activities" in production_support_categories


def test_default_selections_cover_every_applicable_item():
    selections = default_selections_for_work_type("enhancement")
    assert selections  # non-empty
    assert all(status in ("included", "not_included", "unknown") for status in selections.values())


def test_systems_involved_options_present():
    options = systems_involved_options()
    assert "Web application" in options
    assert "Not yet known" in options


def test_compute_scope_counts():
    selections = {"a": "included", "b": "included", "c": "not_included", "d": "unknown"}
    counts = compute_scope_counts(selections)
    assert counts == {"included": 2, "not_included": 1, "unknown": 1}


def test_compute_scope_confirmation_percentage():
    selections = {"a": "included", "b": "not_included", "c": "unknown", "d": "unknown"}
    assert compute_scope_confirmation_percentage(selections) == 50.0


def test_compute_scope_confirmation_percentage_empty():
    assert compute_scope_confirmation_percentage({}) == 0.0


def test_item_key_helpers():
    selections = {"a": "included", "b": "not_included", "c": "unknown"}
    assert unknown_item_keys(selections) == ["c"]
    assert included_item_keys(selections) == ["a"]
    assert not_included_item_keys(selections) == ["b"]


def test_validate_scope_checklist_schema_rejects_missing_categories():
    with pytest.raises(ConfigurationError):
        validate_scope_checklist_schema({})


def test_validate_scope_checklist_schema_rejects_bad_default_status():
    bad_config = {
        "categories": [
            {
                "key": "cat",
                "label": "Cat",
                "applies_to_work_types": ["new_project"],
                "items": [
                    {"key": "item", "label": "Item", "defaults": {"new_project": "maybe"}}
                ],
            }
        ],
        "systems_involved_options": ["Web application"],
    }
    with pytest.raises(ConfigurationError):
        validate_scope_checklist_schema(bad_config)


def test_validate_scope_checklist_schema_rejects_missing_systems_options():
    bad_config = {
        "categories": [
            {
                "key": "cat",
                "label": "Cat",
                "applies_to_work_types": ["new_project"],
                "items": [
                    {"key": "item", "label": "Item", "defaults": {"new_project": "included"}}
                ],
            }
        ],
    }
    with pytest.raises(ConfigurationError):
        validate_scope_checklist_schema(bad_config)
