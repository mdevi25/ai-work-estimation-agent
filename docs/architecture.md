# Architecture: AI Work Estimation and Pricing Assistant

## 1. System purpose

Converts a business request into a deterministic, explainable planning
estimate: complexity assessment, Fibonacci-style Relative Job Size,
T-shirt size, sprint range, phase-based resource effort, baseline
delivery cost, optional contingency and margin, proposed customer
price, support estimates, and draft SOW content. The deterministic
calculation engine is authoritative; AI is a future, optional,
replaceable adapter for intake and explanation only.

## 2. Users and stakeholders

Internal delivery/estimation staff are the primary users (input
requests, review and approve estimates, override values). The project
owner is accountable for the deployed application and its business
rules. Customers receive only the reviewed, human-approved
customer-facing outputs (summaries, SOW drafts) — they do not use the
application directly.

## 3. Scope

This document covers what is implemented through **MVP.M1 —
Estimation foundation** (remediated by **EAP.M1.UI1** and
**EAP.M1.UI2**), **MVP.M2 — Phase and Resource Planning**, **MVP.M3 —
Baseline Cost and Role Rate Card**, and **MVP.M4 — Commercial Scenario
Pricing and Approval**: a guided, self-service 5-step Streamlit wizard
(`app.py`) with a persistent left-side panel, that captures estimate
intake, a suggested/correctable scope checklist, and complexity
answers, feeding the three unchanged deterministic estimation engines
(`src/complexity_engine.py`, `src/sizing_engine.py`,
`src/contract_fit.py`) that compute weighted complexity, Relative Job
Size / T-shirt size / sprint range, and contract-duration fit from
governed JSON configuration under `data/`. It adds a differentiated
action-navigation row on the results screen, a deterministic
**preliminary SOW outline** generator (`src/sow_outline_engine.py` —
explicitly not the governed MVP.M6 SOW capability), a deterministic
**phase and resource planning** pair (`src/phase_planner.py`,
`src/resource_planner.py`, unchanged since MVP.M2) that derives an
editable phase/role/hours plan from the governed sizing result, a
deterministic **baseline cost** engine (`src/pricing_engine.py`,
MVP.M3) that converts those role hours into baseline delivery cost
using a configured rate card (`data/rate_card.csv`), and now a
deterministic **commercial scenario pricing and approval** extension
to the same engine (MVP.M4) that converts baseline delivery cost into
four governed commercial scenarios (Recommended/Competitive/
Conservative/Custom) using contingency and target margin only —
customer price, gross profit, achieved margin, and equivalent markup,
each independently editable, comparable, and requiring an explicit,
auditable human approval before any one scenario may be treated as
selected. No discount, rounding, or management-adjustment lever exists
in this milestone. It establishes the separation of UI, engines,
configuration, and data flow required by architecture-governance
Gate 1.

## 4. Out-of-scope items

No support estimation, final/customer-approved SOW generation, or AI
logic exists yet — all deferred to MVP.M5 through MVP.M7 and **not
implemented in this repository**. Database, authentication, Docker,
paid APIs, and Excel/PowerPoint export are out of scope for early
milestones per `CLAUDE.md` and are not present here. MVP.M4 explicitly
does not implement: discount percentage/amount, coupon or promotional
pricing, a strategic-loss exception pathway, additional scenario types
beyond the four governed ones, or unlimited scenario creation. The
optional AI-capability intake field captured by the wizard (Step 2/4)
drives an optional AI *workstream* in the phase/resource plan (MVP.M2),
baseline cost (MVP.M3), and now a Human-Review trigger on every
commercial scenario (MVP.M4), but still carries no support pricing,
recurring fees, final legal terms, or payment schedule anywhere — that
remains MVP.M5/M6 scope regardless of AI selection.

## 5. Current project stage

**Prototype** (MVP.M1-M4 complete). Complexity of this document
matches that stage: MVP.M1-M4's engines and wizard are documented in
full below; MVP.M5 onward are named only where relevant to note what
is deliberately deferred, not described as implemented.

## 6. Functional requirements

The application must: guide a nontechnical business user through a
5-step wizard (work type, quick facts, scope checklist, complexity and
AI, review and estimate) completable in roughly 5-10 minutes, using
selections rather than free-typed text wherever possible; classify the
work type (3 simplified options, internally compatible with the
original 7-value estimate-type taxonomy); apply and let the user
correct a suggested scope checklist by work type; score seven
complexity dimensions from plain-language answers; compute a weighted
complexity score at full precision; map that score to a Relative Job
Size, T-shirt size, and sprint range; compute contract-duration fit;
generate editable, meaningful assumptions from actual selections; show
a persistent sidebar with step status, the current estimate, a
non-authoritative preliminary running estimate, and warning status;
and show a calculation-transparency breakdown that reconciles exactly
with the displayed governed result. Full functional requirements for
later milestones remain defined in `CLAUDE.md` and the
`work-estimation` skill's reference files, to be implemented when each
milestone begins.

## 7. Non-functional requirements

None formally load-bearing yet at this single-milestone stage. The
product is intended to run as a single-user Streamlit Community Cloud
deployment with no database, so throughput/availability requirements
are expected to remain minimal; this will be revisited if that
assumption changes. Wizard state lives only in `st.session_state` for
the duration of one browser session — nothing persists across
sessions or restarts in MVP.M1.

## 8. Architecture overview

