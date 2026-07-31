import pytest

from src.models import ComplexityDimensionAnswer, ContractFitResult, EstimateRequest, SizingResult
from src.complexity_engine import calculate_weighted_complexity
from src.sow_outline_engine import (
    MANDATORY_DISCLAIMER,
    build_preliminary_sow_outline,
    evaluate_pre_generation_gate,
    render_outline_as_markdown,
    render_outline_as_text,
)


def _complexity_answers(**scores):
    defaults = {
        "functional": 3, "technical": 3, "integration": 3, "data": 3,
        "testing": 3, "dependency": 3, "operational_risk": 3,
    }
    defaults.update(scores)
    return [
        ComplexityDimensionAnswer(dimension_key=k, selected_label="Moderate", score=v)
        for k, v in defaults.items()
    ]


def _base_request(**overrides) -> EstimateRequest:
    kwargs = dict(
        estimate_name="Test Estimate",
        work_type="enhancement",
        estimate_type="enhancement",
        business_objective="Reduce manual processing time",
        system_context="Existing system",
        audience="Internal users",
        contract_term="Six months",
        scope_checklist={"ui_frontend": "included", "documentation": "unknown"},
        items_needing_review=["documentation"],
        assumptions=["Existing source code and environments are accessible."],
        complexity_answers=_complexity_answers(),
    )
    kwargs.update(overrides)
    return EstimateRequest(**kwargs)


def _sizing() -> SizingResult:
    return SizingResult(
        relative_job_size=5, tshirt_size="M", min_sprints=2, max_sprints=4,
        discovery_review_required=False, decomposition_required=False,
    )


def _contract_fit(status="Fits") -> ContractFitResult:
    return ContractFitResult(
        estimated_months=3.0, contract_months=6.0, fit_ratio=0.5,
        status=status, status_explanation="Explanation text.",
    )


# --- Gate: blocking conditions ---------------------------------------------


def test_gate_blocks_on_empty_business_objective():
    request = _base_request(business_objective="   ")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Generation Blocked"
    assert any("Business objective" in reason for reason in result.blocking_reasons)


def test_gate_blocks_on_missing_scope():
    request = _base_request(scope_checklist={}, items_needing_review=[])
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Generation Blocked"
    assert any("scope" in reason.lower() for reason in result.blocking_reasons)


def test_gate_blocks_on_narrow_guarantee_phrase():
    request = _base_request(business_objective="We will provide guaranteed delivery of this project")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Generation Blocked"
    assert any("guaranteed delivery" in reason for reason in result.blocking_reasons)


def test_gate_blocks_on_ssn_like_value():
    request = _base_request(known_dependencies="Contact John at 123-45-6789 for access")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Generation Blocked"


def test_gate_blocks_on_credential_like_text():
    request = _base_request(other_context="Use password: hunter2 to log in")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Generation Blocked"


# --- Gate: narrow vs. broad keyword behavior (correction 3) ----------------


def test_gate_does_not_block_on_single_ambiguous_word():
    # A single generic word like "guarantee" alone must not always block.
    request = _base_request(other_context="The customer wants a guarantee process documented")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Human Review Required"
    assert any("guarantee" in warning.lower() for warning in result.warnings)


def test_gate_does_not_block_on_word_password_alone():
    request = _base_request(other_context="Discuss password reset workflow with the team")
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Human Review Required"


# --- Gate: always Human Review Required when not blocked (correction 1) ---


def test_gate_never_returns_ready_for_ai_drafting():
    request = _base_request(
        scope_checklist={"ui_frontend": "included"},
        items_needing_review=[],
        known_dependencies="All dependencies documented",
        audience="Internal users",
    )
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Human Review Required"
    assert result.status != "Ready for AI Drafting"


def test_gate_warns_on_unknown_items_without_blocking():
    request = _base_request()  # has one unknown item by default
    result = evaluate_pre_generation_gate(request, "Fits")
    assert result.status == "Human Review Required"
    assert any("Unknown" in warning for warning in result.warnings)


def test_gate_warns_on_at_risk_contract_fit():
    request = _base_request(items_needing_review=[], scope_checklist={"ui_frontend": "included"})
    result = evaluate_pre_generation_gate(request, "At Risk")
    assert any("At Risk" in warning for warning in result.warnings)


# --- Outline: structure and content ----------------------------------------


