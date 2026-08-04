```json
{
  "proof_bundle_version": "1.0",
  "scope": {
    "work_item": "quick-044-romaji-frequencia-japones",
    "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
    "requirement_ids": [
      "N/A-QUICK-044-NO-ROADMAP-REQUIREMENT"
    ],
    "slot_ids": [
      "japanese-frequency-romaji-structural-contract"
    ]
  },
  "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
  "environment": "Python 3.12, cutlet 0.5.x, genanki, zipfile, and SQLite; offline; no Anki renderer.",
  "viewport": "Not applicable to this structural claim: no rendered pixels or viewport-dependent behavior is asserted.",
  "evidence_inputs": {
    "kinds": [
      "code",
      "test",
      "runtime"
    ],
    "tools_used": [
      "pytest",
      "genanki",
      "python-zipfile",
      "python-sqlite3",
      "gsdd-ui-proof-validate"
    ],
    "fixed_data_only": true,
    "network_used": false,
    "native_anki_renderer_used": false
  },
  "commands_or_manual_steps": [
    {
      "command": "uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py -q",
      "result": "passed",
      "output": "83 passed in 35.30s; source templates, isolated/dynamic models, generated notes, APKG SQLite contents, frozen-export converter independence, and CSV/TSV structure were checked offline."
    },
    {
      "command": "uv run pytest tests/services/test_japanese_furigana.py tests/domain/test_exporting.py tests/services/test_japanese_frequency_deck.py tests/services/test_assemble_export_cards.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py -q",
      "result": "passed",
      "output": "156 passed, 10 Alembic configuration deprecation warnings in 57.47s."
    },
    {
      "command": "node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/044-romaji-frequencia-japones/UI-PROOF.md",
      "result": "passed",
      "output": "Repository-local proof-bundle metadata validation passed."
    }
  ],
  "observations": [
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "The parsed Front Template contains neither {{Word Romaji}} nor {{Sentence Romaji}}, while retaining Target Word, Word Reading, Sentence, furigana toggle, audio, and conditional Image references.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/japanese_card.md",
      "artifact_refs": [
        "src/multilang/templates/japanese_card.md"
      ],
      "privacy": {
        "data_classification": "repository template source with fixed demonstration field names",
        "raw_artifacts_safe_to_publish": true,
        "retention": "repository source history"
      },
      "result": "passed",
      "claim_limit": "Source inspection proves field omission from front markup, not rendered recall behavior in Anki."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "The parsed Back Template places the Word Romaji div after the Word Reading reference and the Sentence Romaji div after Sentence Furigana and before Sentence Translation; existing Japanese, furigana, audio, and Image references remain present.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/japanese_card.md",
      "artifact_refs": [
        "src/multilang/templates/japanese_card.md"
      ],
      "privacy": {
        "data_classification": "repository template source with fixed demonstration field names",
        "raw_artifacts_safe_to_publish": true,
        "retention": "repository source history"
      },
      "result": "passed",
      "claim_limit": "Markup order and CSS class presence do not prove typography, wrapping, spacing, or usability."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "build_japanese_model() retains model ID 1762800701 and note type Multilang::Japanese Card while exposing the exact 12-field Japanese frequency tuple.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_japanese_frequency_deck.py",
      "artifact_refs": [
        "tests/services/test_japanese_frequency_deck.py"
      ],
      "privacy": {
        "data_classification": "offline repository test with fixed Japanese examples",
        "raw_artifacts_safe_to_publish": true,
        "retention": "repository test history"
      },
      "result": "passed",
      "claim_limit": "The generated genanki model contract is proven; native Anki rendering is not."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "build_multilang_model(source_type='frequency', language=SupportedLanguage.JA) uses the same model ID, note type, exact 12 fields, front omission, back adjacency, and unchanged existing template references as the isolated model.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "artifact_refs": [
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "offline repository test with fixed Japanese examples",
        "raw_artifacts_safe_to_publish": true,
        "retention": "repository test history"
      },
      "result": "passed",
      "claim_limit": "Dynamic model parity is structural and does not establish visual equivalence across Anki clients."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "Generated isolated and dynamic genanki notes contain Word Romaji in field position 4 and Sentence Romaji in field position 8, retain both audio values, and leave Image blank without changing GUID derivation.",
      "evidence_kind": "runtime",
      "artifact_path": "tests/services/test_japanese_frequency_deck.py",
      "artifact_refs": [
        "tests/services/test_japanese_frequency_deck.py",
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "ephemeral in-process genanki objects created from fixed test data",
        "raw_artifacts_safe_to_publish": false,
        "retention": "runtime objects discarded at test completion"
      },
      "result": "passed",
      "claim_limit": "Runtime field arrays prove generated values/order only, not rendered placement."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "A generated APKG contained collection.anki2; SQLite inspection of col.models and notes.flds confirmed the Japanese model identity, exact 12-field schema, both romaji values, existing furigana/audio values, and blank Image.",
      "evidence_kind": "runtime",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "artifact_refs": [
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "local-only temporary APKG and SQLite extraction with fixed test data",
        "raw_artifacts_safe_to_publish": false,
        "retention": "pytest temporary directory only; no raw APKG or SQLite file retained in the repository"
      },
      "result": "passed",
      "claim_limit": "ZIP and SQLite inspection proves import structure and note fields, not Anki Desktop/mobile rendering."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "The generated CSV #columns directive and parsed data row use the exact 12-field Japanese tuple and carry Gakkou and Gakkou ni iku. in the required positions while Image remains blank.",
      "evidence_kind": "runtime",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "artifact_refs": [
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "local-only temporary CSV with fixed test data",
        "raw_artifacts_safe_to_publish": false,
        "retention": "pytest temporary directory only; raw CSV not retained"
      },
      "result": "passed",
      "claim_limit": "CSV serialization proves header/value order only, not Anki import UI behavior."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields.",
      "observation": "The generated TSV #columns directive and parsed data row use the exact 12-field Japanese tuple and carry Gakkou and Gakkou ni iku. in the required positions while Image remains blank.",
      "evidence_kind": "runtime",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "artifact_refs": [
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "local-only temporary TSV with fixed test data",
        "raw_artifacts_safe_to_publish": false,
        "retention": "pytest temporary directory only; raw TSV not retained"
      },
      "result": "passed",
      "claim_limit": "TSV serialization proves header/value order only, not Anki import UI behavior."
    },
    {
      "slot_id": "japanese-frequency-romaji-structural-contract",
      "claim": "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields.",
      "route_state": "Import the dynamic APKG exporter in a fresh process with romanize_japanese forced unavailable, then export a fully populated frozen Japanese row.",
      "observation": "The dynamic exporter imported and generated a Japanese APKG from frozen Word Reading, Word Romaji, Sentence Furigana, and Sentence Romaji values without invoking the unavailable converter.",
      "evidence_kind": "runtime",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "artifact_refs": [
        "tests/services/test_export_anki_package.py"
      ],
      "privacy": {
        "data_classification": "isolated subprocess and temporary APKG using fixed test data",
        "raw_artifacts_safe_to_publish": false,
        "retention": "pytest subprocess and temporary directory only; APKG discarded at test completion"
      },
      "result": "passed",
      "claim_limit": "Proves frozen dynamic export independence from romanization; it does not prove native Anki rendering."
    }
  ],
  "artifacts": [
    {
      "path": "src/multilang/templates/japanese_card.md",
      "type": "code",
      "visibility": "repo_tracked",
      "retention": "repository source history",
      "sensitivity": "non-sensitive fixed template source",
      "safe_to_publish": true
    },
    {
      "path": "tests/services/test_japanese_frequency_deck.py",
      "type": "test",
      "visibility": "repo_tracked",
      "retention": "repository test history",
      "sensitivity": "non-sensitive fixed test data",
      "safe_to_publish": true
    },
    {
      "path": "tests/services/test_export_anki_package.py",
      "type": "test",
      "visibility": "repo_tracked",
      "retention": "repository test history",
      "sensitivity": "non-sensitive fixed test data; generated APKG/SQLite/tabular files are not retained",
      "safe_to_publish": true
    },
    {
      "path": ".planning/quick/044-romaji-frequencia-japones/UI-PROOF.md",
      "type": "report",
      "visibility": "local_only",
      "retention": "quick-task execution record",
      "sensitivity": "local execution metadata and test results; no user data",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "data_classification": "fixed repository examples and local execution metadata; no user data, secrets, provider payloads, screenshots, or traces",
    "raw_artifacts_safe_to_publish": false,
    "retention": "repository source/tests plus this local quick-task record; temporary APKG, SQLite, CSV, and TSV files are discarded by pytest"
  },
  "result": {
    "claim_status": "passed",
    "comparison_status_by_slot": {
      "japanese-frequency-romaji-structural-contract": "satisfied"
    },
    "structural_contract": "passed",
    "manual_acceptance_required": false,
    "native_anki_renderer_exercised": false,
    "screenshots_created": false
  },
  "claim_limits": [
    "Proves field references/order, front omission, back structural adjacency, unchanged existing references, and generated APKG/CSV/TSV contents only; actual Anki Desktop/mobile rendering is outside the claim.",
    "No native Anki renderer, rendered pixels, viewport behavior, typography, wrapping, visual placement, accessibility judgment, or usability was exercised or accepted.",
    "No screenshot, trace, video, or retained raw APKG/SQLite/tabular report was created for publication."
  ]
}
```
