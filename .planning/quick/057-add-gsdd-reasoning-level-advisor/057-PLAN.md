---
quick_task: 057
slug: add-gsdd-reasoning-level-advisor
plan: "057"
type: execute
mode: quick
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
files_modified:
  - .agents/skills/gsdd-reasoning-level/SKILL.md
  - .planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json
autonomous: true
requirements: []
non_goals:
  - Do not change opencode.json, opencode.jsonc, .opencode/, AGENTS.md, or any existing/generated skill.
  - Do not attempt to inspect, set, or verify OpenCode's UI-selected reasoning level.
  - Do not add a plugin, command, agent, runtime hook, UI proof, or GSDD framework modification.
  - Do not update ROADMAP.md, SPEC.md, STATE.md, or the unrelated Phase 32 planning work.
hard_boundaries:
  - The only functional/project write is the new skill; the deterministic Phase 32 baseline is owned as a quick-task 057 artifact.
  - Do not commit this quick task.
  - The skill must not contain a per-task restart reminder; restart is reported only after implementation completes.
escalation_triggers:
  - Stop if auto-discovery cannot be achieved at the confirmed .agents/skills path without configuration changes.
  - Stop if a protected existing skill, OpenCode config, AGENTS.md, or unrelated dirty file would need modification.
approval_gates:
  - Any expansion beyond the one new skill requires a new explicit user decision.
anti_regression_targets:
  - Existing GSDD skills remain byte-untouched.
  - Existing OpenCode configuration and AGENTS.md remain untouched.
  - The known unrelated Phase 32 worktree changes remain outside this task.
known_unknowns:
  - Static repository checks can prove the discovery contract and instructions, not which skill a running OpenCode session actually loaded.
ui_proof_slots: []
no_ui_proof_rationale: This is a repository skill-instruction change with no rendered UI claim; deterministic path, frontmatter, content, and git-scope checks are sufficient.
closure_claim_limit: Claim only that the auto-discoverable skill contract exists and passes static checks; do not claim the running UI level was observed or changed.
parallelism_budget:
  max_concurrent_plans: 1
  safe_parallelism: []
must_haves:
  truths:
    - Before a new top-level project task or explicit /gsdd-* workflow starts, the skill instructs OpenCode to recommend exactly one of Low, Normal, Medium, High, XHigh, or Max, give a brief reason, disclose its UI limitation, and wait for confirmation or adjustment.
    - The current top-level task's confirmed or adjusted gate remains satisfied through subtasks, delegations, checkpoints, corrections, and continue/proceed replies.
    - High is the implementation default; XHigh covers planning, verification, audits, and critical database, licensing, provider, or release work; Max remains exceptional under the confirmed criteria.
    - Low, Normal, and Medium provide distinct coverage for read-only, administrative, and bounded simple quick work.
    - Existing skills, OpenCode config, AGENTS.md, and unrelated Phase 32 planning are unchanged.
  artifacts:
    - path: .agents/skills/gsdd-reasoning-level/SKILL.md
      provides: Auto-discovered reasoning-level advisory and confirmation-gate instructions.
    - path: .planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json
      provides: Deterministic pre-implementation inventory of every Phase 32 path, type, and content hash.
  key_links:
    - from: .agents/skills/gsdd-reasoning-level/SKILL.md frontmatter description
      to: OpenCode external project skill discovery
      via: Exact .agents/skills/<name>/SKILL.md location and trigger-rich description.
    - from: GSDD command and risk matrix
      to: Per-top-level-task advisory gate
      via: Highest-applicable-tier selection followed by one confirmation or adjustment wait.
    - from: .planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json
      to: .planning/phases/32-frequency-portuguese-text-and-audio/
      via: Exact post-implementation path/type/content inventory comparison.
---

# Quick Task 057 Plan: Add GSDD Reasoning-Level Advisor

## Objective

Create one auto-discovered project OpenCode skill that selects and recommends one exact GPT-5.6 Sol reasoning level before new project tasks and GSDD workflows, while honestly treating the UI setting as user-controlled and avoiding repeated prompts inside the same task.

