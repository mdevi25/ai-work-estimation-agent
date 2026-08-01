<!--
PURPOSE:    Dated log of verified decisions for the ai-work-estimation-agent live repository, read at the start of every governed code or configuration change per this repository's CLAUDE.md "Working protocol" step 2.
UPSTREAM:   Governed by this repository's own CLAUDE.md (staged from AI-PPM/projects/ai-work-estimator/CLAUDE.md). No AI-PPM template for this file's structure existed at the time of creation, so this structure was originated for this file, modeled loosely on the dated-entry style used by the retro-log skill's RETRO.md format.
DOWNSTREAM: Read before every future code/configuration change in this repository, per the "Working protocol" section of this repository's CLAUDE.md. Appended to, never rewritten -- prior entries are not edited or removed.
EXPECT:     Only verified decisions with a clear source -- never invented or assumed architecture decisions. Append-only.
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Decision log

Append-only. Do not edit or delete prior entries.

## 2026-07-30 -- Repository governance bootstrap (EAP.S7.D)

**Decisions confirmed:**

- Repository: `ai-work-estimation-agent`
- Repository is private
- Streamlit Community Cloud is the planned deployment target
- AI-PPM remains the framework source (this repository does not fork or
  duplicate framework rules -- it inherits them from the deployed
  `work-estimation` skill and this repository's own `CLAUDE.md`)
- Application development occurs in this live repository, never inside
  AI-PPM
- `work-estimation` is globally deployed to `~/.claude/skills/work-estimation/`
- AI capability is optional and off by default for any estimate produced
  by this application (per `ESTIMATE-TYPES.md` section 11)
- The EAP.S5.E framework archive step is deferred and may resume later --
  it is an AI-PPM documentation task, not a blocker for this repository
- Application implementation and MVP.M1 have not started

**Source:** EAP.S7.D governance-prerequisite remediation, run from the
AI-PPM root.

## 2026-07-30 -- Repository bootstrap (EAP.BOOTSTRAP)

**Decisions confirmed:**

- Python 3.12.10 installed via `winget install Python.Python.3.12` and
  selected as this project's interpreter, over the machine's
  pre-existing Python 3.13 install, to match `CLAUDE.md`'s "Python 3.11
  or 3.12" scope. This is a technology-choice decision made under the
  Change-Impact Gate, approved explicitly by the project owner.
- Deterministic engine before AI: no AI/model logic will be added
  before the deterministic calculation engine exists and is validated
  (earliest MVP.M7, per `CLAUDE.md`).
- CSV or JSON configuration before database: business-rule
  configuration will live in version-controlled `data/` files; no
  database is in scope for early milestones.
- Deployment target: private GitHub repository
  (`ai-work-estimation-agent`) plus Streamlit Community Cloud.
- Initial bootstrap structure created: `README.md`, `requirements.txt`,
  `app.py` (Streamlit placeholder, no business logic), `pages/`,
  `src/__init__.py`, `data/`, `tests/__init__.py` and
  `tests/test_smoke.py`, `docs/architecture.md`,
  `docs/architecture-diagram.mmd`, `.gitignore`. No estimation, sizing,
  pricing, support, SOW, AI, database, or authentication logic was
  added.
- Dependencies pinned to verified current stable versions:
  `streamlit==1.60.0`, `pandas==3.0.5`, `pydantic==2.13.4`,
  `pytest==9.0.3`.
- Architecture-governance Gate 1 ("before MVP.M1 implementation
  planning: establish initial separation of UI, engines, configuration,
  and data flow") applied; see `docs/architecture.md`
  ("prototype" stage).

**Source:** EAP.BOOTSTRAP, run from the live repository root, following
approval of the pre-edit plan presented in that session.

## 2026-07-31 -- MVP.M1: Estimation foundation (EAP.M1)

**Decisions confirmed:**

- Implemented the estimation foundation as an 8-step guided Streamlit
  wizard (`app.py`): estimate type, business request, scope and
  systems, complexity questions, optional AI capability, contract
  term, review, results.
- New governed configuration files added under `data/`:
  `complexity_weights.json`, `complexity_questions.json`,
  `sizing_bands.json`, `contract_terms.json`, `estimate_types.json`,
  `ai_workstream_activities.json`.
- New `src/` modules: `config.py` (JSON loading with controlled
  `ConfigurationError`, no silent fallback), `models.py`
  (`EstimateRequest`, `ComplexityDimensionAnswer`, `ComplexityResult`,
  `SizingResult`, `ContractFitResult`), `validators.py`,
  `complexity_engine.py`, `sizing_engine.py`, `contract_fit.py`.
- Engine ownership: `complexity_engine.py` owns the weighted-score
  calculation and explanatory contribution data only;
  `sizing_engine.py` owns all Relative Job Size, T-shirt size, sprint
  range, and size-13/size-20 warning mapping. No sizing-band mapping
  is duplicated in `complexity_engine.py` (EAP.M1-D1 correction 3).
- Complexity answer scale: every dimension uses the explicit six-level
  scale 0 = None or Not Applicable, 1 = Very Low, 2 = Low, 3 =
  Moderate, 4 = High, 5 = Very High, each with a dimension-specific
  description and example authored for this milestone (not verbatim
  from `COMPLEXITY-AND-SIZING.md`, which only defines 3-tier
  descriptions) -- flagged as a configurable prototype assumption
  requiring business review (EAP.M1-D1 correction 1).
- "Major complexity driver" was rejected as a new business-rule term;
  the transparency view instead labels dimensions scoring 4 or 5 as
  "Higher-scoring complexity dimensions" -- explanatory only, no
  warning, threshold, status, or pricing rule is derived from it, and
  dimensions scoring below 4 remain visible in the full calculation
  detail (EAP.M1-D1 correction 2).
- All six `data/` configuration files are validated at load time
  (schema, weight totals, sizing-band boundary coverage with no gaps
  or overlaps, positive contract durations); any missing, malformed,
  or invalid configuration raises a controlled `ConfigurationError`
  rather than falling back to a hard-coded value (EAP.M1-D1
  correction 4).
- `docs/architecture.md` sections 3, 4, 6-10, 13, and 19-21 updated to
  document the implemented MVP.M1 design only; MVP.M2-M7 remain
  explicitly marked as not implemented (EAP.M1-D1 correction 5).
  `docs/architecture-diagram.mmd` updated to match.
- Fixed a real defect found during implementation: binding a Streamlit
  widget's `key=` directly to a canonical session-state field name
  caused Streamlit to silently delete that field's value whenever the
  wizard navigated to a step that didn't render that widget (a
  documented Streamlit behavior, not particular to this app). Every
  wizard field now uses a separate widget-only key
  (`synced_text_input`/`synced_text_area` helpers, or an explicit
  `index=`/`value=` computed from canonical state), with the canonical
  value stored and read independently -- this is what makes
  Back/Continue value persistence actually work.
- No estimation-adjacent milestone (phase planning, resource planning,
  pricing, contingency, margin, support estimation, customer summary,
  SOW generation, Excel/PowerPoint export, or AI-assisted intake) was
  introduced. The optional AI-capability field captures customer-
  project intake only; no AI phase, role, effort, cost, or pricing
  logic exists anywhere in this milestone.

**Source:** EAP.M1, run from the live repository root, following
approval of the pre-edit Change-Impact Report and the corrections in
EAP.M1-D1.

## 2026-07-31 -- MVP.M1 UI/UX remediation: self-service redesign (EAP.M1.UI1)

**Decisions confirmed:**

- Redesigned MVP.M1's UI from an 8-step technical wizard into a
  5-step self-service wizard (work type, quick facts, scope checklist,
  complexity and AI, review and estimate) with a persistent left-side
  panel (step status, current estimate, running estimate, warning
  status), targeting a 5-10 minute completion time for a nontechnical
  business user.
- The approved deterministic estimation engine is unchanged:
  `src/complexity_engine.py`, `src/sizing_engine.py`, and
  `src/contract_fit.py` were not modified. Complexity weights, the
  weighted-complexity formula, Relative Job Size mapping, T-shirt
  mapping, sprint ranges, the duration formula, and contract-fit
  thresholds are byte-for-byte unchanged, verified by the unmodified
  regression test suite continuing to pass in full.
- Work type is simplified to three UI-facing options (New Project,
  Enhancement, Production Support), stored directly in the existing
  internal `estimate_type` field for compatibility with the original
  7-value taxonomy. Changing work type after scope answers exist
  requires explicit user confirmation before resetting scope defaults.
- Added a non-authoritative "Preliminary" sidebar preview
  (`src/running_estimate_preview.py`) shown before all seven complexity
  dimensions are answered: weights are re-normalized among only the
  answered dimensions, unanswered dimensions are never treated as
  zero, and the preview always states how many of seven are answered.
  The final Step 5 result uses only the unchanged, authoritative
  `complexity_engine.calculate_weighted_complexity` with all seven
  validated answers (EAP.M1.UI1-D1 correction 2).
- No UI prototype file was available in the repository or this
  conversation; the redesign proceeded from the written prototype-
  requirements description only, per explicit instruction not to claim
  pixel-for-pixel equivalence and not to create or copy a prototype
  reference file into the repository (EAP.M1.UI1-D1 correction 1).
- Added `RoleRatePreviewRow`/`RoleRatePreviewSet` to `src/models.py` as
  additive, illustrative-only UI scaffolding for a future MVP.M3/M4
  pricing interaction (role, actual hours, configured default rate,
  scenario rate, required override reason when rates differ, computed
  cost, read-only blended rate). Mirrors the shape already governed by
  `PRICING-RULES.md` sections 10-13 so a later milestone can adopt it
  rather than diverge, but it is never wired to `EstimateRequest`, any
  engine, or any customer-facing output. No `data/rate_card.csv` was
  created; the "Future pricing interaction preview" section in `app.py`
  uses hardcoded illustrative example data only, clearly labeled and
  never presented as a customer quote (EAP.M1.UI1-D1 corrections 3 and
  5).
- Commercial-risk warnings appear only inside that illustrative pricing
  preview section, computed from its own example numbers; the main
  persistent sidebar never shows a commercial warning, since no
  governed rate, cost, or margin data exists yet. Delivery-risk
  warnings are demonstrated from scope-definition signals only
  (unresolved/unknown scope checklist items) — the hours/staffing-based
  trigger described in the milestone prompt is deferred until MVP.M2
  introduces a resource plan to evaluate (EAP.M1.UI1-D1 correction 4).
- Added `src/scope_defaults.py` (scope-checklist defaults and
  scope-confirmation percentage) and `src/assumption_engine.py`
  (deterministic, template-based assumption generation from work type,
  scope selections, unknown items, systems involved, and AI
  selections). Generated assumptions are editable and explicitly not
  presented as approved facts until confirmed at Review (EAP.M1.UI1-D1
  correction 6).
- New configuration files: `data/work_types.json`,
  `data/scope_checklist_items.json`, `data/assumption_templates.json`,
  `data/ai_help_options.json`. All are schema-validated at load with
  the same controlled-`ConfigurationError` pattern as MVP.M1's
  configuration.
- **Standing policy recorded (EAP.M1.UI1-D1 correction 7): every future
  MVP.M milestone ends with automated validation, local Streamlit
  startup, a browser-based UI review checklist, and explicit user
  acceptance, before the next milestone begins.** This is a
  process/documentation requirement, not a code change; see
  `docs/architecture.md` section 22.
- Confirmed test-tooling limitation: `st.segmented_control` (used for
  the compact scope-checklist status control) shares the same
  `streamlit.testing.v1.AppTest` multi-rerun limitation already
  documented for `st.radio`/`st.selectbox`. `st.data_editor` (used by
  the illustrative pricing preview) has no `AppTest` interaction
  wrapper at all in this Streamlit version; that section's live-edit
  behavior is verified manually in the browser review rather than by
  an automated UI-driven test.

**Source:** EAP.M1.UI1, run from the live repository root, following
approval of the pre-edit file-scope report and the corrections in
EAP.M1.UI1-D1.

## 2026-07-31 -- Preliminary SOW outline and action navigation (EAP.M1.UI2)

**Decisions confirmed:**

- Added a differentiated action-navigation row to the Step 5 results
  screen: **Generate Preliminary SOW Outline** (active), **Generate
  Final SOW** (disabled, "Requires approved resource plan and
  pricing"), **Export to Excel** and **Export to PowerPoint** (disabled,
  "Coming in a later milestone"), **Build Resource Plan** (disabled,
  "Available in MVP.M2"). No active, unqualified "Generate SOW" button
  exists (EAP.M1.UI2-D1 correction 7).
- Added `src/sow_outline_engine.py`: a lightweight, milestone-scoped
  Responsible-AI-style pre-generation gate
  (`evaluate_pre_generation_gate`) and a deterministic, template-based
  21-section preliminary SOW outline builder
  (`build_preliminary_sow_outline`), plus Markdown/plain-text
  renderers. This is explicitly not the governed MVP.M6
  `sow_generator.py`.
- The gate only ever returns `Human Review Required` or `Generation
  Blocked` at this milestone -- `Ready for AI Drafting` is intentionally
  unreachable because "timeline is preliminary" is unconditionally true
  before MVP.M6 introduces a governed final duration. The full
  three-status model is preserved on `ResponsibleAIGateResult` for
  MVP.M6 (EAP.M1.UI2-D1 correction 1). On success the UI shows:
  "Preliminary outline generated successfully. Human review is required
  before this content may be used externally." -- never presented as
  an error.
- Unknown scope items are surfaced by construction (always rendered in
  "Items requiring confirmation," no concealment code path exists) and
  always contribute to the Human Review Required warnings. Test
  `test_unknown_items_always_appear_and_cannot_be_concealed` proves
  this directly (EAP.M1.UI2-D1 correction 2).
- Risky-language detection blocks only on narrow, clearly-risky phrases
  ("guaranteed delivery," "100% uptime," "zero defects," "no downtime,"
  "guaranteed accuracy"), SSN-shaped values, and credential-looking
  `key: value` patterns; a single ambiguous word (e.g., "guarantee,"
  "password" alone) only adds a Human-Review warning, never blocks.
  Documented as a simple keyword safeguard, explicitly not a real
  confidential-data or compliance classifier (EAP.M1.UI2-D1
  correction 3).
- Added `data/sow_outline_templates.json` (customer responsibilities,
  vendor responsibilities, next steps) as new governed prototype
  content -- tool-agnostic, non-binding, free of rates/final dates/
  service levels/guarantees/legal terms, flagged for business review
  (EAP.M1.UI2-D1 correction 4).
- Extended `assumption_engine.generate_assumptions` with optional
  keyword-only parameters (`excluded_item_labels`, `system_context`,
  `ai_data`, `contract_term`, `known_dependencies`); existing callers
  and tests are unchanged and continue to pass; the function always
  builds a fresh list rather than mutating a previously returned one
  (EAP.M1.UI2-D1 correction 5). Added a "Known dependencies" input to
  Step 2's optional "Additional details" section so this driver has an
  actual UI source.
- The preliminary outline contains only already-captured/validated
  MVP.M1 data: business objective, work type, system context, audience,
  included/excluded/unknown scope, systems involved, complexity-
  informed size, sprint range, estimated duration, contract-fit
  result, AI selections (only when applicable), proposed assumptions,
  dependencies, risks/open questions, customer/vendor responsibilities,
  next steps, and the mandatory disclaimer verbatim exactly once. It
  never imports `RoleRatePreviewRow`/`RoleRatePreviewSet` or any
  illustrative pricing-preview value -- structurally impossible to leak
  those into the outline, not just filtered at runtime (EAP.M1.UI2-D1
  correction 6).
- Download boundary: Markdown or plain text only, via `st.download_button`;
  no DOCX, PDF, Excel, or PowerPoint generation was introduced.
- No deterministic estimation engine
  (`complexity_engine.py`/`sizing_engine.py`/`contract_fit.py`) was
  modified. No phase/resource engine, rate-card engine, commercial-
  approval logic, support-pricing engine, database, authentication, or
  LLM integration was introduced.

**Source:** EAP.M1.UI2, run from the live repository root, following
approval of the pre-edit file-scope report and the corrections in
EAP.M1.UI2-D1.

## 2026-07-31 -- Phase and resource planning (EAP.M2)

**Decisions confirmed:**

- Added `src/phase_planner.py` and `src/resource_planner.py`. Phase
  durations are derived from the governed `SizingResult.max_sprints`
  multiplied by a configured per-phase weight (weights sum to 1.00 per
  work type), not from a fixed sprint count unrelated to the actual
  estimate. `contract_fit.py` is unchanged and still uses
  `SizingResult.max_sprints` directly, exactly as MVP.M1 established --
  this milestone does not switch contract-fit to a phase-plan-derived
  duration source.
- Implemented the exact governed formulas: `person_sprints =
  phase_duration_in_sprints * (allocation_percent / 100)`;
  `estimated_hours = person_sprints * hours_per_sprint`, with
  `hours_per_sprint = 80` from `data/resource_rules.json`.
- Required effort (`person_sprints`/`estimated_hours` per phase/role) is
  computed independently of staffing model; Lean, Balanced,
  Specialized, and Customer-defined only change the `assigned_to`
  combined-assignment view. Verified directly: total estimated hours
  are identical across all four staffing models for the same phase
  plan.
- Resource warnings implemented in plain language: same-role allocation
  above 100% in one phase, combined assigned-person allocation above
  100% under the selected staffing model, incompatible role
  combinations (Developer/Senior Developer as sole QA; AI-role
  equivalents for Responsible AI/security review), missing deployment/
  stabilization coverage, and missing independent AI evaluation
  coverage.
- QA participates during the `development` phase (before dedicated
  testing) at a lower allocation and more heavily during the dedicated
  testing phase; Business Analyst participates during discovery and
  UAT support -- per `PHASE-RESOURCE-PLANNING.md` §4.
- AI phases/roles/effort are added only when AI is enabled and are
  entirely absent (not zeroed) when AI is off, per §12.2. The detailed
  27-activity catalog drives the AI workstream when populated (the
  optional/advanced section); when empty, a fallback mapping from the
  simplified "AI help" answers is used instead, so an AI-enabled
  estimate never gets an empty AI workstream. Baseline activities
  (use-case definition, Responsible AI review) are always included
  regardless, per `ESTIMATE-TYPES.md` §11.5.
- AI-workstream phase durations use a new configurable prototype
  assumption (`ai_phase_weight_of_core_duration`, 0.25 of the core IT
  total, split evenly across triggered AI phases) -- not sourced from a
  governed reference, flagged for business review.
- The preliminary SOW outline (`sow_outline_engine.py`) gained one new
  optional section, "Preliminary phase and resource plan," appended
  only when a resource plan is supplied; existing calls/tests without
  it are byte-for-byte unchanged (backward compatible). The new section
  contains phases, roles, and hours only -- no rates, cost, price,
  margin, contingency, or payment terms exist on `ResourcePlanResult`
  to leak into it.
- No rate card, default/scenario rate, blended rate, role/phase/
  baseline cost, contingency, margin, discount, customer price, or
  support pricing was introduced anywhere in this milestone's code.
- The resource-plan editor (`st.data_editor`) allows duration to be
  edited per row rather than once per phase, since a phase may have
  multiple role rows -- a documented, deliberate simplification for the
  single combined editable table this milestone's UI requires, not a
  normalized two-table design.

**Source:** EAP.M2, run from the live repository root, following
approval of the pre-edit 10-point design report.

## 2026-07-31 -- EAP.M2 browser review accepted

**Decisions confirmed:**

- EAP.M2 (Phase and Resource Planning) browser review is **accepted**.
  Per the mandatory UI review gate, this clears the way for EAP.M3 --
  Baseline Pricing to begin once explicitly requested; it does not
  begin automatically (`CLAUDE.md` "Working protocol" item 13).
- Deferred enhancements identified during review: minor resource-
  planning UI and usability improvements. Confirmed non-blocking --
  they do not affect the phase/resource-planning calculations or
  workflow. Explicitly deferred to a dedicated UI-polish milestone
  after the core MVP.M1-M6 workflow is complete, rather than addressed
  ad hoc during MVP.M3+.

**Source:** User acceptance message following the EAP.M2 browser-review
handoff.

## 2026-07-31 -- Baseline cost and rate card (EAP.M3)

**Decisions confirmed:**

- Added `data/rate_card.csv` (Role, Default Hourly Rate, Currency,
  Active), with a distinct, non-uniform, illustrative/fictional rate
  for every role MVP.M2's `resource_rules.json` can generate (verified
  programmatically -- zero gaps), plus applicable variation roles.
  Rates are demonstration values only, per `GUARDRAILS.md` section 3
  and `PRICING-RULES.md` section 9; the file is read-only from the
  application's perspective.
