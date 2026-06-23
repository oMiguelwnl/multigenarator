# UI Proof: Phoneme Tablet Audio Icon

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Russian/Polish phoneme Anki card template audio icon styling",
  "route_state": "Generated phoneme card front template with letter, word, and sentence audio fields",
  "environment": "local code/test validation; physical tablet renderer not available in workspace",
  "viewport": "tablet issue inferred from user-provided image-exemplo.jpg; CSS cause removed across viewports",
  "evidence_inputs": {
    "tools_used": ["provided screenshot", "source inspection", "pytest"],
    "files_observed": [
      "image-exemplo.jpg",
      "src/multilang/templates/russian_phoneme_card.md",
      "tests/services/test_russian_phoneme_deck.py"
    ]
  },
  "commands_or_manual_steps": [
    "Inspected image-exemplo.jpg and confirmed a purple CSS triangle appears beside Anki's native gray play button.",
    "Removed the CSS-generated .replay-button::before triangle and stopped hiding native replay SVG markup.",
    "Ran uv run pytest tests/services/test_russian_phoneme_deck.py tests/integration/test_russian_phoneme_template_refresh_flow.py"
  ],
  "observations": [
    {
      "claim": "The template no longer creates a second play arrow beside the native Anki button.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/russian_phoneme_card.md",
      "result": "pass"
    },
    {
      "claim": "Regression coverage prevents reintroducing the pseudo-element duplicate icon.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_russian_phoneme_deck.py",
      "result": "pass"
    }
  ],
  "artifacts": [
    {
      "path": "image-exemplo.jpg",
      "type": "user-provided screenshot",
      "visibility": "local-only",
      "retention": "workspace",
      "sensitivity": "low",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "contains_user_data": false,
    "publication_approved": false
  },
  "result": "pass_with_manual_tablet_confirmation_recommended",
  "claim_limits": "This validates removal of the duplicate CSS-generated arrow cause, but does not prove final rendering on a physical tablet/AnkiDroid instance."
}
```
