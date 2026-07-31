import pytest

from src.config import ConfigurationError
from src.phase_planner import (
    build_ai_phases,
    build_core_phases,
    build_phase_plan,
    load_phase_rules,
    resolve_ai_activities,
)
from src.validators import validate_phase_rules


def test_load_phase_rules_weights_sum_to_one_per_work_type():
    rules = load_phase_rules()
    for work_type, phases in rules["phases_by_work_type"].items():
        total = sum(p["weight"] for p in phases)
        assert total == pytest.approx(1.0), f"{work_type} weights do not sum to 1.0"


def test_build_core_phases_duration_derived_from_total_sprints():
    phases = build_core_phases("enhancement", total_sprints=4)
    total = sum(p.duration_sprints for p in phases)
    assert total == pytest.approx(4.0)
    assert all(not p.is_ai_workstream for p in phases)


def test_build_core_phases_scales_with_different_total_sprints():
    phases_small = build_core_phases("enhancement", total_sprints=2)
    phases_large = build_core_phases("enhancement", total_sprints=8)
    dev_small = next(p for p in phases_small if p.phase_key == "development").duration_sprints
    dev_large = next(p for p in phases_large if p.phase_key == "development").duration_sprints
    assert dev_large == pytest.approx(dev_small * 4)


def test_build_phase_plan_ai_off_has_no_ai_phases():
    phases = build_phase_plan("enhancement", total_sprints=4, ai_included="No")
    assert not any(p.is_ai_workstream for p in phases)


def test_build_phase_plan_ai_on_adds_ai_phases():
    phases = build_phase_plan(
        "enhancement", total_sprints=4, ai_included="Yes", ai_help=["Generate content"]
    )
    ai_phases = [p for p in phases if p.is_ai_workstream]
    assert ai_phases
    core_phases = [p for p in phases if not p.is_ai_workstream]
    assert core_phases  # core phases still present alongside AI ones


def test_build_phase_plan_ai_not_sure_also_adds_ai_phases():
    phases = build_phase_plan(
        "enhancement", total_sprints=4, ai_included="Not sure", ai_help=["Not yet known"]
    )
    assert any(p.is_ai_workstream for p in phases)


def test_resolve_ai_activities_uses_detailed_activities_when_provided():
    activities = resolve_ai_activities(["Data preparation"], [])
    assert "Data preparation" in activities
    assert "AI use-case definition" in activities  # baseline always included


def test_resolve_ai_activities_falls_back_to_simplified_help_when_detailed_empty():
    activities = resolve_ai_activities([], ["Generate content"])
    assert "Prompt and instruction design" in activities
    assert "Responsible AI review and approval" in activities  # baseline


def test_build_ai_phases_empty_when_no_activities():
    assert build_ai_phases([], total_sprints=4) == []


def test_validate_phase_rules_rejects_bad_weight_total():
    bad_rules = {
        "phases_by_work_type": {
            "new_project": [{"key": "a", "label": "A", "weight": 0.5}],
            "enhancement": [{"key": "a", "label": "A", "weight": 1.0}],
            "production_support": [{"key": "a", "label": "A", "weight": 1.0}],
        },
        "ai_phases": [{"key": "x", "label": "X"}],
        "ai_phase_weight_of_core_duration": 0.25,
    }
    with pytest.raises(ConfigurationError):
        validate_phase_rules(bad_rules)