- Added `src/pricing_engine.py`: `load_rate_card`, `build_baseline_cost`,
  `reset_role_rate`, `reset_all_rates`, `reconcile_rate_state`. Formulas:
  `role_cost = total_estimated_hours * scenario_rate`;
  `baseline_delivery_cost = sum(role_cost)`;
  `blended_hourly_rate = baseline_delivery_cost / total_estimated_hours`,
  returned as `None` (never a fabricated `0.00`) when total hours are
  zero (EAP.M3-D1 correction 1).
- Single current-scenario rate model only: one configured default rate
  and one session-only scenario rate per role, no Configured Baseline/
  Working/Draft multi-scenario management -- narrower than the staged
  `prompts/work-estimation/mvp-m3-baseline-pricing.md` prompt, per the
  user's explicit EAP.M3 instructions (EAP.M3-D1 correction 9), flagged
  and approved.
- An override reason is required whenever the scenario rate differs
  from the configured default (`validate_override_reason`); missing
  reason blocks (`Calculation Blocked`). A role with no active
  configured rate is always blocking -- never a fabricated rate
  (EAP.M3-D1 correction 2, verified by
  `test_rate_card_covers_every_role_m2_can_generate` and
  `test_unknown_role_never_gets_a_fabricated_rate`).
- Reset semantics: resetting one role clears both its scenario rate and
  override reason together, restoring the configured default; "Reset
  all" does the same for every active role; `reconcile_rate_state`
  automatically drops stale rate/reason entries for roles no longer
  present in the current resource plan (EAP.M3-D1 correction 3).
