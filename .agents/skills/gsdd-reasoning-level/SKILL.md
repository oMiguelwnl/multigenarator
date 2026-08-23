---
name: gsdd-reasoning-level
description: Before any new project task or /gsdd-* workflow, including /gsdd-new-project, /gsdd-plan, /gsdd-execute, /gsdd-verify, /gsdd-audit-milestone, /gsdd-quick, /gsdd-progress, and milestone or resume workflows, use this skill to recommend and gate on one GPT-5.6 Sol reasoning level.
---

# GSDD Reasoning-Level Advisor

<pre_work_gate>
Classify the task from the user's request and already-present context before project reads, commands, edits, planning, or delegation.

Select exactly one allowed level.
Wait for confirmation or adjustment before work.
Do not re-prompt within the same top-level task.

The replies continue, proceed, go ahead, yes, or {LEVEL} confirm the recommendation.
A reply naming another allowed level adjusts the selection and satisfies the gate.

Once the gate is satisfied, retain that state for all subtasks, delegated roles, checkpoints, corrections, and continuation messages. A new unrelated top-level outcome or a separately invoked `/gsdd-*` command starts a new gate. An internally delegated workflow step does not start a new gate.
</pre_work_gate>

<advisory_response>
Return exactly this complete three-line template, substituting one exact allowed value for `{LEVEL}` at runtime:

Recommended reasoning level: **{LEVEL}**
Reason: {one-sentence task-specific reason}
I cannot inspect or change the reasoning level selected in OpenCode's UI. Please set or confirm **{LEVEL}**, or reply with another allowed level.

Use one sentence tailored to the specific task after the literal Reason: label.

Then stop and wait. Never claim that the UI-selected level was detected, set, changed, or verified. User confirmation acknowledges the recommendation but does not prove a UI change.
</advisory_response>

<general_ladder>
Allowed levels (exact): Low, Normal, Medium, High, XHigh, Max

Use the highest applicable tier.

- Low: narrow read-only status checks and lookups with no writes.
- Normal: routine administrative, routing, or metadata work with low reversible risk.
- Medium: bounded simple quick documentation, configuration, test-maintenance, or broad read-only mapping work.
- High: default for implementation and every code behavior change.
- XHigh: default for planning, verification, and audits, and the floor for critical database/schema/data migration, licensing/redistribution, provider credentials/billing/live side effects, auth/security/privacy, destructive, cross-cutting, and release/deployment/publication/closure work.
- Max: exceptional only under the Max rule below; never a routine default.
</general_ladder>

<gsdd_matrix>
| Workflow | Classification |
|---|---|
| `/gsdd-progress` | Low |
| `/gsdd-pause` | Low |
| `/gsdd-resume` | Normal for restore/route only; otherwise use the resumed operation tier |
| `/gsdd-map-codebase` | Medium |
| `/gsdd-quick` | General ladder: Medium for bounded non-code quick work, High for implementation, XHigh when a critical-risk floor applies |
| `/gsdd-execute` | High unless an XHigh risk floor applies |
| `/gsdd-new-project` | XHigh |
| `/gsdd-new-milestone` | XHigh |
| `/gsdd-plan` | XHigh |
| `/gsdd-plan-milestone-gaps` | XHigh |
| `/gsdd-verify` | XHigh |
| `/gsdd-verify-work` | XHigh |
| `/gsdd-audit-milestone` | XHigh |
| `/gsdd-complete-milestone` | XHigh |

Implementation defaults to High even when entered through `/gsdd-quick` or `/gsdd-resume`. Apply any higher XHigh risk floor from the general ladder.
</gsdd_matrix>

<max_rule>
Max is exceptional: choose it only after XHigh is demonstrably inadequate or before an unusually irreversible decision.
The Max reason must name the concrete XHigh inadequacy or unusual irreversibility.
Rule: never choose Max merely because work is large or important.
</max_rule>
