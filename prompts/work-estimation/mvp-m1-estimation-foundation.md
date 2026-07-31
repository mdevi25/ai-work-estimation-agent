<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M1 -- the estimation foundation (estimate type, complexity scoring, Relative Job Size, T-shirt sizing, sprint range, contract-fit input, and the optional AI capability intake field).
UPSTREAM:   Assumes prompts/work-estimation/bootstrap-project.md has already been run and approved. Retrieves: complexity dimensions/weights and sizing bands from skills/work-estimation/references/COMPLEXITY-AND-SIZING.md, estimate taxonomy and the AI capability intake field from ESTIMATE-TYPES.md section 11, contract-fit rules from CONTRACT-FIT.md, and engine ownership from ENGINE-RESPONSIBILITIES.md.
DOWNSTREAM: Produces src/models.py, src/validators.py, src/complexity_engine.py, src/sizing_engine.py, src/contract_fit.py, related data/ configuration, an assessment UI, and tests in the live repository. Hands off to prompts/work-estimation/mvp-m2-phase-resource-planning.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds only the estimation foundation, including the AI capability intake field -- no phase planning, resourcing, pricing (including AI pricing), support, or SOW logic.
UPDATED:    2026-07-30
VERSION:    1.1
-->

# Prompt: MVP.M1 -- estimation foundation

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and
`prompts/work-estimation/bootstrap-project.md` must already have been run
and approved. Claude Code must be launched from that live repository
root -- this prompt must not be run from inside AI-PPM as though AI-PPM
were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M1 -- Estimation foundation

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- The bootstrap step (prompts/work-estimation/bootstrap-project.md) is
  already complete and approved.
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
   - CONTRACT-FIT.md
4. In scope for this milestone only:
   - Estimate-type input
   - Common scope inputs
   - AI capability intake field ("AI capability included?") with its
     allowed values, defaulting to No -- see ESTIMATE-TYPES.md section 11
   - AI capability type (which "Yes" value, when applicable)
   - AI business objective (free-text, only shown/required when AI
     capability is not No)
   - AI workstream selected activities (multi-select from
     ESTIMATE-TYPES.md section 11.4, only shown when AI capability is not
     No)
   - Material AI assumptions and material AI exclusions (only shown when
     AI capability is not No)
   - Complexity scoring
   - Fibonacci-style Relative Job Size
   - T-shirt sizing
   - Sprint-range mapping
   - Contract-duration input
   - Contract-fit validation
   - Unit tests for every engine built in this milestone
5. Explicit exclusions -- do not build any of:
   - Phase planning
   - Resource planning
   - Pricing -- **including AI pricing**. This milestone captures the AI
     intake fields only; it must not price AI yet.
   - Support estimation
   - SOW generation
   - AI API integration (this refers to the estimator's own AI-assisted
     intake, deferred to MVP.M7 -- unrelated to the AI-capability intake
     field being captured here, which describes AI inside the customer
     project being estimated, per ESTIMATE-TYPES.md section 11.6)
   - Database
6. Likely files to create or modify:
   - src/models.py (include the AI capability intake fields on the
     estimate-request model: AI capability included?, AI capability
     type, AI business objective, AI workstream selected activities,
     material AI assumptions, material AI exclusions)
   - src/validators.py (validate AI capability field values against the
     allowed list; validate that AI-only fields are only meaningful when
     AI capability is not No)
   - src/complexity_engine.py
   - src/sizing_engine.py
   - src/contract_fit.py
   - relevant CSV or JSON configuration files under data/
   - Streamlit setup and assessment UI, only as needed to exercise these
     engines, including the AI capability intake control (defaulted to
     No, with the AI-specific fields shown only when a "Yes" value is
     selected)
   - tests for every engine above