- Pricing-readiness precedence is fixed: `Calculation Blocked` >
  `Human Review Required` > `Ready for Baseline Review` -- blocking
  reasons are checked first regardless of any Human Review condition
  also being true, verified directly by
  `test_blocked_takes_precedence_over_human_review_conditions`
  (EAP.M3-D1 correction 4).
- Delivery-risk warnings already present on the resource plan
  (`ResourcePlanResult.warnings`) are surfaced as a Human Review trigger
  but never rewritten, suppressed, or altered by the pricing engine --
  verified the original warning text on the resource plan object is
  unchanged after baseline-cost calculation (EAP.M3-D1 correction 5).
- The exact required commercial-risk warning text is used verbatim
  whenever a scenario rate is set below the configured default,
  including the appended "Gross profit and margin will be calculated in
  a later milestone" sentence (EAP.M3-D1 correction 8); no gross profit,
  margin, markup, contingency, or customer price exists anywhere in
  `pricing_engine.py` or its models.
- `src/sow_outline_engine.py` gained one new optional boolean parameter,
  `baseline_costing_in_progress`, which appends only the fixed sentence
  "Baseline internal costing is under review." to the existing
  "Document status" section -- never an amount, rate, or dollar figure.
  The module structurally never imports `BaselineCostResult`,
  `RoleCostRow`, or the rate card (EAP.M3-D1 correction 6); existing
  calls/tests without the new parameter are unchanged (backward
  compatible).
