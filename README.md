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

**MVP.M1 — Estimation foundation, remediated by EAP.M1.UI1 and
EAP.M1.UI2, is implemented and awaiting browser-based UI acceptance.**
The app is a guided, self-service 5-step wizard (Work type → Quick
facts → Scope checklist → Complexity and AI → Review and estimate)
with a persistent left-side panel showing step status, the current
estimate, a running (preliminary) size/duration preview, and warning
status. It produces: work-type classification, weighted complexity,
Relative Job Size, T-shirt size, sprint range, estimated duration,
contract-fit status, editable generated assumptions, and (new) a
**Generate Preliminary SOW Outline** action producing a 21-section
draft outline from already-captured data, clearly marked "Preliminary
Draft" with the mandatory disclaimer and downloadable as Markdown or
plain text. Four other actions on the results screen (Generate Final
SOW, Export to Excel, Export to PowerPoint, Build Resource Plan) are
intentionally locked/disabled with labels stating what milestone
unlocks them — this milestone never shows an active, unqualified
"Generate SOW" button.

A separate, clearly labeled "Future pricing interaction preview"
section demonstrates a future role/hours/rate interaction pattern with
illustrative example values only — it is not connected to this
estimate, not part of the SOW outline, and not a customer quote.

No phase planning, resource planning, governed pricing, contingency,
margin, support estimation, final/customer-approved SOW generation,
Excel/PowerPoint export, or AI-assisted intake exists yet — all
deferred to MVP.M2 through MVP.M7. See `decision_log.md` for the
decisions recorded so far and `docs/architecture.md` for the current
architecture.

**Every MVP.M milestone (including this one) now ends with a mandatory
browser-based UI review checkpoint.** The next milestone (MVP.M2 —
Phase and resource planning) does not begin until this UI is explicitly
reviewed and accepted in the browser.

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
  (`validators.py`), JSON config loading (`config.py`), the three
  deterministic engines (`complexity_engine.py`, `sizing_engine.py`,
  `contract_fit.py`, all unchanged since MVP.M1), and the UI-support
  helpers `scope_defaults.py` (scope-checklist defaults and
  scope-confirmation math), `assumption_engine.py` (template-based
  assumption generation), `running_estimate_preview.py`
  (non-authoritative "Preliminary" sidebar preview), and
  `sow_outline_engine.py` (the lightweight Responsible-AI-style gate
  and the preliminary SOW outline builder/renderers — explicitly not
  the governed MVP.M6 SOW capability)
- `data/` — governed JSON configuration: complexity weights and
  questions, sizing bands, contract terms, work types, scope-checklist
  defaults, assumption templates, the simplified AI-intake option
  catalog, the preliminary SOW outline's customer/vendor-responsibility
  and next-steps templates, and the original estimate-type/
  AI-workstream-activity catalogs (retained for internal compatibility
  and the advanced/optional AI section)
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
