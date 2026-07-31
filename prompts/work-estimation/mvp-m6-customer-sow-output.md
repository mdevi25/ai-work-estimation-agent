<!--
PURPOSE:    A fill-in-the-blanks prompt to paste into Claude Code, run from the live AI Work Estimation and Pricing Assistant repository root, to build MVP.M6 -- deterministic customer summaries and SOW-ready draft content from approved structured values.
UPSTREAM:   Assumes prompts/work-estimation/mvp-m5-support-estimation.md has already been run and approved. Retrieves: the Responsible AI pre/post-generation gate from skills/work-estimation/references/RESPONSIBLE-AI.md, SOW section and approved-values-only rules from SOW-RULES.md, and visibility boundaries from BUSINESS-RULES.md and PRICING-RULES.md.
DOWNSTREAM: Produces the ApprovedEstimate model, src/customer_summary.py, src/sow_generator.py, src/responsible_ai_validator.py, and tests in the live repository. Hands off to prompts/work-estimation/mvp-m7-ai-assisted-intake.md once complete and approved.
EXPECT:     A prompt to copy/paste and fill in, not something Claude Code executes automatically from this file alone. Builds deterministic, template-based customer and SOW output only -- AI-assisted rewriting remains deferred to MVP.M7.
UPDATED:    2026-07-30
VERSION:    1.0
-->

# Prompt: MVP.M6 -- customer summary and SOW output

Fill in the bracketed fields, then paste the whole thing into Claude Code.

**Prerequisite:** the `work-estimation` skill must already be deployed to
`~/.claude/skills/work-estimation/`. The applicable project `CLAUDE.md`
must already exist at the live repository root, and MVP.M5 must already
be complete and approved. Claude Code must be launched from that live
repository root -- this prompt must not be run from inside AI-PPM as
though AI-PPM were the live application repository.

```
I'm continuing the AI Work Estimation and Pricing Assistant in its live
repository.

- Live repository path: [LIVE_REPOSITORY_PATH]
- Date: [DATE]

Milestone: MVP.M6 -- Customer and SOW output

Prerequisites (confirm before proceeding):
- The work-estimation skill is deployed at ~/.claude/skills/work-estimation/.
- CLAUDE.md exists at this repository root.
- MVP.M5 is already complete and approved.
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
   - CONTRACT-FIT.md
   - SUPPORT-MODELS.md
   - RESPONSIBLE-AI.md
   - SOW-RULES.md
   - PRICING-RULES.md
   - PHASE-RESOURCE-PLANNING.md
4. Before any implementation, invoke architecture-governance to validate:
   - Internal versus customer-output boundary
   - ApprovedEstimate data flow
   - Responsible AI gate placement
   - Restricted-field handling
   Do not begin coding this milestone until that review is complete.
5. In scope for this milestone only:
   - ApprovedEstimate model
   - Human approval controls
   - src/customer_summary.py
   - src/sow_generator.py
   - src/responsible_ai_validator.py
   - Deterministic, template-based content only
   - Pre-generation gate
   - Post-generation validation
   - Customer summary view
   - Editable SOW draft
   - Text download
   - Tests
6. Explicit exclusion -- AI API or LLM rewriting remains deferred until
   MVP.M7. Everything built in this milestone must be deterministic and
   template-based.
7. Likely files to create or modify:
   - src/models.py (extend with ApprovedEstimate)
   - src/customer_summary.py
   - src/sow_generator.py
   - src/responsible_ai_validator.py
   - tests for all three
   - Streamlit customer-summary view, editable SOW draft, and text
     download
8. Responsible AI statuses, per RESPONSIBLE-AI.md -- implement exactly
   these three, and keep them visibly distinct from any PROTOCOL triage
   status:
   - Ready for AI Drafting
   - Human Review Required
   - Generation Blocked
9. Required controls, per RESPONSIBLE-AI.md and SOW-RULES.md:
   - No generation from unapproved values -- ApprovedEstimate must exist
     and be human-approved before any draft is produced.
   - No invented commitments -- every commitment-bearing value must trace
     back to ApprovedEstimate.
   - No restricted internal data (rates, baseline cost, contingency,
     margin, gross profit, equivalent markup, discount rationale) in any
     customer-facing or SOW output.
   - No unsupported guarantees (legal, regulatory, compliance, security,
     availability, performance, or outcome).
   - Preserve assumptions, dependencies, risks, and exclusions in
     generated content -- do not soften or drop them for brevity.
   - Compare generated text against ApprovedEstimate in post-generation
     validation, flagging every mismatch category listed in
     RESPONSIBLE-AI.md section 6.
   - Include the mandatory disclaimer in every SOW draft.
10. Mandatory disclaimer -- include verbatim in every SOW draft:

    "Draft for business and legal review. This language is not binding
    until approved and incorporated into an executed agreement."

11. Apply the Change-Impact Gate (per CLAUDE.md's "Change-Impact Gate"
    section) before changing any validated business rule, formula,
    threshold, mapping, or terminology established in MVP.M1-MVP.M5.
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
    - An estimate can be marked approved, producing an ApprovedEstimate.
    - The Responsible AI pre-generation gate correctly returns each of
      the three statuses under the right conditions.
    - Customer summaries and SOW drafts generate only from
      ApprovedEstimate, contain the mandatory disclaimer, and expose no
      restricted internal field.
    - Post-generation validation correctly flags an injected mismatch in
      a test case.
    - All tests pass.
16. Run tests and confirm they pass before reporting the milestone
    complete.
17. Update README.md and decision_log.md only if this milestone's scope
    requires it -- state explicitly what changed in each.
18. Validation checklist -- confirm all of:
    - ApprovedEstimate is the only source for commitment-bearing values
      in customer_summary.py and sow_generator.py
    - responsible_ai_validator.py returns the correct status for each
      tested condition in RESPONSIBLE-AI.md sections 2-4
    - No restricted internal field appears in any customer-facing or SOW
      test fixture output
    - The mandatory disclaimer is present in every generated SOW draft
    - Inapplicable SOW sections are omitted, per SOW-RULES.md section 1
19. List the exact files created, modified, or deleted.
20. Do not modify unrelated files. If an unexpected file must change,
    stop and report it as a blocker instead of changing it.
21. Do not silently change validated formulas, mappings, terminology, or
    syntax established in MVP.M1-MVP.M5.
22. Routine typo or formatting-only changes may bypass the full
    Change-Impact Gate only under the exact conditions in this
    repository's CLAUDE.md.
23. Application changes must occur only in this live repository, never
    inside AI-PPM.
24. Stop here. Do not advance to MVP.M7 automatically -- wait for my
    explicit validation before proceeding to
    prompts/work-estimation/mvp-m7-ai-assisted-intake.md.
25. End your response with:

## HANDOFF SUMMARY FOR CHATGPT

Reference:
EAP.M6

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

- The architecture-governance gate in step 4 is required for this
  milestone, not conditional -- it is one of the three defined gates in
  this project's CLAUDE.md.
- Any broader AI disclaimer required by RESPONSE-QUALITY.md section 7 is
  additive to the mandatory SOW disclaimer -- it supplements, never
  replaces it.
- Relative Job Size, complexity score, and every other internal-only
  field from earlier milestones must still be excluded from customer
  output here, per BUSINESS-RULES.md section 5 -- this milestone is
  exactly where that boundary gets tested end to end for the first time.
