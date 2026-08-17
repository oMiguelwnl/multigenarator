from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "korean_foundations"
PHASE_ROOT = (
    PROJECT_ROOT
    / ".planning"
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
)
CURRICULUM_REQUEST = PHASE_ROOT / "31-CURRICULUM-REVIEW.md"
AUDIO_REQUEST = PHASE_ROOT / "31-AUDIO-PLAYBACK-REVIEW.md"
PLAN_PATH = PHASE_ROOT / "31-07-PLAN.md"

MANIFEST_FILENAMES = (
    "korean-concepts-v1.json",
    "hangul-v1.json",
    "pronunciation-i-plus-1-v1.json",
    "korean-foundations-v1-curation.json",
    "korean-foundations-v1-media.json",
)
EXPECTED_FILE_SHA256 = {
    "korean-concepts-v1.json": (
        "79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625"
    ),
    "hangul-v1.json": (
        "80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1"
    ),
    "pronunciation-i-plus-1-v1.json": (
        "6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec"
    ),
    "korean-foundations-v1-curation.json": (
        "6a5ddc06cfdb2ec3546e8854986bbe28ef957d170444dafadb0e97a06980055e"
    ),
    "korean-foundations-v1-media.json": (
        "ad8f05f3846da9874f49a85e045b4d225f15ffdac8fba13cbd39615d94561fcc"
    ),
}
EXPECTED_CANONICAL_SHA256 = {
    "korean-concepts-v1.json": (
        "89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d"
    ),
    "hangul-v1.json": (
        "2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c"
    ),
    "pronunciation-i-plus-1-v1.json": (
        "641b06f4d1c05c70803b859aa2936fc517a1038ad190ac7c58574da8a93ea49e"
    ),
    "korean-foundations-v1-curation.json": (
        "76d08bfa4c2780111a8d7fd89e73c86ee5393609ba1f40c003cc6e77745aff6b"
    ),
    "korean-foundations-v1-media.json": (
        "e7ef7ed570b28ed70bb09a68426567ac5a2dc3df8bb33acb357d32c281e861dc"
    ),
}
EXPECTED_VERSIONS = {
    "korean-concepts-v1.json": "korean-concepts-v1",
    "hangul-v1.json": "hangul-v1",
    "pronunciation-i-plus-1-v1.json": "pronunciation-i-plus-1-v1",
    "korean-foundations-v1-curation.json": "korean-foundations-v1-curation",
    "korean-foundations-v1-media.json": "korean-foundations-v1-media",
}
EXPECTED_REQUEST_SHA256 = {
    "31-CURRICULUM-REVIEW.md": (
        "ec20559593dbc025ccd0ca5485ed1e6fa8c895c4962f58f151a5b1d3025e9bff"
    ),
    "31-AUDIO-PLAYBACK-REVIEW.md": (
        "877eb42abe57d705d69e4a2ace077bfb905b23cd1ff22a0283fb7f256fabec44"
    ),
}

