#!/usr/bin/env node

import { cmdFileOp } from './lib/file-ops.mjs';
import { cmdLifecyclePreflight } from './lib/lifecycle-preflight.mjs';
import { cmdPhaseStatus, cmdVerify } from './lib/phase.mjs';
import { cmdSessionFingerprint } from './lib/session-fingerprint.mjs';
import { cmdUiProof } from './lib/ui-proof.mjs';
import { cmdControlMap } from './lib/control-map.mjs';
import { createCmdCloseoutReport } from './lib/closeout-report.mjs';
import { bootstrapHelperWorkspace, consumeWorkspaceRootArg, resolveWorkspaceContext } from './lib/workspace-root.mjs';

const HELPER_CONTEXT = {
  workflows: [],
  frameworkVersion: 'generated-helper',
};
const cmdCloseoutReport = createCmdCloseoutReport(HELPER_CONTEXT);

const COMMANDS = {
  'file-op': cmdFileOp,
  'lifecycle-preflight': cmdLifecyclePreflight,
  'phase-status': cmdPhaseStatus,
  verify: cmdVerify,
  'session-fingerprint': cmdSessionFingerprint,
  'ui-proof': cmdUiProof,
  'control-map': cmdControlMap,
  'closeout-report': cmdCloseoutReport,
};

function printHelp() {
  console.log([
    'Usage: node .planning/bin/gsdd.mjs [--workspace-root <path>] <command> [args]',
    '',
    'Local workflow helper commands:',
    '  file-op <copy|delete|regex-sub>',
    '                               Run deterministic workspace-confined file operations',
    '                               Example: node .planning/bin/gsdd.mjs file-op delete .planning/.continue-here.bak --missing ok',
    '  phase-status <N> <status>   Update ROADMAP.md phase status ([ ] / [-] / [x])',
    '                               Example: node .planning/bin/gsdd.mjs phase-status 1 done',
    '  verify <N>                  Run direct phase artifact and UI-proof gate checks',
    '                               Example: node .planning/bin/gsdd.mjs verify 1',
    '  lifecycle-preflight <surface> [phase]',
    '                               Inspect lifecycle gate results for a workflow surface',
    '                               Example: node .planning/bin/gsdd.mjs lifecycle-preflight verify 1 --expects-mutation phase-status',
    '  session-fingerprint write [--allow-changed <ROADMAP.md,SPEC.md,config.json>]',
    '                               Rebaseline planning-state drift after reviewing changed planning files',
    '  ui-proof validate <path> [--claim <public|publication|tracked|delivery|release>]',
    '                               Validate UI proof metadata; use --claim for stronger proof uses',
    '  ui-proof compare <planned-slots-json> [observed-bundle-json ...]',
    '                               Compare planned UI proof slots against observed bundles',
    '  control-map [--json] [--with-ignored] [--annotations <path>]',
    '                               Report computed repo/worktree/planning state and local annotations',
    '  closeout-report [--json] [--phase <N>]',
    '                               Replay read-only closeout status from control-map, health, preflight, verify, and UI-proof signals',
    '',
    'Advanced option:',
    '  --workspace-root <path>     Override workspace root discovery before or after the subcommand',
  ].join('\n'));
}

function applyWorkspaceRootOverride(workspaceRootArg) {
  if (!workspaceRootArg) {
    bootstrapHelperWorkspace(import.meta.url);
    return true;
  }

  const context = resolveWorkspaceContext(['--workspace-root', workspaceRootArg]);
  if (context.invalid) {
    console.error(context.error);
    process.exitCode = 1;
    return false;
  }

  process.env.GSDD_WORKSPACE_ROOT = context.workspaceRoot;
  try {
    process.chdir(context.workspaceRoot);
  } catch {
    // best-effort: command handlers also resolve from GSDD_WORKSPACE_ROOT
  }
  return true;
}

async function main() {
  const parsed = consumeWorkspaceRootArg(process.argv.slice(2));
  if (parsed.invalid) {
    console.error('Usage: --workspace-root <path>');
    process.exitCode = 1;
    return;
  }

  if (!applyWorkspaceRootOverride(parsed.workspaceRootArg)) return;

  const [command, ...args] = parsed.args;

  if (!command || command === 'help' || command === '--help') {
    printHelp();
    return;
  }

  const handler = COMMANDS[command];
  if (!handler) {
    printHelp();
    process.exitCode = 1;
    return;
  }

  await handler(...args);
}

await main();