7. Required rules -- implement exactly, per COMPLEXITY-AND-SIZING.md and
   CONTRACT-FIT.md:
   - Complexity dimension scores range from 0 to 5.
   - Complexity weights total 1.0.
   - Store the weighted complexity score at full precision internally.
   - Display the weighted complexity score to two decimals.
   - Map Relative Job Size using the unrounded score.
   - Relative Job Size uses the Fibonacci-style sequence 1, 2, 3, 5, 8,
     13, 20.
   - Explain the Fibonacci context accurately -- do not call the product
     field Story Points.
   - Use the approved Relative Job Size / T-shirt / sprint-range mapping
     exactly as defined in COMPLEXITY-AND-SIZING.md.
   - Relative Job Size 13 triggers a phasing-or-discovery-review warning.
   - Relative Job Size 20 triggers a decomposition-required warning.
   - Contract fit uses the maximum sprint count from the approved sizing
     result in MVP.M1 (per CONTRACT-FIT.md's duration-source rule).
   - No PTO, holiday, meeting, or capacity deductions anywhere in this
     milestone.
   - Required rules, per ESTIMATE-TYPES.md section 11 -- implement
     exactly:
     - AI capability included? defaults to No; AI is never assumed.
     - When No, no AI-specific field beyond the toggle itself may hold a
       meaningful value, and no AI phase, role, effort, or pricing may
       exist anywhere in this or any later milestone's data.
     - When any "Yes" value is selected, capture AI capability type, AI
       business objective, AI workstream selected activities (from the
       catalog in ESTIMATE-TYPES.md section 11.4), and material AI
       assumptions/exclusions -- but do not calculate AI effort or price
       yet.
     - Toggling AI capability from a "Yes" value back to No must clear
       the AI-specific fields captured above, not merely hide them.
8. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
   section) before changing any validated business rule, formula,
   threshold, mapping, or terminology that already exists from a prior
   milestone.
9. Use pdlc-workflow for all code changes: inspect, plan, execute this
   one milestone only, stop for review, prepare a commit summary.
10. architecture-governance is not required for this milestone unless
    you hit a material architectural, data-flow, security, or
    persistent-storage decision not already covered by the bootstrap
    gate -- if that happens, stop and tell me explicitly.
11. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
12. Use these Windows-friendly commands where applicable:
    - Activate the virtual environment: `.venv\Scripts\Activate.ps1`
    - Install any new dependencies: `pip install -r requirements.txt`
    - Run the app: `streamlit run app.py`
    - Run tests: `pytest`
13. Expected output / completion criteria:
    - The app accepts estimate-type and complexity inputs.
    - The weighted complexity score is shown (internal view).
    - Relative Job Size is shown internally.
    - T-shirt size is shown.
    - Sprint range is shown.
    - Contract-fit status is shown.
    - All tests pass.
14. Run tests and confirm they pass before reporting the milestone
    complete.
15. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
16. Required tests -- write and pass tests for:
    - AI capability defaults to No when not explicitly set
    - AI-specific fields remain empty/inert when AI capability is No
    - AI-specific fields capture correctly when a "Yes" value is
      selected
    - Toggling AI capability from Yes to No clears the AI-specific field
      values (not just hides them)
    - Invalid AI capability values are rejected
17. Validation checklist -- confirm all of:
    - Score ranges, weight totals, and full-precision storage are
      enforced (validators.py)
    - Size mapping uses the unrounded score with no overlapping or
      gapped bands
    - Size 13 and size 20 warnings trigger correctly
    - Contract-fit status logic matches CONTRACT-FIT.md exactly
    - No PTO/holiday/meeting/capacity deduction exists anywhere in the
      code
    - No AI phase, role, effort, or price exists anywhere in this
      milestone's code, regardless of the AI capability field's value
18. List the exact files created, modified, or deleted.
19. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
20. Do not silently change validated formulas, mappings, terminology, or
    syntax established during bootstrap.
21. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
22. Application changes must occur only in this live repository, never
    inside AI-PPM.
23. Stop here. Do not advance to MVP.M2 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m2-phase-resource-planning.md.
24. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M1

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

- This milestone produces the estimation foundation only. Pricing,
  resourcing, support, and SOW content are all explicitly out of scope
  here even if they seem like a small addition.
- Relative Job Size stays internal by default per BUSINESS-RULES.md
  section 5 -- do not surface it in any customer-facing view built in
  this milestone.
- If contract-fit status returns "Estimate Definition Required" because
  scope or sizing inputs are insufficient, that is correct behavior, not
  a bug to work around.
- The AI capability field describes AI **inside the customer project
  being estimated**. It is unrelated to the estimator's own AI-assisted
  intake (MVP.M7). Do not conflate the two -- see ESTIMATE-TYPES.md
  section 11.6.
- AI is opt-in, not opt-out. If the AI capability field is left
  unanswered, treat it as No -- never default to Yes and never infer AI
  involvement from other scope fields.
