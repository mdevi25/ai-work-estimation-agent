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
