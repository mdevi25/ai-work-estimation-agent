<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M4 -- contingency and commercial pricing on top of the validated baseline cost, extended to scenario-level commercial levers, non-financial scenario comparison, AI-on/AI-off comparison, and approved-scenario selection.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m3-baseline-pricing.md has already been run and approved, including its session-scoped scenario model and AI cost category. Retrieves: the full pricing sequence and formulas, margin-versus-markup distinction, human-controlled-adjustment rule, non-financial comparison and anti-automatic-recommendation rules, and the AI pricing category from skills/work-estimation/references/PRICING-RULES.md sections 1-9, 11-16, and 19.
DOWNSTREAM: Extends src/pricing_engine.py with contingency, margin, and final-price logic, and extends the MVP.M3 scenario model with commercial levers, non-financial comparison fields, and approval state, plus tests, in the live repository. Hands off to prompts/work-estimation/mvp-m5-support-estimation.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds contingency through final margin, scenario-level commercial and non-financial comparison (including AI-on/AI-off), and approval, only -- no support-package pricing, SOW logic, database, or authentication.
UPDATED:    2026-07-30
VERSION:    1.2
-->

# Prompt: MVP.M4 -- commercial pricing

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M3 must already
be complete and approved -- including its session-scoped scenario model
(Configured Baseline, Working, and Draft scenarios). Claude Code must be
launched from that live repository root -- this prompt must not be run
from inside AI-PPM as though AI-PPM were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M4 -- Commercial pricing

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M3 is already complete and approved, including its scenario model.
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
   - PRICING-RULES.md
4. In scope for this milestone only:
   - Contingency recommendation and user override, per scenario
   - Risk-adjusted cost, per scenario
   - Target margin, per scenario
   - Calculated customer price, per scenario
   - Scenario-specific price rounding
   - Scenario-specific discount
   - Scenario-specific management adjustment
   - Final customer price, gross profit, final margin, and equivalent
     markup, per scenario
   - Side-by-side commercial **and non-financial** comparison of
     scenarios (scope coverage, delivery/timeline feasibility, quality
     and testing controls, security impact, operational readiness,
     support coverage, resource capacity, key-person risk,
     separation-of-duties concerns, assumptions, dependencies,
     exclusions -- per PRICING-RULES.md section 15)
   - Comparing AI-on and AI-off scenarios transparently, showing scope
     and control differences, when both exist for the same estimate
   - Approved-scenario selection (exactly one Approved scenario) -- never
     automatic, and never determined by lowest price alone
   - Replacement of an already-approved scenario, only after explicit
     confirmation
   - Internal warnings (policy-margin breach, discount-into-loss)
   - Tests
5. Explicit exclusions -- do not build any of:
   - Support-package pricing
   - SOW generation
   - The estimator's own AI-assisted intake (MVP.M7 -- unrelated to the
     AI-on/AI-off scenario comparison being built here)
   - Database
   - Authentication
   - Persistent scenario storage (scenarios remain session-only, per
     PRICING-RULES.md section 17)
