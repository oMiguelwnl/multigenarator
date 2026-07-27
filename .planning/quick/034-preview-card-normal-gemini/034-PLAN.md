---
mode: quick
task: 034-preview-card-normal-gemini
plan: 034
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 1
requirements: []
files_modified:
  - normal_card_gemini_preview.html
  - .planning/quick/034-preview-card-normal-gemini/UI-PROOF.md
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/ is empty; this plan applies the supplied quick-mode planner contract directly."
non_goals:
  - "Do not edit the production normal-card template, tests, other previews, templates, application code, LOG.md, ROADMAP.md, or SPEC.md."
  - "Do not claim native Anki Desktop/mobile fidelity or add browser/test infrastructure."
  - "Do not add network requests, scripts, libraries, images, fonts, or other external assets."
hard_boundaries:
  - "Execution may create only the root preview HTML and this quick task's UI-PROOF.md; the executor owns 034-SUMMARY.md after task completion, outside the task write set."
  - "Treat src/multilang/templates/normal_card.md and the entire pre-existing dirty worktree as read-only."
  - "Do not stage, commit, restore, clean, delete, or reformat unrelated files."
anti_regression_targets:
  - "The current dirty contents of src/multilang/templates/normal_card.md remain byte-for-byte unchanged during execution."
  - "The preview contains exactly two normal cards: one front state and one back state, with identical content structure except for Translation visibility state."
closure_claim_limit: "Source inspection may prove the standalone preview's HTML structure, declared responsive CSS, offline containment, and front/back Translation states; it does not prove pixel rendering or native Anki behavior."
ui_proof_slots:
  - slot_id: normal-gemini-preview-source-proof
    claim: "The standalone root preview presents representative normal-card front and back states side by side at wide widths, stacks them responsively at narrow widths, mirrors the effective Gemini declarations, hides Translation only on the front, and has no script or external dependency."
    route_state: "Inspect normal_card_gemini_preview.html as a local standalone document with data-state=front and data-state=back; no application route or native Anki runtime is involved."
    required_evidence_kinds: [code, test]
    minimum_observations: 8
    expected_artifact_types: ["HTML source inspection", "Python stdlib validation output", "source-integrity hash observation"]
    validation_command: >-
      python -c "import re; from pathlib import Path; s=Path('normal_card_gemini_preview.html').read_text(encoding='utf-8'); lt=chr(60); articles=re.findall(lt+r'article class=\"preview-card\" data-state=\"(front|back)\"[^>]*>(.*?)'+lt+r'/article>',s,re.I|re.S); assert len(re.findall(lt+r'article\b',s,re.I))==2 and len(articles)==2; assert [state for state,_ in articles]==['front','back']; front,back=(body for _,body in articles); assert 'class=\"translation is-hidden\"' in front and 'data-translation-state=\"hidden\"' in front; assert 'class=\"translation is-visible\"' in back and 'data-translation-state=\"visible\"' in back; assert front.replace('is-hidden','is-visible').replace('\"hidden\"','\"visible\"').replace('aria-hidden=\"true\"','aria-hidden=\"false\"')==back; assert re.search(r'\.is-hidden\s*\{[^}]*display\s*:\s*none',s,re.I|re.S) and re.search(r'\.is-visible\s*\{[^}]*display\s*:\s*block',s,re.I|re.S); required=('#121212','#1E1E1E','#EAEAEA','#A0A0A0','#333333','Georgia, Cambria, \"Times New Roman\", Times, serif','max-width: 460px','padding: 28px 24px','border-radius: 8px','box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)','font-size: 38px','grid-template-columns: repeat(2, minmax(0, 460px))','@media (max-width: 980px)','grid-template-columns: 1fr'); assert all(token in s for token in required),[token for token in required if token not in s]; forbidden=(lt+r'script\b',lt+r'link\b',r'\b(?:src|href)\s*=',r'@import\b',r'url\s*\(',r'https?://'); assert not any(re.search(p,s,re.I) for p in forbidden),[p for p in forbidden if re.search(p,s,re.I)]; print('preview contract OK: exactly 2 mirrored cards, front hidden, back visible, responsive, offline, script-free')"
    environment: "Offline Python stdlib and source inspection only; no server, network, browser automation, or native Anki client."
    viewport: "CSS contract declares two columns up to 460px each on widths above 980px and one column at or below 980px; no rendered viewport is claimed."
    manual_acceptance_required: false
    claim_limit: "Proves source-declared structure and responsiveness only; does not prove computed pixels, installed-font rendering, audio playback, or Anki WebView fidelity."