- Removed `RoleRatePreviewRow`/`RoleRatePreviewSet` and the "Future
  pricing interaction preview" illustrative scaffolding from
  `src/models.py`/`app.py` (introduced in EAP.M1.UI1 as MVP.M3/M4
  scaffolding), replacing them with the real `RateCardEntry`,
  `RoleCostRow`, and `BaselineCostResult` models and a governed
  "Baseline delivery cost" UI section.
- UI: the Baseline Cost table shows total estimated hours and the
  configured default rate as read-only; only the scenario rate and
  override reason are editable; role cost and both difference fields
  ($ and %) recalculate immediately from the edited values. No hours
  are editable anywhere in this section -- MVP.M2's resource-plan hours
  remain the sole, authoritative hours source (EAP.M3-D1 corrections 7
  and 9).
- No change to `src/phase_planner.py` or `src/resource_planner.py` (both
  unchanged since MVP.M2). No multi-scenario management or commercial
  approval workflow was introduced.

**Source:** EAP.M3, run from the live repository root, following
approval of the pre-edit 13-point Change-Impact Report and the ten
corrections in EAP.M3-D1.

## 2026-07-31 -- Commercial scenario pricing and approval (EAP.M4)

**Decisions confirmed:**

- Added `data/commercial_pricing_defaults.json`: four governed scenario
  defaults (Recommended 10%/30%, Competitive 5%/20%, Conservative
  20%/35%, Custom starts as a copy of Recommended), a maximum permitted
  contingency (50%), and material-difference thresholds (5 percentage
  points) for both contingency and target margin. All percentages are
  explicitly flagged in the file as configurable prototype values
  requiring business review before real-world use, grounded loosely in
  `PRICING-RULES.md` section 4's illustrative contingency table and
  section 3's worked 30%-margin example.