## Context

- `.agents/skills/gsdd-quick/SKILL.md` — local skill frontmatter and XML-like workflow style.
- `.agents/skills/gsdd-plan/SKILL.md` — planning workflow names and boundaries.
- `.agents/skills/gsdd-verify/SKILL.md` — verification and audit posture.
- `.planning/config.json` — confirms project skill workflow usage; no config edit is needed.
- Worktree baseline observed during planning: only `.planning/.state-fingerprint.json`, `.planning/ROADMAP.md`, `.planning/SPEC.md`, `.planning/STATE.md`, and `.planning/phases/32-frequency-portuguese-text-and-audio/` are unrelated dirty surfaces.

## Locked Decisions

- **D-01:** Create only `.agents/skills/gsdd-reasoning-level/SKILL.md`; use valid `name` and trigger-rich `description` frontmatter and no `opencode.json` change.
- **D-02:** Recommend exactly one of Low, Normal, Medium, High, XHigh, or Max using a GSDD command matrix plus risk escalation.
- **D-03:** State that the skill cannot inspect or change the UI-selected level, wait for confirmation/adjustment, and never treat confirmation as proof that the UI changed.
- **D-04:** Prompt once per new top-level task or explicit GSDD invocation, not for subtasks or after a confirming continue/proceed response.
- **D-05:** Keep generated GSDD skills and AGENTS.md untouched; preserve unrelated Phase 32 work.
- **D-06:** Mention the need to restart OpenCode only in implementation completion, never in the skill's recurring advisory.

## Tasks

<task id="057-01" type="auto">
  <name>Fingerprint Phase 32, then create the auto-discovered advisor skill</name>
  <files>
    - CREATE: .planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json
    - CREATE: .agents/skills/gsdd-reasoning-level/SKILL.md
  </files>
  <action>
Before any implementation write, create `.planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json` from `.planning/phases/32-frequency-portuguese-text-and-audio/`. Use the following deterministic command exactly. It inventories the root and every descendant in sorted relative-path order, classifies each as `directory`, `file`, or `symlink`, hashes file bytes and symlink-target bytes with SHA-256, rejects unsupported filesystem types, and writes no timestamp or machine-specific absolute path:

`python -c 'import hashlib,json,os; from pathlib import Path; root=Path(".planning/phases/32-frequency-portuguese-text-and-audio"); out=Path(".planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json"); assert root.is_dir(), root; paths=sorted([root,*root.rglob("*")],key=lambda p:"." if p==root else p.relative_to(root).as_posix()); entries=[{"path":"." if p==root else p.relative_to(root).as_posix(),"type":"symlink" if p.is_symlink() else "file" if p.is_file() else "directory" if p.is_dir() else "unsupported","sha256":hashlib.sha256(os.readlink(p).encode("utf-8") if p.is_symlink() else p.read_bytes() if p.is_file() else b"").hexdigest() if p.is_symlink() or p.is_file() else None} for p in paths]; assert all(e["type"]!="unsupported" for e in entries),entries; out.write_text(json.dumps({"schema_version":1,"root":root.as_posix(),"entries":entries},indent=2,sort_keys=True)+"\n",encoding="utf-8")'`

Only after that baseline exists, create the directory and `SKILL.md` per D-01. Use YAML frontmatter containing exactly `name: gsdd-reasoning-level` and one single-line `description`. Front-load that description with concrete triggers: before any new project task or `/gsdd-*` workflow, including `/gsdd-new-project`, `/gsdd-plan`, `/gsdd-execute`, `/gsdd-verify`, `/gsdd-audit-milestone`, `/gsdd-quick`, `/gsdd-progress`, and milestone/resume workflows. Say what the skill does: recommends and gates on one GPT-5.6 Sol reasoning level.

Write concise Markdown/XML-like instructions with these deterministic contracts:

1. **Pre-work gate, per D-03/D-04:** classify from the user's request and already-present context before project reads, commands, edits, planning, or delegation. Include the exact rules `Select exactly one allowed level.`, `Wait for confirmation or adjustment before work.`, and `Do not re-prompt within the same top-level task.` Include these exact handling rules: `The replies continue, proceed, go ahead, yes, or {LEVEL} confirm the recommendation.` and `A reply naming another allowed level adjusts the selection and satisfies the gate.` Once satisfied, retain that state for all subtasks, delegated roles, checkpoints, corrections, and continuation messages. A new unrelated top-level outcome or a separately invoked `/gsdd-*` command starts a new gate; an internally delegated workflow step does not.
2. **Honest advisory, per D-03:** require this complete literal three-line template, substituting one exact allowed value for `{LEVEL}` at runtime:

   `Recommended reasoning level: **{LEVEL}**`
   `Reason: {one-sentence task-specific reason}`
   `I cannot inspect or change the reasoning level selected in OpenCode's UI. Please set or confirm **{LEVEL}**, or reply with another allowed level.`

   Include exactly `Use one sentence tailored to the specific task after the literal Reason: label.` Then stop and wait. Explicitly forbid claims that the level was detected, set, changed, or verified, and state that user confirmation acknowledges the recommendation but does not prove a UI change.
3. **General ladder, per D-02:** include `Allowed levels (exact): Low, Normal, Medium, High, XHigh, Max`, `Use the highest applicable tier.`, and all six exact definitions below so every tier has deterministic coverage:

   - `Low: narrow read-only status checks and lookups with no writes.`
   - `Normal: routine administrative, routing, or metadata work with low reversible risk.`
   - `Medium: bounded simple quick documentation, configuration, test-maintenance, or broad read-only mapping work.`
   - `High: default for implementation and every code behavior change.`
   - `XHigh: default for planning, verification, and audits, and the floor for critical database/schema/data migration, licensing/redistribution, provider credentials/billing/live side effects, auth/security/privacy, destructive, cross-cutting, and release/deployment/publication/closure work.`
   - `Max: exceptional only under the Max rule below; never a routine default.`

4. **Complete GSDD matrix, per D-02:** include one Markdown table row with the exact command and classification text for every installed workflow:

   - `| /gsdd-progress | Low |`
   - `| /gsdd-pause | Low |`
   - `| /gsdd-resume | Normal for restore/route only; otherwise use the resumed operation tier |`
   - `| /gsdd-map-codebase | Medium |`
   - `| /gsdd-quick | General ladder: Medium for bounded non-code quick work, High for implementation, XHigh when a critical-risk floor applies |`
   - `| /gsdd-execute | High unless an XHigh risk floor applies |`
   - `| /gsdd-new-project | XHigh |`
   - `| /gsdd-new-milestone | XHigh |`
   - `| /gsdd-plan | XHigh |`
   - `| /gsdd-plan-milestone-gaps | XHigh |`
   - `| /gsdd-verify | XHigh |`
   - `| /gsdd-verify-work | XHigh |`
   - `| /gsdd-audit-milestone | XHigh |`
   - `| /gsdd-complete-milestone | XHigh |`

   Backticks around command names are allowed in the actual table. Preserve the global rule that implementation defaults to High even when entered through quick/resume.
5. **Risk escalation and Max, per D-02:** the exact XHigh definition above establishes the required planning/verification/audit defaults and all critical risk floors. Include exactly: `Max is exceptional: choose it only after XHigh is demonstrably inadequate or before an unusually irreversible decision.` and `The Max reason must name the concrete XHigh inadequacy or unusual irreversibility.` Never choose Max merely because work is large or important.

