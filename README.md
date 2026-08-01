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
EAP.M1.UI2), MVP.M2 — Phase and resource planning, MVP.M3 — Baseline
cost and rate card, and MVP.M4 — Commercial scenario pricing and
approval are implemented and awaiting browser-based UI acceptance.**
The app is a guided, self-service 5-step wizard (Work type → Quick
facts → Scope checklist → Complexity and AI → Review and estimate)
with a persistent left-side panel showing step status, the current
estimate, a running (preliminary) size/duration preview, and warning
status. It produces: work-type classification, weighted complexity,
Relative Job Size, T-shirt size, sprint range, estimated duration,
contract-fit status, editable generated assumptions, a **Generate
Preliminary SOW Outline** action producing a draft outline from
already-captured data (clearly marked "Preliminary Draft" with the
mandatory disclaimer, downloadable as Markdown or plain text), a
**Build Resource Plan** action producing an editable phase/role/hours
plan, and (once a resource plan exists) a **Baseline delivery cost**
section converting role hours into cost via a configured rate card
(`data/rate_card.csv`, illustrative/fictional rates only), with
editable session-only scenario rates, override reasons, a blended
hourly rate, and a pricing-readiness status.

New in MVP.M4: once a baseline delivery cost exists, a **Commercial
pricing** section converts it into four governed commercial scenarios
— **Recommended**, **Competitive**, **Conservative**, and **Custom**
(fully editable) — each carrying its own contingency percentage and
target margin percentage (`data/commercial_pricing_defaults.json`,
flagged prototype values). Each scenario computes, at full internal
precision with two-decimal display, contingency amount, risk-adjusted
delivery cost, customer price, gross profit, achieved margin, and
equivalent markup — no discount, rounding, or management-adjustment
lever exists in this milestone. A side-by-side comparison table and
per-scenario cards show a **commercial readiness status** (Ready for
Commercial Review / Human Review Required / Approval Blocked,
Blocked-first precedence) and a separate **approval status** (Draft /
Review Required / Approved / Approval Blocked) — a scenario can be
"Ready for Commercial Review" while still "Draft." Approving a scenario
requires a written note and acknowledging any delivery-risk or
commercial-risk warnings, checked only at the moment of approval; a
missing note never invalidates a scenario's own calculation. Exactly
one scenario may be Approved at a time — approving a different one
replaces the previous approval while fully preserving its inputs and
numbers. A customer price below the calculated delivery cost is always
Approval Blocked, with no override or exception path. Any change to
role rates, hours, the resource plan, or the AI workstream invalidates
existing approval and clearly states why, without silently discarding
scenario inputs; recalculation itself is always an explicit action.
The approved scenario's **name only** (never an amount) may flow into
the preliminary SOW outline alongside a fixed "Commercial terms are
subject to final review" sentence.

Three other actions on the results screen (Generate Final SOW, Export
to Excel, Export to PowerPoint) remain intentionally locked/disabled
with labels stating what milestone unlocks them — this project never
shows an active, unqualified "Generate SOW" button.

No support estimation, final/customer-approved SOW generation,
Excel/PowerPoint export, or AI-assisted intake exists yet — all
deferred to MVP.M5 through MVP.M7. See `decision_log.md` for the
decisions recorded so far and `docs/architecture.md` for the current
architecture.

**Every MVP.M milestone (including this one) ends with a mandatory
browser-based UI review checkpoint.** The next milestone (MVP.M5 —
Support and maintenance pricing) does not begin until this UI is
explicitly reviewed and accepted in the browser.

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
  anywhere in either), the baseline-cost and commercial-pricing engine
  (`pricing_engine.py` — MVP.M3's rate-card loading, role cost, baseline
  delivery cost, blended rate, and pricing-readiness status, plus
  MVP.M4's contingency, risk-adjusted cost, customer price, gross
  profit, achieved margin, equivalent markup, commercial-readiness/
  approval-status derivation, baseline-drift detection, and the
  approval gate — no discount, rounding, or management-adjustment lever
  anywhere in it), and the UI-support helpers `scope_defaults.py`
  (scope-checklist defaults and scope-confirmation math),
  `assumption_engine.py` (template-based assumption generation),
  `running_estimate_preview.py` (non-authoritative "Preliminary"
  sidebar preview), and `sow_outline_engine.py` (the lightweight
  Responsible-AI-style gate and the preliminary SOW outline
  builder/renderers — explicitly not the governed MVP.M6 SOW capability)
- `data/` — governed JSON/CSV configuration: complexity weights and
  questions, sizing bands, contract terms, work types, scope-checklist
  defaults, assumption templates, the simplified AI-intake option
  catalog, phase rules and weights, resource/role rules (including the
  AI-activity-to-phase/role mapping), role-combination rules, the
  configured rate card (`rate_card.csv` — illustrative/fictional
  demonstration rates only), the four governed commercial scenario
  defaults plus maximum contingency and material-difference thresholds
  (`commercial_pricing_defaults.json` — flagged prototype commercial
  percentages), the preliminary SOW outline's customer/vendor-
  responsibility and next-steps templates, and the original estimate-
  type/AI-workstream-activity catalogs (retained for internal
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
