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

This document covers the current bootstrap-stage skeleton: the
Streamlit entry point, the empty `src/`, `pages/`, and `data/`
directories that will hold engines, additional UI pages, and
configuration respectively, and the test scaffold. It establishes the
initial separation of UI, engines, configuration, and data flow
required before MVP.M1, per this repository's `CLAUDE.md`.

## 4. Out-of-scope items

No estimation, sizing, resource-planning, pricing, support, SOW, or AI
logic exists yet — all deferred to MVP.M1 through MVP.M7. Database,
authentication, Docker, and paid APIs are out of scope for early
milestones per `CLAUDE.md` and are not present here.

## 5. Current project stage

**Prototype** (pre-MVP.M1 bootstrap). Complexity of this document is
intentionally minimal to match: most sections below describe what will
exist, not what exists today, and are marked accordingly.

## 6. Functional requirements

At this stage: the application must start and render a placeholder
page with no errors. No other functional requirement applies yet —
full functional requirements are defined per milestone in
`CLAUDE.md` and the `work-estimation` skill's reference files as each
milestone is implemented.

## 7. Non-functional requirements

None formally defined yet at this bootstrap stage. The product is
intended to run as a single-user Streamlit Community Cloud deployment
with no database, so throughput/availability requirements are expected
to remain minimal; this will be revisited if that assumption changes.

## 8. Architecture overview

A single Streamlit application (`app.py` plus future `pages/`) presents
inputs and renders outputs, calling into deterministic engines under
`src/` that read business rules from configuration files under `data/`
(CSV/JSON, no database). This shape was chosen over a spreadsheet-first
or database-backed design because the project's explicit scope
excludes a database and requires configurable-but-versioned business
rules — CSV/JSON in source control gives that without added
infrastructure cost.

## 9. Component responsibilities

- **`app.py` / `pages/`** — Streamlit UI. Collects inputs, displays
  outputs. Must not contain core formulas (per `CLAUDE.md` §"Engine and
  UI separation"). Currently a placeholder page only.
- **`src/`** — deterministic calculation engines and Pydantic
  structured models (empty at this stage; populated starting MVP.M1).
  Engines must not read directly from Streamlit session state.
- **`data/`** — CSV/JSON configuration for business rules (empty at
  this stage).
- **`tests/`** — validates each engine independently, plus the
  bootstrap smoke test currently present (`test_smoke.py`).
- No external systems, APIs, or connectors exist yet. A future AI
  provider adapter is planned no earlier than MVP.M7 and will be
  documented here (§11) when introduced.

## 10. Data flow

**Current state (bootstrap):** no data flow exists — `app.py` renders
static placeholder text with no inputs, storage, or transformations.

**Target state (from MVP.M1 onward):** user input entered in Streamlit
→ structured Pydantic model → deterministic engine(s) in `src/` read
configuration from `data/` → structured result returned to the UI for
display, with an internal/customer-facing view split enforced at the
UI layer (per `CLAUDE.md` §3). No sensitive data, PII, or credentials
are expected in this flow; system of record for business rules is the
versioned `data/` configuration files themselves. This will be
elaborated with the read/write paths for approvals and overrides once
MVP.M1–M3 introduce them.

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

None yet — no AI-generated or engine-generated output exists. Once
introduced, engine output will be classified as **advisory** (a
planning estimate for human review) per `standards/PRINCIPLES.md`
§7, and any customer-facing summary or SOW content will require
explicit human review before distribution (`CLAUDE.md` §6–7,
`RESPONSIBLE-AI.md`). This document will name the exact review point
in the flow once that logic exists.

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

## 20. Known limitations

- No business logic exists yet — this document describes a skeleton,
  not a working estimator.
- No automated test coverage beyond the smoke test (`test_smoke.py`),
  which only confirms `app.py` is present and syntactically valid.
- No CI/CD pipeline exists; validation is manual (`pytest`, `streamlit
  run`) at this stage.

## 21. Future considerations

- MVP.M1 introduces the first deterministic engine (estimation
  foundation) and will require updating §6–10, 13, and 19 of this
  document.
- MVP.M7 introduces an AI adapter and will require populating §11 in
  full, including the replaceable-interface design and human-review
  gating specific to AI-assisted intake.

## 22. Validation criteria

This bootstrap stage is considered complete when: the virtual
environment installs cleanly, `streamlit run app.py` starts without
import errors, `python -m pytest` passes, and the repository structure
matches the approved bootstrap file list in `decision_log.md`. Moving
to MVP.M1 requires this validation to pass first.

## 23. Architecture diagram

See `architecture-diagram.mmd` in this same `docs/` folder.
