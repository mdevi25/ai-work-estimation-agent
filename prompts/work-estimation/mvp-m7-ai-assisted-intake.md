<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M7 -- a replaceable AI-assisted intake adapter, added only after the deterministic engine and Responsible AI controls are validated.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m6-customer-sow-output.md has already been run and approved. Retrieves: the non-authoritative AI intake boundary from skills/work-estimation/references/ENGINE-RESPONSIBILITIES.md section 13, deterministic-authority rules from BUSINESS-RULES.md, and Responsible AI controls this adapter must not bypass from RESPONSIBLE-AI.md.
DOWNSTREAM: Produces a provider-neutral AI intake adapter and tests in the live repository. This is the final milestone in the current EAP milestone sequence.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Adds a non-authoritative, replaceable intake layer only -- it must never become the source of truth for any calculated or approved value.
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Prompt: MVP.M7 -- AI-assisted intake

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M6 must already
be complete and approved -- the deterministic engine path and Responsible
AI controls must be fully validated before this milestone begins. Claude
Code must be launched from that live repository root -- this prompt must
not be run from inside AI-PPM as though AI-PPM were the live application
repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M7 -- AI-assisted intake

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M6 is already complete and approved, and the deterministic engine
  path plus Responsible AI controls are fully validated.
- Claude Code is running from this live repository root -- not from
  inside AI-PPM.
If any prerequisite is not met, stop and tell me before doing anything
else.

Please:

1. Read the deployed project CLAUDE.md at the repository root.
2. Read decision_log.md.
3. Read these work-estimation references:
   - BUSINESS-RULES.md
   - ENGINE-RESPONSIBILITIES.md
   - ESTIMATE-TYPES.md
   - COMPLEXITY-AND-SIZING.md
   - RESPONSIBLE-AI.md
   - SOW-RULES.md
4. Before any implementation, invoke architecture-governance to validate:
   - AI boundary
   - Provider replaceability
   - Prompt and data minimization
   - Human-review points
   - Secret handling
   - Failure and fallback behavior
   - Cost controls
   Do not begin coding this milestone until that review is complete.
5. In scope for this milestone only:
   - Replaceable AI intake adapter
   - Provider-neutral interface
   - Structured extraction model
   - Missing-information detection
   - Suggested assumptions and risks
   - User review and correction step before any deterministic
     calculation runs
   - Optional plain-language rewriting of already-approved content
   - Secrets stored outside source control
   - Deterministic fallback path
   - Tests with mocked responses -- no network dependency in unit tests
6. Required AI boundaries -- AI may:
   - Extract proposed structured values
   - Identify missing information
   - Suggest questions
   - Suggest assumptions and risks
   - Explain approved deterministic results
   - Rewrite approved content
7. Required AI boundaries -- AI may not:
   - Authoritatively set complexity
   - Authoritatively assign Relative Job Size
   - Authoritatively set sprint range
   - Authoritatively set resources
   - Authoritatively calculate price
   - Invent deliverables
   - Invent warranty or support capacity
   - Override human-approved values
   - Bypass Responsible AI validation
8. The user must review and confirm every extracted value before any
   deterministic calculation engine runs on it -- no auto-calculation
   from raw AI extraction.
9. Explicitly require:
   - A free-tier or zero-cost-compatible provider option
   - A provider abstraction with no provider lock-in
   - No paid API without my explicit approval
   - No secrets committed anywhere in source control
   - Usage-limit handling
   - Graceful fallback to manual structured intake if the AI adapter is
     unavailable, rate-limited, or fails
10. Likely files to create or modify:
    - a provider-neutral AI intake adapter module under src/
    - a service-interface boundary separating the adapter from core
      engines (per architecture-governance principle 6)
    - structured extraction model additions to src/models.py
    - tests with mocked provider responses
    - Streamlit intake-review UI (extracted values shown for user
      confirmation/correction before calculation)
11. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
    section) before changing any validated business rule, formula,
    threshold, mapping, or terminology established in MVP.M1-MVP.M6.
    This milestone must not modify any existing engine's authoritative
    behavior -- it only adds a new, non-authoritative upstream path.
12. Use pdlc-workflow for all code changes: inspect, plan, execute this
    one milestone only, stop for review, prepare a commit summary.
13. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
14. Use these Windows-friendly commands where applicable:
    - Activate the virtual environment: `.venv\Scripts\Activate.ps1`
    - Install any new dependencies: `pip install -r requirements.txt`
    - Run the app: `streamlit run app.py`
    - Run tests: `pytest`
15. Expected output / completion criteria:
    - The AI intake adapter extracts a proposed structured value set from
      unstructured input and flags missing information.
    - Extracted values require explicit user confirmation before any
      deterministic engine consumes them.
    - The adapter is swappable behind its service interface without
      touching core engine code.
    - The app functions in deterministic-only mode when the AI adapter
      is unavailable.
    - All tests pass without a live network dependency.
16. Run tests and confirm they pass before reporting the milestone
    complete.
17. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
18. Validation checklist -- confirm all of:
    - No deterministic engine's output can be traced back to
      AI-extracted values without a human confirmation step in between
    - The adapter never appears as a direct dependency inside
      complexity_engine.py, sizing_engine.py, contract_fit.py,
      phase_planner.py, resource_planner.py, pricing_engine.py,
      support_estimator.py, sow_generator.py, or
      responsible_ai_validator.py
    - No secret appears in source code, tests, or committed configuration
    - Unit tests run with mocked responses only, with no network call
    - Fallback to manual structured intake works when the adapter fails
19. List the exact files created, modified, or deleted.
20. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
21. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1-MVP.M6.
22. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
23. Application changes must occur only in this live repository, never
    inside AI-PPM.
24. Stop here after MVP.M7. Do not begin any further milestone
    automatically -- wait for my explicit validation and direction on
    what comes next.
25. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M7

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

- This is the only milestone that introduces an AI API dependency --
  confirm the specific provider and cost model with me explicitly before
  adding it as a dependency, per GUARDRAILS.md section 3.
- If a paid API turns out to be necessary to meet the requirement, stop
  and ask rather than adding it -- the zero-cost constraint from this
  project's CLAUDE.md scope is a hard boundary, not a preference.
