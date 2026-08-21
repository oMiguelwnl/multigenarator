# Korean Foundation Audio, Media Rights, and Playback Review Request

This is a request contract only. It supplies no media, human evidence, rights disposition, recording identity, or heard-playback result. Every selector applies to every identity in the exact hash-bound media candidate; projection digests bind the complete asset and source-text sets without inventing spoken text.

Place future evidence only at the fixed filenames listed in the JSON contract after Plan 31-08 defines their schemas. There is no source-location importer or alternate filename.

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
      "file_sha256": "6c422c5c5edf581af39f91773b40f72ac5570b84b76cd38d6f18bea4ef190c00",
      "record_count": 139,
      "gate_count": 973
    },
    "korean-foundations-v1-media.json": {
      "filename": "korean-foundations-v1-media.json",
      "version": "korean-foundations-v1-media",
      "canonical_content_sha256": "e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc",
      "file_sha256": "9f53766ea174c963e4904dd6172e490079ad693aded8dcb025a952327c90f0e1",
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
    "asset_identity_set_sha256": "a61ebccce4457e70a4e6ec59d7759297d9c2512f62094ebe769fc4f7d918e37e",
    "hangul_asset_identity_sha256": "35ea70b8bedbab165b32a6ae1f367a0ac8c95b58564bdca915a5dfb78ebf7013",
    "pronunciation_asset_identity_sha256": "eaf1033ea4b3b3fd4ba87e68e3f40b5ca451a39d08dcacce6cad1043e6fb61eb",
    "required_asset_identity_sha256": "c4ba5f57ecfadbb62e810dac25f05fe9fcedc38f38f8b85302579a2b47b3bc48",
    "audio_asset_identity_sha256": "5acd7c8c8b3420c407f6caad03c0a549a7598b52e82ffe1ede1f649769fce48e",
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
    "text_binding_set_sha256": "5ef47d0c99d209886b7a35659c465983c2cfc0dfa562b054d16bf7fc0a46881c",
    "hangul_text_binding_sha256": "44471f0833761859e8a831778a69d042f5257f071d02c044da9a9bccda1f1e4e",
    "pronunciation_text_binding_sha256": "50b98918cf50918d8364d21a4239a927ba3d1292e731220f8bad969a8514d343"
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
        "source_pack_version": "hangul-v1",
        "source_content_sha256": "7f68f731516a1b8428bbe157ec45c8798bee9838b7e47473ae32bb81ade2c111",
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
          "source_pack_version": "pronunciation-i-plus-1-v1",
          "source_content_sha256": "a148c652e9c17647f97e229c2673aeda3988be9cdcdf460f8a3090a1699873e8",
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
          "source_pack_version": "pronunciation-i-plus-1-v1",
          "source_content_sha256": "a148c652e9c17647f97e229c2673aeda3988be9cdcdf460f8a3090a1699873e8",
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
          "source_pack_version": "pronunciation-i-plus-1-v1",
          "source_content_sha256": "a148c652e9c17647f97e229c2673aeda3988be9cdcdf460f8a3090a1699873e8",
          "basename": "pron-sentence-audio-0047.wav",
          "storage_relpath": "media/pronunciation/pron-sentence-audio-0047.wav",
          "output_format": "pcm_s16le_wav"
        },
        "text_binding": {
          "slot_id": "pron.sentence-audio.0047",
          "display_text": "needs_review",
          "display_text_sha256": "aa1efaf66b36d5def14c9e7ce99b7d594c953aee266cd512196fc8ef5fd77db5",
          "text_nfc": "needs_review"
        }
      }
    ]
  }
}
```

The request covers all 509 candidate slots, including all 325 required slots and all 233 audio slots. Candidate display text is bound exactly; spoken text and every exact-byte, rights, specialist, independent-native, and heard-playback decision remain unresolved.