Do not mention restarting OpenCode anywhere in the skill per D-06. Do not add `context`, `agent`, unsupported frontmatter, an OpenCode config registration, or edits to generated GSDD skills.
  </action>
  <verify>
    <automated>python -c 'import json; from pathlib import Path; p=Path(".planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json"); d=json.loads(p.read_text(encoding="utf-8")); assert d["schema_version"]==1 and d["root"]==".planning/phases/32-frequency-portuguese-text-and-audio"; assert d["entries"] and d["entries"][0]=={"path":".","sha256":None,"type":"directory"}; assert [e["path"] for e in d["entries"]]==sorted(e["path"] for e in d["entries"]); assert all(e["type"] in {"directory","file","symlink"} for e in d["entries"])'</automated>
    <automated>python -c 'from pathlib import Path; p=Path(".agents/skills/gsdd-reasoning-level/SKILL.md"); s=p.read_text(encoding="utf-8"); parts=s.split("---\n", 2); assert p.is_file() and len(parts)==3 and parts[0]==""; fm=parts[1].strip().splitlines(); assert len(fm)==2 and fm[0]=="name: gsdd-reasoning-level" and fm[1].startswith("description: "); d=fm[1].lower(); assert all(x in d for x in ("new project task", "/gsdd-*", "reasoning level")); assert parts[2].strip()'</automated>
  </verify>
  <done>The deterministic pre-implementation Phase 32 inventory exists before the one functional write, and the new skill has valid minimal frontmatter, a trigger-rich discovery description, the complete advisory/gate contract, and no restart text or config registration.</done>
</task>

<task id="057-02" type="auto">
  <name>Validate matrix, gate behavior, honesty, and no-touch boundaries</name>
  <files>
    - READ ONLY: .agents/skills/gsdd-reasoning-level/SKILL.md
    - READ ONLY: .planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json
    - READ ONLY: .planning/phases/32-frequency-portuguese-text-and-audio/**
    - READ ONLY: .agents/skills/*/SKILL.md excluding gsdd-reasoning-level
    - READ ONLY: AGENTS.md
    - READ ONLY: opencode.json, opencode.jsonc, .opencode/ when present
  </files>
  <action>
Run deterministic read-only checks against the completed skill. Per D-02/D-03/D-04, assert the complete literal three-line response template (including `Reason:` and its one-sentence task-specific instruction), explicit UI limitation, wait gate, both confirmation and adjustment rules, current-task state retention, all six exact tier definitions, High implementation default, XHigh planning/verification/audit default and every named critical-risk floor, every installed command's exact table mapping, and each Max predicate separately. Assert the Max rationale rule and no-large-or-important shortcut are present. Assert the skill contains no restart instruction, so D-06 remains completion-only.

