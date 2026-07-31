<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M3 -- deterministic baseline delivery cost plus session-based baseline-cost pricing scenarios, including the optional AI workstream cost category.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m2-phase-resource-planning.md has already been run and approved, including any AI workstream phases/roles/effort. Retrieves: role-cost and baseline-cost formulas, the configured baseline rate card, scenario/rate-override rules, and the AI pricing category from skills/work-estimation/references/PRICING-RULES.md sections 1-2, 9-13, and 19, and estimated-hours input (including AI role hours) from PHASE-RESOURCE-PLANNING.md.
DOWNSTREAM: Produces baseline-cost functions in src/pricing_engine.py, data/rate_card.csv, a session-scoped scenario model with a distinct AI cost category, and tests in the live repository. Hands off to prompts/work-estimation/mvp-m4-commercial-pricing.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds deterministic baseline cost, baseline-cost-level scenario modeling, and the AI baseline-cost category only -- no contingency, margin, discount, or customer price.
UPDATED:    2026-07-30
VERSION:    1.2
-->

# Prompt: MVP.M3 -- baseline pricing

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M2 must already
be complete and approved. Claude Code must be launched from that live
repository root -- this prompt must not be run from inside AI-PPM as
though AI-PPM were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M3 -- Baseline pricing

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M2 is already complete and approved.
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
   - PHASE-RESOURCE-PLANNING.md
   - PRICING-RULES.md
4. In scope for this milestone only:
   - Baseline-cost functions in src/pricing_engine.py
   - data/rate_card.csv with default illustrative rates (the configured
     baseline)
   - Internal editable rate table (default rate read-only, scenario rate
     editable)
   - Configured Baseline scenario (read-only, loaded from rate_card.csv)
   - Working and Draft baseline-cost scenarios (session-scoped)
   - Duplicate, rename, reset-to-default, compare, and delete operations
     for Draft scenarios
   - Scenario-specific rate override reasons
   - Cost by role and phase, recalculated per scenario
   - Baseline total, recalculated per scenario
   - Session-state-only scenario storage
   - Internal pricing view (internal users only)
   - **AI workstream cost as a separate baseline-cost category** (per
     PRICING-RULES.md section 19), applied only when the estimate's AI
     capability field is not No:
     - Retain AI role and phase costs separately from core IT cost
     - Roll AI cost into the scenario's total baseline cost
     - Support AI-on and AI-off baseline scenarios side by side
     - Ensure toggling AI off removes AI cost cleanly (not zeroed while
       still present)
   - Tests
5. Explicit exclusions -- do not build any of:
   - Contingency
   - Margin
   - Discount
   - Final customer price
   - Support pricing
   - SOW generation
   - The estimator's own AI-assisted intake (MVP.M7 -- unrelated to the
     AI workstream cost category being added here)
6. Likely files to create or modify:
   - src/pricing_engine.py (baseline-cost functions only in this
     milestone; each function operates on a scenario's rates, not a
     single global rate set; include a distinct AI-cost aggregation
     alongside the core IT baseline cost, using the same role_cost/
     baseline_cost formulas for AI roles)
   - src/models.py (extend with a session-scoped scenario model:
     scenario id, name, status, source scenario, configured rates,
     scenario rates, override reasons, baseline cost, and a distinct AI
     cost subtotal field, present only when the estimate's AI capability
     is not No)
   - data/rate_card.csv (illustrative default rates -- the configured
     baseline; never written to by the application; may include
     illustrative AI-specific role rates)
   - tests for the baseline-cost functions and scenario behavior,
     including AI cost category behavior
   - internal pricing view and scenario management UI in the Streamlit
     app, showing the AI cost category as a clearly separate line when
     applicable
