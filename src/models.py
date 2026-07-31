"""Structured data models shared across engines. No business calculations here.

The two preview-only models at the bottom of this file
(`RoleRatePreviewRow`, `RoleRatePreviewSet`) are additive UI scaffolding for
a future pricing interaction (MVP.M3/M4). They are never consumed by
`EstimateRequest`, any engine, or any customer-facing output in this
milestone -- see docs/architecture.md for the boundary.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EstimateType = Literal[
    "new_project",
    "enhancement",
    "production_support",
    "maintenance_support",
    "enhancement_support",
    "implementation_plus_support",
    "discovery_or_assessment",
]

WorkType = Literal["new_project", "enhancement", "production_support"]

ContractTerm = Literal["Quarterly", "Six months", "Nine months", "Annual", "Custom"]

AICapability = Literal[
    "No",
    "Yes - AI-assisted feature",
    "Yes - Generative AI or LLM",
    "Yes - Predictive ML",
    "Yes - AI platform or integration",
    "Yes - Other AI capability",
]

AIIncluded = Literal["No", "Yes", "Not sure"]

SystemContext = Literal["New system", "Existing system", "Not yet known"]

Audience = Literal["Internal users", "Customers or external users", "Both", "Not yet known"]

ScopeItemStatus = Literal["included", "not_included", "unknown"]

ContractFitStatus = Literal["Fits", "At Risk", "Does Not Fit", "Estimate Definition Required"]

# Full three-status model preserved for future MVP.M6 use (RESPONSIBLE-AI.md
# section 1). MVP.M1.UI2's deterministic preliminary-outline gate only ever
# returns "Human Review Required" or "Generation Blocked" -- see
# sow_outline_engine.py for why "Ready for AI Drafting" is intentionally
# unreachable at this milestone.
ResponsibleAIStatus = Literal["Ready for AI Drafting", "Human Review Required", "Generation Blocked"]

COMPLEXITY_DIMENSION_KEYS = (
    "functional",
    "technical",
    "integration",
    "data",
    "testing",
    "dependency",
    "operational_risk",
)


class ComplexityDimensionAnswer(BaseModel):
    """One dimension's plain-language answer plus its internal score."""

    dimension_key: str
    selected_label: str
    score: int = Field(ge=0, le=5)

    @field_validator("dimension_key")
    @classmethod
    def _known_dimension(cls, value: str) -> str:
        if value not in COMPLEXITY_DIMENSION_KEYS:
            raise ValueError(f"Unknown complexity dimension: {value}")
        return value


class EstimateRequest(BaseModel):
    """Structured, human-reviewed input to the deterministic engines.

    Assembled from wizard session state only at the review/results boundary,
    once every required field has already passed per-step validation.

    `work_type` is the 3-option self-service classification (EAP.M1.UI1);
    `estimate_type` is retained for internal/engine compatibility with the
    original 7-value taxonomy and is derived 1:1 from `work_type` for the
    three types this UI exposes.
    """

    estimate_name: str
    work_type: WorkType
    estimate_type: EstimateType
    business_objective: str
    system_context: SystemContext
    audience: Audience

    # Optional in this milestone's model: no longer collected as a dedicated
    # required field (EAP.M1.UI1 removes the long-form project description
    # and free-typed scope from the primary flow). `description` and
    # `included_scope` are populated from optional notes / the structured
    # scope checklist respectively, rather than typed directly.
    description: Optional[str] = None
    included_scope: Optional[str] = None

    known_exclusions: Optional[str] = None
    systems_involved: Optional[str] = None
    systems_involved_list: list[str] = Field(default_factory=list)
    integration_context: Optional[str] = None
    data_considerations: Optional[str] = None
    expected_users: Optional[str] = None
    requested_deadline: Optional[str] = None
    customer_or_business_unit: Optional[str] = None
    other_context: Optional[str] = None
    known_assumptions: Optional[str] = None
    known_dependencies: Optional[str] = None

    # Structured scope checklist: item key -> included / not_included / unknown.
    scope_checklist: dict[str, ScopeItemStatus] = Field(default_factory=dict)

    # Generated, user-editable assumptions and review flags (EAP.M1.UI1).
    assumptions: list[str] = Field(default_factory=list)
    items_needing_review: list[str] = Field(default_factory=list)

    contract_term: ContractTerm
    contract_custom_months: Optional[float] = None

    # New simplified primary-flow AI intake (EAP.M1.UI1).
    ai_included: AIIncluded = "No"
    ai_help: list[str] = Field(default_factory=list)
    ai_data: Optional[str] = None
    ai_human_review: Optional[str] = None

    # Retained for internal/engine compatibility with ESTIMATE-TYPES.md
    # section 11's governed 6-value field; derived from `ai_included`
    # rather than collected directly in the primary flow. Detailed
    # sub-typing and free-text intake move to the optional advanced section.
    ai_capability: AICapability = "No"
    ai_capability_type: Optional[str] = None
    ai_business_objective: Optional[str] = None
    ai_workstream_activities: list[str] = Field(default_factory=list)
    ai_assumptions: Optional[str] = None
    ai_exclusions: Optional[str] = None

    complexity_answers: list[ComplexityDimensionAnswer] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ai_fields_cleared_when_off(self) -> "EstimateRequest":
        if self.ai_included == "No":
            if self.ai_capability != "No" or any(
                [
                    self.ai_help,
                    self.ai_data,
                    self.ai_human_review,
                    self.ai_capability_type,
                    self.ai_business_objective,
                    self.ai_workstream_activities,
                    self.ai_assumptions,
                    self.ai_exclusions,
                ]
            ):
                raise ValueError("AI-specific fields must be empty when AI included is No")
        return self

    @model_validator(mode="after")
    def _complexity_answers_complete(self) -> "EstimateRequest":
        if not self.complexity_answers:
            return self
        keys = [answer.dimension_key for answer in self.complexity_answers]
        if len(keys) != len(COMPLEXITY_DIMENSION_KEYS) or set(keys) != set(COMPLEXITY_DIMENSION_KEYS):
            raise ValueError(
                "complexity_answers must contain exactly one answer for each of the "
                f"{len(COMPLEXITY_DIMENSION_KEYS)} approved dimensions"
            )
        return self