must_haves:
  truths:
    - "The user can open one self-contained root HTML file and compare a representative front and back normal card."
    - "At wide widths the two cards are side by side; at narrow widths they stack without exceeding their container."
    - "Both cards show the same word, IPA, definitions, example, and Unicode audio indicators; only the back displays Translation."
    - "The preview visibly declares the current Gemini palette, serif content typography, 460px card width, 28px 24px padding, 8px radius, shadow, and 38px target word."
    - "The preview contains no scripts, network references, libraries, images, fonts, or external assets."
    - "The production template and all unrelated dirty worktree content remain unchanged."
  artifacts:
    - path: normal_card_gemini_preview.html
      provides: "Responsive, offline, side-by-side normal-card front/back preview"
    - path: .planning/quick/034-preview-card-normal-gemini/UI-PROOF.md
      provides: "Source-level observations, validation command/result, artifact privacy metadata, and claim boundary"
  key_links:
    - from: "normal_card_gemini_preview.html front article"
      to: "normal_card_gemini_preview.html back article"
      via: "mirrored markup and representative data with only Translation state classes/attributes differing"
    - from: "normal_card_gemini_preview.html responsive grid"
      to: "two 460px cards"
      via: "two-column grid above 980px and one-column media-query override at or below 980px"
    - from: normal_card_gemini_preview.html
      to: .planning/quick/034-preview-card-normal-gemini/UI-PROOF.md
      via: "the exact Python source-inspection command and recorded observations"
---

# Quick Task 034 Plan: Preview do card normal Gemini

<objective>
Create and deliver a standalone root HTML preview of the already-adapted normal Gemini card, showing representative front and back states without changing the production template.

Purpose: let the user directly inspect the normal-card result while preserving the verified production implementation and the existing dirty worktree.

Output: `normal_card_gemini_preview.html` plus a proportional source-level proof bundle at `.planning/quick/034-preview-card-normal-gemini/UI-PROOF.md`.
</objective>

<context>
- Source of visual truth: `src/multilang/templates/normal_card.md`, especially its final effective Gemini declarations verified by Quick Task 032.
- The production template is an inspection-only input. Copy its effective visual values into an independent document; do not edit or mechanically transform the template.
- Discovery level 0: this is bounded HTML/CSS composition using existing verified declarations and Python stdlib source inspection, with no new dependency or external API.
- The worktree is already dirty across planning, templates, tests, docs, previews, and deleted generated reports. Preserve all of it exactly; do not clean or absorb unrelated changes.
</context>

## Locked Decisions

- **D-01 — Production remains untouched:** `src/multilang/templates/normal_card.md`, tests, other previews, templates, and application code are read-only.
- **D-02 — Exactly two states:** the root preview contains exactly two `.preview-card` articles in front-then-back order, shown side by side on wide screens and stacked responsively on narrow screens.
- **D-03 — Same representative content:** both cards use the same realistic word, IPA, definitions, example sentence, and Unicode word/sentence audio indicators. Translation exists in both structures, is hidden on the front, and is visible on the back. Omit the empty normal Image area rather than inventing media.
- **D-04 — Effective Gemini visual:** use page `#121212`, card `#1E1E1E`, primary `#EAEAEA`, muted `#A0A0A0`, divider/border `#333333`, Georgia/Cambria/serif content, `460px` maximum card width, `28px 24px` card padding, `8px` radius, the effective shadow, and a `38px` target word.
- **D-05 — Self-contained and responsive:** use only HTML and an inline `<style>` block. No script, network, library, image, font, SVG, stylesheet, or external asset reference is allowed.
- **D-06 — Proportional UI proof:** source inspection and the specified Python validator are sufficient for this deliverable. Do not scaffold or run Playwright/Cypress; native Anki fidelity remains outside the claim.
- **D-07 — Dirty-worktree preservation:** do not edit LOG, ROADMAP, SPEC, stage, commit, restore, delete, clean, or change any unrelated path.

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: "One atomic task covers both deliverables, every verify step is runnable, UI proof is claim-bounded, and the write set excludes the executor-owned summary. Independent role/checker assurance is unavailable because the repository role directory is empty."
</plan_check>
</checks>

<tasks>

