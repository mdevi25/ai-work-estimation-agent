<!--
PURPOSE:    Shared mechanics for any skill that queues actions for approval: batch processing, status labels, output format, async approval, gap-flagging discipline.
UPSTREAM:   Imported by CLAUDE.md (this directory's root) -- loaded automatically in every session once deployed. Retrieves: nothing at load time -- this file has no upstream dependency, it IS the loaded content.
DOWNSTREAM: Referenced directly by skills/jira-triage/SKILL.md and skills/jira-status/SKILL.md. Any future skill that queues write-actions should reference this file too instead of redefining its own queuing rules.
EXPECT:     Conventions only -- no project-specific or task-specific content belongs here. If you're adding a rule that only applies to one skill, it belongs in that skill's SKILL.md instead.
UPDATED:    2026-07-12
VERSION:    1.1
-->

# Shared triage protocol

This document defines conventions shared across every skill in this system.
Any skill that queues actions for approval should reference this file rather
than redefining its own rules, so behavior stays consistent as the skill
library grows.

## 1. Batch processing, no mid-run pauses

When a skill processes multiple items (tickets, PRs, etc.), it completes
analysis on every item in one uninterrupted pass. It does not stop between
items to ask for approval. All proposed actions are staged into a queue
first; nothing executes during this pass.

## 2. Status labels

Every item touched by a skill gets tagged with one of three states. Where
the underlying tool supports labels (e.g. Jira), write the label directly
onto the item so state survives across sessions and devices:

<!-- These three exact label strings are what skills/jira-status/SKILL.md
     queries for. Changing the spelling here breaks that query. -->
- `triage-pending`   — analyzed, action proposed, awaiting approval
- `triage-approved`  — action executed
- `triage-skipped`   — explicitly declined by the user

Do not rely on chat memory alone to track state. If the tool supports a
label, comment, or custom field, use it as the source of truth.

## 3. Output format

After processing a batch, present one consolidated table:

<!-- This exact column order is a contract other files depend on --
     skills/jira-triage/SKILL.md and skills/jira-status/SKILL.md both
     reference "the shared table format" assuming these columns. If you
     change this, update those files too. -->
| ID | Priority | Timeline est. | Dependencies | Gaps flagged | Queued action | Status |

Followed by expanded per-item detail below the table (checklist, reasoning)
for any item worth a closer look.

## 4. Approval is granular and asynchronous

Never require the user to respond to the entire queue at once. Accept any
of the following, at any time, in any order:

- `"approve all"`
- `"approve <ID>, <ID>"`
- `"skip <ID>"`
- `"show pending"` / `"show status"` — reprint only items still `triage-pending`

Execute exactly what's approved in that message immediately. Leave
everything else untouched and pending. The queue is never "closed" on a
timer — it persists until every item is `triage-approved` or
`triage-skipped`.

## 5. Write actions require explicit approval

No action that changes external state (posting a comment, setting a field,
closing an item) executes without an approval message referencing that
specific ID (or "approve all"). Read and analysis actions do not require
approval.

A queued item's label only flips to `triage-approved` after the
underlying write action is confirmed to have succeeded — never before,
and never assumed. If a write fails, leave the item `triage-pending`,
surface the failure to the user, and do not silently retry it as if it
had succeeded.

## 6. Gap-flagging discipline

Flag genuine ambiguity only — missing acceptance criteria, conflicting
signals, an unresolved dependency. Do not fabricate field values, invent
acceptance criteria, or guess at information that isn't present in the
source data. When uncertain, flag it rather than assume.