class ComplexityResult(BaseModel):
    """Deterministic weighted-complexity output. See complexity_engine.py."""

    dimension_scores: dict[str, int]
    dimension_weights: dict[str, float]
    dimension_contributions: dict[str, float]
    weighted_complexity_score: float
    weighted_complexity_display: str
    higher_scoring_dimensions: list[str]


class SizingResult(BaseModel):
    """Deterministic sizing output. See sizing_engine.py."""

    relative_job_size: int
    tshirt_size: str
    min_sprints: float
    max_sprints: float
    discovery_review_required: bool
    decomposition_required: bool


class ContractFitResult(BaseModel):
    """Deterministic contract-fit output. See contract_fit.py."""

    estimated_months: Optional[float]
    contract_months: Optional[float]
    fit_ratio: Optional[float]
    status: ContractFitStatus
    status_explanation: str


StaffingModel = Literal["Lean", "Balanced", "Specialized", "Customer-defined"]


class PhasePlanEntry(BaseModel):
    """One phase's duration. See phase_planner.py. No role or hour data here."""

    phase_key: str
    phase_label: str
    duration_sprints: float = Field(ge=0)
    is_ai_workstream: bool = False


class ResourcePlanRow(BaseModel):
    """Required role effort for one phase. See resource_planner.py.

    `assigned_to` reflects the selected staffing model's combined-assignment
    view only -- it never changes `allocation_percent`, `person_sprints`, or
    `estimated_hours`, which are the required effort and stay constant
    regardless of staffing model (PHASE-RESOURCE-PLANNING.md section 5).
    """

    phase_key: str
    phase_label: str
    role: str
    allocation_percent: float = Field(ge=0)
    person_sprints: float
    estimated_hours: float
    is_ai_workstream: bool = False
    assigned_to: Optional[str] = None


class ResourcePlanResult(BaseModel):
    """Deterministic phase/resource plan output. See phase_planner.py and
    resource_planner.py. No rates, cost, or price anywhere in this model.
    """

    phases: list[PhasePlanEntry]
    rows: list[ResourcePlanRow]
    staffing_model: StaffingModel
    warnings: list[str] = Field(default_factory=list)
    total_hours_by_role: dict[str, float] = Field(default_factory=dict)
    total_hours_by_phase: dict[str, float] = Field(default_factory=dict)
    total_hours_core_it: float = 0.0
    total_hours_ai_workstream: float = 0.0


class ResponsibleAIGateResult(BaseModel):
    """Result of the lightweight pre-generation gate in sow_outline_engine.py.

    Domain-specific generation control per RESPONSIBLE-AI.md -- never a
    PROTOCOL.md triage status.
    """

    status: ResponsibleAIStatus
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RoleRatePreviewRow(BaseModel):
    """Illustrative, non-authoritative scaffolding for a future pricing
    interaction (MVP.M3/M4). Never consumed by EstimateRequest, any engine,
    or any customer-facing output in this milestone -- see
    docs/architecture.md for the boundary and PRICING-RULES.md sections
    10-13 for the governed shape this scaffolding mirrors.
    """

    role: str
    actual_hours: float = Field(ge=0)
    configured_default_rate: float = Field(ge=0)
    scenario_rate: float = Field(ge=0)
    override_reason: Optional[str] = None

    @model_validator(mode="after")
    def _override_reason_required_when_rate_differs(self) -> "RoleRatePreviewRow":
        if self.scenario_rate != self.configured_default_rate and not self.override_reason:
            raise ValueError(
                "An override reason is required when the scenario rate differs from the "
                "configured default rate"
            )
        return self

    @property
    def estimated_cost(self) -> float:
        return self.actual_hours * self.scenario_rate


class RoleRatePreviewSet(BaseModel):
    """A collection of illustrative preview rows, plus the read-only,
    informational blended rate. Illustrative-only -- see RoleRatePreviewRow.
    """

    rows: list[RoleRatePreviewRow] = Field(default_factory=list)

    @property
    def total_hours(self) -> float:
        return sum(row.actual_hours for row in self.rows)

    @property
    def total_cost(self) -> float:
        return sum(row.estimated_cost for row in self.rows)

    @property
    def blended_rate(self) -> Optional[float]:
        if self.total_hours <= 0:
            return None
        return self.total_cost / self.total_hours
