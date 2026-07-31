"""Preliminary SOW outline generation (EAP.M1.UI2).

This is explicitly NOT the governed MVP.M6 SOW capability
(sow_generator.py per ENGINE-RESPONSIBILITIES.md section 11). It produces a
deterministic, template-based DRAFT outline from already-captured MVP.M1
data only -- no phase plan, no resource plan, no rate card, no pricing, no
final dates, no legal terms.

Owns: the lightweight Responsible-AI-style pre-generation gate
(`evaluate_pre_generation_gate`) and the outline builder/renderers. This is
NOT the full `responsible_ai_validator.py` described in
ENGINE-RESPONSIBILITIES.md section 12 (that component's post-generation
validation and auditable result structure remain a MVP.M6 concern) -- it is
a narrower, milestone-scoped gate that reuses the same three status names
for consistency, per explicit instruction.

"Ready for AI Drafting" is intentionally unreachable at this milestone: one
of the governed non-blocking triggers ("timeline is preliminary") is true
of every estimate produced before MVP.M6, so this gate only ever returns
"Human Review Required" or "Generation Blocked" (EAP.M1.UI2-D1 correction
1). The full three-status Literal is preserved on the model for when
MVP.M6 introduces a governed final duration.
"""
from __future__ import annotations

import re

from src.config import ConfigurationError, load_json_config
from src.models import (
    ComplexityResult,
    ContractFitResult,
    EstimateRequest,
    ResponsibleAIGateResult,
    SizingResult,
)

MANDATORY_DISCLAIMER = (
    "Draft for business and legal review. This language is not binding until "
    "approved and incorporated into an executed agreement."
)

PRELIMINARY_STATEMENT = (
    "Preliminary outline generated before resource planning, governed pricing, "
    "support definition, and final commercial approval."
)

GATE_SUCCESS_MESSAGE = (
    "Preliminary outline generated successfully. Human review is required before "
    "this content may be used externally."
)

# Narrow phrases only -- a single ambiguous word like "guarantee" or
# "password" must not block by itself (EAP.M1.UI2-D1 correction 3). This is
# a simple keyword/pattern safeguard for this milestone, not a real
# confidential-data or compliance classifier.
_BLOCKING_PHRASES = (
    "guaranteed delivery",
    "100% uptime",
    "zero defects",
    "no downtime",
    "guaranteed ai accuracy",
    "guaranteed accuracy",
)
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDENTIAL_PATTERNS = (
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"api[_ ]?key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"secret\s*[:=]\s*\S+", re.IGNORECASE),
)
_REVIEW_TERMS = ("guarantee", "guaranteed", "promise", "password", "confidential", "secret", "credentials")


def _scan_for_risky_language(text: str) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    warnings: list[str] = []
    if not text:
        return blocking, warnings

    lowered = text.lower()
    for phrase in _BLOCKING_PHRASES:
        if phrase in lowered:
            blocking.append(f'Unsupported commitment language detected: "{phrase}".')

    if _SSN_PATTERN.search(text):
        blocking.append("A Social-Security-Number-like value was detected in the provided text.")

    for pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(text):
            blocking.append("Text resembling an actual credential or secret was detected.")
            break

    if not blocking:
        for term in _REVIEW_TERMS:
            if term in lowered:
                warnings.append(
                    f'The word "{term}" appears in the provided text -- confirm no unsupported '
                    "commitment or sensitive content is implied before external use."
                )
                break

    return blocking, warnings


