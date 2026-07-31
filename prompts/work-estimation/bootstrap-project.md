<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the actual live Git repository root, to bootstrap the AI Work Estimation and Pricing Assistant repository after it has been created and cloned locally.
UPSTREAM:   Assumes the work-estimation skill is already deployed to ~/.claude/skills/work-estimation/ and projects/ai-work-estimator/CLAUDE.md has already been copied into the live repository root as CLAUDE.md. Retrieves: the initial repository structure, dependency list, and architecture-governance gate requirement from that deployed CLAUDE.md's "Skills that apply here" and "Change-Impact Gate" sections, and the header/prompt format from prompts/_template.md.
DOWNSTREAM: Produces the initial repository skeleton (README.md, decision_log.md, requirements.txt, app.py placeholder, pages/, src/__init__.py, data/, tests/__init__.py, docs/) in the live repository -- never in AI-PPM. Hands off to prompts/work-estimation/mvp-m1-estimation-foundation.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Creates repository scaffolding only -- no estimation business logic.
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Prompt: bootstrap the AI Work Estimation and Pricing Assistant repository

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
(copied from `AI-PPM/projects/ai-work-estimator/CLAUDE.md`) must already
exist at the live repository root. Claude Code must be launched from
that live repository root -- this prompt must not be run from inside
AI-PPM as though AI-PPM were the live application repository.

```
I'm bootstrapping the AI Work Estimation and Pricing Assistant
repository. This is the actual live Git repository, not AI-PPM.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Default branch: [DEFAULT_BRANCH]
- Development branch: [DEVELOPMENT_BRANCH]
- Python version: [PYTHON_VERSION]
- Project owner: [PROJECT_OWNER]
- Date: [DATE]

Please:

1. Confirm you are running from the actual live Git repository root at
   [LIVE_REPOSITORY_PATH], not from inside AI-PPM.
2. Confirm `.git` exists at this location.
3. Confirm the project-level `CLAUDE.md` exists at this repository root
   and matches AI-PPM/projects/ai-work-estimator/CLAUDE.md.
4. Confirm the `work-estimation` skill is deployed at
   `~/.claude/skills/work-estimation/`.
5. Confirm global Claude governance (`~/.claude/CLAUDE.md` and its
   imports of GUARDRAILS.md, PROTOCOL.md, RESPONSE-QUALITY.md) is
   active.
6. If any of checks 1-5 fail, stop here and tell me rather than
   proceeding.
7. Inspect the current repository state before creating anything --
   report what already exists and what is missing.
8. Invoke `architecture-governance` for the initial architecture gate
   (per this project's `CLAUDE.md`, "Before MVP.M1 implementation
   planning: establish initial separation of UI, engines, configuration,
   and data flow") before creating files.
9. Create only the approved initial repository structure -- no
   estimation business logic yet:
   - `README.md`
   - `decision_log.md`
   - `requirements.txt`
   - `app.py` (placeholder only)
   - `pages/`
   - `src/__init__.py`
   - `data/`
   - `tests/__init__.py`
   - `docs/`
10. Use these initial dependencies in `requirements.txt`, pinned to
    current stable versions you verify rather than assume:
    - streamlit
    - pandas
    - pydantic
    - pytest
11. Create a Streamlit placeholder page only in `app.py` (e.g., a title
    and a short description of the product) -- no calculation logic, no
    estimate-type input yet.
12. Do not add:
    - Database
    - Authentication
    - Docker
    - AI API
    - Paid services
13. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
14. Use these Windows-friendly commands where applicable:
    - Create a virtual environment: `python -m venv .venv`
    - Activate it: `.venv\Scripts\Activate.ps1`
    - Install dependencies: `pip install -r requirements.txt`
    - Start the placeholder app: `streamlit run app.py`
    - Run tests: `pytest`
15. Validate:
    - Python environment created and activated successfully
    - Package installation completes without error
    - Streamlit placeholder page starts successfully
    - Pytest starts successfully (even with zero tests collected)
    - Repository structure matches the approved list in step 9
16. Update `decision_log.md` with these three foundational decisions:
    - Deterministic engine before AI
    - CSV or JSON configuration before database
    - Private GitHub plus Streamlit Community Cloud
17. List the exact files created, modified, or deleted.
18. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
19. Apply the Change-Impact Gate (per this project's `CLAUDE.md`) for
    any deviation from this approved initial structure.
20. Stop here before MVP.M1. Do not begin estimation business logic.
    Wait for my explicit validation before proceeding to
    prompts/work-estimation/mvp-m1-estimation-foundation.md.
21. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.BOOTSTRAP

Files changed:
[list]

Decisions confirmed:
[concise numbered list]

Remaining blockers:
[None, or concise list]

Validation performed:
[concise list]

Next recommended action:
[one sentence]
```

## Notes

- This prompt creates repository scaffolding only. No estimate-type
  input, complexity scoring, sizing, pricing, or any other business
  logic belongs here -- that begins with
  `prompts/work-estimation/mvp-m1-estimation-foundation.md`.
- If `docs/architecture.md` does not yet exist when
  `architecture-governance` is invoked in step 8, it should be created
  using that skill's `templates/ARCHITECTURE-TEMPLATE.md` structure, at
  the live repository's `docs/` folder -- never staged inside AI-PPM.
- Do not run this prompt from inside AI-PPM. AI-PPM only stages the
  template that produced this file; it is never the live application
  repository.
