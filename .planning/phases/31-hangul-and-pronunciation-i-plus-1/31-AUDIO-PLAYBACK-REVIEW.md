# Korean Foundation Audio, Media Rights, and Playback Review Request

Review the exact v2 media slots, rights selectors, text bindings, specialist playback, independent native playback, and heard playback.

This is a request contract only. It supplies no human, legal, media, playback, activation, or export evidence. Every selector applies to the exact current-candidate bundle and remains scanner-detectable.

Place future evidence only at the fixed filenames listed in the JSON contract. There is no source-location importer or alternate filename.

`review_status=needs_review`
`human_checkpoint_count=0`

```json
{
  "artifact_type": "korean_foundation_audio_playback_review_request",
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
    "asset_count": 509,
    "required_asset_count": 325,
    "optional_asset_count": 184,
    "hangul_asset_count": 368,
    "pronunciation_asset_count": 141,
    "hangul_required_asset_count": 184,
    "pronunciation_required_asset_count": 141,
    "audio_asset_count": 233,
    "non_audio_asset_count": 276,
    "asset_kind_counts": {
      "picture": 92,
      "strokes": 92,
      "gif": 92,
      "audio": 92,
      "letter_audio": 47,
      "word_audio": 47,
      "sentence_audio": 47
    },
    "asset_id_selectors": [
      {
        "family": "hangul",
        "media_kind": "picture",
        "prefix": "hangul.picture.",
        "first_sequence": 1,
        "last_sequence": 92,
        "zero_pad_width": 4,
        "count": 92
      },
      {
        "family": "hangul",
        "media_kind": "strokes",
        "prefix": "hangul.strokes.",
        "first_sequence": 1,
        "last_sequence": 92,
        "zero_pad_width": 4,
        "count": 92
      },
      {
        "family": "hangul",
        "media_kind": "gif",
        "prefix": "hangul.gif.",
        "first_sequence": 1,
        "last_sequence": 92,
        "zero_pad_width": 4,
        "count": 92
      },
      {
        "family": "hangul",
        "media_kind": "audio",
        "prefix": "hangul.audio.",
        "first_sequence": 1,
        "last_sequence": 92,
        "zero_pad_width": 4,
        "count": 92
      },
      {
        "family": "pronunciation",
        "media_kind": "letter_audio",
        "prefix": "pron.letter-audio.",
        "first_sequence": 1,
        "last_sequence": 47,
        "zero_pad_width": 4,
        "count": 47
      },
      {
        "family": "pronunciation",
        "media_kind": "word_audio",
        "prefix": "pron.word-audio.",
        "first_sequence": 1,
        "last_sequence": 47,
        "zero_pad_width": 4,
        "count": 47
      },
      {
        "family": "pronunciation",
        "media_kind": "sentence_audio",
        "prefix": "pron.sentence-audio.",
        "first_sequence": 1,
        "last_sequence": 47,
        "zero_pad_width": 4,
        "count": 47
      }
    ],
    "asset_identity_projection": {
      "source_array": "slots",
      "selection": "all",
      "fields": [
        "family",
        "item_key",
        "sequence",
        "slot_id",
        "media_kind",
        "required",
        "source_pack_version",
        "source_content_sha256",
        "basename",
        "storage_relpath",
        "output_format"
      ],
      "order": "media-manifest-source-order",
      "hash_algorithm": "sha256-utf8-canonical-json"
    },
    "asset_id_set_sha256": "2a5131dfd268fb8a261dead300104c029e42e06392f8472e3987f91fa4be2949",
    "asset_identity_set_sha256": "d113fd532953e0fe7f6929b1792e6cbc08d5aa0bfac1c78a818b4a6638101194",
    "hangul_asset_identity_sha256": "10d95dd905cbef78ab633d359df8e86b30640d171cc90b7ce5c69d13e7b3f490",
    "pronunciation_asset_identity_sha256": "51224ca533d9c5816b0b595309c6ea1faaa0cd177f0065f7b8fa7d3150843e1d",
    "required_asset_identity_sha256": "042cd1d6bbca31ac56badb4ac706e5e5527911f0b8c5183dd45fdef44df7f8c5",
    "audio_asset_identity_sha256": "c86eac564395e8f32d526773590b6c57d58cfed8c4c5db8f4200322fb2ae99c4",
    "text_binding_projection": {
      "hangul": "pedagogical_jamo_mapping.display_glyph-if-present-else-canonical_jamo_or_block",
      "pronunciation_letter_audio": "spellings",
      "pronunciation_word_audio": "example_word",
      "pronunciation_sentence_audio": "example_sentence",
      "selection": "all-assets",
      "fields": [
        "slot_id",
        "display_text",
        "display_text_sha256",
        "text_nfc"
      ],
      "hash_algorithm": "sha256-utf8-canonical-json"
    },
    "text_binding_set_sha256": "78391d554cb55bba485e0cd1fe786602fb95408af417425f8bde3024f64e8d06",
    "hangul_text_binding_sha256": "44471f0833761859e8a831778a69d042f5257f071d02c044da9a9bccda1f1e4e",
    "pronunciation_text_binding_sha256": "058679e852250fcd91ed715dfae2954bc4f1d5a58144160a95bbaa75a6257a95"
  },
  "item_gate_role_matrix": {
    "hangul": [
      {
        "gate_name": "media_license",
        "required_role": "media-rights-reviewer",
        "scope_ids": [
          "all-declared-media-rights"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      },
      {
        "gate_name": "media_integrity",
        "required_role": "media-integrity-reviewer",
        "scope_ids": [
          "all-required-media-slots"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      },
      {
        "gate_name": "audio_playback",
        "required_role": "audio-playback-reviewer",
        "scope_ids": [
          "exact-audio-bytes",
          "heard-playback"
        ],
        "selector": "all-hangul-items",
        "decision_count": 92,
        "status": "needs_review"
      }
    ],
    "pronunciation": [
      {
        "gate_name": "media_license",
        "required_role": "media-rights-reviewer",
        "scope_ids": [
          "all-declared-audio-rights"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      },
      {
        "gate_name": "media_integrity",
        "required_role": "media-integrity-reviewer",
        "scope_ids": [
          "letter-word-sentence-audio"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      },
      {
        "gate_name": "audio_playback",
        "required_role": "audio-playback-reviewer",
        "scope_ids": [
          "exact-audio-bytes",
          "heard-playback"
        ],
        "selector": "all-pronunciation-items",
        "decision_count": 47,
        "status": "needs_review"
      }
    ]
  },
  "asset_role_matrix": {
    "non_audio_assets": {
      "media_kinds": [
        "picture",
        "strokes",
        "gif"
      ],
      "selector": "all-non-audio-assets",
      "asset_count": 276,
      "required_roles": [
        "media-rights-reviewer",
        "media-integrity-reviewer"
      ]
    },
    "audio_assets": {
      "media_kinds": [
        "audio",
        "letter_audio",
        "word_audio",
        "sentence_audio"
      ],
      "selector": "all-audio-assets",
      "asset_count": 233,
      "required_roles": [
        "media-rights-reviewer",
        "media-integrity-reviewer",
        "audio-playback-reviewer",
        "korean-phonetics-specialist",
        "independent-native-speaker"
      ],
      "distinct_role_constraints": [
        [
          "korean-phonetics-specialist",
          "independent-native-speaker"
        ]
      ]
    }
  },
  "decision_matrix": [
    {
      "decision_name": "source_identity",
      "gate_name": "media_license",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-rights-reviewer",
      "required_evidence_fields": [
        "source_id",
        "source_version"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "attribution",
      "gate_name": "media_license",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-rights-reviewer",
      "required_evidence_fields": [
        "attribution"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "license",
      "gate_name": "media_license",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-rights-reviewer",
      "required_evidence_fields": [
        "license_id"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "reuse",
      "gate_name": "media_license",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-rights-reviewer",
      "required_evidence_fields": [
        "reuse_disposition"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "redistribution",
      "gate_name": "media_license",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-rights-reviewer",
      "required_evidence_fields": [
        "redistribution_disposition"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "exact_byte_integrity",
      "gate_name": "media_integrity",
      "selector": "all-assets",
      "decision_count": 509,
      "required_role": "media-integrity-reviewer",
      "required_evidence_fields": [
        "artifact_sha256",
        "reviewed_artifact_sha256",
        "metadata_sha256",
        "reviewed_metadata_sha256",
        "output_format",
        "duration_ms"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "exact_spoken_text",
      "gate_name": "audio_playback",
      "selector": "all-audio-assets",
      "decision_count": 233,
      "required_role": "korean-phonetics-specialist",
      "required_evidence_fields": [
        "display_text",
        "display_text_sha256",
        "spoken_text",
        "spoken_text_sha256",
        "text_nfc",
        "text_nfc_sha256"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "specialist_playback",
      "gate_name": "audio_playback",
      "selector": "all-audio-assets",
      "decision_count": 233,
      "required_role": "korean-phonetics-specialist",
      "required_evidence_fields": [
        "exact_media_version",
        "exact_text_hashes",
        "exact_byte_hash",
        "heard_playback_result"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "independent_native_playback",
      "gate_name": "audio_playback",
      "selector": "all-audio-assets",
      "decision_count": 233,
      "required_role": "independent-native-speaker",
      "required_evidence_fields": [
        "exact_media_version",
        "exact_text_hashes",
        "exact_byte_hash",
        "heard_playback_result"
      ],
      "status": "needs_review"
    },
    {
      "decision_name": "heard_playback",
      "gate_name": "audio_playback",
      "selector": "all-audio-assets",
      "decision_count": 233,
      "required_role": "audio-playback-reviewer",
      "required_evidence_fields": [
        "exact_media_version",
        "exact_text_hashes",
        "exact_byte_hash",
        "heard_playback_result"
      ],
      "status": "needs_review"
    }
  ],
  "decision_counts": {
    "item_gate_decisions": 417,
    "asset_decisions": 3986,
    "total_decisions": 4403,
    "unique_item_and_asset_role_bindings": 2134,
    "by_required_role": {
      "media-rights-reviewer": 2684,
      "media-integrity-reviewer": 648,
      "audio-playback-reviewer": 372,
      "korean-phonetics-specialist": 466,
      "independent-native-speaker": 233
    }
  },
  "future_fixed_evidence_filenames": [
    "proposed-media.json",
    "audio-playback-review.json",
    "rights.json",
    "reviewers/korean-phonetics.json",
    "reviewers/independent-native-speaker.json"
  ],
  "high_leverage_traces": {
    "hangul_first_audio": {
      "asset": {
        "family": "hangul",
        "item_key": "ko-hangul-0001",
        "sequence": 4,
        "slot_id": "hangul.audio.0001",
        "media_kind": "audio",
        "required": true,
        "source_pack_version": "hangul-v2",
        "source_content_sha256": "397f390fa320837ccdd12882af9015e0b7ab993c6f9dcc0a2c135d49cd6af038",
        "basename": "hangul-audio-0001.wav",
        "storage_relpath": "media/hangul/hangul-audio-0001.wav",
        "output_format": "pcm_s16le_wav"
      },
      "text_binding": {
        "slot_id": "hangul.audio.0001",
        "display_text": "ㄱ",
        "display_text_sha256": "fcae0b0f80045e9a25c6d1a52cf03370e9992654f8e00b2a49bda476a6029156",
        "text_nfc": "ㄱ"
      }
    },
    "pronunciation_p13_audio": [
      {
        "asset": {
          "family": "pronunciation",
          "item_key": "ko-pron-0047",
          "sequence": 507,
          "slot_id": "pron.letter-audio.0047",
          "media_kind": "letter_audio",
          "required": true,
          "source_pack_version": "pronunciation-i-plus-1-v2",
          "source_content_sha256": "4847aa58fc0bb771d3769742f4f76063b2d62e9a8a52cfe0422238fcbff26f74",
          "basename": "pron-letter-audio-0047.wav",
          "storage_relpath": "media/pronunciation/pron-letter-audio-0047.wav",
          "output_format": "pcm_s16le_wav"
        },
        "text_binding": {
          "slot_id": "pron.letter-audio.0047",
          "display_text": "읽는",
          "display_text_sha256": "e465851d8d5aa366222239c84af6b7d6178675bb70ed8fa00aa5d01085abce64",
          "text_nfc": "읽는"
        }
      },
      {
        "asset": {
          "family": "pronunciation",
          "item_key": "ko-pron-0047",
          "sequence": 508,
          "slot_id": "pron.word-audio.0047",
          "media_kind": "word_audio",
          "required": true,
          "source_pack_version": "pronunciation-i-plus-1-v2",
          "source_content_sha256": "4847aa58fc0bb771d3769742f4f76063b2d62e9a8a52cfe0422238fcbff26f74",
          "basename": "pron-word-audio-0047.wav",
          "storage_relpath": "media/pronunciation/pron-word-audio-0047.wav",
          "output_format": "pcm_s16le_wav"
        },
        "text_binding": {
          "slot_id": "pron.word-audio.0047",
          "display_text": "읽는",
          "display_text_sha256": "e465851d8d5aa366222239c84af6b7d6178675bb70ed8fa00aa5d01085abce64",
          "text_nfc": "읽는"
        }
      },
      {
        "asset": {
          "family": "pronunciation",
          "item_key": "ko-pron-0047",
          "sequence": 509,
          "slot_id": "pron.sentence-audio.0047",
          "media_kind": "sentence_audio",
          "required": true,
          "source_pack_version": "pronunciation-i-plus-1-v2",
          "source_content_sha256": "4847aa58fc0bb771d3769742f4f76063b2d62e9a8a52cfe0422238fcbff26f74",
          "basename": "pron-sentence-audio-0047.wav",
          "storage_relpath": "media/pronunciation/pron-sentence-audio-0047.wav",
          "output_format": "pcm_s16le_wav"
        },
        "text_binding": {
          "slot_id": "pron.sentence-audio.0047",
          "display_text": "책을 읽는 사람이에요.",
          "display_text_sha256": "c35c3b152ff4386008a618c3f99678f70909bdd422f2a593f682f2748dd785a1",
          "text_nfc": "책을 읽는 사람이에요."
        }
      }
    ]
  }
}
```

This request selects no approval, regional policy, rights disposition, spoken-text result, media byte, activation, export, or production state.
