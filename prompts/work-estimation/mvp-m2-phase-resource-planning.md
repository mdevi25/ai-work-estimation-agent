<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M2 -- phase-based estimation and resource planning, including the optional AI workstream's phases, roles, and effort when AI capability was selected in MVP.M1.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m1-estimation-foundation.md has already been run and approved, including its AI capability intake field. Retrieves: phase and role rules from skills/work-estimation/references/PHASE-RESOURCE-PLANNING.md sections 1-11, AI workstream phase/resource rules from section 12, phase applicability by type from ESTIMATE-TYPES.md, and the duration-source rule from CONTRACT-FIT.md.
DOWNSTREAM: Produces src/phase_planner.py, src/resource_planner.py, related structured models and configuration, and tests in the live repository. Hands off to prompts/work-estimation/mvp-m3-baseline-pricing.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds phase and resource planning, including the optional AI workstream's phases/roles/effort -- no rate cards, cost, contingency, margin, or SOW logic.
UPDATED:    2026-07-30
VERSION:    1.1
-->

# Prompt: MVP.M2 -- phase and resource planning

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M1 must already
be complete and approved. Claude Code must be launched from that live
repository root -- this prompt must not be run from inside AI-PPM as
though AI-PPM were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M2 -- Phase and resource planning

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M1 is already complete and approved.
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
   - PHASE-RESOURCE-PLANNING.md (including section 12, the optional AI
     workstream)
   - COMPLEXITY-AND-SIZING.md
   - CONTRACT-FIT.md
4. In scope for this milestone only:
   - Phase selection by estimate type
   - Phase duration in sprints, including approved phase overlap
   - Required roles by phase
   - Person-sprint and hour calculations
   - Lean, Balanced, Specialized, and Customer-defined staffing models
   - Required-role/required-effort/assigned-person separation
   - Resource warnings
   - Re-evaluating contract fit using the approved phase-plan duration
     where appropriate
   - **When the MVP.M1 estimate's AI capability field is any "Yes"
     value:** add applicable AI phases, add AI roles, add AI effort
     (using the same formulas as core IT), add AI-specific dependencies
     and warnings, and allow the AI workstream to be reviewed on its own
     before pricing (MVP.M3) -- per PHASE-RESOURCE-PLANNING.md section
     12.1.
   - **When the AI capability field is No:** no AI phase, role, or
     effort may exist in the plan -- per section 12.2.
5. Explicit exclusions -- do not build any of:
   - Rate card
   - Baseline cost
   - Contingency
   - Margin
   - Customer price
   - SOW generation
   - AI pricing or cost (that is MVP.M3's scope -- this milestone adds AI
     phases, roles, and effort only, not cost)
   - The estimator's own AI-assisted intake (MVP.M7 -- unrelated to the
     AI workstream being planned here, per ESTIMATE-TYPES.md section
     11.6)
6. Likely files to create or modify:
   - src/phase_planner.py (include AI phase selection, applied only when
     AI capability is not No)
   - src/resource_planner.py (include AI role/effort calculation, using
     the same person_sprints/estimated_hours formulas as core IT roles)
   - structured models required for phases and resources (extend
     src/models.py, do not fork a parallel model file; keep AI phase/role
     entries clearly tagged as AI workstream, not merged indistinguishably
     with core IT entries)
   - phase_rules configuration (including which AI phases map to which
     selected AI workstream activities)
   - resource_rules configuration (including the possible AI roles from
     PHASE-RESOURCE-PLANNING.md section 12.3)
   - role_combinations configuration
   - tests for phase_planner.py and resource_planner.py, including AI
     workstream behavior
   - Streamlit phase and resource views, with the AI workstream shown as
     a clearly separate, reviewable section only when AI capability is
     not No
