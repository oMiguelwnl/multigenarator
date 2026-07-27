# UI Proof: Anki Template Dark Restyle

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Normal, shared phoneme, and Mandarin Anki template source/model contracts and dark stylesheet fidelity",
  "route_state": "load_card_template frequency and zh frequency/word-list models plus generated Russian, Polish, and Greek phoneme models",
  "environment": "Python 3.12 source and generated genanki model inspection; agent-browser is not a native Anki renderer and no Anki Desktop/mobile runtime is available in this workspace; installed gsdd-cli does not expose the planned ui-proof subcommand",
  "viewport": "Source/model inspection confirms max-width and responsive CSS only; actual Anki Desktop and representative portrait mobile viewports remain unobserved",
  "evidence_inputs": {
    "tools_used": [
      "pytest",
      "Python model inspection",
      "source diff inspection",
      "gsdd-cli capability probe"
    ],
    "files_observed": [
      "freq_card_hero_dark.html",
      "phoneme_card_restyle.html",
      "unified_templates_preview.html",
      "src/multilang/templates/normal_card.md",
      "src/multilang/templates/russian_phoneme_card.md",
      "src/multilang/templates/mandarin_card.md",
      "tests/services/test_card_template_loader.py",
      "tests/services/test_export_anki_package.py",
      "tests/services/test_russian_phoneme_deck.py"
    ],
    "automated_observations": [
      "The focused suite passes 57 tests covering source templates and generated models.",
      "Normal model fields remain SortIndex, word, IPA, Definitions, Example Sentence, Translation, word_audio, sentence_audio, Image in that order.",
      "Normal front/back retain hidden-front Translation, FrontSide, and the reveal script while CSS exposes the approved page, card, accent, centered hero, callout, and responsive signatures.",
      "Mandarin frequency and word-list generated templates are equal and retain the exact 12-field Mandarin model contract.",
      "Mandarin composed CSS starts with the complete normal CSS and then applies readable Pinyin and Traditional-line overrides.",
      "Russian, Polish, and Greek phoneme models share identical front/back templates and CSS with the exact nine-field phoneme order.",
      "Phoneme CSS retains native replay SVG paths and adds the approved dark shell, target box, divider, hierarchy, and circular replay-button treatment.",
      "Git diff inspection shows production template changes only inside the three Styling (CSS) fenced sections."
    ]
  },
  "commands_or_manual_steps": [
    "RED: uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q produced 4 expected stylesheet assertion failures and 53 passes before production CSS edits.",
    "GREEN: uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q produced 57 passes.",
    "Generated and inspected normal, Mandarin frequency, Mandarin word-list, Russian phoneme, Polish phoneme, and Greek phoneme models with uv run python.",
    "Validator probe: npx -y gsdd-cli ui-proof validate .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md returned the CLI help because this installed gsdd-cli has no ui-proof command; therefore no validator pass is claimed.",
    "Human: inspect normal card front and back in Anki Desktop.",
    "Human: inspect normal card front and back in a mobile Anki client.",
    "Human: inspect phoneme card front and back in Anki Desktop.",
    "Human: inspect phoneme card front and back in a mobile Anki client.",
    "Human: inspect Mandarin card front and back in Anki Desktop.",
    "Human: inspect Mandarin card front and back in a mobile Anki client."
  ],
  "observations": [
    {
      "claim": "Normal source and generated model retain their field-reference and reveal contracts.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass"
    },
    {
      "claim": "Normal generated model carries the approved dark palette, centered hero, callout, and responsive stylesheet signatures.",
      "evidence_kind": "runtime",
      "artifact_path": "src/multilang/templates/normal_card.md",
      "result": "pass"
    },
    {
      "claim": "Phoneme generated models retain exact fields, references, FrontSide behavior, and translation reveal.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_russian_phoneme_deck.py",
      "result": "pass"
    },
    {
      "claim": "Shared phoneme CSS carries the approved dark-blue shell, target box, hierarchy, and native replay SVG styling.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/russian_phoneme_card.md",
      "result": "pass"
    },
    {
      "claim": "Mandarin frequency and word-list models retain exact field order and normal CSS prefix composition.",
      "evidence_kind": "runtime",
      "artifact_path": "src/multilang/services/card_template_loader.py",
      "result": "pass"
    },
    {
      "claim": "Mandarin auxiliary Pinyin and Traditional lines carry explicit readable dark colors.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/mandarin_card.md",
      "result": "pass"
    },
    {
      "claim": "Focused template and generated-model regression suite is green.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_export_anki_package.py",
      "result": "pass"
    },
    {
      "claim": "Exact visual equivalence in native Anki Desktop and mobile rendering, including front/back reveal appearance.",
      "evidence_kind": "human",
      "artifact_path": ".planning/quick/029-restyle-anki-card-templates/UI-PROOF.md",
      "result": "human_needed"
    }
  ],
  "artifacts": [
    {
      "path": ".planning/quick/029-restyle-anki-card-templates/UI-PROOF.md",
      "type": "local source/model proof bundle and manual acceptance checklist",
      "visibility": "local_only",
      "retention": "retain with quick-task records",
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
  "claim_limits": "Automated checks prove template source/model contracts and stylesheet signatures only. agent-browser cannot represent native Anki rendering, and no real Anki Desktop/mobile screenshots were captured. The planned npx gsdd-cli validator is incompatible with the installed CLI because its command list has no ui-proof subcommand, so metadata validation is not claimed. Exact pixels, font availability, overflow, audio-control appearance, and translation reveal appearance remain human_needed until all twelve normal/phoneme/Mandarin front/back Desktop/mobile observations are recorded."
}
```
