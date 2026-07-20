---
mode: quick
task: 028-install-recommended-agent-skills
runtime: opencode
assurance: self_checked
status: complete
completed: 2026-07-20
duration: 5m08s
---

# Quick Task 028 Summary: Install Recommended Agent Skills

Installed six authoritative skill packages as copied, project-scoped OpenCode skills while preserving all existing GSDD manifests and unrelated dirty worktree state.

## Result

| Skill | Authoritative source | Installed manifest |
|---|---|---|
| `systematic-debugging` | `obra/superpowers` | `.agents/skills/systematic-debugging/SKILL.md` |
| `test-driven-development` | `obra/superpowers` | `.agents/skills/test-driven-development/SKILL.md` |
| `azure-ai` | `microsoft/azure-skills` | `.agents/skills/azure-ai/SKILL.md` |
| `supabase-postgres-best-practices` | `supabase/agent-skills` | `.agents/skills/supabase-postgres-best-practices/SKILL.md` |
| `code-security` | `semgrep/skills` | `.agents/skills/code-security/SKILL.md` |
| `llm-security` | `semgrep/skills` | `.agents/skills/llm-security/SKILL.md` |

Every listed manifest is a non-empty regular copied file whose frontmatter `name` matches its directory. Supporting files supplied by each package were copied within the corresponding skill tree.

## Lockfile

The Skills CLI generated project lock metadata at `skills-lock.json` (`version: 1`). It records all six source repositories, source skill paths, and computed hashes. No pre-existing lockfile was replaced.

## Exact Skills CLI Commands

CLI inspected:

```bash
npx -y skills --help
npx -y skills --version
```

Successful installations (Skills CLI `1.5.19`):

```bash
npx -y skills add obra/superpowers --skill systematic-debugging test-driven-development --agent opencode --copy --yes
npx -y skills add microsoft/azure-skills --skill azure-ai --agent opencode --copy --yes && npx -y skills add supabase/agent-skills --skill supabase-postgres-best-practices --agent opencode --copy --yes && npx -y skills add semgrep/skills --skill code-security llm-security --agent opencode --copy --yes
```

The initial invocation without `--yes` reached the project/global selector but could not consume input because the executor shell is non-interactive; it made no repository changes:

```bash
npx -y skills add obra/superpowers --skill systematic-debugging test-driven-development --agent opencode --copy
```

Piping Enter and `winpty` experiments also could not provide a usable TTY and made no repository changes. The successful commands therefore used the CLI-documented `--yes` scope auto-detection only after all six destination paths were proven absent. No `--global` flag or existing skill path was used.

## Exact Verification Commands And Results

Manifest existence and content:

```bash
node -e "const fs=require('node:fs');const names=['systematic-debugging','test-driven-development','azure-ai','supabase-postgres-best-practices','code-security','llm-security'];for(const n of names){const p='.agents/skills/'+n+'/SKILL.md';if(!fs.existsSync(p)||!fs.statSync(p).isFile()||!fs.readFileSync(p,'utf8').trim())throw new Error('Missing or empty '+p)}console.log('verified 6 skill manifests')"
```

Result: `verified 6 skill manifests`.

GSDD manifest count and clean diff:

```bash
node -e "const fs=require('node:fs');const root='.agents/skills';const names=fs.readdirSync(root,{withFileTypes:true}).filter(e=>e.isDirectory()&&e.name.startsWith('gsdd-')&&fs.existsSync(root+'/'+e.name+'/SKILL.md')).map(e=>e.name);if(names.length!==14)throw new Error('Expected 14 GSDD manifests, found '+names.length);console.log('verified 14 GSDD manifests')"
git diff --exit-code HEAD -- .agents/skills/gsdd-*/SKILL.md
```

Results: `verified 14 GSDD manifests`; Git exited `0` with no GSDD diff.

Source, identity, and copy validation:

```bash
node -e "const fs=require('node:fs');const expected={'systematic-debugging':'obra/superpowers','test-driven-development':'obra/superpowers','azure-ai':'microsoft/azure-skills','supabase-postgres-best-practices':'supabase/agent-skills','code-security':'semgrep/skills','llm-security':'semgrep/skills'};const lock=JSON.parse(fs.readFileSync('skills-lock.json','utf8'));for(const [name,source] of Object.entries(expected)){const root='.agents/skills/'+name;const p=root+'/SKILL.md';const text=fs.readFileSync(p,'utf8');const identity=(text.match(/^name:\s*(.+)$/m)||[])[1];if(identity!==name)throw new Error('Identity mismatch '+name+': '+identity);if(lock.skills?.[name]?.source!==source)throw new Error('Source mismatch '+name);if(fs.lstatSync(root).isSymbolicLink()||fs.lstatSync(p).isSymbolicLink())throw new Error('Expected copied files for '+name)}console.log('verified identities, authoritative sources, and copied project files for 6 skills')"
```