<task id="034-01" type="auto">
  <name>Create the standalone normal-card preview and source proof</name>
  <files>
    - CREATE: normal_card_gemini_preview.html
    - CREATE: .planning/quick/034-preview-card-normal-gemini/UI-PROOF.md
  </files>
  <action>
    Before writing, capture `git status --short` and the SHA-256 of the current bytes in `src/multilang/templates/normal_card.md`; retain both as the protected baseline per D-01/D-07. Create `normal_card_gemini_preview.html` as a valid standalone HTML5 document with inline CSS only. Use a centered `.preview-grid` whose wide layout is exactly `repeat(2, minmax(0, 460px))`, then switch to one column in `@media (max-width: 980px)` so the document remains readable on narrow screens. Put a concise `Front` or `Back` label above each card, outside the card article.

    Add exactly two article elements using the deterministic opening tags `<article class="preview-card" data-state="front">` and `<article class="preview-card" data-state="back">`, in that order (D-02). Duplicate the same semantic card body and representative data in both: target word `saudade`, IPA `/sawˈdadʒi/`, two concise definitions, Portuguese example `Sinto saudade das tardes que passávamos juntos.`, English Translation `I miss the afternoons we used to spend together.`, and separate Unicode `▶` indicators with accessible labels for word and sentence audio (D-03). Preserve the normal hierarchy of target row, divider, Definition section, divider, and example section. Do not render an image block because this represents the normal empty-Image case. The only body differences must be the Translation state tokens: front uses `class="translation is-hidden"`, `data-translation-state="hidden"`, and `aria-hidden="true"`; back uses the corresponding `is-visible`, `visible`, and `false` values. Define `.is-hidden { display: none; }` and `.is-visible { display: block; }`; do not use JavaScript.

    Mirror every effective value in D-04 literally in the inline CSS, including `box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)`, while retaining overflow containment, border-box sizing, readable line heights, muted IPA/headings/Translation, and the unboxed example treatment from the production template. Keep audio indicators visually muted and non-interactive; they represent the presence and placement of Anki audio controls rather than playback.

    Run the exact Python validator from `ui_proof_slots`. Then create `UI-PROOF.md` with fenced JSON containing all required top-level fields: `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result`, and `claim_limits`. Record at least eight exact observations matching slot `normal-gemini-preview-source-proof`: two-card count/order, mirrored structure, front hidden state, back visible state, representative IPA/definitions/example/audio content, effective palette/dimensions/type, wide two-column layout, narrow one-column override, and absence of scripts/external references. Record the validator command and passing output. Add `source_integrity` with the before/after SHA-256 values for `normal_card.md`; both must equal the live final hash. Give both artifacts `visibility`, `retention`, `sensitivity`, and `safe_to_publish` metadata. Set `result` to `pass` only after all source checks pass, and retain D-06's explicit non-Anki/non-pixel claim limit. Do not create or edit `034-SUMMARY.md`; the executor writes that lifecycle artifact after this task.
  </action>
  <verify>
    <automated>python -c "import re; from pathlib import Path; s=Path('normal_card_gemini_preview.html').read_text(encoding='utf-8'); lt=chr(60); articles=re.findall(lt+r'article class=\"preview-card\" data-state=\"(front|back)\"[^>]*>(.*?)'+lt+r'/article>',s,re.I|re.S); assert len(re.findall(lt+r'article\b',s,re.I))==2 and len(articles)==2; assert [state for state,_ in articles]==['front','back']; front,back=(body for _,body in articles); assert 'class=\"translation is-hidden\"' in front and 'data-translation-state=\"hidden\"' in front; assert 'class=\"translation is-visible\"' in back and 'data-translation-state=\"visible\"' in back; assert front.replace('is-hidden','is-visible').replace('\"hidden\"','\"visible\"').replace('aria-hidden=\"true\"','aria-hidden=\"false\"')==back; assert re.search(r'\.is-hidden\s*\{[^}]*display\s*:\s*none',s,re.I|re.S) and re.search(r'\.is-visible\s*\{[^}]*display\s*:\s*block',s,re.I|re.S); required=('#121212','#1E1E1E','#EAEAEA','#A0A0A0','#333333','Georgia, Cambria, \"Times New Roman\", Times, serif','max-width: 460px','padding: 28px 24px','border-radius: 8px','box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5)','font-size: 38px','grid-template-columns: repeat(2, minmax(0, 460px))','@media (max-width: 980px)','grid-template-columns: 1fr'); assert all(token in s for token in required),[token for token in required if token not in s]; forbidden=(lt+r'script\b',lt+r'link\b',r'\b(?:src|href)\s*=',r'@import\b',r'url\s*\(',r'https?://'); assert not any(re.search(p,s,re.I) for p in forbidden),[p for p in forbidden if re.search(p,s,re.I)]; print('preview contract OK: exactly 2 mirrored cards, front hidden, back visible, responsive, offline, script-free')"</automated>
    <automated>python -c "import hashlib,json,re; from pathlib import Path; p=Path('.planning/quick/034-preview-card-normal-gemini/UI-PROOF.md').read_text(encoding='utf-8'); m=re.search(r'```json\s*(.*?)\s*```',p,re.S); assert m; d=json.loads(m.group(1)); required={'proof_bundle_version','scope','route_state','environment','viewport','evidence_inputs','commands_or_manual_steps','observations','artifacts','privacy','result','claim_limits','source_integrity'}; assert required.issubset(d.keys()),sorted(required-d.keys()); assert d['result']=='pass'; assert len(d['observations'])>=8; assert all({'visibility','retention','sensitivity','safe_to_publish'}.issubset(a.keys()) for a in d['artifacts']); live=hashlib.sha256(Path('src/multilang/templates/normal_card.md').read_bytes()).hexdigest(); integrity=d['source_integrity']; assert integrity['normal_card_before_sha256']==integrity['normal_card_after_sha256']==live; print('UI proof OK: complete, source-integrity preserved, claim remains source-only')"</automated>
    <automated>git diff --check -- "normal_card_gemini_preview.html" ".planning/quick/034-preview-card-normal-gemini/UI-PROOF.md" ".planning/quick/034-preview-card-normal-gemini/034-PLAN.md"</automated>
    <automated>git diff --cached --exit-code -- "normal_card_gemini_preview.html" ".planning/quick/034-preview-card-normal-gemini" "src/multilang/templates/normal_card.md"</automated>
  </verify>
  <done>`normal_card_gemini_preview.html` is an offline, responsive two-state comparison matching D-02 through D-05; the Python checks and UI proof pass; `normal_card.md` retains its captured SHA-256; and no unrelated, staged, or committed change is made.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Local preview file -> browser HTML renderer | The delivered standalone document is opened locally and must not load or execute remote/active content. |
