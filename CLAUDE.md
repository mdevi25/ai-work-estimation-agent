<!--
PURPOSE:    Staged project CLAUDE.md for the AI Work Estimation and Pricing Assistant -- scope, skill whitelist, connectors, scope-specific rules, the Change-Impact Gate, and the working protocol for the future deployed application repository.
UPSTREAM:   Follows the structure of projects/_template/CLAUDE.md and the header/versioning conventions in CONTRIBUTING.md. Follows GUARDRAILS.md's standards (imported globally via the root CLAUDE.md). Reads skills/work-estimation/SKILL.md and its ten references (BUSINESS-RULES.md, ENGINE-RESPONSIBILITIES.md, ESTIMATE-TYPES.md, COMPLEXITY-AND-SIZING.md, PHASE-RESOURCE-PLANNING.md, PRICING-RULES.md, CONTRACT-FIT.md, SUPPORT-MODELS.md, RESPONSIBLE-AI.md, SOW-RULES.md) for domain rules, skills/pdlc-workflow/SKILL.md for governed code changes, skills/retro-log/SKILL.md for milestone logging, and skills/architecture-governance/SKILL.md plus standards/PRINCIPLES.md for conditional architecture review. Retrieves: milestone sequence, visibility boundaries, and terminology from BUSINESS-RULES.md; engine ownership from ENGINE-RESPONSIBILITIES.md; all finalized EAP.D1-EAP.D12 decisions as already encoded in those reference files.
DOWNSTREAM: Not active from this staged location. Once copied into the root of the future private GitHub repository for this project as `CLAUDE.md`, it governs that repository's Claude Code sessions alongside the global `~/.claude/CLAUDE.md` and its imports and the globally deployed `work-estimation` skill. Generates `decision_log.md`, `RETRO.md`, and (conditionally) `docs/architecture.md` at that deployed location, never staged here.
EXPECT:     Scope, skill whitelist, connectors, scope-specific rules, and the Change-Impact Gate procedure -- not application code, not milestone prompts, and not a record of the gate actually being run (that happens per-request once this file is deployed).
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Project: AI Work Estimation and Pricing Assistant

> GUARDRAILS.md at the root of this system applies here and everywhere else — it is not overridden by anything in this file.

## Scope

**Project purpose**

Build a zero-cost, explainable planning-estimation application that
converts a business request into:

- Estimate type
- Complexity assessment
- Fibonacci-style Relative Job Size
- Business-friendly T-shirt size
- Sprint range
- Planning duration
- Contract-duration fit
- Phase-based resource effort
- Lean, Balanced, Specialized, or Customer-defined staffing
- Baseline delivery cost
- Optional contingency
- Optional target margin
- Proposed customer price
- Warranty, maintenance, and enhancement support estimates
- Plain-language customer summary
- Draft SOW content

The deterministic calculation engine is authoritative.

AI may later:

- Extract structured inputs
- Identify missing information
- Suggest assumptions and risks
- Explain approved results
- Rewrite approved content in plain language

AI must not invent or override authoritative values or commitments.

**In scope**

- Python 3.11 or 3.12
- Streamlit
- Pandas
- Pydantic
- Pytest
- CSV or JSON configuration files
- Private GitHub repository
- Streamlit Community Cloud
- Deterministic calculation engines
- Configurable business rules
- Human review and overrides
- Responsible AI pre- and post-generation validation
- Customer-facing estimate summaries
- SOW-ready draft content

**Supported estimate types**

- New Project
- Enhancement
- Production Support
- Maintenance Support
- Enhancement Support
- Implementation plus Support
- Discovery or Assessment

**Out of scope for early milestones**

- Database
- Authentication
- Docker
- Paid APIs
- LangChain
- LangGraph
- CrewAI
- AutoGen
- AI API integration before MVP.M7
- Spreadsheet-first implementation
- Jira integration
- Enterprise workflow integration
- Detailed implementation scheduling
- PTO, holiday, meeting, ceremony, training, administrative, or
  person-specific availability deductions
- Static PM-template generation through `pm-template-builder`

**Explicit boundary**

This project builds a working deterministic product, not a reusable
static template artifact.

Do not invoke `pm-template-builder`.