A single Streamlit application (`app.py`) renders a 5-step wizard plus
a persistent sidebar, and calls into three deterministic engines under
`src/` (`complexity_engine.py`, `sizing_engine.py`, `contract_fit.py`,
unchanged since MVP.M1), which read governed business rules from JSON
configuration files under `data/` (no database). Shared structured
models live in `src/models.py` (Pydantic), shared validation in
`src/validators.py`, and shared JSON/CSV loading with controlled-error
handling in `src/config.py`. Three additional non-authoritative
UI-support modules were added by EAP.M1.UI1: `src/scope_defaults.py`
(scope-checklist defaults and scope-confirmation math),
`src/assumption_engine.py` (deterministic, template-based assumption
generation), and `src/running_estimate_preview.py` (the sidebar's
"Preliminary" partial-complexity preview). None of these three touch
or duplicate the authoritative engines' formulas. MVP.M2 added
`src/phase_planner.py` and `src/resource_planner.py` (deterministic
phase/resource-effort engines, no rates or cost). MVP.M3 added
`src/pricing_engine.py` (deterministic baseline-cost engine reading
`data/rate_card.csv`, a new CSV-configuration source alongside the
existing JSON files). MVP.M4 extended the same `src/pricing_engine.py`
(per `ENGINE-RESPONSIBILITIES.md` section 8's single-engine ownership
of the whole pricing sequence) with the contingency-through-approval
functions, reading a new JSON file, `data/commercial_pricing_defaults.json`.
This shape was chosen over a spreadsheet-first or
database-backed design because the project's explicit scope excludes a
database and requires configurable-but-versioned business rules —
CSV/JSON in source control gives that without added infrastructure
cost. `pages/` remains empty; the wizard is implemented as one page
with internal step-state rather than Streamlit's native multi-page
routing, since a linear, stateful Back/Continue/Review flow with a
persistent sidebar is materially simpler to guarantee that way than
across independently-routed pages.

## 9. Component responsibilities

- **`app.py`** — Streamlit UI only. Renders the 5-step wizard and
  persistent sidebar, calls the engines below with a structured
  `EstimateRequest`, and displays their results, including the
  resource-plan, baseline-cost, and commercial-pricing sections.
  Contains no complexity, sizing, contract-fit, resource-planning, or
  pricing formulas itself.
- **`src/models.py`** — structured Pydantic models only
  (`EstimateRequest`, `ComplexityDimensionAnswer`, `ComplexityResult`,
  `SizingResult`, `ContractFitResult`, the MVP.M2 resource-planning
  models, the MVP.M3 pricing models `RateCardEntry`, `RoleCostRow`,
  `BaselineCostResult`, and the MVP.M4 `PricingScenario` model). No
  business calculations beyond trivial, clearly-scoped field defaults.
- **`src/validators.py`** — reusable validation (score ranges, weight
  totals, sizing-band schema and boundary coverage, contract-duration
  positivity, AI-field validity, scope-checklist schema, required-field
  detection, rate-card schema, scenario-rate numeric/non-negative
  validity, override-reason requirement, and the MVP.M4 contingency/
  target-margin/baseline-cost bounds plus the standalone commercial-loss
  detector) shared by the engines and the UI.
- **`src/config.py`** — generic JSON and CSV configuration loading.
  Raises a controlled `ConfigurationError` on any missing or malformed
  file; no engine falls back to a silently hard-coded value.
- **`src/complexity_engine.py`** — unchanged since MVP.M1. Loads and
  validates complexity weights and questions, computes the weighted
  complexity score at full precision plus its two-decimal display
  value, and identifies higher-scoring dimensions. Does not map
  Relative Job Size, T-shirt size, or sprint range.
- **`src/sizing_engine.py`** — unchanged since MVP.M1. Loads and
  validates sizing bands, and maps the unrounded weighted complexity
  score to Relative Job Size, T-shirt size, sprint range, and the
  size-13/size-20 warnings. Does not calculate cost or price.
- **`src/contract_fit.py`** — unchanged since MVP.M1. Loads and
  validates contract terms, converts the maximum estimated sprint
  count to months, and computes contract-fit status. Models no PTO,
  holiday, meeting, or capacity-related deductions.
- **`src/scope_defaults.py`** — loads/validates the scope-checklist
  configuration, selects applicable categories by work type, applies
  suggested defaults, and computes scope-confirmation percentage and
  included/not-included/unknown counts. Never feeds the complexity,
  sizing, or contract-fit engines.
- **`src/assumption_engine.py`** — combines assumption templates with
  actual user selections (work type, unknown scope, systems, AI) into
  a concrete, editable list. Plain template substitution, not AI
  generation.
- **`src/running_estimate_preview.py`** — computes a non-authoritative,
  clearly-labeled "Preliminary" partial-complexity score (weights
  re-normalized among only the answered dimensions, never treating an
  unanswered dimension as zero) for the sidebar, reusing the
  unmodified `sizing_engine.map_to_size` for its preliminary size. Not
  used anywhere in the final Step 5 calculation, which calls only the
  authoritative `complexity_engine.calculate_weighted_complexity` with
  all seven validated answers.
- **`src/sow_outline_engine.py`** — owns two things: (1)
  `evaluate_pre_generation_gate`, a lightweight, milestone-scoped
  Responsible-AI-style check (`Human Review Required` or `Generation
  Blocked` only at this milestone — see §19) and (2)
  `build_preliminary_sow_outline`, a deterministic, template-based
  21-section draft builder that reads only already-captured/validated
  `EstimateRequest`/engine-result data, plus two primitive-only signals:
  `baseline_costing_in_progress` (MVP.M3, boolean) and
  `approved_commercial_scenario_name` (MVP.M4, a plain string or
  `None`) that each append one fixed status-only sentence. Never
  imports `RateCardEntry`, `RoleCostRow`, `BaselineCostResult`, or
  `PricingScenario` — structurally cannot leak pricing or commercial
  values into the outline (verified directly by an AST-based test).
  Not the governed `sow_generator.py` described in
  `ENGINE-RESPONSIBILITIES.md` section 11 (MVP.M6).
- **`src/phase_planner.py`** — selects phases by work type and derives
  each phase's duration in sprints from the governed sizing result
  (`SizingResult.max_sprints`, weighted per `data/phase_rules.json`),
  plus the optional AI workstream's phases (only when AI is enabled,
  driven by the effective AI activity set). Does not assign roles,
  calculate hours, or calculate cost.