Per D-01/D-05, inspect scoped git status and fail closed if any existing `.agents/skills/**`, `AGENTS.md`, `opencode.json*`, or `.opencode/**` path is dirty; the only allowed path on that protected status query is the new skill. Independently regenerate the full Phase 32 path/type/content inventory in memory and compare it exactly with `phase32-before.json`. Report and fail on added paths, removed paths, renamed paths (represented by removal plus addition), changed path types, changed file bytes, or changed symlink targets. Do not use a Phase 32 prefix allowlist, and do not clean, stash, restore, stage, or otherwise alter unrelated work to make checks pass.
  </action>
  <verify>
    <automated>python -c 'from pathlib import Path; s=Path(".agents/skills/gsdd-reasoning-level/SKILL.md").read_text(encoding="utf-8"); response="Recommended reasoning level: **{LEVEL}**\nReason: {one-sentence task-specific reason}\nI cannot inspect or change the reasoning level selected in OpenCode\x27s UI. Please set or confirm **{LEVEL}**, or reply with another allowed level."; tiers=["Low: narrow read-only status checks and lookups with no writes.","Normal: routine administrative, routing, or metadata work with low reversible risk.","Medium: bounded simple quick documentation, configuration, test-maintenance, or broad read-only mapping work.","High: default for implementation and every code behavior change.","XHigh: default for planning, verification, and audits, and the floor for critical database/schema/data migration, licensing/redistribution, provider credentials/billing/live side effects, auth/security/privacy, destructive, cross-cutting, and release/deployment/publication/closure work.","Max: exceptional only under the Max rule below; never a routine default."]; mappings={"/gsdd-progress":"Low","/gsdd-pause":"Low","/gsdd-resume":"Normal for restore/route only; otherwise use the resumed operation tier","/gsdd-map-codebase":"Medium","/gsdd-quick":"General ladder: Medium for bounded non-code quick work, High for implementation, XHigh when a critical-risk floor applies","/gsdd-execute":"High unless an XHigh risk floor applies","/gsdd-new-project":"XHigh","/gsdd-new-milestone":"XHigh","/gsdd-plan":"XHigh","/gsdd-plan-milestone-gaps":"XHigh","/gsdd-verify":"XHigh","/gsdd-verify-work":"XHigh","/gsdd-audit-milestone":"XHigh","/gsdd-complete-milestone":"XHigh"}; required=["Allowed levels (exact): Low, Normal, Medium, High, XHigh, Max","Select exactly one allowed level.","Wait for confirmation or adjustment before work.","Do not re-prompt within the same top-level task.","Use one sentence tailored to the specific task after the literal Reason: label.","The replies continue, proceed, go ahead, yes, or {LEVEL} confirm the recommendation.","A reply naming another allowed level adjusts the selection and satisfies the gate.","Use the highest applicable tier.","after XHigh is demonstrably inadequate","before an unusually irreversible decision","The Max reason must name the concrete XHigh inadequacy or unusual irreversibility.","never choose Max merely because work is large or important"]; missing=[x for x in [response,*tiers,*required] if x not in s]+[cmd for cmd,value in mappings.items() if f"| `{cmd}` | {value} |" not in s and f"| {cmd} | {value} |" not in s]; assert not missing,missing; assert "restart" not in s.lower()'</automated>
    <automated>python -c 'import subprocess; target=".agents/skills/gsdd-reasoning-level/SKILL.md"; out=subprocess.run(["git","status","--short","--untracked-files=all","--","AGENTS.md","opencode.json","opencode.jsonc",".opencode",".agents/skills"],check=True,capture_output=True,text=True).stdout.splitlines(); bad=[line for line in out if line[3:] != target]; assert not bad, "protected paths changed: "+repr(bad)'</automated>
    <automated>python -c 'import hashlib,json,os; from pathlib import Path; root=Path(".planning/phases/32-frequency-portuguese-text-and-audio"); baseline=json.loads(Path(".planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json").read_text(encoding="utf-8")); assert root.is_dir() and baseline["schema_version"]==1 and baseline["root"]==root.as_posix(); paths=sorted([root,*root.rglob("*")],key=lambda p:"." if p==root else p.relative_to(root).as_posix()); entries=[{"path":"." if p==root else p.relative_to(root).as_posix(),"type":"symlink" if p.is_symlink() else "file" if p.is_file() else "directory" if p.is_dir() else "unsupported","sha256":hashlib.sha256(os.readlink(p).encode("utf-8") if p.is_symlink() else p.read_bytes() if p.is_file() else b"").hexdigest() if p.is_symlink() or p.is_file() else None} for p in paths]; assert all(e["type"]!="unsupported" for e in entries),entries; before={e["path"]:e for e in baseline["entries"]}; after={e["path"]:e for e in entries}; added=sorted(after.keys()-before.keys()); removed=sorted(before.keys()-after.keys()); changed=sorted(p for p in before.keys()&after.keys() if before[p]!=after[p]); assert not (added or removed or changed),{"added":added,"removed":removed,"changed":changed}'</automated>
  </verify>
  <done>All expanded static contract checks pass, only the new skill is dirty among protected OpenCode/GSDD surfaces, and exact pre/post inventory proves Phase 32 has no content, path, or type delta.</done>
</task>

## Threat Model

### Trust Boundaries

| Boundary | Description |
|---|---|
| User request -> advisory skill | Task wording is untrusted input used only to classify risk and select one allowed level. |
| Skill instruction -> OpenCode UI | The skill can advise but has no trustworthy read/write channel to the UI-selected level. |
| Quick-task write scope -> existing workflow assets | A new external skill sits beside generated GSDD skills and must not mutate them or configuration. |

### STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q057-01 | Spoofing | Advisory response | mitigate | Canonical disclaimer forbids claiming the UI level was inspected, set, changed, or verified. |
| T-Q057-02 | Tampering | Existing skills/config | mitigate | Exact create-only path plus scoped and full-worktree git-status allowlist checks. |
| T-Q057-03 | Denial of service | Confirmation gate | mitigate | Gate is once per top-level task/invocation and remains satisfied through subtasks and continue/proceed messages. |
| T-Q057-04 | Elevation of privilege | Risk classification | mitigate | Highest-applicable-tier rule and explicit XHigh floors prevent a low-risk command baseline from overriding critical task content. |

## Verification

- Run all automated checks from Tasks 057-01 and 057-02 in under 60 seconds without network access.
- Confirm `phase32-before.json` was created before the skill and exact post-implementation inventory comparison reports no added, removed/renamed, type-changed, or content-changed Phase 32 path.
- Confirm no `opencode.json`, `.opencode/`, `AGENTS.md`, or pre-existing `.agents/skills/*/SKILL.md` diff exists.
- No UI proof or live OpenCode behavior claim is required.

## Success Criteria

- `.agents/skills/gsdd-reasoning-level/SKILL.md` exists at the exact auto-discovery path with valid minimal frontmatter.
- The skill deterministically passes complete response-shape, reason, confirmation/adjustment, six-tier, command-matrix, High/XHigh, risk-floor, and dual-Max-predicate checks.
- Exact deterministic pre/post inventory proves every Phase 32 path, type, file byte sequence, and symlink target is unchanged, with no additions, removals, or renames.
- No implementation/configuration file except the new skill is created or modified by execution.
- No commit, ROADMAP/SPEC update, generated-skill edit, AGENTS.md edit, or UI claim occurs.
- The implementation completion summary tells the user to quit and restart OpenCode so the new skill can be discovered; that reminder does not appear in the skill's per-task advisory.

## Source Coverage Audit

| Source | ID | Feature / Constraint | Task | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Auto-discovered reasoning-level advisor with confirmation gate | 057-01, 057-02 | COVERED | Derived from the quick-task description; no ROADMAP phase goal applies. |
| REQ | — | No phase requirement IDs | — | EXCLUDED | Quick mode explicitly has no ROADMAP/SPEC requirement changes. |
| RESEARCH | — | No research phase | — | EXCLUDED | Confirmed local OpenCode skill path/frontmatter pattern is already established. |
| CONTEXT | D-01 | One new skill at exact path; no config | 057-01, 057-02 | COVERED | Path/frontmatter and protected-status checks. |
| CONTEXT | D-02 | Six levels, command matrix, risk escalation | 057-01, 057-02 | COVERED | Complete installed-command inventory is asserted. |
| CONTEXT | D-03 | Honest UI limitation and wait gate | 057-01, 057-02 | COVERED | Canonical response and prohibited claims are explicit. |
| CONTEXT | D-04 | No repeated prompt within current task | 057-01, 057-02 | COVERED | Session-boundary behavior is explicit and checked. |
| CONTEXT | D-05 | Preserve generated skills, AGENTS, and dirty Phase 32 work | 057-01, 057-02 | COVERED | Protected git checks plus exact pre/post Phase 32 inventory fail closed. |
| CONTEXT | D-06 | Restart only in completion | 057-01, 057-02 | COVERED | Skill forbids restart text; success criteria require completion reminder. |

## Checks

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Quick-plan revision keeps two tasks and adds complete deterministic skill-contract assertions plus an owned pre/post Phase 32 path/type/content fingerprint. No independent checker was available in this planning run.
</plan_check>
</checks>

## Output

After later execution, retain `.planning/quick/057-add-gsdd-reasoning-level-advisor/phase32-before.json` as verification evidence and create `.planning/quick/057-add-gsdd-reasoning-level-advisor/057-SUMMARY.md`. In that completion summary and user-facing completion response, state that OpenCode must be quit and restarted to discover the new skill. Do not commit.