6. Likely files to create or modify:
   - src/pricing_engine.py (extend with contingency-through-final-margin
     functions, each operating on a single scenario's inputs)
   - src/models.py (extend the MVP.M3 scenario model with contingency,
     target margin, rounding, discount, management adjustment, and
     approval status/timestamp/reviewer fields)
   - tests for the new pricing functions and scenario commercial/
     approval behavior
   - internal pricing view and scenario comparison UI updates (still
     internal-only)
7. Required formulas, per PRICING-RULES.md sections 2 and 14 -- implement
   exactly, computed independently per scenario:
   - contingency_amount = baseline_cost * contingency_percent
   - risk_adjusted_cost = baseline_cost + contingency_amount
   - customer_price = risk_adjusted_cost / (1 - target_margin)
   - gross_profit = final_price - risk_adjusted_cost
   - final_margin = gross_profit / final_price
   - equivalent_markup = (final_price - risk_adjusted_cost) /
     risk_adjusted_cost
8. Required controls:
   - Do not confuse margin with markup -- keep them as distinct,
     separately labeled values everywhere they appear.
   - Target margin must remain at least 0 and below 1 (below 100%).
   - Discount, rounding, and management adjustment are human-controlled
     inputs -- the engine calculates their consequences but never
     chooses them.
   - Recalculate final margin after every adjustment -- never leave it
     stale.
   - Warn when final margin falls below the configured policy minimum.
   - Warn when a discount converts the engagement into a loss (final
     price below risk-adjusted cost).
   - Do not expose internal commercial values (rates, baseline cost,
     contingency, margin, gross profit, equivalent markup) to any
     customer-facing view -- there is no customer-facing pricing view in
     this milestone, but do not build a code path that could expose one
     yet.
   - Keep rate override, contingency, target margin, and discount/
     management adjustment as four distinct levers, per PRICING-RULES.md
     section 14 -- do not merge or conflate them.
   - A change to one scenario's commercial levers must never alter
     another scenario's values.
   - The Configured Baseline scenario remains Reference status and
     cannot be overwritten, approved, or deleted.
   - Marking a scenario Approved requires an explicit human action.
     Exactly one scenario may hold Approved status at a time.
   - Replacing an already-approved scenario with a different one
     requires a separate, explicit confirmation step; the previously
     approved scenario reverts to Draft rather than being deleted.
   - Only the Approved scenario may be treated as the source for
     downstream customer summary, proposal, or SOW content in later
     milestones -- this milestone only needs to mark and expose that
     selection, not build the downstream consumers yet.
   - **The scenario with the lowest customer price must not automatically
     become the recommended or approved scenario** -- per
     PRICING-RULES.md section 15. Recommendation and approval are human
     decisions; the engine may display comparison data but must never
     compute or default to a "recommended" flag based on price.
   - The side-by-side comparison view must show, at minimum, both
     financial and non-financial fields (internal-only):
     - Financial: scenario name, status, baseline delivery cost,
       contingency percentage and amount, risk-adjusted cost, target
       margin, discount or adjustment, final customer price, gross
       profit, final margin, key rate differences from the configured
       baseline
     - Non-financial (where applicable): scope coverage, delivery
       feasibility, timeline feasibility, quality and testing controls,
       security impact, operational readiness, support coverage,
       resource capacity, key-person risk, separation-of-duties
       concerns, assumptions, dependencies, exclusions
   - A lower-cost scenario created by removing work must show, next to
     its price: removed scope, reduced controls, changed assumptions,
     increased risks, support impact, and customer impact -- it must not
     be presented as equivalent to a scenario with different scope,
     controls, risk, or support coverage.
   - When both an AI-on and an AI-off scenario exist for the same
     estimate, compare them transparently: show the AI cost difference,
     the AI-related scope/functionality difference, and any resulting
     control or risk difference. Do not present an AI-off scenario as
     equivalent to an AI-on scenario when AI functionality was removed
     to produce it.
9. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
   section) before changing any validated business rule, formula,
   threshold, mapping, or terminology established in MVP.M1-MVP.M3 --
   including the baseline-cost formula and scenario model from MVP.M3,
   which this milestone must extend, not silently redefine.
10. Use pdlc-workflow for all code changes: inspect, plan, execute this
    one milestone only, stop for review, prepare a commit summary.
11. architecture-governance is not required for this milestone unless
    you hit a material architectural, data-flow, security, or
    persistent-storage decision -- if that happens, stop and tell me
    explicitly.
12. Provide complete, ready-to-publish files -- never partial fragments
    or diffs presented as the file.
13. Use these Windows-friendly commands where applicable:
    - Activate the virtual environment: `.venv\Scripts\Activate.ps1`
    - Install any new dependencies: `pip install -r requirements.txt`
    - Run the app: `streamlit run app.py`
    - Run tests: `pytest`