- **Single-baseline, four-fixed-scenario model, not `PRICING-RULES.md`
  section 11's Configured Baseline/Working/Draft model**: per the
  user's explicit EAP.M4 instructions (narrower than the staged
  `prompts/work-estimation/mvp-m4-commercial-pricing.md` prompt), no
  per-scenario role-rate override and no discount/rounding/management-
  adjustment lever exist in this milestone -- `customer_price` is the
  direct output of contingency and target margin on top of the single
  M3 `baseline_delivery_cost` only. Confirmed and flagged as a
  deliberate divergence, the same pattern already used at M3
  (EAP.M4-D1 item 1).
- Extended `src/pricing_engine.py` (not a new file) with the full
  contingency-through-approval sequence, per `ENGINE-RESPONSIBILITIES.md`
  section 8 assigning this whole sequence to one engine. Implemented
  exactly:
  `contingency_amount = baseline_delivery_cost * contingency_percentage`;
  `risk_adjusted_delivery_cost = baseline_delivery_cost + contingency_amount`;
  `customer_price = risk_adjusted_delivery_cost / (1 - target_margin_percentage)`;
  `gross_profit = customer_price - risk_adjusted_delivery_cost`;
  `achieved_margin = gross_profit / customer_price` (`None`, never a
  fabricated `0/0`, when `customer_price` is 0);
  `equivalent_markup = (customer_price - risk_adjusted_delivery_cost) / risk_adjusted_delivery_cost`
  (`None` when `risk_adjusted_delivery_cost` is 0). **Full precision is
  retained internally; only UI display rounds to two decimals** -- a
  deliberate difference from M3's `pricing_engine.py` functions, which
  round internally, per the user's explicit "use full precision
  internally" instruction for M4.
