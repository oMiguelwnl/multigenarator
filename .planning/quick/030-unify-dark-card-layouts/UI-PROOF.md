# UI Proof: Three Revised Dark Families and Two Preserved Japanese Families

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Source and generated-model verification for five front/back families: the revised always-dark normal, shared phoneme, and Mandarin cards plus unchanged Japanese frequency and Kana production designs.",
  "route_state": "Static source inspection of modified_templates_preview.html containing five labeled front/back pairs in the corrected mixed-design scope; no live Anki route was available.",
  "environment": {
    "kind": "repository source and pytest model inspection",
    "agent_browser": "unavailable in the current shell",
    "screenshots_captured": false,
    "native_anki_available": false
  },
  "viewport": "Responsive CSS inspected at source level only; no browser viewport was rendered or observed.",
  "evidence_inputs": [
    "tests/services/test_card_template_loader.py",
    "src/multilang/templates/normal_card.md",
    "src/multilang/templates/russian_phoneme_card.md",
    "src/multilang/templates/mandarin_card.md",
    "src/multilang/templates/japanese_card.md",
    "src/multilang/templates/japanese_kana_card.md",
    "modified_templates_preview.html"
  ],
  "commands_or_manual_steps": [
    "uv run pytest tests/services/test_card_template_loader.py -q",
    "uv run python -c generated-model inspection from 030-PLAN.md",
    "uv run pytest tests/services/test_russian_phoneme_deck.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q",
    "uv run python -c preview pair-count validation from 030-PLAN.md",
    "Manual source inspection of each labeled preview article; no browser rendering was claimed."
  ],
  "verification_results": {
    "combined_focused_suites": "78 passed",
    "japanese_frequency_production_template": "No final diff; byte-for-byte HEAD/pre-task state",
    "japanese_kana_production_template": "No final diff; byte-for-byte HEAD/pre-task state"
  },
  "observations": [
    {"template": "normal", "side": "front", "status": "source_observed", "observation": "Dark hero, definition, sentence/audio panel, and hidden answer-only translation are represented."},
    {"template": "normal", "side": "back", "status": "source_observed", "observation": "Translation is represented as revealed inside the same example panel."},
    {"template": "phoneme", "side": "front", "status": "source_observed", "observation": "Spelling, sound, native audio placeholders, example word, and sentence panel remain distinct."},
    {"template": "phoneme", "side": "back", "status": "source_observed", "observation": "Sentence translation is represented inside its sentence panel while source tests preserve the reveal fallback."},
    {"template": "mandarin", "side": "front", "status": "source_observed", "observation": "Simplified word, Pinyin, Traditional form, sentence variants, and hidden translation remain ordered."},
    {"template": "mandarin", "side": "back", "status": "source_observed", "observation": "Pinyin, Traditional Sentence, and revealed translation share the example panel."},
    {"template": "japanese-frequency", "side": "front", "status": "source_observed", "observation": "Preview represents the original light/night purple design and preserves recall-first word/sentence hierarchy, furigana toggle, two audio controls, and instruction."},
    {"template": "japanese-frequency", "side": "back", "status": "source_observed", "observation": "Preview represents the original design with optional image, furigana content, two audio positions, meaning rows, and Jisho/Images/Weblio links; production template has no final quick-030 diff."},
    {"template": "kana", "side": "front", "status": "source_observed", "observation": "Preview represents the original light/night purple recognition side with script, glyph, and recall instruction only."},
    {"template": "kana", "side": "back", "status": "source_observed", "observation": "Preview represents the original reveal design and Gif, divider, Romaji/audio, Picture, Strokes, and Mnemonic order; production template has no final quick-030 diff."}
  ],
  "artifacts": [
    {"path": "modified_templates_preview.html", "type": "static_html_source", "visibility": "local_only", "retention": "working_tree", "sensitivity": "none", "safe_to_publish": false},
    {"path": "tests/services/test_card_template_loader.py", "type": "focused_contract_tests", "visibility": "repository", "retention": "project_source", "sensitivity": "none", "safe_to_publish": true},
    {"path": ".planning/quick/030-unify-dark-card-layouts/UI-PROOF.md", "type": "proof_metadata", "visibility": "repository", "retention": "quick_task", "sensitivity": "none", "safe_to_publish": true}
  ],
  "privacy": "Representative vocabulary is synthetic/public and contains no user highlights, local private paths, credentials, or provider data.",
  "result": "human_needed",
  "claim_limits": "Automated evidence supports the corrected source claim: normal, shared phoneme, and Mandarin use the revised dark design, while Japanese frequency and Kana retain their original production designs and are represented that way in the static preview. Exact browser layout, font metrics, native replay controls, WebView behavior, reveal rendering, and native Anki Desktop/mobile appearance remain human_needed; no browser or native Anki screenshot was captured."
}
```
