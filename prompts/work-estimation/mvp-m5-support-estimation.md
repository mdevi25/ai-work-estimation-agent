<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M5 -- warranty, stabilization, maintenance, enhancement support, and combined first-year contract estimates.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m4-commercial-pricing.md has already been run and approved. Retrieves: support definitions and commercial-model structures from skills/work-estimation/references/SUPPORT-MODELS.md, Production Support and Implementation plus Support type rules from ESTIMATE-TYPES.md, and the pricing formulas this milestone reuses from PRICING-RULES.md.
DOWNSTREAM: Produces src/support_estimator.py, support configuration, a support view, and tests in the live repository. Hands off to prompts/work-estimation/mvp-m6-customer-sow-output.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds support estimation only -- no customer SOW generation or AI-assisted intake.
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Prompt: MVP.M5 -- support estimation

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M4 must already
be complete and approved. Claude Code must be launched from that live
repository root -- this prompt must not be run from inside AI-PPM as
though AI-PPM were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M5 -- Support estimation

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M4 is already complete and approved.
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
   - SUPPORT-MODELS.md
   - PHASE-RESOURCE-PLANNING.md
   - PRICING-RULES.md
   - CONTRACT-FIT.md
4. In scope for this milestone only:
   - src/support_estimator.py
   - Support configuration
   - Warranty and stabilization
   - Maintenance support
   - Enhancement capacity
   - Monthly retainer
   - Monthly capacity block
   - Sprint-based capacity
   - Time and materials
   - Base maintenance plus enhancement pool
   - Tiered support
   - Monthly recurring value
   - Annual support value
   - Total first-year contract value
   - Tests
   - Streamlit support view
5. Explicit exclusions -- do not build any of:
   - Customer SOW generation
   - AI-assisted intake
6. Likely files to create or modify:
   - src/support_estimator.py
   - support configuration under data/
   - tests for support_estimator.py
   - Streamlit support view
7. Required distinctions, per SUPPORT-MODELS.md section 1 -- implement
   as distinct, correctly labeled concepts, not synonyms:
   - Defect
   - Warranty
   - Stabilization
   - Maintenance
   - Enhancement
8. Production Support behavior, per ESTIMATE-TYPES.md section 5 and
   SUPPORT-MODELS.md section 3:
   - Unknown root cause produces an investigation estimate first.
   - A remediation estimate follows only after investigation findings
     exist.
   - No unsupported fixed remediation commitment may be produced before
     investigation completes.
9. Implementation plus Support behavior, per ESTIMATE-TYPES.md section 8
   and SUPPORT-MODELS.md section 4 -- calculate and display separately:
   1. Implementation
   2. Warranty and stabilization
   3. Maintenance
   4. Enhancement capacity
   5. First-year contract value
   Support work must never be silently absorbed into implementation
   capacity.
10. Reuse the pricing formulas from src/pricing_engine.py (MVP.M3 and
    MVP.M4) for any cost or price calculation inside
    support_estimator.py -- do not redefine baseline cost, contingency,
    or margin formulas here.
11. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
    section) before changing any validated business rule, formula,
    threshold, mapping, or terminology established in MVP.M1-MVP.M4.
12. Use pdlc-workflow for all code changes: inspect, plan, execute this
    one milestone only, stop for review, prepare a commit summary.
13. architecture-governance is not required for this milestone unless
    you hit a material architectural, data-flow, security, or
    persistent-storage decision -- if that happens, stop and tell me
    explicitly.
14. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
15. Use these Windows-friendly commands where applicable:
    - Activate the virtual environment: `.venv\Scripts\Activate.ps1`
    - Install any new dependencies: `pip install -r requirements.txt`
    - Run the app: `streamlit run app.py`
    - Run tests: `pytest`
16. Expected output / completion criteria:
    - Each of the six support commercial structures produces a correctly
      labeled result with its capacity basis, included services, and
      exclusions.
    - Production Support with unknown root cause correctly stops at an
      investigation estimate and does not fabricate a remediation price.
    - Implementation plus Support displays all five required components
      separately, plus the combined first-year total.
    - All tests pass.
17. Run tests and confirm they pass before reporting the milestone
    complete.
18. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
19. Validation checklist -- confirm all of:
    - Defect/warranty/stabilization/maintenance/enhancement remain
      distinct in code, data, and UI labels
    - Unknown-root-cause Production Support never produces a fixed
      remediation price
    - Implementation plus Support always shows all five components
      separately, never merged
    - support_estimator.py calls into pricing_engine.py rather than
      redefining baseline/contingency/margin formulas
20. List the exact files created, modified, or deleted.
21. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
22. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1-MVP.M4.
23. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
24. Application changes must occur only in this live repository, never
    inside AI-PPM.
25. Stop here. Do not advance to MVP.M6 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m6-customer-sow-output.md.
26. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M5

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

- Every support commercial structure in SUPPORT-MODELS.md section 2 must
  state its carryover-rule handling explicitly in both code and UI --
  don't leave carryover behavior implicit.
- This milestone is the last one before customer-facing and SOW output.
  Keep all support results internal-view only for now -- MVP.M6 defines
  what becomes customer-visible.
