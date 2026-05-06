# Phase 13: Highlight Export and Template - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 13 exports generated highlight cards to Anki-compatible APKG, CSV, and TSV artifacts with a dedicated highlight note type and study template. It covers highlight-only export field order, no `Translation` field, safe media references, centered responsive highlight card styling, front/back template behavior, and validation that highlight exports do not collide with existing frequency or manual word-list exports. It does not change highlight ingestion, text generation, audio synthesis, WebDAV fetching, phonetics templates, or the existing frequency/word-list template behavior.

</domain>

<decisions>
## Implementation Decisions

### Front Card
- **D-01:** The highlight card front should show the learner-facing prompt content: `Word`, `IPA`, `word_audio`, `Example Sentence`, and `sentence_audio`.
- **D-02:** The example sentence appears on the front together with `sentence_audio` so the card studies the reading-derived word in context.
- **D-03:** `Image` remains an exported field but renders only through a conditional block when populated. Blank images must not create an empty placeholder.
- **D-04:** Front labels should be minimal. The template may use a small example label if useful, but the card should not feel label-heavy.

### Back Definition
- **D-05:** The back template must keep `{{FrontSide}}`, then add an answer divider and a `Definition` answer area.
- **D-06:** The answer area should use a clear `Definition` label, not `Translation` or a generic answer label.
- **D-07:** Multiple definitions should render as a clean bullet list when possible, rather than one dense paragraph.
- **D-08:** Do not repeat audio controls or trigger autoplay on the back. Beyond the required `{{FrontSide}}`, the only new answer content on the back is the divider and `Definition` block.

### Visual Style
- **D-09:** The exact visual direction is the agent's discretion, but it must stay visibly Multilang-branded and use the existing blue theme as the default reference unless implementation research finds a better minimal variant.
- **D-10:** The card shell should be centered.
- **D-11:** Density should be comfortable rather than cramped, with enough room for a sentence on the front and definitions on the back.
- **D-12:** Mobile behavior should allow vertical scrolling for long content while avoiding horizontal scroll and preserving responsive layout.

### Export Safety
- **D-13:** Highlight export artifacts should contain only `highlights`/internal `kindle-highlights` rows. Mixed-source exports with `frequency` or `word-list` rows must fail closed with a clear error.
- **D-14:** Highlight templates must reference only the final exported highlight card fields. They must not reference raw highlight text, book metadata, source paths, private import records, or `Translation`.
- **D-15:** Because Azure TTS audio is expected for highlight cards, APKG export must fail before writing a broken package if `word_audio` or `sentence_audio` media is missing or mismatched.
- **D-16:** CSV and TSV exports must include strict Anki headers, including `#notetype`, `#deck`, and exact `#columns` for the highlight field set.

### Source Mode Boundaries
- **D-17:** Keep the three source modes distinct: `frequency` for frequency/wordfreq decks, `word-list` for manual user-provided word lists, and `highlights` for reading-derived highlight vocabulary.
- **D-18:** Phase 13 applies the new dedicated template to `highlights` only. Existing `frequency` and `word-list` export/template behavior must remain unchanged in this phase.