- **`src/resource_planner.py`** — required roles by phase, the
  `person_sprints`/`estimated_hours` formulas, staffing-model combined-
  assignment views (Lean/Balanced/Specialized/Customer-defined —
  required effort per role is identical across all four), and resource
  warnings (over-allocation, incompatible combinations, missing
  deployment/stabilization coverage, missing independent AI evaluation
  coverage). Does not apply rates or calculate cost or price.
- **`src/pricing_engine.py`** — MVP.M3 section: loads and validates
  `data/rate_card.csv` (`load_rate_card`); computes each role's cost
  (`total_estimated_hours * scenario_rate`), baseline delivery cost
  (sum of role costs), and the read-only blended hourly rate (`None`,
  never a fabricated `0.00`, when total hours are zero)
  (`build_baseline_cost`); manages session-only scenario-rate/
  override-reason state (`reset_role_rate`, `reset_all_rates`,
  `reconcile_rate_state`); and computes the pricing-readiness status
  (`Calculation Blocked` > `Human Review Required` > `Ready for
  Baseline Review`, in that precedence). MVP.M4 section (additive, no
  changes to the M3 functions above): loads/validates
  `data/commercial_pricing_defaults.json` (`load_commercial_pricing_defaults`);
  builds/resets the four governed scenarios (`build_default_scenarios`,
  `reset_scenario_to_default`); computes contingency through equivalent
  markup at full precision (`calculate_scenario_financials`); derives
  commercial-readiness status and the independent approval-status axis
  (`compute_commercial_readiness`, `compute_approval_status`);
  orchestrates one scenario's full recalculation against the live
  baseline (`recalculate_scenario`); detects baseline drift and
  invalidates stale approval (`detect_baseline_drift`,
  `refresh_scenario_staleness`); maps M2 delivery warnings to the two
  governed EAP.M4 warning levels (`derive_delivery_risk_warnings`); and
  gates an approval attempt (`approve_scenario`). No discount, rounding,
  or management-adjustment lever, and no support pricing or final SOW
  logic, anywhere in this module. Both the rate card and the commercial
  defaults are read-only from the application's perspective; nothing
  is ever written back to either file.
- **`data/`** — governed JSON/CSV configuration only: complexity
  weights, the 7-dimension × 6-level answer scale, sizing bands,
  contract terms, the original 7-value estimate-type catalog (internal
  compatibility), the 3-value work-type catalog, the scope-checklist
  catalog and defaults, assumption templates, the simplified AI-intake
  option catalog, phase rules (duration weights per work type plus the
  4 AI-workstream phases), resource rules (required roles/allocation
  per phase, `hours_per_sprint`, the AI-activity-to-phase/role
  mapping), role-combination rules (compatible and incompatible
  combinations), the configured rate card (`rate_card.csv` —
  illustrative/fictional demonstration rates only), the four governed
  commercial scenario defaults plus maximum contingency and material-
  difference thresholds (`commercial_pricing_defaults.json` —
  explicitly flagged prototype commercial percentages), the preliminary
  SOW outline's responsibility/next-steps templates, and the original
  AI workstream activity catalog (retained for the advanced/optional AI
  section). No customer data, commercial transaction data, real rates,
  or secrets.
- **`tests/`** — one test module per engine/validator/helper plus
  `test_app_wizard.py` (Streamlit `AppTest`-driven UI, sidebar, and
  transparency checks) and the original bootstrap smoke test.
- No external systems, APIs, or connectors exist yet. A future AI
  provider adapter is planned no earlier than MVP.M7 and will be
  documented here (§11) when introduced.

## 10. Data flow

**Primary (governed) flow:** user input entered across the wizard's
five steps → held in `st.session_state` as plain values (never as a
Pydantic model mid-flow, so engines never touch Streamlit session
state directly) → at the Review step, assembled into one structured
`EstimateRequest` (`src/models.py`) → passed to
`complexity_engine.calculate_weighted_complexity` → its unrounded
score passed to `sizing_engine.map_to_size` → the sizing result passed
to `contract_fit.calculate_contract_fit` alongside the user's delivery
term → all three structured results (`ComplexityResult`,
`SizingResult`, `ContractFitResult`) returned to `app.py` for display,
including the calculation-transparency breakdown.

**Sidebar preview flow (non-authoritative):** as each complexity
dimension is answered, the partial answers are passed to
`running_estimate_preview.compute_preliminary_view`, which
re-normalizes weights among answered dimensions only and reuses
`sizing_engine.map_to_size` for a preliminary size — displayed in the
sidebar labeled "Preliminary," replaced by the real, governed result
once Step 5's "Confirm and generate estimate" runs the primary flow
above.

**Scope and assumptions flow:** work-type selection →
`scope_defaults.default_selections_for_work_type` seeds the Step 3
checklist → user corrections held in `st.session_state` →
`scope_defaults.compute_scope_confirmation_percentage` feeds the
sidebar → at Review, unknown items, excluded items, systems, system
context, AI data type, delivery term, and known dependencies pass to
`assumption_engine.generate_assumptions`, producing an editable
suggestion list the user confirms before generation.

**Preliminary SOW outline flow (EAP.M1.UI2, non-authoritative content,
governed gate):** after the primary flow produces a result, selecting
"Generate Preliminary SOW Outline" passes the same `EstimateRequest`
and its three structured results to
`sow_outline_engine.evaluate_pre_generation_gate` → if not `Generation
Blocked`, the same data passes to
`sow_outline_engine.build_preliminary_sow_outline`, which reads
`data/sow_outline_templates.json` for its responsibility/next-steps
content and returns the ordered sections (21, or 22 when a resource
plan exists) → `app.py` renders them with a "Preliminary Draft" status
badge and offers a Markdown/plain-text download. This flow never reads
`RoleRatePreviewRow`/`RoleRatePreviewSet` or the illustrative
pricing-preview section's session state.

