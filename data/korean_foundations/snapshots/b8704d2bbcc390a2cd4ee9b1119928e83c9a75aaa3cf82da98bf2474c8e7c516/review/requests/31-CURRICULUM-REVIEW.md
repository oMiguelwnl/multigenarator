# Korean Foundation Curriculum Review Request

Review the exact v2 Hangul and pronunciation candidate identities, curriculum atomicity, Korean orthography/phonetics, and Portuguese policy.

This is a request contract only. It supplies no human, legal, media, playback, activation, or export evidence. Every selector applies to the exact current-candidate bundle and remains scanner-detectable.

Place future evidence only at the fixed filenames listed in the JSON contract. There is no source-location importer or alternate filename.

`review_status=needs_review`
`human_checkpoint_count=0`

```json
{
  "artifact_type": "korean_foundation_curriculum_review_request",
  "schema_version": 1,
  "request_status": "needs_review",
  "request_only": true,
  "evidence_supplied": false,
  "human_checkpoint_count": 0,
  "candidate_bindings": {
    "current-candidate.json": {
      "filename": "current-candidate.json",
      "bundle_sha256": "36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0",
      "bundle_relpath": "candidate-bundles/36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0",
      "bundle_manifest_sha256": "2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40",
      "file_sha256": "0fa9e0756ab59969dc55ab428544c18aad1d1d14631b0d2569a33823feb24518"
    },
    "bundle-manifest.json": {
      "filename": "bundle-manifest.json",
      "bundle_sha256": "36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0",
      "selected_draft_manifest_sha256": "8f053a815b4b18c9e8004d295849f562989410f05f4a1cc8725bc37f8c7f26b5",
      "draft_validation_sha256": "d254eac81d058ea6406d5d0d981480cce5d8968801116063d9835b1f7625bfe0",
      "file_sha256": "2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40",
      "total_record_count": 139,
      "media_slot_count": 509
    },
    "hangul-v2.json": {
      "filename": "hangul-v2.json",
      "version": "hangul-v2",
      "canonical_content_sha256": "15143e23dea2236b0ada6f3603f79babb52bc4a89213906084d16c8bf864843a",
      "file_sha256": "63c36c50c0efa61f7ba76ebdf92ff174f79aadedb63b46d15da01599f2594f59",
      "item_count": 92
    },
    "pronunciation-i-plus-1-v2.json": {
      "filename": "pronunciation-i-plus-1-v2.json",
      "version": "pronunciation-i-plus-1-v2",
      "canonical_content_sha256": "4cb7f0b2a453a61858bf6a4b15a95568328a7348ba164d6ef9fd2bdf68119682",
      "file_sha256": "cdac65b7e3a9615e62f187dcf7c7f6c543a480710b618ce0c9eb580281cd955c",
      "item_count": 47
    },
    "korean-foundations-v2-curation.json": {
      "filename": "korean-foundations-v2-curation.json",
      "version": "korean-foundations-v2-curation",
      "canonical_content_sha256": "08874c6f4c64240d79cbdb982c1aa0d8a886749bc8100da41036b7c1b8ba9b22",
      "file_sha256": "faa233cdc67f99c28c3f203e1b206f4ad4f631bc34b8e2fbb970db336f1157db",
      "record_count": 139,
      "gate_count": 973
    },
    "korean-foundations-v2-media.json": {
      "filename": "korean-foundations-v2-media.json",
      "version": "korean-foundations-v2-media",
      "canonical_content_sha256": "8d860b5e41738d2322dc63eb220eb23de66f4b68b4ff1f9e3dd8979e90b5b55a",
      "file_sha256": "e21c7a11006cf70a0559ec7fff7279b466097cf3bbc1fa092cee84e7b963e938",
      "asset_count": 509,
      "required_asset_count": 325
    }
  },
  "coverage": {
    "item_count": 139,
    "hangul_item_count": 92,
    "pronunciation_item_count": 47,
    "item_key_selectors": [
      {
        "family": "hangul",
        "prefix": "ko-hangul-",
        "first_sequence": 1,
        "last_sequence": 92,
        "zero_pad_width": 4,
        "count": 92
      },
      {
        "family": "pronunciation",
        "prefix": "ko-pron-",
        "first_sequence": 1,
        "last_sequence": 47,
        "zero_pad_width": 4,
        "count": 47
      }
    ],
    "stage_counts": {
      "H0": 7,
      "H1": 6,
      "H2": 3,
      "H3": 9,
      "H4": 8,
      "H5": 9,
      "H6": 7,
      "H7": 8,
      "H8": 27,
      "H9": 3,
      "H10": 5,
      "P0": 8,
      "P1": 6,
      "P2": 8,
      "P3": 1,
      "P4": 1,
      "P5": 3,
      "P6": 2,
      "P7": 2,
      "P8": 3,
      "P9": 3,
      "P10": 4,
      "P11": 1,
      "P12": 4,
      "P13": 1
    },
    "item_identity_projection": {
      "source_array": "entries",
      "selection": "all",
      "fields": [
        "family",
        "item_key",
        "sequence",
        "stage_id",
        "category_id",
        "source_pack_version",
        "source_content_sha256",
        "target_concept_id",
        "active_rule_ids"
      ],
      "order": "hangul-then-pronunciation-source-order",
      "hash_algorithm": "sha256-utf8-canonical-json"
    },
    "item_key_set_sha256": "197e248708bfa675c618631b00c5a8a4fc36246b21d1e4fa393905f0e8f86b7b",
    "item_identity_set_sha256": "06cc331130811e1c6a27081d86ca14a1afa1abd060fe485ca2c8d463a182375d",
    "hangul_item_identity_sha256": "216c5923a3f7b46891bba14526d38f5ec43b5c2b9e2bebe77336329cc0f5ee36",
    "pronunciation_item_identity_sha256": "b616562e591907343189e6f326870bc79080a8ee390380c1a109b122b6182841"
  },
  "gate_role_matrix": {
    "hangul": [
      {
        "gate_name": "source_content",
        "required_role": "korean-foundation-content-reviewer",
        "scope_ids": [
          "mapping",
          "name-or-reading",
          "block-or-example",
          "stroke-order",
          "mnemonic"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      },
      {
        "gate_name": "curriculum_atomicity",
        "required_role": "korean-curriculum-reviewer",
        "scope_ids": [
          "target-concept",
          "prerequisites",
          "observed-concepts",
          "one-target-unknown"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      },
      {
        "gate_name": "korean_orthography",
        "required_role": "korean-orthography-reviewer",
        "scope_ids": [
          "canonical-jamo-or-block",
          "pedagogical-jamo-mapping",
          "orthographic-example"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      },
      {
        "gate_name": "portuguese",
        "required_role": "portuguese-reviewer",
        "scope_ids": [
          "learner-facing-portuguese"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      }
    ],
    "pronunciation": [
      {
        "gate_name": "source_content",
        "required_role": "korean-foundation-content-reviewer",
        "scope_ids": [
          "spelling",
          "example-word",
          "example-sentence",
          "register-context"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      },
      {
        "gate_name": "curriculum_atomicity",
        "required_role": "korean-curriculum-reviewer",
        "scope_ids": [
          "target-concept",
          "prerequisites",
          "active-rules",
          "one-target-unknown"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      },
      {
        "gate_name": "korean_phonetics",
        "required_role": "korean-phonetics-specialist",
        "scope_ids": [
          "normative-pronunciation",
          "surface-pronunciation",
          "optional-ipa",
          "phonological-rules"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      },
      {
        "gate_name": "portuguese",
        "required_role": "portuguese-reviewer",
        "scope_ids": [
          "word-translation",
          "sentence-translation",
          "register-alignment"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      }
    ]
  },
  "global_decisions": [
    {
      "decision_name": "portuguese_editorial_policy",
      "canonical_language_code": "pt",
      "required_role": "portuguese-reviewer",
      "required_output_field": "regional_editorial_policy",
      "decision_count": 1,
      "status": "needs_review"
    }
  ],
  "additional_role_requirements": [
    {
      "requirement_name": "specialist_atomization",
      "gate_name": "curriculum_atomicity",
      "required_role": "korean-phonetics-specialist",
      "selector": {
        "family": "pronunciation",
        "item_keys": [
          "ko-pron-0042",
          "ko-pron-0043",
          "ko-pron-0044",
          "ko-pron-0045",
          "ko-pron-0046",
          "ko-pron-0047"
        ],
        "stages": [
          "P11",
          "P12",
          "P13"
        ],
        "source_reason_code": "specialist-atomization-review-required"
      },
      "scope_ids": [
        "P11-P13-atomization",
        "active-rule-analysis",
        "rule-ordering"
      ],
      "role_assignment_count": 6,
      "status": "needs_review"
    }
  ],
  "decision_counts": {
    "item_gate_decisions": 556,
    "global_policy_decisions": 1,
    "total_decisions": 557,
    "total_role_assignments": 563,
    "by_required_role": {
      "korean-foundation-content-reviewer": 139,
      "korean-curriculum-reviewer": 139,
      "korean-orthography-reviewer": 92,
      "korean-phonetics-specialist": 53,
      "portuguese-reviewer": 140
    }
  },
  "future_fixed_evidence_filenames": [
    "proposed-curation.json",
    "curriculum-review.json",
    "reviewers/korean-orthography.json",
    "reviewers/korean-phonetics.json",
    "reviewers/portuguese.json"
  ],
  "high_leverage_traces": [
    {
      "family": "hangul",
      "item_key": "ko-hangul-0001",
      "sequence": 1,
      "stage_id": "H0",
      "category_id": "jamo-unit",
      "source_pack_version": "hangul-v2",
      "source_content_sha256": "397f390fa320837ccdd12882af9015e0b7ab993c6f9dcc0a2c135d49cd6af038",
      "target_concept_id": "orthography.jamo.unit",
      "active_rule_ids": [
        "orthography.jamo.unit"
      ]
    },
    {
      "family": "pronunciation",
      "item_key": "ko-pron-0047",
      "sequence": 47,
      "stage_id": "P13",
      "category_id": "rule-ordering-relation",
      "source_pack_version": "pronunciation-i-plus-1-v2",
      "source_content_sha256": "f17a60790b4cd659dbf14909d7e57d15480b630a831b752276384278ce1ab6bb",
      "target_concept_id": "phonology.p13.rule.ordering.relation",
      "active_rule_ids": [
        "phonology.p2.unreleased.coda",
        "phonology.p5.nasalization.velar",
        "phonology.p9.complex.coda.before.consonant",
        "phonology.p13.rule.ordering.relation"
      ]
    }
  ]
}
```

This request selects no approval, regional policy, rights disposition, spoken-text result, media byte, activation, export, or production state.