## Skills that apply here

Whitelist exactly:

- work-estimation
- pdlc-workflow
- retro-log
- architecture-governance

**Usage**

- **work-estimation** — primary domain skill for all estimation, sizing,
  resource, pricing, support, contract-fit, Responsible AI, and SOW work.
- **pdlc-workflow** — required for governed code and configuration
  changes.
- **retro-log** — use at validated milestone completion in the deployed
  project repository.
- **architecture-governance** — whitelisted but conditional. Invoke at
  defined gates, not for every routine code edit.

**Architecture-governance gates**

1. Before MVP.M1 implementation planning: establish initial separation
   of UI, engines, configuration, and data flow.
2. Before MVP.M6: validate internal versus customer-output boundaries.
3. Before MVP.M7: validate AI intake boundary, replaceability, and
   human-review points.
4. On explicit request for material changes involving:
   - Architecture
   - Data flow
   - Security
   - Deployment
   - Cost-bearing services
   - Persistent storage
   - Authentication
   - AI-provider integration

**Do not whitelist**

- pm-template-builder
- jira-triage
- jira-status
- resume-tailor
- unrelated skills

## Connectors used

- No connectors are required for MVP.M1-MVP.M6.
- No database or external system is connected in early milestones.
- A future AI API may be introduced only in MVP.M7 after deterministic
  calculations and Responsible AI controls are validated.
- Streamlit Community Cloud deployment may require repository access and
  secrets configuration later.
- Secrets must never be committed.

## Scope-specific rules

**1. Deterministic authority**

- Calculation engines are authoritative.
- AI must not become the source of truth for:
  - Complexity
  - Relative Job Size
  - T-shirt size
  - Sprint range
  - Duration
  - Resources
  - Pricing
  - Warranty
  - Support capacity
  - Deliverables
  - Commercial commitments

**2. Planning boundary**

Contract duration is a planning and commercial boundary only.

Do not deduct:

- Public holidays
- PTO
- Meetings
- Scrum ceremonies
- Training
- Administrative time
- Unplanned-work reserve
- Person-specific availability

**3. Internal and customer views**

Internal view may show:

- Complexity score
- Relative Job Size
- T-shirt size
- Sprint range
- Role effort
- Internal rates
- Baseline cost
- Contingency
- Margin
- Gross profit
- Discounts and adjustments
- Override history

Customer view must not expose:

- Complexity score
- Fibonacci Relative Job Size by default
- Internal rates
- Internal delivery cost
- Contingency reserve
- Target margin
- Gross profit
- Staffing optimization logic

T-shirt size may appear when useful.

**4. Engine and UI separation**

- Streamlit pages collect inputs and display outputs.
- Streamlit pages must not contain core formulas.
- Business rules belong in configuration files.
- Engines consume structured models.
- Engines must not read directly from Streamlit session state.
- Tests validate each engine independently.

**5. Milestone discipline**

Only the approved milestone may be implemented.

Milestones:

- MVP.M1 — Estimation foundation
- MVP.M2 — Phase and resource planning
- MVP.M3 — Baseline pricing
- MVP.M4 — Commercial pricing
- MVP.M5 — Support estimation
- MVP.M6 — Customer and SOW output
- MVP.M7 — AI-assisted intake

Do not skip a milestone without explicit approval.

**6. Responsible AI**

Before generating customer summaries, proposals, or SOW content:

- Require approved structured values.
- Run the Responsible AI pre-generation gate.
- Prevent disclosure of restricted internal data.
- Prevent unsupported guarantees.
- Preserve material assumptions, risks, dependencies, and exclusions.
- Run post-generation validation.
- Require human business and legal review where applicable.

Statuses:

- Ready for AI Drafting
- Human Review Required
- Generation Blocked

These statuses must remain separate from PROTOCOL triage statuses.

**7. SOW content**

Generate only from `ApprovedEstimate`.

Never invent:

- Price
- Timeline
- Scope
- Deliverables
- Hours
- Resource quantities
- Warranty
- Support capacity
- Service level
- Acceptance criteria
- Commercial model

Every draft must include:

> "Draft for business and legal review. This language is not binding
> until approved and incorporated into an executed agreement."