- Added `PricingScenario` to `src/models.py` with every field the user
  specified (scenario id/name/description, contingency and target
  margin percentages, contingency amount, risk-adjusted cost, customer
  price, gross profit, achieved margin, equivalent markup, a baseline
  snapshot pair for drift detection, readiness status, approval status,
  approval reason, two warning-acknowledgement flags, created/
  recalculated timestamps, `needs_recalculation`/`stale_reason`, and
  separate validation-warning/blocking-condition lists). Removed a
  stale module-level docstring reference in `models.py` to the
  `RoleRatePreviewRow`/`RoleRatePreviewSet` scaffolding already deleted
  at M3.
- **Commercial readiness** (`Ready for Commercial Review` / `Human
  Review Required` / `Approval Blocked`, Blocked-first precedence) and
  **approval status** (`Draft` / `Review Required` / `Approved` /
  `Approval Blocked`) are two independent axes, confirmed explicitly
  (EAP.M4-D1 item 5): a scenario may be "Ready for Commercial Review"
  and still "Draft." Implemented mapping: Approval Blocked whenever a
  blocking condition exists; Approved only for the current
  `approved_scenario_id`; Review Required when readiness is Human
  Review Required and not approved; Draft when readiness is Ready and
  not approved. Human-Review triggers implemented exactly per spec
  (rate overrides, material contingency/margin difference from
  Recommended, delivery warnings, AI workstream, Customer-defined
  staffing, unresolved scope, the Competitive scenario always, zero
  contingency, zero target margin); zero baseline delivery cost is a
  Human-Review trigger, never a block, and never a silently "Ready"
  result.
