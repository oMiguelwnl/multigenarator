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
    "asset_identity_set_sha256": "7b66c592d2c7683299dc013524aa5fe254a7df997e4fe0ad3cdeccec8c4780cf",
    "hangul_asset_identity_sha256": "1d531667b1a8ba2fd025f2923dd01102961073350daf7a52ce3f4d45d9eba72e",
    "pronunciation_asset_identity_sha256": "87cab969d513b166b04cfa0542c99b4651b0e6eb393e5a55e024b5efe94073bf",
    "required_asset_identity_sha256": "8258400e916a37f0f955423925287ac17efc9976568898faedf9312ad77dc006",
    "audio_asset_identity_sha256": "4cfdcf75329e4829ea7713357219c24541a3599e78c390a46da7b5ed13babcf2",
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
    "text_binding_set_sha256": "23ac50549577581591ae7687f9fdda2a74dcddf7675e57625a21a4c8bf053a6e",
    "hangul_text_binding_sha256": "44471f0833761859e8a831778a69d042f5257f071d02c044da9a9bccda1f1e4e",
    "pronunciation_text_binding_sha256": "b8238b2bcde043e3daa4324a05fb78f9d72bbc31cf32d5e50c22514435d02f9e"
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
          "source_content_sha256": "f17a60790b4cd659dbf14909d7e57d15480b630a831b752276384278ce1ab6bb",
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
          "source_content_sha256": "f17a60790b4cd659dbf14909d7e57d15480b630a831b752276384278ce1ab6bb",
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
          "source_content_sha256": "f17a60790b4cd659dbf14909d7e57d15480b630a831b752276384278ce1ab6bb",
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

This request selects no approval, regional policy, rights disposition, spoken-text result, media byte, activation, export, or production state.