def evaluate_pre_generation_gate(
    estimate_request: EstimateRequest, contract_fit_status: str
) -> ResponsibleAIGateResult:
    """Lightweight pre-generation check. Only ever returns "Human Review
    Required" or "Generation Blocked" at this milestone -- see module
    docstring for why "Ready for AI Drafting" is not reachable here.
    """
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if not estimate_request.business_objective or not estimate_request.business_objective.strip():
        blocking_reasons.append("Business objective is empty.")
    if not estimate_request.work_type:
        blocking_reasons.append("Work type is missing.")
    if not estimate_request.scope_checklist:
        blocking_reasons.append("Required scope has not been captured.")

    combined_text = " ".join(
        text
        for text in (
            estimate_request.business_objective,
            estimate_request.description,
            estimate_request.other_context,
            estimate_request.known_assumptions,
            estimate_request.known_dependencies,
        )
        if text
    )
    text_blocking, text_warnings = _scan_for_risky_language(combined_text)
    blocking_reasons.extend(text_blocking)
    warnings.extend(text_warnings)

    if blocking_reasons:
        return ResponsibleAIGateResult(
            status="Generation Blocked", blocking_reasons=blocking_reasons, warnings=warnings
        )

    # Unknown scope items always contribute to Human Review Required --
    # never a reason to conceal them (EAP.M1.UI2-D1 correction 2). They are
    # always rendered in the outline's own "Items requiring confirmation"
    # section regardless of this warning.
    if estimate_request.items_needing_review:
        warnings.append(
            f"{len(estimate_request.items_needing_review)} scope item(s) remain Unknown and "
            "require review."
        )
    if estimate_request.ai_included != "No" and (
        not estimate_request.ai_data or estimate_request.ai_data == "Sensitive or regulated information"
    ):
        warnings.append("AI data sensitivity is not fully resolved.")
    if estimate_request.audience == "Not yet known":
        warnings.append("Customer responsibilities cannot be fully confirmed until the audience is known.")
    if not estimate_request.known_dependencies:
        warnings.append("Dependencies have not been documented and remain unresolved.")
    if contract_fit_status in ("At Risk", "Does Not Fit"):
        warnings.append(f"Contract fit is {contract_fit_status}.")
    warnings.append(
        "This is a preliminary timeline -- no governed final duration exists until later "
        "milestones."
    )

    return ResponsibleAIGateResult(status="Human Review Required", blocking_reasons=[], warnings=warnings)


def _load_outline_templates() -> dict:
    templates = load_json_config("sow_outline_templates.json")
    for key in ("customer_responsibilities", "vendor_responsibilities", "next_steps"):
        if not templates.get(key):
            raise ConfigurationError(f"SOW outline templates are missing {key}")
    return templates


def _bullet_list(items: list[str], empty_message: str) -> str:
    if not items:
        return empty_message
    return "\n".join(f"- {item}" for item in items)