- **Approval-note and warning-acknowledgement requirements apply only
  at the moment of an approval attempt** (EAP.M4-D1 items 3-4), via a
  separate `approve_scenario` gate function -- never baked into
  `readiness_status`/`blocking_conditions`, so a missing note never
  makes an otherwise-valid Draft scenario numerically invalid or
  blocks calculation/comparison.
- **Commercial-loss detection** (`customer_price < risk_adjusted_delivery_cost`)
  is a standalone, independently-tested guard (`detect_commercial_loss`
  in `validators.py`) even though the fixed formula makes it
  algebraically unreachable through normal contingency/margin ranges
  alone (margin in [0,1) and non-negative cost always yield price >=
  cost) -- implemented as defensive validation per the user's explicit
  requirement. A commercial-loss scenario is always Approval Blocked
  with no note, acknowledgement, or exception able to override it
  (EAP.M4-D1 item 7) -- confirmed as a real defect risk during
  implementation: the first draft's approve button relied solely on
  Streamlit's `disabled=` attribute with no re-check inside the click
  handler; fixed to re-verify `can_approve` inside the handler itself
  as defense-in-depth, since a disabled-button click can bypass the
  `disabled` attribute under `AppTest` (and, defensively, should never
  be trusted as the only gate for an irreversible action).