**Phase and resource planning flow (MVP.M2, no rates or cost):** after
the primary flow produces a result, selecting "Build Resource Plan"
passes the work type, `SizingResult.max_sprints`, AI selections, and
the chosen staffing model to `phase_planner.build_phase_plan` (core
phases always; AI phases only when AI is enabled, sized from the same
governed sizing result) → the resulting phases pass to
`resource_planner.build_resource_plan`, which computes the required-
effort table (`person_sprints`/`estimated_hours` per phase/role,
constant regardless of staffing model), applies the selected staffing
model's combined-assignment view, and computes warnings → `app.py`
renders an editable table (`st.data_editor`) where duration and
allocation edits are recalculated immediately by re-deriving
`ResourcePlanRow`s and re-running `compute_warnings`/`compute_totals`
live. The resulting `ResourcePlanResult` optionally flows into the
preliminary SOW outline (above) as additional preliminary planning
information — phases, roles, and hours only, never rates or cost
(`ResourcePlanResult` has no such fields to leak).

**Baseline cost flow (MVP.M3):** once a `ResourcePlanResult` exists,
`app.py` reconciles session-only scenario-rate/override-reason state
against the plan's current role set
(`pricing_engine.reconcile_rate_state`), then passes the plan, that
state, the AI/staffing-model/unresolved-items signals to
`pricing_engine.build_baseline_cost`, which loads
`data/rate_card.csv` (`load_rate_card`) and returns a
`BaselineCostResult` (per-role cost rows, baseline delivery cost,
blended hourly rate, pricing-readiness status and reasons, commercial
warnings) → `app.py` renders an editable table (`st.data_editor`,
scenario rate and override reason only — hours and the configured
default rate are read-only) where edits are read back into session
state and immediately recalculated by re-running
`build_baseline_cost`. Only a boolean (`baseline_cost_result is not
None`) passes into the preliminary SOW outline flow, appending one
fixed status sentence — never an amount, rate, or dollar figure
(`sow_outline_engine.py` has no dependency on the pricing models to
leak).