Result: `verified identities, authoritative sources, and copied project files for 6 skills`.

Project scope and OpenCode discovery:

```bash
npx -y skills list --json
npx -y skills list --json | node -e "let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{const expected=['systematic-debugging','test-driven-development','azure-ai','supabase-postgres-best-practices','code-security','llm-security'];const rows=JSON.parse(s);for(const name of expected){const row=rows.find(x=>x.name===name);if(!row||row.scope!=='project'||!row.agents.includes('OpenCode'))throw new Error('Missing project OpenCode registration: '+name)}console.log('verified project scope and OpenCode discovery for 6 skills')})"
```

Result: all six list entries report `scope: project`, their repository paths, and `OpenCode` discovery; the parser printed `verified project scope and OpenCode discovery for 6 skills`.

Boundary inspection:

```bash
git status --short
git diff --binary -- danish-test-deck/generation-report.json danish-test-deck/generation-report.md | git hash-object --stdin
git hash-object -- jap-back.png jap-front.png jap1.png jap2.png japonese.md
```

Results:

- Pre-existing Danish deletion diff stayed `cab88753f9be41bda3f85249bb6fcd6a9f916180`.
- Pre-existing Japanese file hashes stayed, in command order: `b7558402e555b8a6dabe5d2989ef19ebdc3ee471`, `3818d764ed1c369c0e814e20ba6baf10d96d6423`, `4216c0ccf9361a9e33038c097d429f3777308e96`, `801d3926299362dadc7ed3c0474c5acfb4e056d7`, and `fa64ee5d308a57e61f9d310b8499594abcda14dc`.
- The task-owned additions are only the six requested skill trees, `skills-lock.json`, and this quick-task summary within the already-untracked quick-task directory.
- An unrelated `.planning/quick/027-adicionar-mandarim-integrado/027-PLAN.md` appeared concurrently after the initial status capture and after that directory had been observed empty. It was not read, modified, or removed; its preserved Git object hash at detection was `374d07882f5643b9d9642b68a4499ece258deb5d`.

## Constraints Honored

- Installed in project scope for OpenCode with `--copy`; no global installation was requested.
- Checked all destination paths before installation and did not overwrite any existing skill.
- Preserved all 14 GSDD skills byte-for-byte relative to `HEAD`.
- Preserved the existing `danish-test-deck` deletions and untracked Japanese files.
- Preserved the concurrent untracked quick-task 027 plan without claiming it as task output.
- Did not modify application code, `.planning/STATE.md`, `.planning/ROADMAP.md`, or `.planning/SPEC.md`.
- Did not stage, commit, amend, push, create a PR, or perform destructive Git operations.

## Deviations

- **Recoverable factual discovery:** Skills CLI `1.5.19` has no project flag for `add`; project is the default scope. Its interactive scope prompt requires a TTY unavailable to the executor shell, so the successful invocations used help-documented `--yes` project auto-detection after destination nonexistence checks. This changed only invocation mechanics, not installation scope or overwrite protections.
- **Concurrent unrelated worktree change:** `.planning/quick/027-adicionar-mandarim-integrado/027-PLAN.md` was created by another actor during execution. It remains untouched and outside this task's output set.

## Git Actions

Read-only Git status, diff, log, branch, and hash checks only. No repository delivery action was performed.

## Self-Check: PASSED

- Summary exists and is non-empty.
- Six copied manifests are non-empty and match their requested identities and lockfile sources.
- Skills CLI reports all six at project scope with OpenCode discovery.
- Exactly 14 GSDD manifests remain and `git diff --exit-code HEAD -- .agents/skills/gsdd-*/SKILL.md` passes.
- Danish diff and Japanese file hashes match the pre-install baseline.
- `HEAD` remains `35c7bfd137ddf4911cf81765521f0f464ddcc3df`, the index is unchanged, and no commit or other delivery action occurred.
- No tracked application diff was introduced; only the two pre-existing Danish deletions remain in `git diff --name-only`.