| Preview work -> dirty production worktree | Creating a review artifact must not mutate the already-verified production template or unrelated concurrent changes. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q034-01 | Tampering / Information disclosure | `normal_card_gemini_preview.html` | mitigate | Reject scripts, links, `src`/`href`, CSS imports/URLs, and HTTP(S) references with the Python source validator; use only fixed representative text. |
| T-Q034-02 | Tampering / Repudiation | `src/multilang/templates/normal_card.md` and dirty worktree | mitigate | Capture and record before/after SHA-256 for the production template, compare against the live final hash, constrain writes to two new files, and prohibit staging/commit/cleanup. |
</threat_model>

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Deliver a viewable preview of the already-adapted normal Gemini card | Task 034-01 creates the root HTML comparison |
| REQ | Quick mode has no active ROADMAP requirement IDs | `requirements: []`; active planning remains read-only |
| RESEARCH | Quick 032 verified the current template's effective Gemini values and contracts | D-04 and literal CSS/source checks in Task 034-01 |
| CONTEXT | Production untouched; exactly two front/back cards; Translation state; representative fields/audio; responsive/offline; bounded proof; no commit/staging | D-01 through D-07, all implemented and verified in Task 034-01 |

Excluded without gap: changing production/templates/tests, native Anki rendering fidelity, browser automation infrastructure, image media for the normal empty-Image case, and updates to LOG/ROADMAP/SPEC.

<verification>
Run every task-level command from the repository root. Treat the first Python command as the authoritative preview contract check and the second as proof-bundle/source-integrity validation. Source inspection is sufficient only for the bounded standalone-preview claim stated in `closure_claim_limit`.
</verification>

<success_criteria>
- Exactly one standalone root preview file contains exactly two mirrored normal cards in front/back order.
- Translation is structurally present but hidden on the front and visible on the back without JavaScript.
- IPA, definitions, example, and separate Unicode audio indicators are represented on both cards; no image area appears for the empty-Image case.
- The literal effective Gemini palette, serif stack, 460px width, 28px 24px padding, 8px radius, shadow, and 38px word are present.
- Source CSS declares side-by-side wide layout and one-column narrow layout with containment.
- The HTML is self-contained and has no script, network, library, image, font, or external asset reference.
- `UI-PROOF.md` contains valid fenced JSON, at least eight matching observations, complete artifact privacy metadata, passing validation, source-integrity hashes, and a source-only claim limit.
- The production template, tests, existing previews, LOG, ROADMAP, SPEC, staged state, and all unrelated dirty files remain unchanged; no commit is created.
</success_criteria>
