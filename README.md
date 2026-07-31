# AI Work Estimation and Pricing Assistant

A zero-cost, explainable planning-estimation application that converts a
business request into a deterministic, reviewable estimate: complexity,
Relative Job Size, T-shirt size, sprint range, phase-based resource
effort, baseline delivery cost, optional contingency and margin,
proposed customer price, support estimates, and draft SOW content.

The deterministic calculation engine is authoritative. AI may extract
inputs, explain results, or draft content from approved values — it
never invents or overrides approved calculations or commercial
commitments.

## Status

**MVP.M1 — Estimation foundation (remediated by EAP.M1.UI1 and
EAP.M1.UI2), MVP.M2 — Phase and resource planning, and MVP.M3 —
Baseline cost and rate card are implemented and awaiting browser-based
UI acceptance.** The app is a guided, self-service 5-step wizard (Work
type → Quick facts → Scope checklist → Complexity and AI → Review and
estimate) with a persistent left-side panel showing step status, the
current estimate, a running (preliminary) size/duration preview, and
warning status. It produces: work-type classification, weighted
complexity, Relative Job Size, T-shirt size, sprint range, estimated
duration, contract-fit status, editable generated assumptions, a
**Generate Preliminary SOW Outline** action producing a draft outline
from already-captured data (clearly marked "Preliminary Draft" with the
mandatory disclaimer, downloadable as Markdown or plain text), a
**Build Resource Plan** action producing an editable phase/role/hours
plan: phase duration in sprints, required roles and allocation by
phase, person-sprints and estimated hours, four staffing patterns
(Lean, Balanced, Specialized, Customer-defined) that change only who is
assigned — never the required effort — plain-language allocation and
role-combination warnings, and an optional AI workstream that appears
only when AI is enabled and disappears entirely when it's turned off.

New in MVP.M3: once a resource plan exists, a **Baseline delivery cost**
section converts the resource plan's role hours into cost using a
configured rate card (`data/rate_card.csv`, illustrative/fictional
rates only). Each role shows its total hours (read-only), configured
default rate (read-only), an editable session-only scenario rate, and
an editable override reason (required whenever the scenario rate
differs from the default). The section shows role cost, the $ and %
difference from default, the baseline delivery cost total, and a
blended hourly rate — displayed as "Not available — total estimated
hours are zero" rather than a fabricated 0.00 when there are no hours.
A commercial-risk warning appears whenever a scenario rate is set below
the configured default. A **pricing readiness status** (Ready for
Baseline Review / Human Review Required / Calculation Blocked) governs
whether the numbers are ready for internal review, following a fixed
precedence: Blocked beats Human Review, which beats Ready. Individual
and "reset all" controls restore configured defaults; switching
staffing models, toggling AI, or editing resource-plan hours
automatically reconciles stale rate overrides. No contingency, margin,
markup, discount, or customer price exists anywhere in this milestone —
that is MVP.M4 scope. The resource plan's and baseline cost's presence
also flow into the preliminary SOW outline as additional preliminary
planning information and a status-only sentence, respectively — never
as amounts, rates, or dollar figures.

Three other actions on the results screen (Generate Final SOW, Export
to Excel, Export to PowerPoint) remain intentionally locked/disabled
with labels stating what milestone unlocks them — this project never
shows an active, unqualified "Generate SOW" button.

No governed commercial pricing, support estimation, final/
customer-approved SOW generation, Excel/PowerPoint export, or
AI-assisted intake exists yet — all deferred to MVP.M4 through MVP.M7.
See `decision_log.md` for the decisions recorded so far and
`docs/architecture.md` for the current architecture.

**Every MVP.M milestone (including this one) ends with a mandatory
browser-based UI review checkpoint.** The next milestone (MVP.M4 —
Commercial pricing) does not begin until this UI is explicitly reviewed
and accepted in the browser.

## Requirements

- Python 3.12
- See `requirements.txt` for pinned dependencies

## Setup (Windows)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the app

```powershell
streamlit run app.py
```

## Run tests

```powershell
pytest
```

## Project structure

- `app.py` — Streamlit UI: the 5-step estimation wizard and persistent
  sidebar. No business formulas live here.
- `pages/` — additional Streamlit pages (still empty; the wizard uses a
  single page with internal step-state, see `docs/architecture.md` §8)
- `src/` — structured models (`models.py`), shared validation
  (`validators.py`), JSON/CSV config loading (`config.py`), the three
  deterministic estimation engines (`complexity_engine.py`,
  `sizing_engine.py`, `contract_fit.py`, all unchanged since MVP.M1),
  the phase/resource planning engines (`phase_planner.py`,
  `resource_planner.py`, unchanged since MVP.M2 — no rates or cost
  anywhere in either), the baseline-cost engine (`pricing_engine.py` —
  rate-card loading, role cost, baseline delivery cost, blended rate,
  and pricing-readiness status; no contingency, margin, markup,
  discount, or customer price anywhere in it), and the UI-support
  helpers `scope_defaults.py` (scope-checklist defaults and
  scope-confirmation math), `assumption_engine.py` (template-based
  assumption generation), `running_estimate_preview.py`
  (non-authoritative "Preliminary" sidebar preview), and
  `sow_outline_engine.py` (the lightweight Responsible-AI-style gate
  and the preliminary SOW outline builder/renderers — explicitly not
  the governed MVP.M6 SOW capability)
- `data/` — governed JSON/CSV configuration: complexity weights and
  questions, sizing bands, contract terms, work types, scope-checklist
  defaults, assumption templates, the simplified AI-intake option
  catalog, phase rules and weights, resource/role rules (including the
  AI-activity-to-phase/role mapping), role-combination rules, the
  configured rate card (`rate_card.csv` — illustrative/fictional
  demonstration rates only), the preliminary SOW outline's customer/
  vendor-responsibility and next-steps templates, and the original
  estimate-type/AI-workstream-activity catalogs (retained for internal
  compatibility and the advanced/optional AI section)
- `tests/` — one test module per engine/validator/helper, an
  `AppTest`-driven wizard/sidebar/transparency test module, and the
  bootstrap smoke test
- `docs/` — architecture documentation
- `prompts/work-estimation/` — staged milestone prompts

## Governance

This repository is governed by its own `CLAUDE.md`, which imports
`GUARDRAILS.md` and `PROTOCOL.md`. Code and configuration changes
follow the `pdlc-workflow` skill and this repository's Change-Impact
Gate. See `decision_log.md` for the append-only record of verified
decisions.