**Commercial pricing flow (MVP.M4):** once a `BaselineCostResult`
exists, `app.py` ensures the four governed `PricingScenario` objects
exist (`pricing_engine.build_default_scenarios`, calculated immediately
on first creation), then on every render compares each scenario's
stored baseline snapshot to the live `BaselineCostResult`
(`pricing_engine.refresh_scenario_staleness` /
`detect_baseline_drift`) — a mismatch immediately clears approval and
flags the scenario `needs_recalculation`, without altering its
contingency/margin/name/description inputs or silently recomputing its
stored dollar fields. Editing a scenario's contingency or target margin
recalculates that one scenario immediately
(`pricing_engine.recalculate_scenario`, which calls
`calculate_scenario_financials` → `compute_commercial_readiness` →
`compute_approval_status` in sequence) without touching any other
scenario's values. Approving a scenario runs a separate gate
(`pricing_engine.approve_scenario`) checked only at that moment —
requires a non-empty approval note and, only when the corresponding
warning list is non-empty, an explicit delivery-risk and/or commercial-
risk acknowledgement checkbox; a commercial-loss condition
(`customer_price < risk_adjusted_delivery_cost`, detected by
`validators.detect_commercial_loss`) blocks unconditionally with no
override. `app.py`'s approve-button click handler re-verifies
`can_approve` itself rather than trusting the widget's `disabled=`
attribute alone (a real gap found and fixed during implementation — see
§19). Only the approved scenario's name (a plain string, never a
`PricingScenario` object) passes into the preliminary SOW outline flow,
appending one fixed sentence ("Commercial terms are subject to final
review.") — never an amount, rate, cost, margin, or markup.

No sensitive data, PII, or credentials are collected — inputs are
structured selections, short business-objective text, and complexity
answers only. Nothing is persisted beyond the browser session: no
database, no file writes of user input, no estimate history. System of
record for the governed mappings themselves is the versioned `data/`
configuration files. Internal/customer-facing view separation
(`CLAUDE.md` §3) does not yet apply operationally, since this
milestone has no customer-facing output — Relative Job Size and the
weighted complexity score are shown only inside an internal-facing
wizard, never in a customer-distributed document.

## 11. AI/model flow

Not present. No AI/model integration exists in this repository.
`CLAUDE.md` explicitly defers any AI API integration to MVP.M7, after
deterministic calculations and Responsible AI controls are validated.
When introduced, the model provider must be isolated behind a
replaceable service interface rather than coupled to engine logic —
this will be documented here at that gate.

## 12. Security and privacy

No secrets exist in this repository. `.gitignore` excludes
`.streamlit/secrets.toml` and virtual-environment/cache directories.
No authentication or database exists (explicitly out of scope for
early milestones per `CLAUDE.md`). No PII/PHI is collected at this
stage — the application accepts only business-request text and
structured planning inputs in later milestones.

## 13. Human review points

No AI-generated output exists in this milestone (the AI-intake fields
only capture intake text about AI inside the *customer's* project — no
AI is invoked). Engine output (`ComplexityResult`, `SizingResult`,
`ContractFitResult`) is **advisory**, per `standards/PRINCIPLES.md` §7:
the wizard's own Review step (Step 5) is the human-review point,
requiring the user to confirm all captured inputs — including
editing/confirming the generated assumptions, which are explicitly not
treated as approved facts until confirmed — with missing-field
validation blocking progress, before the deterministic calculation
runs.

The preliminary SOW outline (EAP.M1.UI2) adds a second, explicit human
review point: `sow_outline_engine.evaluate_pre_generation_gate` always
resolves to **Human Review Required** whenever it does not block
generation entirely (see §19 for why "Ready for AI Drafting" is
unreachable here), and the rendered outline states plainly that human
review is required before external use — it is never presented as
approved or final. There is still no customer-facing *final* summary
or SOW content, so the distribution-approval review point defined in
`CLAUDE.md` §6–7 and `RESPONSIBLE-AI.md` does not yet fully apply; it
will be completed here when MVP.M6 introduces the governed, final SOW
capability and a governed final duration/commercial position to
support "Ready for AI Drafting."

The baseline-cost section (MVP.M3) adds a third human review signal:
`pricing_engine.build_baseline_cost`'s pricing-readiness status
(`Ready for Baseline Review` / `Human Review Required` / `Calculation
Blocked`) surfaces every condition that should stop a baseline cost
from being treated as final — missing/invalid rates, override reasons,
below-default commercial risk, AI workstream presence, Customer-defined
staffing, carried-forward delivery-risk warnings, and unresolved scope
items — governed by a fixed precedence (Blocked beats Human Review,
which beats Ready) rather than any single condition silently winning.
This is still not a commercial-approval workflow; no gross profit,
margin, or customer price exists yet to approve (MVP.M4).

The commercial-pricing section (MVP.M4) adds the first real,
auditable **approval workflow** in this repository: each scenario
carries an independent commercial-readiness axis (calculation
cleanliness) and approval-status axis (human decision state — Draft /
Review Required / Approved / Approval Blocked), and
`pricing_engine.approve_scenario` requires an explicit human-entered
approval note plus explicit acknowledgement of every applicable
delivery-risk and commercial-risk warning before a scenario may become
Approved — never inferred from price, never automatic, and never
overridable by a note or acknowledgement when a commercial-loss
condition exists. Exactly one scenario may be Approved at a time;
replacing it is a separate explicit button click that preserves the
previous scenario's inputs and calculations rather than deleting them.
This is still not the governed final commercial approval that will
feed `ApprovedEstimate` in MVP.M6 — no customer-facing output exists
yet to approve toward.

A **mandatory UI review checkpoint** now also applies at the process
level (not a code review point, a milestone-acceptance gate): every
MVP.M milestone stops after automated validation and local Streamlit
startup, for an explicit human browser-based review and acceptance,
before the next milestone begins. See `decision_log.md`'s EAP.M1.UI1
entry.

## 14. Failure handling

The placeholder app has no external dependencies to fail. Future
engines will read local configuration files only (no network calls at
the deterministic-engine layer), so failure handling at this stage is
limited to standard Python exceptions during file/parse errors — to be
elaborated when `src/` and `data/` gain real content.

## 15. Observability

None implemented — appropriate for a single-user, zero-cost prototype
with no deployed traffic yet. Streamlit Community Cloud's built-in logs
are the only current visibility mechanism once deployed.

## 16. Cost considerations

Zero-cost by design: Streamlit Community Cloud (free tier), no paid
APIs, no database, no metered services. `requirements.txt` pins only
open-source packages (`streamlit`, `pandas`, `pydantic`, `pytest`).

## 17. Deployment model

Not yet deployed. Planned target is Streamlit Community Cloud from this
private GitHub repository (`ai-work-estimation-agent`), per
`decision_log.md`. This repository currently has no commits and has not
been connected to Streamlit Community Cloud. No Dev/UAT/Prod separation
is defined yet; all current work happens directly in this repository's
working tree.

## 18. Assumptions

- Python 3.12 is the target interpreter (installed this session;
  the machine also has Python 3.13 installed but that version is not
  used for this project, per `CLAUDE.md`'s "Python 3.11 or 3.12" scope).
- A single Streamlit app with local CSV/JSON configuration will remain
  sufficient through at least MVP.M6 — if usage or data-volume needs
  change this, the "no database" decision would need revisiting.
- No concurrent multi-user access is assumed at this stage.

## 19. Decisions and trade-offs

- **CSV/JSON configuration vs. a database:** chosen to avoid
  infrastructure cost and keep business rules versioned in git,
  reviewable via pull request. Trade-off: no concurrent-write safety
  and no query capability — acceptable given the single-user, low-scale
  scope through MVP.M6.
- **Deterministic engine before AI:** chosen so every calculation is
  explainable and testable before any AI-assisted intake is
  introduced, rather than building AI-first and retrofitting
  determinism. Trade-off: manual structured input is required until
  MVP.M7.
- **`complexity_engine.py` computes the score only; `sizing_engine.py`
  owns all RJS/T-shirt/sprint/warning mapping:** `ENGINE-RESPONSIBILITIES.md`
  §3 and §4 have overlapping wording on which engine maps Relative Job
  Size. This split was chosen because it matches §4's explicit,
  detailed ownership of T-shirt/sprint/warnings and §3's "must not...
  select T-shirt size" constraint, keeping the sizing-band mapping in
  exactly one place. Alternative considered: letting
  `complexity_engine.py` also perform the mapping, rejected because it
  would duplicate the sizing-band logic across two files.
- **One-page wizard with internal step-state vs. Streamlit's native
  multi-page `pages/` routing:** chosen because the required guided,
  linear Back/Continue/Review experience with shared, always-persisted
  state is materially simpler to guarantee in one script than across
  independently-routed pages. Trade-off: `app.py` is a single, long
  file; acceptable at this scale and revisited only if it becomes hard
  to maintain.
- **Six-level explicit complexity answer scale (None/Very Low/Low/
  Moderate/High/Very High) instead of subdividing the reference file's
  Low/Moderate/High tiers:** chosen per explicit correction during
  MVP.M1's Change-Impact review, to give every score 0-5 a named,
  dimension-specific level rather than inferring intermediate levels
  from a 3-tier description.
- **`RoleRatePreviewRow`/`RoleRatePreviewSet` (EAP.M1.UI1's
  illustrative-only scaffolding) were removed in MVP.M3, replaced by
  the real, governed models:** those preview models mirrored
  `PRICING-RULES.md` §10-13's shape but were populated with hardcoded
  illustrative example data, never wired to `EstimateRequest` or a real
  `data/rate_card.csv`. MVP.M3 needed the real shape (`RateCardEntry`,
  `RoleCostRow`, `BaselineCostResult`) wired to the actual resource
  plan and a real, governed rate card, so the placeholder models and
  the "Future pricing interaction preview" UI section were deleted
  rather than kept alongside the real implementation.
- **Sidebar "Preliminary low/likely/high" reuses the unchanged
  `contract_fit.sprint_to_months` formula against three different
  sprint inputs (min/midpoint/max), rather than inventing a new
  duration formula:** the governed MVP.M1 duration source is the
  maximum sprint estimate only (`CONTRACT-FIT.md` §3); the sidebar's
  preliminary "low" and "likely" figures are a display-only planning
  aid computed the same way but are never used as the authoritative
  duration, which continues to come from max sprints alone at Step 5.
- **Delivery-risk warning demonstrated from scope-definition signals
  only (unresolved/unknown scope items), not from hours or staffing:**
  per EAP.M1.UI1 correction 4, this milestone has no phase, resource,
  or hours model yet, so the delivery-risk warning is scoped to what's
  actually knowable now. The hours/staffing-based trigger described in
  the milestone prompt is deferred until MVP.M2 introduces a resource
  plan to evaluate.
- **Commercial-risk warning shown only inside the illustrative pricing
  preview, never in the main sidebar:** no governed rate, cost, or
  margin data exists yet: showing a "real" commercial warning outside
  that clearly-labeled illustrative section would misrepresent
  illustrative example numbers as governed commercial fact.
- **`evaluate_pre_generation_gate` only ever returns "Human Review
  Required" or "Generation Blocked," never "Ready for AI Drafting":**
  per EAP.M1.UI2-D1 correction 1, one of the governed non-blocking
  triggers ("timeline is preliminary") is unconditionally true of every
  estimate produced before MVP.M6 introduces a governed final duration,
  so this status is intentionally unreachable at this milestone rather
  than a bug. The full three-status `Literal` is preserved on
  `ResponsibleAIGateResult` for MVP.M6.
- **Unknown scope items are surfaced by construction, not by a runtime
  "don't hide unknowns" check:** the outline's "Items requiring
  confirmation" section always renders every unknown item, and no
  parameter or mode exists to omit it — there is nothing to check at
  runtime because concealment isn't a reachable code path. Tested
  directly (`test_unknown_items_always_appear_and_cannot_be_concealed`).
- **Risky-language detection uses narrow, clearly-risky phrases for
  blocking, and single ambiguous words only for a warning:** per
  EAP.M1.UI2-D1 correction 3, a lone word like "guarantee" or
  "password" must not block by itself. `sow_outline_engine.py` blocks
  only on specific phrases ("guaranteed delivery," "100% uptime," "zero
  defects," "no downtime," "guaranteed accuracy"), SSN-shaped values,
  and credential-looking `key: value` patterns; a bare risky word
  elsewhere in the text only adds a warning. This is a simple keyword
  safeguard for this milestone, explicitly not a real confidential-data
  or compliance classifier.
- **Customer/vendor-responsibility and next-steps content in
  `data/sow_outline_templates.json` is new content, not pulled from an
  existing governed reference:** no file in the `work-estimation` skill
  defines this granularity of responsibility list. Approved as governed
  prototype content per EAP.M1.UI2-D1 correction 4 — tool-agnostic,
  non-binding, free of rates/dates/service levels/guarantees, and
  flagged here for business review the same way the complexity
  6-level scale text was flagged in MVP.M1.
- **The preliminary SOW outline never imports the illustrative pricing
  preview's models or session state:** `sow_outline_engine.py` has no
  dependency on `RoleRatePreviewRow`/`RoleRatePreviewSet` at all, making
  pricing-preview leakage into the outline a structural impossibility
  rather than something enforced only by a runtime filter (backed by
  `test_outline_never_contains_pricing_preview_indicators`).
- **Phase durations are derived from `SizingResult.max_sprints` ×
  configured per-phase weight (weights sum to 1.00 per work type),
  rather than fixed sprint counts per work type:** this ties the phase
  plan to *this estimate's* governed size (satisfying "generate an
  initial phase plan from the governed estimate result"), rather than
  a template unrelated to the actual sizing. `contract_fit.py` itself
  is unchanged and still uses `SizingResult.max_sprints` directly as
  MVP.M1 established — this milestone does not switch contract-fit to
  a phase-plan-derived duration source (`CONTRACT-FIT.md` §3 makes that
  switch optional ("may"), and it wasn't requested for MVP.M2).
- **Required effort (`person_sprints`/`estimated_hours` per phase/role)
  is computed independently of staffing model; staffing model only
  changes the `assigned_to` combined-assignment view:** this is the
  literal "required role vs. required effort vs. assigned person"
  separation in `PHASE-RESOURCE-PLANNING.md` §5. Verified directly:
  `test_effort_totals_identical_across_all_staffing_models` asserts
  identical total hours across Lean/Balanced/Specialized/Customer-
  defined for the same phase plan.
- **The optional AI workstream's detailed activity set falls back to a
  derived mapping from the simplified "AI help" answers when the
  optional/advanced detailed-activity picklist is empty:** MVP.M1.UI1's
  primary AI intake only collects the simplified `ai_help` answers; the
  detailed 27-activity catalog lives in a collapsed advanced section
  users may skip. Per `PHASE-RESOURCE-PLANNING.md` §12.1 ("add only the
  applicable AI phases and roles identified from the selected AI
  workstream activities"), an AI-enabled estimate with no detailed
  activities selected still needs *some* defensible activity set rather
  than an empty AI workstream — `data/resource_rules.json`'s
  `ai_help_fallback_activities` provides that mapping, and
  `ai_baseline_activities` (use-case definition, Responsible AI review)
  is always included regardless, per `ESTIMATE-TYPES.md` §11.5's rule
  that required oversight is never a simplification to drop.
- **AI workstream phase durations are sized as a fixed fraction
  (`ai_phase_weight_of_core_duration`, 0.25) of the core IT total,
  split evenly across whichever AI phases are actually triggered:**
  a configurable prototype assumption, not a governed formula — no
  reference file specifies AI-workstream duration sizing, so this is
  new content flagged here for business review, the same as the other
  configurable assumptions in this document.
- **The single-table resource-plan editor allows duration to be edited
  per row rather than once per phase:** since a phase can have multiple
  role rows, editing duration on one row does not automatically update
  other rows for the same phase. This is a documented, deliberate
  simplification for a self-service `st.data_editor` table (see
  Known limitations) rather than a normalized two-table design, to
  satisfy the requirement for one combined, editable Phase/Duration/
  Role/Allocation/Person-sprints/Hours view.
- **Single current-scenario rate model, not a multi-scenario Configured
  Baseline/Working/Draft model:** the staged
  `prompts/work-estimation/mvp-m3-baseline-pricing.md` prompt described
  a fuller multi-scenario management model; the user's own explicit
  EAP.M3 instructions scoped this milestone to one configured default
  rate and one session-only scenario rate per role only. Followed the
  narrower, explicit instruction and flagged the divergence from the
  staged prompt rather than silently picking either interpretation.
- **Blended hourly rate is `None`, never a fabricated `0.00`, when
  total estimated hours are zero:** a real `0.00` would misrepresent
  "no hours yet" as "a calculated zero-cost rate." The UI renders "Not
  available — total estimated hours are zero" instead, per explicit
  correction during MVP.M3's Change-Impact review.
- **An unmapped or inactive role in the rate card always blocks rather
  than defaulting to a fallback rate:** fabricating a rate for a role
  with no configured entry would silently misstate cost. Verified the
  rate card has zero gaps against every role MVP.M2's `resource_rules.json`
  can generate (`test_rate_card_covers_every_role_m2_can_generate`), so
  this path should only trigger for a genuinely new/renamed role
  introduced later without an updated rate card.
- **Readiness precedence is fixed (Blocked > Human Review > Ready)
  rather than a first-match-wins or severity-summed model:** a
  correction during MVP.M3's Change-Impact review required blocking
  conditions to always win regardless of how many Human Review
  conditions are also present, verified directly by
  `test_blocked_takes_precedence_over_human_review_conditions`.
- **Single-baseline, four-fixed-scenario commercial model, not
  `PRICING-RULES.md` §11's Configured Baseline/Working/Draft model:**
  the staged `prompts/work-estimation/mvp-m4-commercial-pricing.md`
  prompt described per-scenario role-rate overrides plus a discount/
  rounding/management-adjustment lever; the user's own explicit EAP.M4
  instructions scoped this milestone to exactly four named scenarios
  (Recommended/Competitive/Conservative/Custom) varying only
  contingency and target margin on top of the single M3
  `baseline_delivery_cost`, with no discount lever at all. Followed the
  narrower, explicit instruction and flagged the divergence, the same
  pattern already used and approved at M3.
- **Full precision retained internally for M4's commercial formulas;
  only UI display rounds to two decimals** — deliberately different
  from M3's `pricing_engine.py` functions, which round
  `baseline_delivery_cost`/`blended_hourly_rate` internally to two
  decimals. Per the user's explicit "use full precision internally"
  instruction specific to M4.
- **Commercial readiness and approval status are independent axes,
  confirmed explicitly (EAP.M4-D1 item 5):** a scenario may be "Ready
  for Commercial Review" and still "Draft." Approval status mapping
  (Approval Blocked whenever a blocking condition exists; Approved only
  for the current `approved_scenario_id`; Review Required when
  readiness is Human Review Required and not approved; Draft when
  readiness is Ready and not approved) is this project's own
  interpretation of the four named states, not literal text from the
  milestone prompt — flagged for the user's confirmation during the
  Change-Impact review and confirmed unchanged.
- **Approval-note and warning-acknowledgement requirements are checked
  only inside `approve_scenario`, never baked into a scenario's
  `readiness_status`/`blocking_conditions`:** per EAP.M4-D1 items 3-4, a
  missing note must never make an otherwise-valid Draft scenario
  numerically invalid or block calculation/comparison — only an
  approval attempt itself.
- **Commercial-loss detection (`customer_price < risk_adjusted_delivery_cost`)
  is implemented as a standalone, independently-tested guard even
  though the governed formula makes it algebraically unreachable
  through normal contingency/margin ranges alone** (margin in [0, 1)
  and a non-negative risk-adjusted cost always yield price ≥ cost):
  defensive validation per the user's explicit requirement, not a
  trust assumption that the formula alone is sufficient protection.
- **A real defect was found and fixed during implementation: the
  Approve button's click handler originally relied solely on
  Streamlit's `disabled=` attribute to prevent approval when
  `can_approve` was `False`, with no re-check inside the handler
  itself.** Testing via `AppTest.click()` showed a disabled button's
  click can still register and execute its handler body. Fixed by
  re-verifying `can_approve` inside the handler (`if st.button(...) and
  can_approve:`) as defense-in-depth for an action this milestone
  explicitly requires to never happen accidentally (commercial-loss
  approval, missing-note approval).
- **"High delivery risk" (one of MVP.M4's two governed delivery-warning
  levels) is triggered by a simple keyword check (`"missing"` present
  in an underlying M2 resource-plan warning) rather than a numeric
  "insufficient hours" threshold:** no governed reference defines a
  numeric threshold for what counts as insufficient phase hours, and
  inventing one would be fabricating a business rule. Uses the same
  lightweight-keyword-safeguard pattern already established and
  accepted in `sow_outline_engine.py`'s risky-language scan — flagged
  here for business review the same way.
- **M3's `COMMERCIAL_BELOW_DEFAULT_WARNING` text is left completely
  unedited in MVP.M4, even though its trailing "will be calculated in a
  later milestone" sentence is now factually stale:** that string is a
  validated financial-disclaimer label under `CLAUDE.md`'s Change-
  Impact Gate, and the bypass rules explicitly exclude financial labels
  and disclaimers from the typo/formatting-only shortcut. No change to
  its wording was requested during EAP.M4's Change-Impact review, so it
  was left verbatim; the resulting gross profit and achieved margin are
  now shown alongside it in the UI instead, per the user's instruction.

## 20. Known limitations

- No support pricing, final/customer-approved SOW, or AI logic exists —
  this document describes MVP.M1 through MVP.M4 only, per the
  milestone-discipline rule in `CLAUDE.md`. The preliminary SOW outline
  (EAP.M1.UI2) is explicitly a draft-only, always-human-review-required
  artifact, not the governed MVP.M6 capability.
- `data/rate_card.csv`'s rates and `data/commercial_pricing_defaults.json`'s
  contingency/margin percentages are fictional/illustrative
  demonstration values authored for this prototype, not real commercial
  rates or policy — per `GUARDRAILS.md` §3 and `PRICING-RULES.md` §9,
  both files are explicitly flagged for business review before any real
  commercial use.
- MVP.M4's commercial scenarios, like MVP.M2's resource plan and
  MVP.M3's baseline cost before them, are session-only: refreshing or
  restarting the app loses all scenario edits and approval state, per
  `PRICING-RULES.md` §17. This is expected MVP behavior, not a defect.
- "High delivery risk" detection (see §19) is a simple keyword check
  against M2's existing warning text, not a governed numeric threshold
  for insufficient phase hours — flagged for business review.
- The resource-plan editor lets duration be edited per row rather than
  once per phase (see §19) — editing one role's row for a phase does
  not propagate to other roles in that same phase automatically.
- AI-workstream phase-duration sizing (`ai_phase_weight_of_core_duration`)
  is a configurable prototype assumption authored for this milestone,
  not sourced from a governed reference (see §19).
- Wizard state is transient: closing the browser tab or restarting the
  app loses all in-progress input. There is no save/resume capability
  and none is planned before a milestone explicitly adds persistence.
- The 6-level complexity answer descriptions/examples in
  `data/complexity_questions.json` are new content authored for this
  milestone, not verbatim text from `COMPLEXITY-AND-SIZING.md` (which
  only defines 3-tier Low/Moderate/High descriptions) — flagged for
  business review as a configurable prototype assumption.
- `streamlit.testing.v1.AppTest` (this Streamlit version) cannot
  reliably drive more than a couple of script reruns past a page
  containing an abandoned `st.radio`/`st.selectbox`/`st.segmented_control`
  widget without an internal framework error unrelated to this
  application's code. Deep wizard-flow tests work around this by
  pre-seeding `session_state` and rendering directly to the target
  step rather than clicking through every prior selection widget; this
  is a test-authoring workaround, not an application defect.
- `st.data_editor` (used by the resource-plan and baseline-cost tables)
  has no `AppTest` interaction wrapper in this Streamlit version, so
  those sections' live edit/recalculation behavior is verified by
  manual browser review rather than an automated UI-driven test; their
  initial render and static content are automated-tested.
- No CI/CD pipeline exists; validation is manual (`pytest`, `streamlit
  run`) at this stage.

## 21. Future considerations

- MVP.M5 introduces support estimation (warranty, maintenance,
  enhancement support, including combined first-year contract value for
  scenarios such as Implementation plus Support), reusing MVP.M4's
  pricing formulas rather than redefining them, per
  `ENGINE-RESPONSIBILITIES.md` section 9. Not present in this
  repository yet.
- MVP.M4's `PricingScenario` objects are currently regenerated/
  recalculated in `st.session_state` and not themselves part of
  `EstimateRequest` — MVP.M6 will need to decide how the Approved
  scenario feeds `ApprovedEstimate` (per `PRICING-RULES.md` §16, "the
  Approved scenario is how `ApprovedEstimate`'s values get populated"),
  and whether a real multi-scenario (Configured Baseline/Working/Draft)
  model with per-scenario role-rate overrides and a discount/rounding/
  management-adjustment lever belongs there instead of MVP.M4's four-
  fixed-scenario, contingency-and-margin-only simplification (see §19).
- MVP.M6 introduces the governed, final SOW capability
  (`sow_generator.py`) and customer-facing output, and will require
  revisiting §9's internal/customer-view separation, since this
  milestone has no customer-facing output to separate yet. The
  generated, editable assumptions (`assumption_engine.py`) and the
  preliminary outline's section structure (`sow_outline_engine.py`) are
  intended to inform that future capability's design, not be reused
  as-is without the governed approved-values-only rule in
  `SOW-RULES.md` section 2. "Ready for AI Drafting" becomes reachable
  once MVP.M6 introduces a governed final duration and commercial
  position.
- MVP.M7 introduces an AI adapter for the estimator's own intake (
  distinct from the customer-project AI-capability field already
  captured here) and will require populating §11 in full, including
  the replaceable-interface design and human-review gating specific to
  AI-assisted intake.

## 22. Validation criteria

Each milestone's automated validation is considered complete when: the
virtual environment installs cleanly, `streamlit run app.py` starts
without import errors, `python -m pytest` passes in full (including
unchanged regression coverage for every prior milestone's deterministic
engine), and the repository structure matches that milestone's approved
file list in `decision_log.md`.

**Beyond automated validation, every MVP.M milestone (per EAP.M1.UI1)
also requires a mandatory browser-based UI review checkpoint**: start
the app locally, provide the reviewer a browser-review checklist
covering that milestone's UI behavior, and obtain explicit human
acceptance. The next milestone must not begin until that acceptance is
given — automated validation passing is necessary but not sufficient
to proceed.

## 23. Architecture diagram

See `architecture-diagram.mmd` in this same `docs/` folder.