7. Required behavior, per PHASE-RESOURCE-PLANNING.md:
   - Select phases by estimate type.
   - Phase duration is measured in sprints, consistently.
   - Allow approved phase overlap.
   - Determine required roles by phase.
   - Calculate person-sprints: phase_duration_sprints * role_allocation.
   - Calculate hours using the configurable hours_per_sprint assumption
     (initial value 80).
   - Support Lean, Balanced, Specialized, and Customer-defined staffing.
   - Separate required role, required effort, and assigned person --
     combining roles must not remove underlying effort.
   - Flag same-phase allocation above 100%.
   - Flag risky or incompatible role combinations (e.g., developer as
     sole independent QA, developer as security approver).
   - Allow QA involvement before development completion (acceptance-
     criteria review, test planning, test-data prep, incremental
     testing).
   - Allow BA or PO involvement during requirements, refinement, and
     UAT.
   - Re-evaluate contract fit using the approved phase-plan duration when
     it becomes the authoritative duration source, per CONTRACT-FIT.md.
   - When AI capability is not No: add only the AI phases/roles needed
     for the selected AI workstream activities, do not prescribe a
     universal AI staffing model, and apply the same combined-role rules
     (preserve effort, flag over-allocation, flag key-person risk, flag
     incompatible review/approval roles, flag missing independent
     evaluation where materially required) per PHASE-RESOURCE-PLANNING.md
     section 12.4.
   - When AI capability is No: confirm no AI phase, role, or effort
     exists anywhere in the plan.
   - If AI capability is toggled from Yes to No after AI phases/roles
     were added, remove them entirely -- do not zero their duration or
     allocation and leave them present.
8. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
   section) before changing any validated business rule, formula,
   threshold, mapping, or terminology established in MVP.M1.
9. Use pdlc-workflow for all code changes: inspect, plan, execute this
   one milestone only, stop for review, prepare a commit summary.
10. architecture-governance is not required for this milestone unless
    you hit a material architectural, data-flow, security, or
    persistent-storage decision -- if that happens, stop and tell me
    explicitly.
11. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
12. Use these Windows-friendly commands where applicable:
    - Activate the virtual environment: `.venv\Scripts\Activate.ps1`
    - Install any new dependencies: `pip install -r requirements.txt`
    - Run the app: `streamlit run app.py`
    - Run tests: `pytest`
13. Expected output / completion criteria:
    - The app selects applicable phases for the chosen estimate type.
    - Required roles, person-sprints, and hours are shown per phase.
    - The selected staffing model changes the resource view without
      changing underlying required effort.
    - Resource warnings surface correctly for the flagged conditions.
    - All tests pass.
14. Run tests and confirm they pass before reporting the milestone
    complete.
15. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
16. Required tests -- write and pass tests for:
    - AI phases/roles/effort are added only when AI capability is not No
    - AI phases/roles/effort are entirely absent when AI capability is No
    - AI role effort uses the same person_sprints/estimated_hours
      formulas as core IT roles
    - Combining AI roles never changes underlying required AI effort
    - Missing independent AI evaluation coverage is flagged when
      materially required
    - Toggling AI capability from Yes to No removes AI phases/roles/
      effort entirely, leaving no stale values
17. Validation checklist -- confirm all of:
    - Phase selection matches ESTIMATE-TYPES.md per type
    - person_sprints and estimated_hours formulas match
      PHASE-RESOURCE-PLANNING.md exactly, for both core IT and AI roles
    - Combining roles never changes underlying required effort
    - All required resource warnings are implemented and tested,
      including the AI-specific warnings in section 8
    - No rate, cost, contingency, or margin logic exists anywhere in
      this milestone's code
    - No AI phase, role, or effort exists when AI capability is No
18. List the exact files created, modified, or deleted.
19. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
20. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1.
21. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
22. Application changes must occur only in this live repository, never
    inside AI-PPM.
23. Stop here. Do not advance to MVP.M3 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m3-baseline-pricing.md.
24. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M2

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

- Duration is not simply divisible by headcount -- resource warnings and
  UI framing should reflect that adding people does not proportionally
  reduce duration, per PHASE-RESOURCE-PLANNING.md.
- Required role, required effort, and assigned person must remain three
  distinct, separately visible concepts in both the data model and the
  UI -- do not collapse them for display convenience.
- The AI workstream is optional and disabled by default -- it appears
  only when MVP.M1's AI capability field is not No, and only the
  selected AI workstream activities determine which AI phases/roles are
  added, never the full catalog by default.
- Do not confuse the optional AI workstream (AI inside the customer
  project) with the estimator's own future AI-assisted intake (MVP.M7) --
  see ESTIMATE-TYPES.md section 11.6.