def _build_outline(request, unknown_scope_labels=None):
    complexity = calculate_weighted_complexity(
        {a.dimension_key: a.score for a in request.complexity_answers}
    )
    sizing = _sizing()
    contract_fit = _contract_fit()
    display_names = {
        "functional": "Functional complexity", "technical": "Technical complexity",
        "integration": "Integration complexity", "data": "Data complexity",
        "testing": "Testing complexity", "dependency": "Dependency complexity",
        "operational_risk": "Operational risk",
    }
    return build_preliminary_sow_outline(
        estimate_request=request,
        complexity_result=complexity,
        sizing_result=sizing,
        contract_fit_result=contract_fit,
        work_type_label="Enhancement",
        included_scope_labels=["User interface or frontend"],
        excluded_scope_labels=["Reporting or analytics"],
        unknown_scope_labels=["Documentation"] if unknown_scope_labels is None else unknown_scope_labels,
        dimension_display_names=display_names,
        generated_at="2026-07-31",
    )


def test_outline_has_all_21_sections_in_order():
    request = _base_request(
        ai_included="Yes",
        ai_help=["Generate content"],
        ai_data="Internal business information",
        ai_human_review="Always",
    )
    sections = _build_outline(request)
    assert len(sections) == 21
    expected_titles = [
        "Document status", "Estimate name", "Work type", "Business objective",
        "Background or context", "Preliminary scope", "Included scope", "Excluded scope",
        "Items requiring confirmation", "Systems involved", "Preliminary delivery range",
        "Preliminary estimated duration", "Contract-fit status", "AI considerations",
        "Proposed assumptions -- review and confirm", "Dependencies",
        "Risks and open questions", "Customer responsibilities", "Vendor responsibilities",
        "Next steps", "Mandatory disclaimer",
    ]
    assert [title for title, _ in sections] == expected_titles


def test_outline_omits_ai_section_when_ai_off():
    request = _base_request(ai_included="No")
    sections = _build_outline(request)
    assert len(sections) == 20
    assert "AI considerations" not in [title for title, _ in sections]


def test_outline_includes_ai_section_when_ai_on():
    request = _base_request(
        ai_included="Yes", ai_help=["Generate content"], ai_data="Internal business information",
        ai_human_review="Always",
    )
    sections = _build_outline(request)
    ai_section = dict(sections)["AI considerations"]
    assert "Generate content" in ai_section
    assert "Internal business information" in ai_section


def test_outline_contains_exact_disclaimer_once():
    request = _base_request()
    sections = _build_outline(request)
    disclaimer_sections = [body for title, body in sections if title == "Mandatory disclaimer"]
    assert disclaimer_sections == [MANDATORY_DISCLAIMER]
    markdown = render_outline_as_markdown(sections, request.estimate_name, "2026-07-31")
    assert markdown.count(MANDATORY_DISCLAIMER) == 1
    text = render_outline_as_text(sections, request.estimate_name, "2026-07-31")
    assert text.count(MANDATORY_DISCLAIMER) == 1


def test_outline_never_contains_pricing_preview_indicators():
    request = _base_request()
    sections = _build_outline(request)
    combined = " ".join(body for _, body in sections).lower()
    for forbidden in ("$", "margin", "contingency", "blended rate", "hourly rate", "gross profit"):
        assert forbidden not in combined


def test_included_and_excluded_scope_remain_separate():
    request = _base_request()
    sections = _build_outline(request)
    section_map = dict(sections)
    assert "User interface or frontend" in section_map["Included scope"]
    assert "User interface or frontend" not in section_map["Excluded scope"]
    assert "Reporting or analytics" in section_map["Excluded scope"]
    assert "Reporting or analytics" not in section_map["Included scope"]


# --- Correction 2: unknown items cannot disappear from the outline --------


def test_unknown_items_always_appear_and_cannot_be_concealed():
    request = _base_request()
    sections = _build_outline(request)
    section_map = dict(sections)
    assert "Documentation" in section_map["Items requiring confirmation"]
    # Also surfaced as an open item/risk -- reinforced, never hidden.
    assert any("Unknown" in section_map["Risks and open questions"] for _ in [None])


def test_no_unknown_items_shows_explicit_confirmation_not_omission():
    request = _base_request(items_needing_review=[])
    sections = _build_outline(request, unknown_scope_labels=[])
    section_map = dict(sections)
    assert "confirmed status" in section_map["Items requiring confirmation"]