14. Expected output / completion criteria:
    - Contingency, risk-adjusted cost, target margin, and calculated
      customer price all compute correctly per scenario, from MVP.M3's
      baseline cost.
    - Discount, rounding, and management adjustment are all
      human-entered inputs, never auto-selected, and are scenario-
      specific.
    - Final price, gross profit, final margin, and equivalent markup
      recompute correctly per scenario after every adjustment.
    - Policy-margin and loss warnings trigger correctly per scenario.
    - The comparison view correctly shows multiple scenarios side by
      side without cross-contaminating their values.
    - Exactly one scenario can be Approved at a time, and replacing it
      requires explicit confirmation.
    - All tests pass.
15. Run tests and confirm they pass before reporting the milestone
    complete.
16. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
17. Required tests -- write and pass tests for:
    - Scenario commercial isolation (changing one scenario's contingency,
      margin, discount, or adjustment does not affect another scenario)
    - Correct contingency calculations
    - Correct margin calculations
    - Discount impact on final price and margin
    - Management adjustment impact on final price and margin
    - Final-margin recalculation after every adjustment
    - Loss warnings trigger correctly
    - Minimum-margin warning triggers correctly
    - Exactly one scenario can hold Approved status at any time
    - Approval replacement requires explicit confirmation before taking
      effect
    - Approved-scenario selection is correctly retrievable as the single
      downstream source
    - The Configured Baseline scenario remains Reference status and
      cannot be overwritten, approved, or deleted
    - The lowest-priced scenario is never automatically marked
      recommended or approved -- approval requires an explicit action
      regardless of relative price
    - The comparison view includes the required non-financial fields
      alongside the financial ones
    - An AI-on and an AI-off scenario for the same estimate compare
      transparently, with AI cost, scope, and control differences
      visible, and are never presented as equivalent
    - A scenario with materially required AI controls removed (while
      keeping the same AI functionality and customer commitment) is
      flagged, not silently accepted as equivalent
18. Validation checklist -- confirm all of:
    - Every formula in step 7 matches PRICING-RULES.md exactly, with a
      passing test at a real numeric example, per scenario
    - Margin and markup are never used interchangeably anywhere in code,
      comments, or UI labels
    - Discount/rounding/adjustment fields are human-entered, not
      computed or defaulted by the engine
    - Final margin recalculates after every adjustment
    - No internal commercial value is reachable from a customer-facing
      code path
    - Exactly one Approved scenario exists at any point in the session
    - No scenario is persisted outside Streamlit session state
    - No scenario approval or recommendation is ever derived
      automatically from price
    - AI-on and AI-off scenarios are never presented as equivalent when
      AI functionality differs between them
19. List the exact files created, modified, or deleted.
20. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
21. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1-MVP.M3.
22. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
23. Application changes must occur only in this live repository, never
    inside AI-PPM.
24. Stop here. Do not advance to MVP.M5 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m5-support-estimation.md.
25. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M4

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

- Margin and markup produce different numbers at the same dollar profit
  -- if a test or UI label conflates them, that is a defect, not a
  rounding difference. See PRICING-RULES.md section 3 for the worked
  example.
- Contingency guidance in PRICING-RULES.md section 4 is illustrative,
  configurable guidance, not a formula -- the contingency percentage
  itself must remain a human-reviewable input, not an automatic
  computation from complexity.
- Rate override, contingency, target margin, and discount/management
  adjustment are four distinct levers with different effects (cost
  basis, risk-adjusted cost, selling price from cost, and final price
  independent of cost, respectively) -- see PRICING-RULES.md section 14.
  Do not build a single generic "adjustment" field that conflates them.
- Scenarios remain session-only in this milestone, per PRICING-RULES.md
  section 17 -- approving a scenario does not persist it beyond the
  session and does not modify the Configured Baseline. Do not add a
  database or file-based persistence to work around this.
- Cheaper is not the same as better. The comparison view exists so a
  human can weigh scope, risk, and quality alongside price -- it must
  never collapse into a single "lowest price wins" recommendation, per
  PRICING-RULES.md section 15.
- AI cost, scope, and control visibility in the comparison view is what
  prevents an AI-off scenario from being mistaken for an equivalent,
  cheaper version of an AI-on scenario -- keep the AI difference explicit
  rather than folding it into an undifferentiated price delta.
