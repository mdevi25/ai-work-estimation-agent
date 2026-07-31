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

This repository currently contains only the initial bootstrap
structure. No estimation, sizing, pricing, support, or SOW logic has
been implemented yet. See `decision_log.md` for the decisions recorded
so far and `docs/architecture.md` for the current (prototype-stage)
architecture.

Milestones are tracked in this repository's `CLAUDE.md`. The next
milestone is **MVP.M1 — Estimation foundation**.

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

- `app.py` — Streamlit entry point (placeholder only at this stage)
- `pages/` — additional Streamlit pages (empty at this stage)
- `src/` — deterministic engines and structured models (empty at this
  stage)
- `data/` — CSV/JSON business-rule configuration (empty at this stage)
- `tests/` — engine and application tests
- `docs/` — architecture documentation
- `prompts/work-estimation/` — staged milestone prompts

## Governance

This repository is governed by its own `CLAUDE.md`, which imports
`GUARDRAILS.md` and `PROTOCOL.md`. Code and configuration changes
follow the `pdlc-workflow` skill and this repository's Change-Impact
Gate. See `decision_log.md` for the append-only record of verified
decisions.