IDENTITY_FIELDS = (
    "family",
    "item_key",
    "sequence",
    "stage_id",
    "category_id",
    "source_pack_version",
    "source_content_sha256",
    "target_concept_id",
    "active_rule_ids",
)
ASSET_IDENTITY_FIELDS = (
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
    "output_format",
)
AUDIO_KINDS = frozenset(
    {"audio", "letter_audio", "word_audio", "sentence_audio"}
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _load_json(filename: str) -> dict[str, Any]:
    return json.loads((DATA_ROOT / filename).read_text(encoding="utf-8"))


def _load_request(path: Path) -> tuple[dict[str, Any], str]:
    assert path.is_file(), f"missing review request: {path.name}"
    text = path.read_text(encoding="utf-8")
    assert text.count("```json\n") == 1
    payload_text = text.split("```json\n", maxsplit=1)[1].split(
        "\n```", maxsplit=1
    )[0]
    return json.loads(payload_text), text


def _manifests() -> dict[str, dict[str, Any]]:
    return {filename: _load_json(filename) for filename in MANIFEST_FILENAMES}


def _expected_candidate_bindings() -> dict[str, dict[str, Any]]:
    manifests = _manifests()
    counts = {
        "korean-concepts-v1.json": {"concept_count": 139},
        "hangul-v1.json": {"item_count": 92},
        "pronunciation-i-plus-1-v1.json": {"item_count": 47},
        "korean-foundations-v1-curation.json": {
            "record_count": 139,
            "gate_count": 973,
        },
        "korean-foundations-v1-media.json": {
            "asset_count": 509,
            "required_asset_count": 325,
        },
    }
    version_fields = {
        "korean-concepts-v1.json": "registry_version",
        "hangul-v1.json": "source_pack_version",
        "pronunciation-i-plus-1-v1.json": "source_pack_version",
        "korean-foundations-v1-curation.json": "manifest_version",
        "korean-foundations-v1-media.json": "manifest_version",
    }
    bindings: dict[str, dict[str, Any]] = {}
    for filename in MANIFEST_FILENAMES:
        path = DATA_ROOT / filename
        manifest = manifests[filename]
        binding = {
            "filename": filename,
            "version": manifest[version_fields[filename]],
            "canonical_content_sha256": manifest["content_hash"],
            "file_sha256": _sha256_bytes(path.read_bytes()),
            **counts[filename],
        }
        bindings[filename] = binding
    return bindings


def _source_entries() -> list[dict[str, Any]]:
    return [
        *_load_json("hangul-v1.json")["entries"],
        *_load_json("pronunciation-i-plus-1-v1.json")["entries"],
    ]


def _item_identity_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": entry["family"],
            "item_key": entry["item_key"],
            "sequence": entry["sequence"],
            "stage_id": entry["stage_id"],
            "category_id": entry["category_id"],
            "source_pack_version": entry["source_pack_version"],
            "source_content_sha256": entry["content_hash"],
            "target_concept_id": entry["evidence"]["target_concept_id"],
            "active_rule_ids": entry["active_rule_ids"],
        }
        for entry in _source_entries()
    ]


def _asset_identity_rows() -> list[dict[str, Any]]:
    media = _load_json("korean-foundations-v1-media.json")
    return [
        {field: slot[field] for field in ASSET_IDENTITY_FIELDS}
        for slot in media["slots"]
    ]


def _entry_lookup() -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (entry["family"], entry["item_key"]): entry
        for entry in _source_entries()
    }


def _expected_display_text(
    slot: dict[str, Any], entry: dict[str, Any]
) -> str:
    if slot["family"] == "hangul":
        mapping = entry.get("pedagogical_jamo_mapping")
        if mapping is not None:
            return mapping["display_glyph"]
        return entry["canonical_jamo_or_block"]
    if slot["media_kind"] == "letter_audio":
        return entry["spellings"]
    if slot["media_kind"] == "word_audio":
        return entry["example_word"]
    return entry["example_sentence"]


def _text_binding_rows() -> list[dict[str, str]]:
    media = _load_json("korean-foundations-v1-media.json")
    entries = _entry_lookup()
    rows: list[dict[str, str]] = []
    for slot in media["slots"]:
        display_text = _expected_display_text(
            slot, entries[(slot["family"], slot["item_key"])]
        )
        rows.append(
            {
                "slot_id": slot["slot_id"],
                "display_text": display_text,
                "display_text_sha256": _sha256_bytes(
                    display_text.encode("utf-8")
                ),
                "text_nfc": unicodedata.normalize("NFC", display_text),
            }
        )
    return rows


def _assert_common_request_contract(payload: dict[str, Any]) -> None:
    assert payload["schema_version"] == 1
    assert payload["request_status"] == "needs_review"
    assert payload["request_only"] is True
    assert payload["evidence_supplied"] is False
    assert payload["human_checkpoint_count"] == 0
    assert payload["candidate_bindings"] == _expected_candidate_bindings()


def test_curriculum_request_binds_exact_candidate_versions_hashes_and_item_set() -> None:
    payload, _ = _load_request(CURRICULUM_REQUEST)
    _assert_common_request_contract(payload)

    rows = _item_identity_rows()
    hangul_rows = [row for row in rows if row["family"] == "hangul"]
    pronunciation_rows = [
        row for row in rows if row["family"] == "pronunciation"
    ]
    expected_coverage = {
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
                "count": 92,
            },
            {
                "family": "pronunciation",
                "prefix": "ko-pron-",
                "first_sequence": 1,
                "last_sequence": 47,
                "zero_pad_width": 4,
                "count": 47,
            },
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
            "P13": 1,
        },
        "item_identity_projection": {
            "source_array": "entries",
            "selection": "all",
            "fields": list(IDENTITY_FIELDS),
            "order": "hangul-then-pronunciation-source-order",
            "hash_algorithm": "sha256-utf8-canonical-json",
        },
        "item_key_set_sha256": _canonical_sha256(
            [[row["family"], row["item_key"]] for row in rows]
        ),
        "item_identity_set_sha256": _canonical_sha256(rows),
        "hangul_item_identity_sha256": _canonical_sha256(hangul_rows),
        "pronunciation_item_identity_sha256": _canonical_sha256(
            pronunciation_rows
        ),
    }
    assert payload["coverage"] == expected_coverage
    assert payload["high_leverage_traces"] == [rows[0], rows[-1]]
    expanded_item_keys = [
        f"{selector['prefix']}{sequence:0{selector['zero_pad_width']}d}"
        for selector in payload["coverage"]["item_key_selectors"]
        for sequence in range(
            selector["first_sequence"], selector["last_sequence"] + 1
        )
    ]
    assert expanded_item_keys == [row["item_key"] for row in rows]