- **Baseline-drift invalidation**: each scenario snapshots the
  `baseline_delivery_cost`/`readiness_status` it was last calculated
  against; every render compares that snapshot to the live
  `BaselineCostResult` (`detect_baseline_drift`) and, on any mismatch,
  immediately clears approval and flags `needs_recalculation` with a
  visible reason (`refresh_scenario_staleness`) -- without silently
  recomputing the scenario's stored dollar fields. This one generic
  comparison covers role-rate changes, hours changes, resource-plan
  changes, and AI on/off transitions alike, since all of them change
  `baseline_delivery_cost` or its readiness status on the live M3
  result -- no special-casing needed per trigger type (EAP.M4-D1 item
  8). Editing a scenario's own contingency/margin, by contrast,
  recalculates immediately using its existing baseline snapshot.
- Two new delivery-risk warning texts (`DELIVERY_RISK_WARNING`,
  `HIGH_DELIVERY_RISK_WARNING`) and the exact `COMMERCIAL_LOSS_WARNING`
  text are used verbatim as specified. `derive_delivery_risk_warnings`
  maps M2's resource-plan warnings to these two levels; "High delivery
  risk" fires when any underlying M2 warning text contains "missing"
  (a simple keyword heuristic, the same lightweight-safeguard pattern
  already used in `sow_outline_engine.py`'s risky-language scan, not a
  numeric threshold invented for this milestone -- flagged for business
  review). M3's `COMMERCIAL_BELOW_DEFAULT_WARNING` text is carried
  forward completely unedited (its trailing "will be calculated in a
  later milestone" sentence is now stale now that M4 exists, but
  editing a validated financial-disclaimer string requires its own
  full Change-Impact Gate pass per `CLAUDE.md`'s bypass exclusions, and
  no such change was requested) -- gross profit and achieved margin are
  now shown alongside it in the UI instead, per the user's instruction.
- Extended `src/sow_outline_engine.py`'s `build_preliminary_sow_outline`
  with one new optional parameter, `approved_commercial_scenario_name:
  Optional[str]` -- a plain string, never a `PricingScenario` object.
  When provided, appends only the scenario's name plus the fixed
  sentence "Commercial terms are subject to final review." to the
  Document status section; no customer price, baseline cost,
  contingency, gross profit, margin, markup, internal rate, or approval
  note is ever included (EAP.M4-D1 item 2). The module structurally
  still never imports `PricingScenario`/`BaselineCostResult`/
  `RoleCostRow`/`RateCardEntry` -- verified directly via a new AST-based
  test (`test_sow_outline_engine_never_imports_pricing_scenario_model`),
  the same structural-impossibility approach used for M3's boundary.
- UI: a "Commercial pricing" section renders after Baseline Cost
  (gated on a `BaselineCostResult` existing) with a side-by-side
  comparison table plus one expander per scenario (editable contingency
  %, target margin %, and -- Custom only -- name/description; per-
  scenario Recalculate and Reset-to-defaults; approval note, warning
  acknowledgements, and Approve/Replace-approval/Remove-approval
  controls; a "How was customer price calculated?" expander with
  substituted values and both the difference-from-Recommended and
  difference-from-baseline). Scenarios are calculated immediately on
  first creation (not left at a blank `customer_price: None` requiring
  a manual click) -- this is ordinary initial computation, not the
  "recalculate only after explicit action" rule, which governs
  baseline-drift recalculation specifically.
- No change to `src/complexity_engine.py`, `src/sizing_engine.py`,
  `src/contract_fit.py`, `src/phase_planner.py`, or `src/resource_planner.py`.
  M3's existing `pricing_engine.py` functions (`load_rate_card`,
  `build_baseline_cost`, `reset_role_rate`, `reset_all_rates`,
  `reconcile_rate_state`) are unmodified -- M4 only adds new functions
  to the same file. No support pricing, final SOW, export functionality,
  database, authentication, or persistence was introduced.

**Source:** EAP.M4, run from the live repository root, following
approval of the pre-edit 15-point Change-Impact Report and the ten
numbered confirmations in EAP.M4-D1.
