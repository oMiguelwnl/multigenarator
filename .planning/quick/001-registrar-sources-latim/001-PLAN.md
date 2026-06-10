---
quick: 001-registrar-sources-latim
type: quick-plan
task_count: 2
autonomous: true
files_modified:
  - data/latin_mvp/source_candidates.json
  - tests/domain/test_latin_source_candidates.py
  - .planning/quick/001-registrar-sources-latim/001-SUMMARY.md
no_ui_proof_rationale: "This quick task creates a structured project data/evidence artifact only; it does not add or modify UI, CLI commands, API routes, generation behavior, export behavior, or runtime provider wiring."
locked_context:
  - "Registrar candidates only from new2.md."
  - "Do not activate any provider or change runtime behavior."
  - "Do not update generation/export flows, ROADMAP.md, or SPEC.md."
  - "Do not perform deep web research."
  - "Preserve new2.md as raw input."
---

<objective>
Register the sources found in `new2.md` as structured candidates for future Latin audio and frequency decisions.

Purpose: preserve user-discovered source leads in a validated, fail-closed project artifact without changing runtime behavior or committing to any provider/source.

Output: a small candidate inventory under `data/latin_mvp/`, a focused validation test, and a quick execution summary.
</objective>

<context>
@new2.md
@src/multilang/domain/latin.py
@src/multilang/services/latin_audio.py
@src/multilang/services/latin_frequency.py
@data/latin_mvp/

Constraints:
- Treat every listed source as `candidate_only`, not approved or active.
- Keep current Latin audio policy intact: eSpeak NG `la` remains the classical approximation; Azure Latin remains blocked absent verified native Classical Latin/`la` support.
- Do not modify runtime files unless needed only to confirm no wiring changed; expected implementation should not touch runtime modules.
- Leave `new2.md` unchanged as raw input evidence.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add structured Latin source candidate inventory</name>
  <files>data/latin_mvp/source_candidates.json, new2.md</files>
  <action>
Create `data/latin_mvp/source_candidates.json` as a committed structured inventory copied from `new2.md` and keep `new2.md` unchanged. Use explicit fields that prevent accidental activation: `status: "candidate_only"`, `runtime_enabled: false`, `decision: "unreviewed"`, `source_input: "new2.md"`, and `notes` explaining that these are leads for future evaluation only.

Include these candidate entries exactly as leads:
- Audio candidate mention: Google Translate Latin, no URL in raw input, candidate-only note that this needs future verification and must not replace the current policy.
- Audio candidate mention: ElevenLabs Italian, no URL in raw input, candidate-only note that it is Italian rather than verified Latin/Classical Latin.
- Audio candidate URL: FineVoice Latin voice library, `https://finevoice.ai/voicelibrary/latin`.
- Frequency candidate URL: My Little Word Land Latin frequent words, `https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim`.
- Frequency/library candidate URL: Bridge/Haverford, `https://bridge.haverford.edu/`.
- Frequency candidate URL: DCC Latin Core List, `https://dcc.dickinson.edu/latin-core-list1`.
- Related/non-Latin reference candidate URL: DCC Greek Core List, `https://dcc.dickinson.edu/greek-core-list`, marked as `related_reference_only` so it cannot be mistaken for Latin frequency data.
- Frequency candidate URL: DCC Portuguese Latin Core List, `https://dcc.dickinson.edu/pt/latin-core-list1`.

Do not add provider configuration, environment variables, service imports, CLI commands, generation/export references, or activation flags. Do not edit `ROADMAP.md` or `SPEC.md`.
  </action>
  <verify>
    <automated>python -m json.tool data/latin_mvp/source_candidates.json</automated>
    <automated>git diff -- new2.md</automated>
  </verify>
  <done>`source_candidates.json` exists, parses as JSON, contains all source leads from `new2.md`, marks every entry as candidate-only/non-runtime, and `new2.md` has no diff.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add focused fail-closed validation test</name>
  <files>tests/domain/test_latin_source_candidates.py, data/latin_mvp/source_candidates.json</files>
  <action>
Add a focused pytest file that loads `data/latin_mvp/source_candidates.json` and verifies the artifact is safe evidence, not runtime wiring. Test expectations:
- the file exists and parses;
- every candidate has `status == "candidate_only"` and `runtime_enabled is False`;
- the expected URLs from `new2.md` are present;
- Google Translate Latin and ElevenLabs Italian are represented as source mentions without fabricated URLs;
- the DCC Greek Core List is categorized as related/non-Latin reference, not Latin frequency input;
- no candidate is marked approved/active.

Keep the test local to the artifact; do not import Latin runtime services or alter production behavior.
  </action>
  <verify>
    <automated>pytest tests/domain/test_latin_source_candidates.py -q</automated>
  </verify>
  <done>The focused test passes and proves the candidate artifact remains fail-closed and complete against the raw `new2.md` source list.</done>
</task>

</tasks>

<verification>
Run these focused checks after implementation:
- `python -m json.tool data/latin_mvp/source_candidates.json`
- `pytest tests/domain/test_latin_source_candidates.py -q`
- `git diff -- src/multilang data/latin_mvp/source_candidates.json tests/domain/test_latin_source_candidates.py new2.md .planning/quick/001-registrar-sources-latim/001-SUMMARY.md`

Confirm the diff does not modify runtime generation/export flows, `ROADMAP.md`, `SPEC.md`, or `new2.md`.
</verification>

<success_criteria>
- All sources from `new2.md` are represented once in a structured candidate artifact.
- Every entry is explicitly candidate-only and runtime-disabled.
- No provider/source is activated or recommended as final.
- Focused validation test passes.
- `new2.md` is preserved as raw input.
</success_criteria>

<output>
After execution, create `.planning/quick/001-registrar-sources-latim/001-SUMMARY.md` with what changed, verification commands/results, and confirmation that no runtime behavior changed.
</output>