def build_preliminary_sow_outline(
    estimate_request: EstimateRequest,
    complexity_result: ComplexityResult,
    sizing_result: SizingResult,
    contract_fit_result: ContractFitResult,
    work_type_label: str,
    included_scope_labels: list[str],
    excluded_scope_labels: list[str],
    unknown_scope_labels: list[str],
    dimension_display_names: dict[str, str],
    generated_at: str,
) -> list[tuple[str, str]]:
    """Build the 21-section preliminary outline. Callers must only invoke
    this after `evaluate_pre_generation_gate` returns a non-blocked result.

    Uses only already-captured/validated MVP.M1 data -- never the
    illustrative pricing-preview values, which this module never imports.
    """
    templates = _load_outline_templates()

    background_parts = [
        text
        for text in (
            estimate_request.other_context,
            estimate_request.description,
            estimate_request.customer_or_business_unit,
        )
        if text
    ]
    background = " ".join(background_parts) or "No additional background provided yet."

    ai_enabled = estimate_request.ai_included != "No"

    risks: list[str] = []
    if unknown_scope_labels:
        risks.append(f"{len(unknown_scope_labels)} scope item(s) remain Unknown (see section 9).")
    if contract_fit_result.status in ("At Risk", "Does Not Fit"):
        risks.append(f"Contract fit is {contract_fit_result.status}: {contract_fit_result.status_explanation}")
    if contract_fit_result.status == "Estimate Definition Required":
        risks.append("Scope is not yet sufficiently defined to responsibly estimate a delivery duration.")
    if complexity_result.higher_scoring_dimensions:
        higher = ", ".join(dimension_display_names[key] for key in complexity_result.higher_scoring_dimensions)
        risks.append(f"Higher-scoring complexity dimensions may carry more risk: {higher}.")
    if sizing_result.discovery_review_required:
        risks.append("This work is large enough to warrant a discovery or phasing review.")
    if sizing_result.decomposition_required:
        risks.append("This work should be decomposed into smaller estimates before commercial commitment.")
    if not estimate_request.known_dependencies:
        risks.append("No dependencies have been documented yet -- open question for review.")

    sections: list[tuple[str, str]] = []
    sections.append(("Document status", "Preliminary Draft. " + GATE_SUCCESS_MESSAGE))
    sections.append(("Estimate name", estimate_request.estimate_name))
    sections.append(("Work type", work_type_label))
    sections.append(("Business objective", estimate_request.business_objective))
    sections.append(("Background or context", background))
    sections.append(
        (
            "Preliminary scope",
            f"System context: {estimate_request.system_context}. Audience: {estimate_request.audience}. "
            "The scope below reflects current selections and may change as open items are resolved.",
        )
    )
    sections.append(("Included scope", _bullet_list(included_scope_labels, "None marked included yet.")))
    sections.append(("Excluded scope", _bullet_list(excluded_scope_labels, "None marked excluded yet.")))
    sections.append(
        (
            "Items requiring confirmation",
            _bullet_list(unknown_scope_labels, "None -- all reviewed scope items have a confirmed status."),
        )
    )
    sections.append(
        (
            "Systems involved",
            _bullet_list(estimate_request.systems_involved_list, "Not yet specified.")
        )
    )
    sections.append(
        (
            "Preliminary delivery range",
            f"T-shirt size: {sizing_result.tshirt_size}. Sprint range: {sizing_result.min_sprints:g}-"
            f"{sizing_result.max_sprints:g} sprints. This is a planning-level range, not a committed scope.",
        )
    )
    if contract_fit_result.estimated_months is not None:
        duration_text = f"Approximately {contract_fit_result.estimated_months:.1f} months (preliminary planning estimate only)."
    else:
        duration_text = "Not yet calculable -- additional scope definition is required."
    sections.append(("Preliminary estimated duration", duration_text))
    sections.append(
        ("Contract-fit status", f"{contract_fit_result.status}. {contract_fit_result.status_explanation}")
    )
    if ai_enabled:
        ai_lines = [
            f"AI included: {estimate_request.ai_included}.",
            f"Intended AI help: {', '.join(estimate_request.ai_help) or 'Not yet specified.'}",
            f"Data type: {estimate_request.ai_data or 'Not yet specified.'}",
            f"Human review of AI output: {estimate_request.ai_human_review or 'Not yet decided.'}",
        ]
        sections.append(("AI considerations", "\n".join(ai_lines)))
    sections.append(
        (
            "Proposed assumptions -- review and confirm",
            _bullet_list(estimate_request.assumptions, "No assumptions generated yet."),
        )
    )
    sections.append(
        ("Dependencies", estimate_request.known_dependencies or "No dependencies documented yet -- confirm during review.")
    )
    sections.append(("Risks and open questions", _bullet_list(risks, "No material risks or open questions identified yet.")))
    sections.append(("Customer responsibilities", _bullet_list(templates["customer_responsibilities"], "None documented.")))
    sections.append(("Vendor responsibilities", _bullet_list(templates["vendor_responsibilities"], "None documented.")))
    sections.append(("Next steps", _bullet_list(templates["next_steps"], "None documented.")))
    sections.append(("Mandatory disclaimer", MANDATORY_DISCLAIMER))

    return sections


def render_outline_as_markdown(sections: list[tuple[str, str]], estimate_name: str, generated_at: str) -> str:
    lines = [
        f"# Preliminary SOW Outline: {estimate_name}",
        "",
        f"_Generated: {generated_at}_",
        "",
        f"**{PRELIMINARY_STATEMENT}**",
        "",
    ]
    for index, (title, body) in enumerate(sections, start=1):
        lines.append(f"## {index}. {title}")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def render_outline_as_text(sections: list[tuple[str, str]], estimate_name: str, generated_at: str) -> str:
    lines = [
        f"PRELIMINARY SOW OUTLINE: {estimate_name}",
        f"Generated: {generated_at}",
        "",
        PRELIMINARY_STATEMENT,
        "",
    ]
    for index, (title, body) in enumerate(sections, start=1):
        lines.append(f"{index}. {title}")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)
