# Korean Foundation Curriculum Review Request

This is a request contract only. It supplies no human or legal evidence. Every selector applies to every identity in the exact hash-bound candidate arrays described below; the projection digests make omissions or drift scanner-detectable.

Place future evidence only at the fixed filenames listed in the JSON contract after Plan 31-08 defines their schemas. There is no source-location importer or alternate filename.

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
    "korean-concepts-v1.json": {
      "filename": "korean-concepts-v1.json",
      "version": "korean-concepts-v1",
      "canonical_content_sha256": "89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d",
      "file_sha256": "79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625",
      "concept_count": 139
    },
    "hangul-v1.json": {
      "filename": "hangul-v1.json",
      "version": "hangul-v1",
      "canonical_content_sha256": "2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c",
      "file_sha256": "80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1",
      "item_count": 92
    },
    "pronunciation-i-plus-1-v1.json": {
      "filename": "pronunciation-i-plus-1-v1.json",
      "version": "pronunciation-i-plus-1-v1",
      "canonical_content_sha256": "641b06f4d1c05c70803b859aa2936fc517a1038ad190ac7c58574da8a93ea49e",
      "file_sha256": "6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec",
      "item_count": 47
    },
    "korean-foundations-v1-curation.json": {
      "filename": "korean-foundations-v1-curation.json",
      "version": "korean-foundations-v1-curation",
      "canonical_content_sha256": "76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b",
      "file_sha256": "6a5ddc06cfdb2ec3546e8854986bbe28ef957d170444dafadb0e97a06980055e",
      "record_count": 139,
      "gate_count": 973
    },
    "korean-foundations-v1-media.json": {
      "filename": "korean-foundations-v1-media.json",
      "version": "korean-foundations-v1-media",
      "canonical_content_sha256": "e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc",
      "file_sha256": "ad8f05f3846da9874f49a85e045b4d225f15ffdac8fba13cbd39615d94561fcc",
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
    "item_identity_set_sha256": "b5d0c55c4ecaf92651dde54b75a30261b2e9832a0eef1d4861d3e72481d0b27a",
    "hangul_item_identity_sha256": "04471f50c11124d0b58b13008cbfee404fd2dc70b557f1ee8293a237064ca6ad",
    "pronunciation_item_identity_sha256": "28e1d38b0200239865d88280351f30261b7c6394968e22a4e0b21a26538c52fa"
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
      "source_pack_version": "hangul-v1",
      "source_content_sha256": "7f68f731516a1b8428bbe157ec45c8798bee9838b7e47473ae32bb81ade2c111",
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
      "source_pack_version": "pronunciation-i-plus-1-v1",
      "source_content_sha256": "a148c652e9c17647f97e229c2673aeda3988be9cdcdf460f8a3090a1699873e8",
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

The content and curriculum selectors cover all 92 Hangul candidates and all 47 P0-P13 pronunciation candidates. The global Portuguese policy remains unresolved under canonical language identity `pt`; this request selects no regional policy.