def test_curriculum_request_has_exact_gate_role_matrix_and_pending_decisions() -> None:
    payload, _ = _load_request(CURRICULUM_REQUEST)
    expected_matrix = {
        "hangul": [
            {
                "gate_name": "source_content",
                "required_role": "korean-foundation-content-reviewer",
                "scope_ids": [
                    "mapping",
                    "name-or-reading",
                    "block-or-example",
                    "stroke-order",
                    "mnemonic",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "curriculum_atomicity",
                "required_role": "korean-curriculum-reviewer",
                "scope_ids": [
                    "target-concept",
                    "prerequisites",
                    "observed-concepts",
                    "one-target-unknown",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "korean_orthography",
                "required_role": "korean-orthography-reviewer",
                "scope_ids": [
                    "canonical-jamo-or-block",
                    "pedagogical-jamo-mapping",
                    "orthographic-example",
                ],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "portuguese",
                "required_role": "portuguese-reviewer",
                "scope_ids": ["learner-facing-portuguese"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
        ],
        "pronunciation": [
            {
                "gate_name": "source_content",
                "required_role": "korean-foundation-content-reviewer",
                "scope_ids": [
                    "spelling",
                    "example-word",
                    "example-sentence",
                    "register-context",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "curriculum_atomicity",
                "required_role": "korean-curriculum-reviewer",
                "scope_ids": [
                    "target-concept",
                    "prerequisites",
                    "active-rules",
                    "one-target-unknown",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "korean_phonetics",
                "required_role": "korean-phonetics-specialist",
                "scope_ids": [
                    "normative-pronunciation",
                    "surface-pronunciation",
                    "optional-ipa",
                    "phonological-rules",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "portuguese",
                "required_role": "portuguese-reviewer",
                "scope_ids": [
                    "word-translation",
                    "sentence-translation",
                    "register-alignment",
                ],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
        ],
    }
    assert payload["gate_role_matrix"] == expected_matrix
    assert payload["global_decisions"] == [
        {
            "decision_name": "portuguese_editorial_policy",
            "canonical_language_code": "pt",
            "required_role": "portuguese-reviewer",
            "required_output_field": "regional_editorial_policy",
            "decision_count": 1,
            "status": "needs_review",
        }
    ]
    assert payload["additional_role_requirements"] == [
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
                    "ko-pron-0047",
                ],
                "stages": ["P11", "P12", "P13"],
                "source_reason_code": "specialist-atomization-review-required",
            },
            "scope_ids": [
                "P11-P13-atomization",
                "active-rule-analysis",
                "rule-ordering",
            ],
            "role_assignment_count": 6,
            "status": "needs_review",
        }
    ]
    assert payload["decision_counts"] == {
        "item_gate_decisions": 556,
        "global_policy_decisions": 1,
        "total_decisions": 557,
        "total_role_assignments": 563,
        "by_required_role": {
            "korean-foundation-content-reviewer": 139,
            "korean-curriculum-reviewer": 139,
            "korean-orthography-reviewer": 92,
            "korean-phonetics-specialist": 53,
            "portuguese-reviewer": 140,
        },
    }


def test_audio_request_binds_exact_asset_set_text_projection_and_counts() -> None:
    payload, _ = _load_request(AUDIO_REQUEST)
    _assert_common_request_contract(payload)

    assets = _asset_identity_rows()
    media = _load_json("korean-foundations-v1-media.json")
    slots = media["slots"]
    text_rows = _text_binding_rows()
    expected_coverage = {
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
            "sentence_audio": 47,
        },
        "asset_id_selectors": [
            {
                "family": "hangul",
                "media_kind": kind,
                "prefix": f"hangul.{kind}.",
                "first_sequence": 1,
                "last_sequence": 92,
                "zero_pad_width": 4,
                "count": 92,
            }
            for kind in ("picture", "strokes", "gif", "audio")
        ]
        + [
            {
                "family": "pronunciation",
                "media_kind": kind,
                "prefix": f"pron.{kind.replace('_', '-')}.",
                "first_sequence": 1,
                "last_sequence": 47,
                "zero_pad_width": 4,
                "count": 47,
            }
            for kind in ("letter_audio", "word_audio", "sentence_audio")
        ],
        "asset_identity_projection": {
            "source_array": "slots",
            "selection": "all",
            "fields": list(ASSET_IDENTITY_FIELDS),
            "order": "media-manifest-source-order",
            "hash_algorithm": "sha256-utf8-canonical-json",
        },
        "asset_id_set_sha256": _canonical_sha256(
            [asset["slot_id"] for asset in assets]
        ),
        "asset_identity_set_sha256": _canonical_sha256(assets),
        "hangul_asset_identity_sha256": _canonical_sha256(
            [asset for asset in assets if asset["family"] == "hangul"]
        ),
        "pronunciation_asset_identity_sha256": _canonical_sha256(
            [
                asset
                for asset in assets
                if asset["family"] == "pronunciation"
            ]
        ),
        "required_asset_identity_sha256": _canonical_sha256(
            [asset for asset, slot in zip(assets, slots) if slot["required"]]
        ),
        "audio_asset_identity_sha256": _canonical_sha256(
            [
                asset
                for asset, slot in zip(assets, slots)
                if slot["media_kind"] in AUDIO_KINDS
            ]
        ),
        "text_binding_projection": {
            "hangul": (
                "pedagogical_jamo_mapping.display_glyph-if-present-else-"
                "canonical_jamo_or_block"
            ),
            "pronunciation_letter_audio": "spellings",
            "pronunciation_word_audio": "example_word",
            "pronunciation_sentence_audio": "example_sentence",
            "selection": "all-assets",
            "fields": [
                "slot_id",
                "display_text",
                "display_text_sha256",
                "text_nfc",
            ],
            "hash_algorithm": "sha256-utf8-canonical-json",
        },
        "text_binding_set_sha256": _canonical_sha256(text_rows),
        "hangul_text_binding_sha256": _canonical_sha256(text_rows[:368]),
        "pronunciation_text_binding_sha256": _canonical_sha256(
            text_rows[368:]
        ),
    }
    assert payload["coverage"] == expected_coverage
    assert payload["high_leverage_traces"] == {
        "hangul_first_audio": {
            "asset": assets[3],
            "text_binding": text_rows[3],
        },
        "pronunciation_p13_audio": [
            {"asset": asset, "text_binding": text}
            for asset, text in zip(assets[-3:], text_rows[-3:])
        ],
    }
    expanded_asset_ids = [
        f"{selector['prefix']}{sequence:0{selector['zero_pad_width']}d}"
        for selector in payload["coverage"]["asset_id_selectors"]
        for sequence in range(
            selector["first_sequence"], selector["last_sequence"] + 1
        )
    ]
    assert len(expanded_asset_ids) == len(set(expanded_asset_ids)) == len(assets)
    assert set(expanded_asset_ids) == {asset["slot_id"] for asset in assets}


def test_audio_request_has_exact_item_gates_asset_roles_and_decision_matrix() -> None:
    payload, _ = _load_request(AUDIO_REQUEST)
    assert payload["item_gate_role_matrix"] == {
        "hangul": [
            {
                "gate_name": "media_license",
                "required_role": "media-rights-reviewer",
                "scope_ids": ["all-declared-media-rights"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "media_integrity",
                "required_role": "media-integrity-reviewer",
                "scope_ids": ["all-required-media-slots"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
            {
                "gate_name": "audio_playback",
                "required_role": "audio-playback-reviewer",
                "scope_ids": ["exact-audio-bytes", "heard-playback"],
                "selector": "all-hangul-items",
                "decision_count": 92,
                "status": "needs_review",
            },
        ],
        "pronunciation": [
            {
                "gate_name": "media_license",
                "required_role": "media-rights-reviewer",
                "scope_ids": ["all-declared-audio-rights"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "media_integrity",
                "required_role": "media-integrity-reviewer",
                "scope_ids": ["letter-word-sentence-audio"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
            {
                "gate_name": "audio_playback",
                "required_role": "audio-playback-reviewer",
                "scope_ids": ["exact-audio-bytes", "heard-playback"],
                "selector": "all-pronunciation-items",
                "decision_count": 47,
                "status": "needs_review",
            },
        ],
    }
    assert payload["asset_role_matrix"] == {
        "non_audio_assets": {
            "media_kinds": ["picture", "strokes", "gif"],
            "selector": "all-non-audio-assets",
            "asset_count": 276,
            "required_roles": [
                "media-rights-reviewer",
                "media-integrity-reviewer",
            ],
        },
        "audio_assets": {
            "media_kinds": [
                "audio",
                "letter_audio",
                "word_audio",
                "sentence_audio",
            ],
            "selector": "all-audio-assets",
            "asset_count": 233,
            "required_roles": [
                "media-rights-reviewer",
                "media-integrity-reviewer",
                "audio-playback-reviewer",
                "korean-phonetics-specialist",
                "independent-native-speaker",
            ],
            "distinct_role_constraints": [
                [
                    "korean-phonetics-specialist",
                    "independent-native-speaker",
                ]
            ],
        },
    }
    decision_names = [
        "source_identity",
        "attribution",
        "license",
        "reuse",
        "redistribution",
        "exact_byte_integrity",
        "exact_spoken_text",
        "specialist_playback",
        "independent_native_playback",
        "heard_playback",
    ]
    assert [
        decision["decision_name"] for decision in payload["decision_matrix"]
    ] == decision_names
    expected_decision_contracts = {
        "source_identity": ("media_license", "all-assets", 509, "media-rights-reviewer"),
        "attribution": ("media_license", "all-assets", 509, "media-rights-reviewer"),
        "license": ("media_license", "all-assets", 509, "media-rights-reviewer"),
        "reuse": ("media_license", "all-assets", 509, "media-rights-reviewer"),
        "redistribution": ("media_license", "all-assets", 509, "media-rights-reviewer"),
        "exact_byte_integrity": (
            "media_integrity",
            "all-assets",
            509,
            "media-integrity-reviewer",
        ),
        "exact_spoken_text": (
            "audio_playback",
            "all-audio-assets",
            233,
            "korean-phonetics-specialist",
        ),
        "specialist_playback": (
            "audio_playback",
            "all-audio-assets",
            233,
            "korean-phonetics-specialist",
        ),
        "independent_native_playback": (
            "audio_playback",
            "all-audio-assets",
            233,
            "independent-native-speaker",
        ),
        "heard_playback": (
            "audio_playback",
            "all-audio-assets",
            233,
            "audio-playback-reviewer",
        ),
    }
    for decision in payload["decision_matrix"]:
        assert (
            decision["gate_name"],
            decision["selector"],
            decision["decision_count"],
            decision["required_role"],
        ) == expected_decision_contracts[decision["decision_name"]]
        assert decision["required_evidence_fields"]
    assert payload["decision_counts"] == {
        "item_gate_decisions": 417,
        "asset_decisions": 3986,
        "total_decisions": 4403,
        "unique_item_and_asset_role_bindings": 2134,
        "by_required_role": {
            "media-rights-reviewer": 2684,
            "media-integrity-reviewer": 648,
            "audio-playback-reviewer": 372,
            "korean-phonetics-specialist": 466,
            "independent-native-speaker": 233,
        },
    }
    assert all(
        decision["status"] == "needs_review"
        for decision in payload["decision_matrix"]
    )


def test_requests_name_only_fixed_future_evidence_filenames() -> None:
    curriculum, _ = _load_request(CURRICULUM_REQUEST)
    audio, _ = _load_request(AUDIO_REQUEST)
    assert curriculum["future_fixed_evidence_filenames"] == [
        "proposed-curation.json",
        "curriculum-review.json",
        "reviewers/korean-orthography.json",
        "reviewers/korean-phonetics.json",
        "reviewers/portuguese.json",
    ]
    assert audio["future_fixed_evidence_filenames"] == [
        "proposed-media.json",
        "audio-playback-review.json",
        "rights.json",
        "reviewers/korean-phonetics.json",
        "reviewers/independent-native-speaker.json",
    ]
    for filename in [
        *curriculum["future_fixed_evidence_filenames"],
        *audio["future_fixed_evidence_filenames"],
    ]:
        assert not filename.startswith(("/", "\\"))
        assert ".." not in Path(filename).parts
        assert ":" not in filename
        assert not filename.startswith(("http://", "https://"))


def _walk(value: Any, *, key: str = "") -> list[tuple[str, Any]]:
    values = [(key, value)]
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            values.extend(_walk(child_value, key=child_key))
    elif isinstance(value, list):
        for child_value in value:
            values.extend(_walk(child_value, key=key))
    return values


def test_requests_remain_pending_without_fabricated_evidence_or_checkpoint() -> None:
    curriculum, curriculum_text = _load_request(CURRICULUM_REQUEST)
    audio, audio_text = _load_request(AUDIO_REQUEST)
    payloads = (curriculum, audio)

    status_values = [
        value
        for payload in payloads
        for key, value in _walk(payload)
        if key in {"status", "request_status"}
    ]
    assert status_values
    assert set(status_values) == {"needs_review"}

    forbidden_populated_keys = {
        "reviewer_id",
        "reviewed_at",
        "decision_timestamp",
        "approval",
        "provider_call",
        "media_bytes",
        "artifact_sha256",
        "reviewed_artifact_sha256",
        "receipt",
        "snapshot",
        "activation",
        "export",
    }
    for payload in payloads:
        for key, value in _walk(payload):
            assert not (key in forbidden_populated_keys and value not in (None, "", []))
            if isinstance(value, str):
                assert value != "approved"
                assert not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
                    value,
                )
                assert "evidence-inbox" not in value

    assert "human_checkpoint_count=0" in curriculum_text
    assert "human_checkpoint_count=0" in audio_text
    assert _sha256_bytes(CURRICULUM_REQUEST.read_bytes()) == EXPECTED_REQUEST_SHA256[
        CURRICULUM_REQUEST.name
    ]
    assert _sha256_bytes(AUDIO_REQUEST.read_bytes()) == EXPECTED_REQUEST_SHA256[
        AUDIO_REQUEST.name
    ]
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    task_tags = re.findall(r"<task\b[^>]*>", plan_text)
    assert len(task_tags) == 1
    assert all('type="checkpoint' not in tag for tag in task_tags)


def test_candidate_manifests_remain_byte_identical_and_pending() -> None:
    manifests = _manifests()
    for filename in MANIFEST_FILENAMES:
        path = DATA_ROOT / filename
        assert _sha256_bytes(path.read_bytes()) == EXPECTED_FILE_SHA256[filename]
        assert manifests[filename]["content_hash"] == EXPECTED_CANONICAL_SHA256[
            filename
        ]
        binding = _expected_candidate_bindings()[filename]
        assert binding["version"] == EXPECTED_VERSIONS[filename]

    for manifest_name in (
        "hangul-v1.json",
        "pronunciation-i-plus-1-v1.json",
    ):
        manifest = manifests[manifest_name]
        assert manifest["review_status"] == "needs_review"
        assert manifest["inventory_status"] == "complete"
        assert all(
            review["status"] == "needs_review"
            for entry in manifest["entries"]
            for review in entry["pending_reviews"]
        )
    assert all(
        gate["status"] == "needs_review"
        and gate["reviewer_id"] is None
        and gate["reviewed_at"] is None
        for record in manifests["korean-foundations-v1-curation.json"]["records"]
        for gate in record["gates"]
    )
    assert all(
        slot["status"] == "needs_review"
        and slot["artifact_sha256"] is None
        and slot["review_receipts"] == []
        for slot in manifests["korean-foundations-v1-media.json"]["slots"]
    )


def test_request_coverage_reconciles_exact_item_asset_gate_and_role_counts() -> None:
    curriculum, _ = _load_request(CURRICULUM_REQUEST)
    audio, _ = _load_request(AUDIO_REQUEST)
    curriculum_gate_counts = Counter(
        row["gate_name"]
        for rows in curriculum["gate_role_matrix"].values()
        for row in rows
        for _ in range(row["decision_count"])
    )
    assert curriculum_gate_counts == {
        "source_content": 139,
        "curriculum_atomicity": 139,
        "korean_orthography": 92,
        "korean_phonetics": 47,
        "portuguese": 139,
    }

    audio_item_gate_counts = Counter(
        row["gate_name"]
        for rows in audio["item_gate_role_matrix"].values()
        for row in rows
        for _ in range(row["decision_count"])
    )
    assert audio_item_gate_counts == {
        "media_license": 139,
        "media_integrity": 139,
        "audio_playback": 139,
    }
    assert curriculum["decision_counts"]["total_decisions"] == 557
    assert audio["decision_counts"]["total_decisions"] == 4403
    assert curriculum["coverage"]["item_count"] == 139
    assert audio["coverage"]["asset_count"] == 509
    assert audio["coverage"]["required_asset_count"] == 325
