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
      "bundle_sha256": "e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357",
      "bundle_relpath": "candidate-bundles/e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357",
      "bundle_manifest_sha256": "6852f7cc6eeedf2ec88f33ab8f027e76a72981a4179015b8aa40a0f3eb40a3ab",
      "file_sha256": "225ff85c19346866640400765a3b33ac9d13e2e9a13ee67c6edb11455a6179e5"
    },
    "bundle-manifest.json": {
      "filename": "bundle-manifest.json",
      "bundle_sha256": "e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357",
      "selected_draft_manifest_sha256": "2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2",
      "draft_validation_sha256": "a300a5376119d3e2fb4a734390d61e2cf0c5f8db794f758c95ad4de64aa2fb78",
      "file_sha256": "6852f7cc6eeedf2ec88f33ab8f027e76a72981a4179015b8aa40a0f3eb40a3ab",
      "total_record_count": 139,
      "media_slot_count": 509
    },
    "hangul-v2.json": {
      "filename": "hangul-v2.json",
      "version": "hangul-v2",
      "canonical_content_sha256": "640a67431043f56aa568af364223a462349ae8cd837ddffe4d60b7f5469b79b6",
      "file_sha256": "da12a49c5f42483eeeb6da4f251ea2eba3295afa7cf07c2c621e4dddfa5ff038",
      "item_count": 92
    },
    "pronunciation-i-plus-1-v2.json": {
      "filename": "pronunciation-i-plus-1-v2.json",
      "version": "pronunciation-i-plus-1-v2",
      "canonical_content_sha256": "235f1c966ad0bd28d7429d0336501572d675566fda15b415f9b23c40f6b2222c",
      "file_sha256": "889acedc9de497cfa25d8699ac4d2434bd102653c31276874a8b4336fd15448e",
      "item_count": 47
    },
    "korean-foundations-v2-curation.json": {
      "filename": "korean-foundations-v2-curation.json",
      "version": "korean-foundations-v2-curation",
      "canonical_content_sha256": "d3744339e6bdf2217f99adead7cd997468fce76d713a195ff78a639c3ac7bdfe",
      "file_sha256": "695346c70e34e163e459e3f2e1c8156b39ed4f126c4803e98258d229a8164caf",
      "record_count": 139,
      "gate_count": 973
    },
    "korean-foundations-v2-media.json": {
      "filename": "korean-foundations-v2-media.json",
      "version": "korean-foundations-v2-media",
      "canonical_content_sha256": "ad5ae28f96a75848f60555366748589e44c16f0e3dd07aa7e419230a2f8e3708",
      "file_sha256": "545bd060992e9a17d7a95a3397d774678c3cb3e3cddbe593e93c949f9b12326d",
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
    "item_identity_set_sha256": "b215d2a6fb36bf70f0ff5c902d1f05828f586317e9b125812e18800c90d10cb2",
    "hangul_item_identity_sha256": "48295e0e9af74ad2c1fae6704bcf17f3fc2846e4fa81a5e933581025ff01dc57",
    "pronunciation_item_identity_sha256": "6be24aba724c8983064399056e42756fe5f7282a2f2697c8bfbd2eee05749bd1"
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
      "source_content_sha256": "4847aa58fc0bb771d3769742f4f76063b2d62e9a8a52cfe0422238fcbff26f74",
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