7. Required rules, per PRICING-RULES.md sections 1-2 and 9-13:
   - role_cost = estimated_hours * internal_hourly_rate
   - baseline_cost = sum(role_cost)
   - Use fictional demonstration rates only in data/rate_card.csv --
     never real customer commercial data.
   - Label rates as illustrative wherever they appear, in code comments
     and in any UI surface.
   - The configured default rate is read-only in the UI; the scenario
     rate is editable.
   - An override reason is required whenever a scenario's rate differs
     from the configured default.
   - Scenario rate changes must never rewrite data/rate_card.csv.
   - Rates must be numeric and non-negative; currency is required for
     every role.
   - Every priced resource role must resolve to an applicable rate, or
     the mismatch must be explicitly resolved rather than silently
     defaulted.
   - A disabled or excluded role is not priced unless restored to active
     status.
   - The Configured Baseline scenario is never overwritten by UI
     adjustments, and cannot be deleted.
   - Each scenario recalculates its own role cost, phase cost, and
     baseline cost independently -- a change to one scenario must never
     alter another scenario's values.
   - Do not persist customer transactions or scenario values anywhere in
     source control.
   - Keep internal pricing (rates, baseline cost) hidden from any
     customer-facing view -- there is no customer-facing pricing view in
     this milestone, but do not build a code path that could expose one
     yet.
   - Per PRICING-RULES.md section 19: AI-off scenarios must show zero AI
     effort and zero AI cost (no AI line item at all, not a hidden or
     zeroed one); AI-on scenarios must show AI cost separately from core
     IT cost while it still rolls into the scenario's total baseline
     cost; no separate AI pricing formula exists -- AI roles use the same
     role_cost/baseline_cost formulas as core IT roles.
8. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
   section) before changing any validated business rule, formula,
   threshold, mapping, or terminology established in MVP.M1 or MVP.M2.
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
    - Role cost and baseline cost are calculated correctly from
      MVP.M2's resource plan and the configured rate card.
    - A user can create a Working/Draft scenario from the Configured
      Baseline, duplicate it, rename it, override rates with a required
      reason, reset it to default rates, compare it against other
      scenarios, and delete an unapproved draft -- all without altering
      data/rate_card.csv or any other scenario.
    - The internal pricing view shows role cost and baseline total per
      scenario, clearly labeled as internal-only and illustrative.
    - All tests pass.
14. Run tests and confirm they pass before reporting the milestone
    complete.
15. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
16. Required tests -- write and pass tests for:
    - Default-rate calculation
    - Scenario-rate calculation
    - Baseline preservation (Configured Baseline never changes when a
      scenario is edited)
    - Scenario isolation (editing one scenario does not alter another)
    - Reset to defaults
    - Duplicate scenario
    - Invalid or negative rates are rejected
    - Missing override reason is rejected when scenario rate differs
      from default
    - Missing role rate is flagged, not silently defaulted
    - Excluded role is not priced
    - Scenario deletion controls (baseline cannot be deleted; deleting
      one draft does not affect another)
    - AI-off scenario shows zero AI effort and zero AI cost, with no AI
      line item present
    - AI-on scenario shows AI cost separately, and that AI cost rolls
      into the scenario's total baseline cost
    - Toggling AI off removes AI cost entirely, with no stale AI value
      left in any total
    - AI role cost uses the same role_cost/baseline_cost formulas as
      core IT roles
17. Validation checklist -- confirm all of:
    - role_cost and baseline_cost formulas match PRICING-RULES.md
      section 2 exactly, for both core IT and AI roles
    - Rate data is fictional and clearly labeled illustrative
    - Rate-to-role mismatches are validated, not silently defaulted
    - The Configured Baseline scenario is read-only and undeletable
    - No contingency, margin, discount, or customer-price logic exists
      anywhere in this milestone's code
    - No AI cost appears anywhere when AI capability is No
18. List the exact files created, modified, or deleted.
19. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
20. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1 or MVP.M2.
21. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
22. Application changes must occur only in this live repository, never
    inside AI-PPM.
23. Stop here. Do not advance to MVP.M4 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m4-commercial-pricing.md.
24. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M3

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

- The rate card in this milestone is illustrative and fictional by
  design, per GUARDRAILS.md section 3 and PRICING-RULES.md section 9 --
  never substitute a real rate card here, even temporarily.
- Baseline cost is an internal-only figure. Nothing in this milestone
  should make it reachable from a customer-facing surface, even though
  that surface does not exist yet.
- Scenarios are stored only in Streamlit session state in this
  milestone, per PRICING-RULES.md section 17 -- refreshing or restarting
  the app may remove Draft scenarios, and that is expected MVP behavior,
  not a defect. Do not add a database or file-based persistence to work
  around this.
- MVP.M3 introduces the scenario model at the baseline-cost level only.
  Contingency, margin, discount, management adjustment, and
  approved-scenario selection are scenario-level commercial levers added
  in MVP.M4 -- do not add them here even though the scenario structure
  will need to carry them later.
- The AI cost category exists only when MVP.M1's AI capability field is
  not No, and only for the AI activities actually selected in MVP.M2 --
  never a default or assumed AI cost.