### the agent's Discretion
- Exact CSS class names, spacing, typography, and whether the highlight visual is a light variant of the current normal card or a slightly softer reading-card variant.
- Exact parser/loader structure for multiple templates, as long as source-profile selection remains explicit and existing modes stay stable.
- Exact validation helper names for dangling field references, as long as the gates prove no `Translation`, missing field, mixed-source note model, or broken media reference can ship.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` - Phase 13 goal, dependencies, requirements `EXPORT-01`, `EXPORT-02`, `EXPORT-03`, and success criteria for dedicated note type, English fields, no `Translation`, Definition-on-back template, responsive styling, media safety, and no mixed-source collisions.
- `.planning/REQUIREMENTS.md` - v1.2 export/template requirements, out-of-scope constraints for highlight translations and private data, and traceability showing Phase 13 owns only highlight export/template requirements.
- `.planning/PROJECT.md` - Current milestone target features, product constraints, blank image decision, Azure audio direction, and requirement to preserve existing modes.
- `.planning/STATE.md` - Carry-forward decisions that highlight exports use a dedicated note model, omit `Translation`, fail closed for mixed-source exports, and keep phonetics refresh isolated.

### Prior Phase Contracts
- `.planning/phases/11-highlight-pipeline-integration/11-CONTEXT.md` - Public `highlights` mode, internal `kindle-highlights` profile, import identity, private provenance, and count-only summaries.
- `.planning/phases/12-highlight-generation-audio-and-qa/12-VERIFICATION.md` - Verification that highlight rows preserve audio, IPA/spoken form, definitions, example sentence, blank `Image`, blank learner-facing `Translation`, and source-aware QA.
- `.planning/phases/12-highlight-generation-audio-and-qa/12-GENERATION-QA-EVIDENCE.md` - Phase 12 evidence for highlight text/audio/QA behavior that Phase 13 exports.
- `.planning/phases/08-card-quality-refresh/08-CONTEXT.md` - Existing normal card blue styling source and decision not to change unrelated phonetics template behavior.

### Existing Code Entry Points
- `CARD_TEMPLATE.md` - Current normal deck front/back/CSS template and Multilang blue styling reference.
- `src/multilang/domain/source_profiles.py` - Source-profile note type names, template names, and translation-export policy for `frequency`, `word-list`, and `kindle-highlights`.
- `src/multilang/domain/exporting.py` - Export field names, highlight field aliases, `Translation` omission, row mapping, and mixed-source field-name guard.
- `src/multilang/services/assemble_export_cards.py` - Assembly of accepted text, lexical data, audio sound tags, source profile export policy, blank `Image`, and highlight row construction.
- `src/multilang/services/export_anki_package.py` - Genanki model selection, note type IDs, template loading, APKG writing, media packaging, and mixed-source export guard.
- `src/multilang/services/export_tabular_bundle.py` - CSV/TSV Anki headers and source-aware field order.
- `tests/domain/test_exporting.py` - Current export-contract tests, including highlight field names and no `Translation`.
- `tests/services/test_assemble_export_cards.py` - Current highlight row assembly tests.
- `tests/services/test_export_anki_package.py` - Current APKG model, media, and mixed-source tests.
- `tests/services/test_export_tabular_bundle.py` - Current CSV/TSV header and field-order tests.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SourceProfile` already defines `kindle-highlights` with `note_type_name="Multilang::Highlight Card"`, `template_name="highlight_card"`, and `exports_translation_field=False`.
- `HIGHLIGHT_EXPORT_CARD_FIELD_NAMES` already defines exact English highlight fields: `SortIndex`, `Word`, `IPA`, `word_audio`, `Example Sentence`, `sentence_audio`, `Definition`, and `Image`.
- `ExportCardRow.ordered_field_mapping()` already synthesizes highlight aliases from normal internal fields, mapping `word` to `Word` and `Definitions` to `Definition` while omitting `Translation` for highlight source profiles.
- `export_anki_package()` already has separate model IDs/note type names and fails mixed-source APKG exports.
- `write_export_tabular_bundle()` already writes Anki-compatible headers and resolves source-aware field names from rows.

### Established Patterns
- Source-specific export behavior should flow through explicit source profiles, not ad hoc string branches at call sites.
- Existing frequency and manual word-list modes must remain stable while highlight-specific behavior is added.
- APKG export fails closed for missing media instead of producing importable but broken decks.
- Tabular exports include Anki metadata headers before rows.
- Current template loading parses `CARD_TEMPLATE.md`; Phase 13 likely needs either multi-template parsing or a dedicated highlight template source without breaking the normal template parser.

### Integration Points
- `export_anki_package._load_project_card_template()` currently ignores `source_type` while accepting it as a parameter. This is the likely integration point for selecting a dedicated highlight template.
- `build_multilang_model(source_type="kindle-highlights")` already selects highlight fields and note type identity, so planner should focus on template selection and validation rather than rebuilding model identity from scratch.
- `assemble_export_cards` already emits highlight rows without learner-facing translation, so Phase 13 should prove export artifacts preserve that contract through APKG/CSV/TSV.
- Existing export tests already cover part of the highlight contract; Phase 13 should extend them to prove actual highlight template content, dangling-reference validation, and import-safe headers/media.

</code_context>

<specifics>
## Specific Ideas

- The user wants the front to show: word, IPA, audio, and sentence.
- The user explicitly wants the example sentence on the front with sentence audio.
- The user confirmed the back should not add repeated audio; it should show the required `{{FrontSide}}` plus only the new definition answer content.
- The user wants mobile content to be allowed to scroll downward when long.
- The user asked whether manual `word-list` is the same as frequency/wordfreq. Clarification captured: `frequency`, `word-list`, and `highlights` are separate modes.

</specifics>

<deferred>
## Deferred Ideas

- Apply the new highlight-style template to manual `word-list` decks too. This is outside Phase 13 because Phase 13 is scoped to highlight export/template and existing `word-list` behavior must remain stable.

</deferred>

---

*Phase: 13-highlight-export-and-template*
*Context gathered: 2026-05-06*
