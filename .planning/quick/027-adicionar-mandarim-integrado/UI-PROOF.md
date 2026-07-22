# UI Proof: Mandarin Anki Static Contract and Human Render Gate

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Mandarin frequency and word-list note schema, Multilang template structure, APKG media packaging, and CSV/TSV serialization",
  "route_state": "SupportedLanguage.ZH through persisted ExportCardRow snapshots into Multilang::Mandarin Card for frequency and word-list exports",
  "environment": "Offline Python/genanki tests with APKG ZIP and collection.anki2 inspection; no Anki renderer is available in the automated workspace",
  "viewport": "Static contract: CSS max-width 400px; pending human review on Anki Desktop 1280x800 and Google Pixel 7/AnkiDroid 412x915 portrait",
  "evidence_inputs": {
    "tools_used": [
      "pytest",
      "genanki",
      "zipfile",
      "sqlite3",
      "csv"
    ],
    "files_observed": [
      "src/multilang/templates/normal_card.md",
      "src/multilang/templates/mandarin_card.md",
      "tests/services/test_card_template_loader.py",
      "tests/services/test_export_anki_package.py",
      "tests/services/test_export_tabular_bundle.py",
      "tests/integration/test_mandarin_modern_flow.py"
    ],
    "automated_observations": [
      "Both Mandarin source types resolve model id 1762800901 and the exact 12-field Mandarin tuple.",
      "The loaded Mandarin CSS contains the complete normal-card CSS followed only by auxiliary Mandarin selectors.",
      "Template marker order places Simplified word, Pinyin, Traditional, Simplified sentence, sentence Pinyin, and Traditional sentence in the planned hierarchy.",
      "Translation remains hidden in the front template and is revealed by the fixed normal-card back script.",
      "The APKG collection model, note values, blank Image, two sound tags, media manifest, and archived audio payloads pass offline inspection.",
      "UTF-8 CSV and TSV exports preserve the exact field order and both sound basenames without claiming to package media."
    ]
  },
  "commands_or_manual_steps": [
    "Ran uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_mandarin_modern_flow.py -q.",
    "Inspected generated APKG ZIP media mapping and collection.anki2 model/note records in offline integration tests.",
    "Verified CSV and TSV five-line Anki headers, UTF-8 values, field order, sound tags, and empty Image in offline integration tests.",
    "Generated the persistent proof APKG once from the offline frequency fixture and validated one zh note with exactly two media payloads.",
    "Human: import this exact APKG hash into Anki Desktop at 1280x800 and inspect front and back.",
    "Human: import the same APKG hash into AnkiDroid on Google Pixel 7 at 412x915 portrait and inspect front and back."
  ],
  "observations": [],
  "artifacts": [
    {
      "path": ".planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg",
      "type": "Anki package for manual Desktop and AnkiDroid review",
      "byte_size": 66024,
      "sha256": "63712333c79acd2e42002d8c7465d45257cac99dd06df83a4764932f89a4433c",
      "visibility": "local_only",
      "retention": "retain until human visual review is complete",
      "sensitivity": "low",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "contains_user_data": false,
    "contains_reference_deck_content": false,
    "publication_approved": false,
    "screenshots_included": false
  },
  "result": "human_needed",
  "claim_limits": "Automated evidence proves schema, template references and order, CSS inheritance, hidden-front Translation, serialized values, and APKG media integrity only. It does not prove pixel placement, overflow, collision, or legibility in Anki Desktop or AnkiDroid."
}
```