## Knowledge files in this project

The deployed project should maintain:

- `README.md`
- `decision_log.md`
- `docs/architecture.md` when architecture-governance is invoked
- `docs/architecture-diagram.mmd` when applicable
- `RETRO.md` at validated milestones

The globally deployed `work-estimation` skill and its references remain
the domain source of truth.

The live application repository may also contain:

- `data/` configuration files
- `src/` engine files
- `tests/`
- Streamlit pages

## Architecture documentation

- Architecture documentation is required at defined gates, not every
  edit (see the architecture-governance gates above).
- Initial architecture should document:
  - Streamlit UI
  - Structured models
  - Deterministic engines
  - Configuration files
  - Internal/customer output boundary
  - Responsible AI gate
  - Future replaceable AI adapter
- Generated architecture documents live in the deployed project
  repository, not inside `AI-PPM/projects/`.

## Where this file lives

- This file is staged at: `AI-PPM/projects/ai-work-estimator/CLAUDE.md`
- It does not govern a live application while it remains only in
  AI-PPM.
- Copy it into the root of the actual private GitHub repository as
  `CLAUDE.md`.
- Run Claude Code from the deployed project repository root.
- The deployed project receives:
  - Global `~/.claude/CLAUDE.md` and imports
  - Globally deployed skills
  - This project-specific `CLAUDE.md`

## Retrospective log

- `RETRO.md` exists only in the deployed project repository.
- It is created or updated through `retro-log` at validated milestones.
- It is not staged inside `AI-PPM/projects/ai-work-estimator/`.

## Change-Impact Gate

Before modifying any validated:

- Business rule
- Complexity weight
- Sizing band
- Sprint range
- Formula
- Threshold
- Estimate type
- Phase rule
- Resource rule
- Staffing model
- Rate assumption
- Pricing behavior
- Contract-fit rule
- Support model
- Workflow
- Structured data model
- Customer-facing output
- SOW behavior
- Responsible AI control
- Technology choice
- Deployment behavior

Claude must first:

1. Classify the requested change.
2. Identify affected files.
3. Identify affected business rules.
4. Identify upstream dependencies.
5. Identify downstream impact.
6. State expected behavior after the change.
7. State expected output.
8. Identify backward-compatibility or reproducibility risk.
9. List required tests.
10. List required documentation and decision-log updates.
11. Ask only unresolved, decision-critical questions.
12. Present the proposed implementation scope.
13. Stop for explicit approval before editing.

The impact review must consider, where applicable:

- Complexity and sizing
- Sprint and duration
- Contract fit
- Phase planning
- Resource effort
- Baseline cost
- Contingency
- Margin
- Customer price
- Support estimates
- Customer summary
- SOW content
- Responsible AI validation
- Existing tests
- Existing estimates or reproducibility
- Configuration versioning

**Limited bypass**

Allow a limited bypass only when all are true:

- The change is strictly typographical or formatting-only.
- Meaning does not change.
- Behavior does not change.
- No formula, threshold, label meaning, field, workflow, output, or
  validation rule changes.
- No customer or commercial commitment changes.

If uncertain whether meaning or behavior changes, run the full gate.

This bypass must not apply to:

- Business terminology
- Customer-facing wording with contractual meaning
- Disclaimers
- SOW clauses
- Financial labels
- Status labels
- Field names used by code or configuration
- Test expectations

## Working protocol

For every code or configuration change:

1. Read this `CLAUDE.md`.
2. Read `decision_log.md` in the deployed project.
3. Read the applicable work-estimation references.
4. Use `pdlc-workflow`.
5. Inspect current files and tests.
6. Apply the Change-Impact Gate when required.
7. Work on one approved milestone or approved change only.
8. Provide complete ready-to-publish files, not partial fragments, when
   presenting file replacements.
9. Preserve existing syntax and validated behavior.
10. Run tests.
11. Update `README.md` and `decision_log.md` when required.
12. Stop for review before commit preparation.
13. Do not proceed automatically to the next milestone.

## Current status

- Framework staging in progress
- Work-estimation skill completed
- Staged project instructions being created
- Application repository not yet created
- MVP.M1 not yet started
