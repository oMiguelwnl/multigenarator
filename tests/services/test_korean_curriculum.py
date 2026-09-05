"""Contracts for bounded Korean foundation manifests and strict i+1 evidence."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
import inspect
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unicodedata

import pytest
from pydantic import ValidationError


def _curriculum() -> ModuleType:
    assert util.find_spec("multilang.services.korean_curriculum") is not None, (
        "the Korean curriculum service module must exist"
    )
    return import_module("multilang.services.korean_curriculum")


def _canonical_hash(payload: object) -> str:
    data = deepcopy(payload)
    if isinstance(data, dict):
        data.pop("content_hash", None)
    encoded = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _sealed(payload: dict[str, object]) -> dict[str, object]:
    result = deepcopy(payload)
    result["content_hash"] = _canonical_hash(result)
    return result


def _provenance() -> dict[str, object]:
    return {
        "source_id": "unicode.hangul",
        "source_version": "17.0",
        "citation": "Unicode Core Specification Hangul algorithms",
        "source_reference": "unicode:hangul-algorithm",
        "source_hash": "b" * 64,
    }


def _pending(role: str = "korean_orthography") -> dict[str, object]:
    return {
        "status": "needs_review",
        "reason_code": "qualified_review_required",
        "required_reviewer_role": role,
    }


def _media_slot(
    slot_id: str,
    media_kind: str,
) -> dict[str, object]:
    return {
        "slot_id": slot_id,
        "media_kind": media_kind,
        "required": True,
        "review_status": "needs_review",
        "reason_code": "media_missing",
    }


def _concepts() -> list[dict[str, object]]:
    return [
        {
            "id": "orthography.jamo.unit",
            "domain": "orthography",
            "prerequisite_ids": [],
            "sequence": 1,
        },
        {
            "id": "orthography.block.unit",
            "domain": "orthography",
            "prerequisite_ids": ["orthography.jamo.unit"],
            "sequence": 2,
        },
        {
            "id": "orthography.vowel.a",
            "domain": "orthography",
            "prerequisite_ids": ["orthography.jamo.unit"],
            "sequence": 3,
        },
        {
            "id": "phonology.syllable.timing",
            "domain": "phonology",
            "prerequisite_ids": ["orthography.jamo.unit"],
            "sequence": 4,
        },
        {
            "id": "phonology.nasalization.velar",
            "domain": "phonology",
            "prerequisite_ids": [
                "orthography.jamo.unit",
                "phonology.syllable.timing",
            ],
            "sequence": 5,
        },
    ]


def _registry(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "language_code": "ko",
        "registry_version": "korean-concepts-v1",
        "provenance": [_provenance()],
        "concepts": _concepts(),
    }
    payload.update(overrides)
    return _sealed(payload)


def _evidence(
    target: str,
    prerequisites: tuple[str, ...],
    *,
    observed: tuple[str, ...] | None = None,
    unknown: tuple[str, ...] | None = None,
    policy: str = "strict",
) -> dict[str, object]:
    return {
        "target_concept_id": target,
        "prerequisite_concept_ids": list(prerequisites),
        "observed_concept_ids": list(observed or (*prerequisites, target)),
        "unknown_concept_ids": list(unknown or (target,)),
        "policy": policy,
    }


def _hangul_entry(
    sequence: int,
    *,
    target: str,
    prerequisites: tuple[str, ...],
    stage_id: str,
    category_id: str,
    active_rule_ids: tuple[str, ...] | None = None,
) -> dict[str, object]:
    mapping = None
    if sequence == 1:
        mapping = {
            "display_glyph": "ㄱ",
            "canonical_jamo": "ᄀ",
            "jamo_position": "initial",
            "unicode_name": "HANGUL CHOSEONG KIYEOK",
            "source_version": "unicode-17.0",
            "source_hash": "c" * 64,
            "review_status": "needs_review",
        }
    payload: dict[str, object] = {
        "item_key": f"ko-hangul-{sequence:04d}",
        "family": "hangul",
        "stage_id": stage_id,
        "category_id": category_id,
        "sequence": sequence,
        "source_pack_version": "hangul-v1",
        "evidence": _evidence(target, prerequisites),
        "active_rule_ids": list(active_rule_ids or (target,)),
        "inherited_orthographic_concept_ids": [],
        "provenance": [_provenance()],
        "pending_reviews": [_pending()],
        "media_slots": [
            {
                **_media_slot(f"hangul.picture.{sequence:04d}", "picture"),
                "required": False,
            },
            _media_slot(f"hangul.strokes.{sequence:04d}", "strokes"),
            {
                **_media_slot(f"hangul.gif.{sequence:04d}", "gif"),
                "required": False,
            },
            _media_slot(f"hangul.audio.{sequence:04d}", "audio"),
        ],
        "sort_index": sequence,
        "category": category_id,
        "canonical_jamo_or_block": "ᄀ" if sequence == 1 else "가",
        "reading_or_name": None,
        "sound": None,
        "mnemonic": None,
        "pedagogical_jamo_mapping": mapping,
    }
    return _sealed(payload)


def _hangul_pack(**overrides: object) -> dict[str, object]:
    entries = [
        _hangul_entry(
            1,
            target="orthography.jamo.unit",
            prerequisites=(),
            stage_id="H0",
            category_id="jamo-unit",
        ),
        _hangul_entry(
            2,
            target="orthography.block.unit",
            prerequisites=("orthography.jamo.unit",),
            stage_id="H0",
            category_id="syllable-block-unit",
        ),
        _hangul_entry(
            3,
            target="orthography.vowel.a",
            prerequisites=("orthography.jamo.unit",),
            stage_id="H1",
            category_id="vowel-a",
        ),
    ]
    registry = _registry()
    payload: dict[str, object] = {
        "language_code": "ko",
        "family": "hangul",
        "source_pack_version": "hangul-v1",
        "registry_version": "korean-concepts-v1",
        "registry_content_hash": registry["content_hash"],
        "item_key_pattern": "ko-hangul-{sequence:04d}",
        "sequence_policy": "contiguous-from-1",
        "inventory_status": "skeleton",
        "review_status": "needs_review",
        "learner_field_order": list(_HANGUL_FIELD_ORDER),
        "media_slot_schema": [
            {
                "media_kind": "picture",
                "required": False,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
            {
                "media_kind": "strokes",
                "required": True,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
            {
                "media_kind": "gif",
                "required": False,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
            {
                "media_kind": "audio",
                "required": True,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
        ],
        "strict_start_sequence": 1,
        "bootstrap_concept_ids": [
            "orthography.jamo.unit",
            "orthography.block.unit",
        ],
        "inherited_orthographic_concept_ids": [],
        "stage_coverage": [
            {
                "family": "hangul",
                "stage_id": stage_id,
                "required_category_ids": list(categories),
            }
            for stage_id, categories in _HANGUL_STAGE_CATEGORIES.items()
        ],
        "provenance": [_provenance()],
        "entries": entries,
    }
    payload.update(overrides)
    return _sealed(payload)


def _pronunciation_entry(
    sequence: int,
    *,
    target: str,
    prerequisites: tuple[str, ...],
    stage_id: str,
    category_id: str,
    active_rule_ids: tuple[str, ...],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "item_key": f"ko-pron-{sequence:04d}",
        "family": "pronunciation",
        "stage_id": stage_id,
        "category_id": category_id,
        "sequence": sequence,
        "source_pack_version": "pronunciation-i-plus-1-v1",
        "evidence": _evidence(target, prerequisites),
        "active_rule_ids": list(active_rule_ids),
        "inherited_orthographic_concept_ids": ["orthography.jamo.unit"],
        "provenance": [_provenance()],
        "pending_reviews": [_pending("korean_phonetics")],
        "media_slots": [
            _media_slot(f"pron.letter-audio.{sequence:04d}", "letter_audio"),
            _media_slot(f"pron.word-audio.{sequence:04d}", "word_audio"),
            _media_slot(f"pron.sentence-audio.{sequence:04d}", "sentence_audio"),
        ],
        "spellings": "국물",
        "sound": "[궁물]",
        "example_word": "국물",
        "word_translation": "caldo",
        "example_sentence": "국물이 뜨거워요.",
        "sentence_translation": "O caldo está quente.",
        "register_context": "standard-seoul",
        "pronunciation_evidence": {
            "canonical_spelling": "국물",
            "normative_pronunciation": "[궁물]",
            "surface_pronunciation": "[궁물]",
            "ipa": None,
            "phonological_rule_ids": list(active_rule_ids),
            "review_status": "needs_review",
        },
    }
    return _sealed(payload)


def _pronunciation_pack(**overrides: object) -> dict[str, object]:
    entries = [
        _pronunciation_entry(
            1,
            target="phonology.syllable.timing",
            prerequisites=("orthography.jamo.unit",),
            stage_id="P0",
            category_id="syllable-timing",
            active_rule_ids=("phonology.syllable.timing",),
        ),
        _pronunciation_entry(
            2,
            target="phonology.nasalization.velar",
            prerequisites=(
                "orthography.jamo.unit",
                "phonology.syllable.timing",
            ),
            stage_id="P5",
            category_id="nasalization-velar",
            active_rule_ids=(
                "phonology.syllable.timing",
                "phonology.nasalization.velar",
            ),
        ),
    ]
    registry = _registry()
    payload: dict[str, object] = {
        "language_code": "ko",
        "family": "pronunciation",
        "source_pack_version": "pronunciation-i-plus-1-v1",
        "registry_version": "korean-concepts-v1",
        "registry_content_hash": registry["content_hash"],
        "item_key_pattern": "ko-pron-{sequence:04d}",
        "sequence_policy": "contiguous-from-1",
        "inventory_status": "skeleton",
        "review_status": "needs_review",
        "learner_field_order": list(_PRONUNCIATION_FIELD_ORDER),
        "media_slot_schema": [
            {
                "media_kind": "letter_audio",
                "required": True,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
            {
                "media_kind": "word_audio",
                "required": True,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
            {
                "media_kind": "sentence_audio",
                "required": True,
                "review_status": "needs_review",
                "reason_code": "media-evidence-required",
            },
        ],
        "strict_start_sequence": 1,
        "bootstrap_concept_ids": [],
        "inherited_orthographic_concept_ids": ["orthography.jamo.unit"],
        "stage_coverage": [
            {
                "family": "pronunciation",
                "stage_id": stage_id,
                "required_category_ids": list(categories),
            }
            for stage_id, categories in _PRONUNCIATION_STAGE_CATEGORIES.items()
        ],
        "provenance": [_provenance()],
        "entries": entries,
    }
    payload.update(overrides)
    return _sealed(payload)


def _typed_registry(api: ModuleType) -> object:
    return api.KoreanConceptRegistry.model_validate(_registry())


def _typed_hangul_pack(api: ModuleType) -> object:
    return api.KoreanHangulSourcePack.model_validate(_hangul_pack())


def _typed_pronunciation_pack(api: ModuleType) -> object:
    return api.KoreanPronunciationSourcePack.model_validate(_pronunciation_pack())


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    reason_code = getattr(exc_info.value, "reason_code")
    return getattr(reason_code, "value", reason_code)


def test_curriculum_contracts_and_only_fixed_no_argument_loaders_are_exported() -> None:
    api = _curriculum()
    expected = {
        "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH",
        "CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH",
        "DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH",
        "DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH",
        "KOREAN_CONCEPT_REGISTRY_V1_PATH",
        "KOREAN_HANGUL_SOURCE_PACK_V1_PATH",
        "KOREAN_PRONUNCIATION_SOURCE_PACK_V1_PATH",
        "KoreanConceptRegistry",
        "KoreanCurriculumError",
        "KoreanCurriculumReasonCode",
        "KoreanFoundationSourceBundle",
        "KoreanCurriculumValidation",
        "KoreanFoundationEntry",
        "KoreanFoundationFamily",
        "KoreanHangulSourceEntry",
        "KoreanHangulSourcePack",
        "KoreanMediaSlotReference",
        "KoreanPendingReview",
        "KoreanPronunciationSourceEntry",
        "KoreanPronunciationSourcePack",
        "KoreanSourceProvenance",
        "KoreanStageCoverage",
        "korean_canonical_json_sha256",
        "load_korean_current_foundation_bundle",
        "load_korean_concept_registry",
        "load_korean_hangul_source_pack",
        "load_korean_v1_foundation_bundle",
        "load_korean_v1_hangul_source_pack",
        "load_korean_v1_pronunciation_source_pack",
        "load_korean_pronunciation_source_pack",
        "validate_korean_foundation_pack",
    }

    assert expected <= set(api.__all__)
    for loader_name in (
        "load_korean_concept_registry",
        "load_korean_hangul_source_pack",
        "load_korean_pronunciation_source_pack",
    ):
        assert not inspect.signature(getattr(api, loader_name)).parameters
    validator_parameters = inspect.signature(
        api.validate_korean_foundation_pack
    ).parameters
    assert tuple(validator_parameters) == (
        "registry",
        "pack",
        "inherited_known_ids",
    )
    assert all(
        forbidden not in name.casefold()
        for name in validator_parameters
        for forbidden in ("path", "root", "url", "archive", "apkg")
    )


def test_canonical_json_hash_is_deterministic_and_manifest_models_are_frozen() -> None:
    api = _curriculum()
    first = {"z": "한글", "a": [2, 1]}
    second = {"a": [2, 1], "z": "한글"}

    assert api.korean_canonical_json_sha256(first) == _canonical_hash(first)
    assert api.korean_canonical_json_sha256(first) == api.korean_canonical_json_sha256(
        second
    )

    registry = _typed_registry(api)
    with pytest.raises(ValidationError):
        registry.registry_version = "changed"
    invalid = _registry()
    invalid["unexpected"] = True
    invalid["content_hash"] = _canonical_hash(invalid)
    with pytest.raises(ValidationError):
        api.KoreanConceptRegistry.model_validate(invalid)


def test_fixed_utf8_json_loaders_return_typed_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _curriculum()
    paths = {
        "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH": tmp_path / "concepts.json",
        "DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH": tmp_path / "hangul.json",
        "DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH": tmp_path / "pron.json",
    }
    payloads = (_registry(), _hangul_pack(), _pronunciation_pack())
    for (constant_name, path), payload in zip(paths.items(), payloads, strict=True):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(api, constant_name, path)

    assert isinstance(api.load_korean_concept_registry(), api.KoreanConceptRegistry)
    assert isinstance(api.load_korean_v1_hangul_source_pack(), api.KoreanHangulSourcePack)
    assert isinstance(
        api.load_korean_v1_pronunciation_source_pack(),
        api.KoreanPronunciationSourcePack,
    )


@pytest.mark.parametrize("failure", ["missing", "malformed", "non_utf8", "oversized"])
def test_fixed_loader_failures_are_bounded_and_content_free(
    failure: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _curriculum()
    manifest = tmp_path / "private-korean-source.json"
    marker = "private-source-content-must-not-appear"
    if failure == "malformed":
        manifest.write_text("{" + marker, encoding="utf-8")
    elif failure == "non_utf8":
        manifest.write_bytes(b"\xff\xfe" + marker.encode())
    elif failure == "oversized":
        manifest.write_bytes(b"x" * (api.KOREAN_MANIFEST_MAX_BYTES + 1))
    monkeypatch.setattr(api, "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH", manifest)

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.load_korean_concept_registry()

    assert _reason(exc_info) in {
        "manifest_missing",
        "manifest_malformed",
        "manifest_oversized",
    }
    error = str(exc_info.value)
    assert marker not in error
    assert str(tmp_path) not in error


def test_fixed_loader_rechecks_actual_bytes_after_the_size_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _curriculum()

    class GrowingManifest:
        def stat(self) -> object:
            return SimpleNamespace(st_size=1)

        def read_bytes(self) -> bytes:
            return b"x" * (api.KOREAN_MANIFEST_MAX_BYTES + 1)

    monkeypatch.setattr(
        api,
        "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH",
        GrowingManifest(),
    )

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.load_korean_concept_registry()

    assert _reason(exc_info) == "manifest_oversized"


@pytest.mark.parametrize(
    "mutation",
    ["extra", "hash", "unsafe_markup", "oversized_value", "oversized_pack"],
)
def test_manifest_schema_rejects_extra_unsafe_unbounded_or_drifted_data(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _curriculum()
    payload = _registry()
    if mutation == "extra":
        payload["unexpected"] = True
        payload["content_hash"] = _canonical_hash(payload)
    elif mutation == "hash":
        payload["content_hash"] = "0" * 64
    elif mutation == "unsafe_markup":
        payload["provenance"][0]["citation"] = "<script>private marker</script>"
        payload["content_hash"] = _canonical_hash(payload)
    elif mutation == "oversized_value":
        payload["provenance"][0]["citation"] = "x" * 2049
        payload["content_hash"] = _canonical_hash(payload)
    else:
        payload["concepts"] = payload["concepts"] * 820
        payload["content_hash"] = _canonical_hash(payload)
    manifest = tmp_path / "untrusted.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(api, "DEFAULT_KOREAN_CONCEPT_REGISTRY_PATH", manifest)

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.load_korean_concept_registry()

    assert _reason(exc_info) == "manifest_invalid"
    assert "private marker" not in str(exc_info.value)
    assert str(tmp_path) not in str(exc_info.value)


def test_curriculum_defaults_to_atomic_v2_candidate_bundle() -> None:
    api = _curriculum()

    bundle = api.load_korean_current_foundation_bundle()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()

    assert bundle.source_kind == "current-candidate"
    assert bundle.source_root == (
        "data/korean_foundations/candidate-bundles/"
        "e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357"
    )
    assert bundle.bundle_sha256 == (
        "e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357"
    )
    assert bundle.bundle_manifest_sha256 == (
        "6852f7cc6eeedf2ec88f33ab8f027e76a72981a4179015b8aa40a0f3eb40a3ab"
    )
    assert bundle.member_file_sha256 == {
        "hangul-v2.json": "da12a49c5f42483eeeb6da4f251ea2eba3295afa7cf07c2c621e4dddfa5ff038",
        "pronunciation-i-plus-1-v2.json": "889acedc9de497cfa25d8699ac4d2434bd102653c31276874a8b4336fd15448e",
        "korean-foundations-v2-curation.json": "695346c70e34e163e459e3f2e1c8156b39ed4f126c4803e98258d229a8164caf",
        "korean-foundations-v2-media.json": "545bd060992e9a17d7a95a3397d774678c3cb3e3cddbe593e93c949f9b12326d",
    }
    assert registry == bundle.registry
    assert hangul == bundle.hangul
    assert pronunciation == bundle.pronunciation
    assert registry.registry_version == "korean-concepts-v1"
    assert hangul.source_pack_version == "hangul-v2"
    assert pronunciation.source_pack_version == "pronunciation-i-plus-1-v2"
    assert len(hangul.entries) == 92
    assert len(pronunciation.entries) == 47
    assert hangul.registry_content_hash == registry.content_hash
    assert pronunciation.registry_content_hash == registry.content_hash
    assert set(_all_status_values(bundle.model_dump(mode="json"))) == {"needs_review"}

    hangul_validation = api.validate_korean_foundation_pack(
        registry=registry,
        pack=hangul,
    )
    pronunciation_validation = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pronunciation,
        inherited_known_ids=hangul_validation.known_concept_ids,
    )
    assert hangul_validation.validated_entry_count == 92
    assert pronunciation_validation.validated_entry_count == 47


def test_curriculum_explicit_history_resolves_v1_without_changing_defaults() -> None:
    api = _curriculum()

    history = api.load_korean_v1_foundation_bundle()

    assert history.source_kind == "v1-history"
    assert history.source_root == "data/korean_foundations"
    assert history.bundle_sha256 is None
    assert history.bundle_manifest_sha256 is None
    assert history.registry.registry_version == "korean-concepts-v1"
    assert history.hangul.source_pack_version == "hangul-v1"
    assert history.pronunciation.source_pack_version == "pronunciation-i-plus-1-v1"
    assert api.load_korean_hangul_source_pack().source_pack_version == "hangul-v2"
    assert (
        api.load_korean_pronunciation_source_pack().source_pack_version
        == "pronunciation-i-plus-1-v2"
    )
    assert api.load_korean_v1_hangul_source_pack() == history.hangul
    assert api.load_korean_v1_pronunciation_source_pack() == history.pronunciation


def _registry_with_concepts(concepts: list[dict[str, object]]) -> dict[str, object]:
    return _registry(concepts=concepts)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_id",
        "duplicate_sequence",
        "missing_predecessor",
        "cycle",
        "forward_edge",
        "missing_closure",
        "nondeterministic_order",
    ],
)
def test_registry_rejects_invalid_graphs_and_nondeterministic_order(
    mutation: str,
) -> None:
    api = _curriculum()
    concepts = _concepts()
    if mutation == "duplicate_id":
        concepts[1]["id"] = concepts[0]["id"]
    elif mutation == "duplicate_sequence":
        concepts[1]["sequence"] = concepts[0]["sequence"]
    elif mutation == "missing_predecessor":
        concepts[1]["prerequisite_ids"] = ["orthography.missing"]
    elif mutation == "cycle":
        concepts[0]["prerequisite_ids"] = ["orthography.block.unit"]
    elif mutation == "forward_edge":
        concepts[0]["prerequisite_ids"] = ["orthography.block.unit"]
        concepts[1]["prerequisite_ids"] = []
    elif mutation == "missing_closure":
        concepts[4]["prerequisite_ids"] = ["phonology.syllable.timing"]
    else:
        concepts[0], concepts[1] = concepts[1], concepts[0]

    with pytest.raises(ValidationError):
        api.KoreanConceptRegistry.model_validate(_registry_with_concepts(concepts))


@pytest.mark.parametrize(
    "concepts",
    [
        [
            {
                "id": "grammar.unsupported",
                "domain": "grammar",
                "prerequisite_ids": [],
                "sequence": 1,
            }
        ],
        [
            {
                "id": "phonology.seed",
                "domain": "phonology",
                "prerequisite_ids": [],
                "sequence": 1,
            },
            {
                "id": "orthography.invalid-dependency",
                "domain": "orthography",
                "prerequisite_ids": ["phonology.seed"],
                "sequence": 2,
            },
        ],
    ],
)
def test_registry_rejects_unsupported_foundation_domains_and_links(
    concepts: list[dict[str, object]],
) -> None:
    api = _curriculum()

    with pytest.raises(ValidationError):
        api.KoreanConceptRegistry.model_validate(_registry_with_concepts(concepts))


def test_registry_errors_hide_unknown_source_identifiers() -> None:
    api = _curriculum()
    marker = "private.missing.predecessor"
    concepts = _concepts()
    concepts[1]["prerequisite_ids"] = [marker]

    with pytest.raises(ValidationError) as exc_info:
        api.KoreanConceptRegistry.model_validate(_registry_with_concepts(concepts))

    assert marker not in str(exc_info.value)


def test_valid_hangul_bootstrap_admits_each_target_only_after_its_entry() -> None:
    api = _curriculum()
    result = api.validate_korean_foundation_pack(
        registry=_typed_registry(api),
        pack=_typed_hangul_pack(api),
    )

    assert isinstance(result, api.KoreanCurriculumValidation)
    assert result.family.value == "hangul"
    assert result.validated_entry_count == 3
    assert result.bootstrap_concept_ids == (
        "orthography.jamo.unit",
        "orthography.block.unit",
    )
    assert result.admitted_target_concept_ids == (
        "orthography.jamo.unit",
        "orthography.block.unit",
        "orthography.vowel.a",
    )
    assert result.known_concept_ids == result.admitted_target_concept_ids


def test_valid_pronunciation_uses_exact_declared_inherited_orthography() -> None:
    api = _curriculum()
    result = api.validate_korean_foundation_pack(
        registry=_typed_registry(api),
        pack=_typed_pronunciation_pack(api),
        inherited_known_ids=("orthography.jamo.unit",),
    )

    assert result.family.value == "pronunciation"
    assert result.inherited_known_concept_ids == ("orthography.jamo.unit",)
    assert result.admitted_target_concept_ids == (
        "phonology.syllable.timing",
        "phonology.nasalization.velar",
    )


def _replace_entry(pack: object, index: int, entry: object) -> object:
    entries = list(getattr(pack, "entries"))
    entries[index] = entry
    return pack.model_copy(update={"entries": tuple(entries)})


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    [
        ("bootstrap_order", "bootstrap_mismatch"),
        ("bootstrap_preknown", "recomputed_unknown_mismatch"),
        ("omitted_target", "target_not_observed"),
        ("forged_unknown", "serialized_unknown_mismatch"),
        ("unknown_prerequisite", "unknown_prerequisite"),
        ("undeclared_active_rule", "active_rule_not_prerequisite"),
        ("repeated_target", "repeated_target"),
        ("non_strict", "strict_policy_required"),
        ("unknown_observed", "unknown_concept"),
    ],
)
def test_strict_engine_recomputes_every_entry_and_rejects_false_evidence(
    mutation: str,
    reason_code: str,
) -> None:
    api = _curriculum()
    registry = _typed_registry(api)
    pack = _typed_hangul_pack(api)
    entry = pack.entries[0]
    if mutation == "bootstrap_order":
        pack = pack.model_copy(
            update={"bootstrap_concept_ids": tuple(reversed(pack.bootstrap_concept_ids))}
        )
    elif mutation == "bootstrap_preknown":
        evidence = entry.evidence.model_copy(
            update={
                "observed_concept_ids": (
                    "orthography.block.unit",
                    "orthography.jamo.unit",
                ),
                "unknown_concept_ids": ("orthography.jamo.unit",),
            }
        )
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))
    elif mutation == "omitted_target":
        evidence = entry.evidence.model_copy(update={"observed_concept_ids": ()})
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))
    elif mutation == "forged_unknown":
        evidence = entry.evidence.model_copy(
            update={"unknown_concept_ids": ("orthography.block.unit",)}
        )
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))
    elif mutation == "unknown_prerequisite":
        evidence = entry.evidence.model_copy(
            update={
                "prerequisite_concept_ids": ("orthography.block.unit",),
                "observed_concept_ids": (
                    "orthography.block.unit",
                    "orthography.jamo.unit",
                ),
            }
        )
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))
    elif mutation == "undeclared_active_rule":
        later = pack.entries[2]
        pack = _replace_entry(
            pack,
            2,
            later.model_copy(
                update={
                    "active_rule_ids": (
                        "orthography.block.unit",
                        later.evidence.target_concept_id,
                    )
                }
            ),
        )
    elif mutation == "repeated_target":
        later = pack.entries[2]
        evidence = later.evidence.model_copy(
            update={
                "target_concept_id": "orthography.block.unit",
                "observed_concept_ids": ("orthography.block.unit",),
                "unknown_concept_ids": ("orthography.block.unit",),
                "prerequisite_concept_ids": (),
            }
        )
        pack = _replace_entry(pack, 2, later.model_copy(update={"evidence": evidence}))
    elif mutation == "non_strict":
        evidence = entry.evidence.model_copy(update={"policy": "adaptive"})
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))
    else:
        evidence = entry.evidence.model_copy(
            update={
                "observed_concept_ids": (
                    "orthography.private.missing",
                    "orthography.jamo.unit",
                )
            }
        )
        pack = _replace_entry(pack, 0, entry.model_copy(update={"evidence": evidence}))

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(registry=registry, pack=pack)

    assert _reason(exc_info) == reason_code
    assert "orthography.private.missing" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("inherited", "reason_code"),
    [
        (
            ("orthography.jamo.unit", "orthography.block.unit"),
            "inherited_concepts_mismatch",
        ),
        (("phonology.syllable.timing",), "inherited_concepts_mismatch"),
        ((), "inherited_concepts_mismatch"),
    ],
)
def test_pronunciation_rejects_forged_or_missing_inherited_known_concepts(
    inherited: tuple[str, ...],
    reason_code: str,
) -> None:
    api = _curriculum()

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=_typed_registry(api),
            pack=_typed_pronunciation_pack(api),
            inherited_known_ids=inherited,
        )

    assert _reason(exc_info) == reason_code


def test_registry_and_pack_version_or_hash_drift_fails_before_graph_admission() -> None:
    api = _curriculum()
    pack = _typed_hangul_pack(api).model_copy(
        update={"registry_content_hash": "0" * 64}
    )

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=_typed_registry(api),
            pack=pack,
        )

    assert _reason(exc_info) == "registry_mismatch"


def test_family_domain_links_fail_closed() -> None:
    api = _curriculum()
    pack = _typed_hangul_pack(api)
    entry = pack.entries[2]
    evidence = entry.evidence.model_copy(
        update={
            "target_concept_id": "phonology.syllable.timing",
            "observed_concept_ids": (
                "orthography.jamo.unit",
                "phonology.syllable.timing",
            ),
            "unknown_concept_ids": ("phonology.syllable.timing",),
        }
    )
    pack = _replace_entry(pack, 2, entry.model_copy(update={"evidence": evidence}))

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=_typed_registry(api),
            pack=pack,
        )

    assert _reason(exc_info) == "unsupported_domain"


_HANGUL_STAGE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "H0": (
        "jamo-unit",
        "syllable-block-unit",
        "onset-slot",
        "nucleus-slot",
        "optional-coda-slot",
        "vertical-vowel-layout",
        "horizontal-vowel-layout",
    ),
    "H1": (
        "vowel-a",
        "vowel-eo",
        "vowel-o",
        "vowel-u",
        "vowel-eu",
        "vowel-i",
    ),
    "H2": (
        "null-onset-ieung",
        "vertical-block-composition",
        "horizontal-block-composition",
    ),
    "H3": (
        "basic-onset-nieun",
        "basic-onset-mieum",
        "basic-onset-rieul",
        "basic-onset-kiyeok",
        "basic-onset-tikeut",
        "basic-onset-pieup",
        "basic-onset-cieuc",
        "basic-onset-sios",
        "basic-onset-hieuh",
    ),
    "H4": (
        "vowel-ya",
        "vowel-yeo",
        "vowel-yo",
        "vowel-yu",
        "vowel-ae",
        "vowel-e",
        "vowel-yae",
        "vowel-ye",
    ),
    "H5": (
        "aspirated-onset-khieukh",
        "aspirated-onset-thieuth",
        "aspirated-onset-phieuph",
        "aspirated-onset-chieuch",
        "tense-onset-ssangkiyeok",
        "tense-onset-ssangtikeut",
        "tense-onset-ssangpieup",
        "tense-onset-ssangsios",
        "tense-onset-ssangcieuc",
    ),
    "H6": (
        "vowel-wa",
        "vowel-wo",
        "vowel-wae",
        "vowel-we",
        "vowel-oe",
        "vowel-wi",
        "vowel-ui",
    ),
    "H7": (
        "batchim-position",
        "coda-output-kiyeok",
        "coda-output-nieun",
        "coda-output-tikeut",
        "coda-output-rieul",
        "coda-output-mieum",
        "coda-output-pieup",
        "coda-output-ieung",
    ),
    "H8": (
        "final-kiyeok",
        "final-ssangkiyeok",
        "final-kiyeok-sios",
        "final-nieun",
        "final-nieun-cieuc",
        "final-nieun-hieuh",
        "final-tikeut",
        "final-rieul",
        "final-rieul-kiyeok",
        "final-rieul-mieum",
        "final-rieul-pieup",
        "final-rieul-sios",
        "final-rieul-thieuth",
        "final-rieul-phieuph",
        "final-rieul-hieuh",
        "final-mieum",
        "final-pieup",
        "final-pieup-sios",
        "final-sios",
        "final-ssangsios",
        "final-ieung",
        "final-cieuc",
        "final-chieuch",
        "final-khieukh",
        "final-thieuth",
        "final-phieuph",
        "final-hieuh",
    ),
    "H9": (
        "morpheme-preserving-spelling",
        "basic-word-spacing",
        "attached-particle-spacing",
    ),
    "H10": (
        "nfc-nfd-equivalence",
        "keyboard-orientation",
        "punctuation",
        "numerals",
        "bounded-mixed-script",
    ),
}

_PRONUNCIATION_STAGE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "P0": (
        "syllable-timing",
        "vowel-quality",
        "null-onset",
        "sonorant-nieun",
        "sonorant-mieum",
        "sonorant-ieung",
        "rieul-intervocalic",
        "rieul-coda",
    ),
    "P1": (
        "onset-contrast-pieup",
        "onset-contrast-tikeut",
        "onset-contrast-kiyeok",
        "onset-contrast-cieuc",
        "onset-contrast-sios",
        "onset-hieuh",
    ),
    "P2": (
        "unreleased-coda",
        "coda-neutralization-kiyeok",
        "coda-neutralization-nieun",
        "coda-neutralization-tikeut",
        "coda-neutralization-rieul",
        "coda-neutralization-mieum",
        "coda-neutralization-pieup",
        "coda-neutralization-ieung",
    ),
    "P3": ("liaison-vowel-initial-morpheme",),
    "P4": ("post-obstruent-tensification",),
    "P5": (
        "nasalization-velar",
        "nasalization-coronal",
        "nasalization-labial",
    ),
    "P6": (
        "h-aspiration-coda-to-onset",
        "h-aspiration-onset-from-coda",
    ),
    "P7": ("palatalization-tikeut", "palatalization-thieuth"),
    "P8": ("liquid-assimilation", "rieul-related-process", "n-insertion"),
    "P9": (
        "complex-coda-before-consonant",
        "complex-coda-before-vowel",
        "complex-coda-rule-interaction",
    ),
    "P10": (
        "contraction-boa-bwa",
        "contraction-jueo-jwo",
        "contraction-doeeo-dwae",
        "contraction-hayeo-hae",
    ),
    "P11": ("optional-reduction-register-context",),
    "P12": (
        "phrase-accent",
        "focus",
        "boundary-intonation",
        "rate-conditioned-effects",
    ),
    "P13": ("rule-ordering-relation",),
}

_HANGUL_FIELD_ORDER = (
    "SortIndex",
    "Category",
    "JamoOrBlock",
    "ReadingOrName",
    "Sound",
    "Mnemonic",
    "Picture",
    "Strokes",
    "Gif",
    "Audio",
    "TargetConceptId",
    "PrerequisiteConceptIds",
    "ObservedConceptIds",
    "UnknownConceptIds",
    "IPlusOnePolicy",
)

_PRONUNCIATION_FIELD_ORDER = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)

_PROVENANCE_HASHES = {
    "unicode.hangul-17.0": (
        "6006005d2a1fd7e63e5cab103aeb22487b8f3980f01efc37b76e569859429c7b"
    ),
    "unicode.uax15-r57": (
        "ba490809ca63d80e4d5eb9877f3065aa9235bf129511efedf8951cd4189ce85a"
    ),
    "nikl.orthography-0001": (
        "13712afb60ada5cac9cd164c223344c3e9e6eb1e567ace3dd57997d566ac91e4"
    ),
    "nikl.pronunciation-0002": (
        "a7f939a7dd4454df1c6cf8acab61b04436ede8902c23ae6282315066eeeb4408"
    ),
}


def _concept_id(stage_id: str, category_id: str) -> str:
    overrides = {
        ("H0", "jamo-unit"): "orthography.jamo.unit",
        ("H0", "syllable-block-unit"): "orthography.block.unit",
        ("H0", "onset-slot"): "orthography.block.slot.onset",
        ("H0", "nucleus-slot"): "orthography.block.slot.nucleus",
        ("H0", "optional-coda-slot"): "orthography.block.slot.coda-optional",
        ("H0", "vertical-vowel-layout"): "orthography.block.layout.vertical",
        ("H0", "horizontal-vowel-layout"): "orthography.block.layout.horizontal",
        ("P0", "syllable-timing"): "phonology.syllable.timing",
    }
    if (stage_id, category_id) in overrides:
        return overrides[(stage_id, category_id)]
    domain = "orthography" if stage_id.startswith("H") else "phonology"
    return f"{domain}.{stage_id.casefold()}.{category_id.replace('-', '.')}"


def _expected_concept_ids(
    coverage: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    return tuple(
        _concept_id(stage_id, category_id)
        for stage_id, categories in coverage.items()
        for category_id in categories
    )


def _declared_coverage(pack: object) -> dict[str, tuple[str, ...]]:
    return {
        coverage.stage_id: tuple(coverage.required_category_ids)
        for coverage in getattr(pack, "stage_coverage")
    }


def _all_status_values(value: object) -> list[str]:
    if isinstance(value, dict):
        statuses = [
            item
            for key, item in value.items()
            if (
                key in {"status", "review_status"}
                or key.endswith("_review_status")
            )
            and isinstance(item, str)
        ]
        for item in value.values():
            statuses.extend(_all_status_values(item))
        return statuses
    if isinstance(value, list):
        statuses: list[str] = []
        for item in value:
            statuses.extend(_all_status_values(item))
        return statuses
    return []


def test_real_registry_and_complete_packs_load_from_fixed_paths() -> None:
    api = _curriculum()

    bundle = api.load_korean_current_foundation_bundle()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()

    assert bundle.hangul == hangul
    assert bundle.pronunciation == pronunciation
    assert registry.registry_version == "korean-concepts-v1"
    assert hangul.source_pack_version == "hangul-v2"
    assert pronunciation.source_pack_version == "pronunciation-i-plus-1-v2"
    assert hangul.registry_content_hash == registry.content_hash
    assert pronunciation.registry_content_hash == registry.content_hash
    assert registry.content_hash == _canonical_hash(registry.model_dump(mode="json"))
    assert hangul.content_hash == _canonical_hash(hangul.model_dump(mode="json"))
    assert pronunciation.content_hash == _canonical_hash(
        pronunciation.model_dump(mode="json")
    )

    for manifest in (registry, hangul, pronunciation):
        for source in manifest.provenance:
            assert source.source_id in _PROVENANCE_HASHES
            assert source.source_hash == _PROVENANCE_HASHES[source.source_id]
            assert "://" not in source.source_reference
            assert "\\" not in source.source_reference
            assert "../" not in source.source_reference


def test_real_registry_contains_every_declared_h_and_p_candidate_family() -> None:
    registry = _curriculum().load_korean_concept_registry()
    expected_ids = (
        *_expected_concept_ids(_HANGUL_STAGE_CATEGORIES),
        *_expected_concept_ids(_PRONUNCIATION_STAGE_CATEGORIES),
    )

    assert tuple(concept.id for concept in registry.concepts) == expected_ids
    assert tuple(concept.sequence for concept in registry.concepts) == tuple(
        range(1, len(expected_ids) + 1)
    )
    assert len(expected_ids) == 139
    assert {concept.domain for concept in registry.concepts} == {
        "orthography",
        "phonology",
    }


def test_real_hangul_bootstrap_is_explicit_ordered_and_strict() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    expected_h0 = _expected_concept_ids({"H0": _HANGUL_STAGE_CATEGORIES["H0"]})

    assert pack.bootstrap_concept_ids == expected_h0
    assert pack.strict_start_sequence == 1
    h0_entries = _entries_for_stage(pack, "H0")
    assert tuple(entry.stage_id for entry in h0_entries) == ("H0",) * len(expected_h0)
    assert tuple(entry.evidence.target_concept_id for entry in h0_entries) == expected_h0

    result = api.validate_korean_foundation_pack(registry=registry, pack=pack)

    assert result.validated_entry_count == len(pack.entries)
    assert result.bootstrap_concept_ids == expected_h0
    assert result.admitted_target_concept_ids[: len(expected_h0)] == expected_h0
    assert result.known_concept_ids[: len(expected_h0)] == expected_h0


def test_pack_headers_freeze_fields_media_and_pending_policy() -> None:
    api = _curriculum()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()

    assert _declared_coverage(hangul) == _HANGUL_STAGE_CATEGORIES
    assert _declared_coverage(pronunciation) == _PRONUNCIATION_STAGE_CATEGORIES
    assert hangul.item_key_pattern == "ko-hangul-{sequence:04d}"
    assert pronunciation.item_key_pattern == "ko-pron-{sequence:04d}"
    assert hangul.sequence_policy == pronunciation.sequence_policy == "contiguous-from-1"
    assert hangul.review_status == pronunciation.review_status == "needs_review"
    assert hangul.learner_field_order == _HANGUL_FIELD_ORDER
    assert pronunciation.learner_field_order == _PRONUNCIATION_FIELD_ORDER
    assert tuple(
        (slot.media_kind, slot.required, slot.review_status)
        for slot in hangul.media_slot_schema
    ) == (
        ("picture", False, "needs_review"),
        ("strokes", True, "needs_review"),
        ("gif", False, "needs_review"),
        ("audio", True, "needs_review"),
    )
    assert tuple(
        (slot.media_kind, slot.required, slot.review_status)
        for slot in pronunciation.media_slot_schema
    ) == (
        ("letter_audio", True, "needs_review"),
        ("word_audio", True, "needs_review"),
        ("sentence_audio", True, "needs_review"),
    )
    assert pronunciation.inventory_status == "complete"
    assert len(pronunciation.entries) == 47

    status_values = _all_status_values(
        {
            "hangul": hangul.model_dump(mode="json"),
            "pronunciation": pronunciation.model_dump(mode="json"),
        }
    )
    assert status_values
    assert set(status_values) == {"needs_review"}


def test_pronunciation_pack_inherits_completed_hangul_identity_only() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()
    inherited = _expected_concept_ids(_HANGUL_STAGE_CATEGORIES)

    assert pronunciation.inherited_orthographic_concept_ids == inherited
    assert set(inherited) == {
        concept.id
        for concept in registry.concepts
        if concept.domain == "orthography"
    }
    assert set(inherited) == {
        entry.evidence.target_concept_id for entry in hangul.entries
    } | set(_expected_concept_ids({
        stage: categories
        for stage, categories in _HANGUL_STAGE_CATEGORIES.items()
        if stage != "H0"
    }))
    assert not any(concept_id.startswith("phonology.") for concept_id in inherited)

    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pronunciation,
        inherited_known_ids=inherited,
    )
    assert result.validated_entry_count == 47
    assert result.inherited_known_concept_ids == inherited
    assert result.admitted_target_concept_ids == _expected_concept_ids(
        _PRONUNCIATION_STAGE_CATEGORIES
    )
    assert result.known_concept_ids == (
        *inherited,
        *_expected_concept_ids(_PRONUNCIATION_STAGE_CATEGORIES),
    )


@pytest.mark.parametrize(
    ("family", "mutation"),
    [
        ("hangul", "missing_stage"),
        ("hangul", "duplicate_stage"),
        ("hangul", "unknown_stage"),
        ("hangul", "missing_category"),
        ("hangul", "duplicate_category"),
        ("hangul", "unknown_category"),
        ("pronunciation", "missing_stage"),
        ("pronunciation", "duplicate_stage"),
        ("pronunciation", "unknown_stage"),
        ("pronunciation", "missing_category"),
        ("pronunciation", "duplicate_category"),
        ("pronunciation", "unknown_category"),
    ],
)
def test_coverage_validator_rejects_missing_duplicate_or_unknown_declarations(
    family: str,
    mutation: str,
) -> None:
    api = _curriculum()
    pack = (
        api.load_korean_hangul_source_pack()
        if family == "hangul"
        else api.load_korean_pronunciation_source_pack()
    )
    payload = pack.model_dump(mode="json")
    coverage = payload["stage_coverage"]
    if mutation == "missing_stage":
        coverage.pop()
    elif mutation == "duplicate_stage":
        coverage.append(deepcopy(coverage[-1]))
    elif mutation == "unknown_stage":
        coverage[-1]["stage_id"] = "H11" if family == "hangul" else "P14"
    elif mutation == "missing_category":
        coverage[-1]["required_category_ids"].pop()
    elif mutation == "duplicate_category":
        coverage[-1]["required_category_ids"].append(
            coverage[-1]["required_category_ids"][-1]
        )
    else:
        coverage[-1]["required_category_ids"][-1] = "private-unknown-category"
    payload["content_hash"] = _canonical_hash(payload)
    model_type = (
        api.KoreanHangulSourcePack
        if family == "hangul"
        else api.KoreanPronunciationSourcePack
    )

    with pytest.raises(ValidationError):
        model_type.model_validate(payload)


def _entries_for_stage(pack: object, stage_id: str) -> tuple[object, ...]:
    return tuple(
        entry for entry in getattr(pack, "entries") if entry.stage_id == stage_id
    )


def _mapped_display_glyphs(pack: object, stage_id: str) -> tuple[str, ...]:
    return tuple(
        entry.pedagogical_jamo_mapping.display_glyph
        for entry in _entries_for_stage(pack, stage_id)
        if entry.pedagogical_jamo_mapping is not None
    )


def _mapped_canonical_jamo(pack: object, stage_id: str) -> tuple[str, ...]:
    return tuple(
        entry.pedagogical_jamo_mapping.canonical_jamo
        for entry in _entries_for_stage(pack, stage_id)
        if entry.pedagogical_jamo_mapping is not None
    )


def test_hangul_h1_h6_exact_locked_candidate_inventory() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()

    assert _mapped_display_glyphs(pack, "H1") == tuple("ㅏㅓㅗㅜㅡㅣ")
    assert _mapped_display_glyphs(pack, "H3") == tuple("ㄴㅁㄹㄱㄷㅂㅈㅅㅎ")
    assert _mapped_display_glyphs(pack, "H4") == tuple("ㅑㅕㅛㅠㅐㅔㅒㅖ")
    assert _mapped_display_glyphs(pack, "H5") == tuple("ㅋㅌㅍㅊㄲㄸㅃㅆㅉ")
    assert _mapped_display_glyphs(pack, "H6") == tuple("ㅘㅝㅙㅞㅚㅟㅢ")
    assert tuple(len(_entries_for_stage(pack, stage)) for stage in ("H1", "H2", "H3", "H4", "H5", "H6")) == (
        6,
        3,
        9,
        8,
        9,
        7,
    )


def test_normative_h3_contains_pieup_and_never_contains_invalid_typo() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    h3 = _mapped_display_glyphs(pack, "H3")
    serialized = json.dumps(pack.model_dump(mode="json"), ensure_ascii=False)

    assert "ㅂ" in h3
    assert "㄂" not in h3
    assert "㄂" not in serialized
    assert "basic-onset-pieup" in {
        entry.category_id for entry in _entries_for_stage(pack, "H3")
    }


def test_modern_choseong_inventory_is_exactly_19_positional_identities() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    canonical = (
        *_mapped_canonical_jamo(pack, "H2"),
        *_mapped_canonical_jamo(pack, "H3"),
        *_mapped_canonical_jamo(pack, "H5"),
    )
    expected = tuple(chr(codepoint) for codepoint in range(0x1100, 0x1113))

    assert len(canonical) == 19
    assert len(set(canonical)) == 19
    assert set(canonical) == set(expected)
    assert all(unicodedata.name(value).startswith("HANGUL CHOSEONG ") for value in canonical)


def test_modern_jungseong_inventory_is_exactly_21_positional_identities() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    canonical = (
        *_mapped_canonical_jamo(pack, "H1"),
        *_mapped_canonical_jamo(pack, "H4"),
        *_mapped_canonical_jamo(pack, "H6"),
    )
    expected = tuple(chr(codepoint) for codepoint in range(0x1161, 0x1176))

    assert len(canonical) == 21
    assert len(set(canonical)) == 21
    assert set(canonical) == set(expected)
    assert all(unicodedata.name(value).startswith("HANGUL JUNGSEONG ") for value in canonical)


def test_hangul_h2_declares_null_onset_and_both_known_vowel_layouts() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    entries = {entry.category_id: entry for entry in _entries_for_stage(pack, "H2")}

    assert entries["null-onset-ieung"].pedagogical_jamo_mapping.display_glyph == "ㅇ"
    assert entries["null-onset-ieung"].pedagogical_jamo_mapping.canonical_jamo == "ᄋ"
    assert entries["vertical-block-composition"].canonical_jamo_or_block == "아"
    assert entries["horizontal-block-composition"].canonical_jamo_or_block == "오"

    concept_by_id = {concept.id: concept for concept in registry.concepts}
    vertical_dependencies = set(
        concept_by_id[
            entries["vertical-block-composition"].evidence.target_concept_id
        ].prerequisite_ids
    )
    horizontal_dependencies = set(
        concept_by_id[
            entries["horizontal-block-composition"].evidence.target_concept_id
        ].prerequisite_ids
    )
    assert {
        _concept_id("H0", "vertical-vowel-layout"),
        _concept_id("H1", "vowel-a"),
        _concept_id("H1", "vowel-eo"),
        _concept_id("H1", "vowel-i"),
        _concept_id("H2", "null-onset-ieung"),
    } <= vertical_dependencies
    assert {
        _concept_id("H0", "horizontal-vowel-layout"),
        _concept_id("H1", "vowel-o"),
        _concept_id("H1", "vowel-u"),
        _concept_id("H1", "vowel-eu"),
        _concept_id("H2", "null-onset-ieung"),
    } <= horizontal_dependencies


def test_hangul_h1_h6_candidates_are_nfc_provenance_bound_pending_and_strict() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    entries = tuple(
        entry
        for entry in pack.entries
        if entry.stage_id in {"H1", "H2", "H3", "H4", "H5", "H6"}
    )

    assert len(entries) == 42
    for entry in entries:
        assert unicodedata.normalize("NFC", entry.canonical_jamo_or_block) == entry.canonical_jamo_or_block
        for learner_text in (entry.reading_or_name, entry.sound, entry.mnemonic):
            if learner_text is not None:
                assert learner_text
                assert unicodedata.normalize("NFC", learner_text) == learner_text
        assert {source.source_id for source in entry.provenance} >= {
            "unicode.hangul-17.0",
            "nikl.orthography-0001",
        }
        assert {review.status for review in entry.pending_reviews} == {"needs_review"}
        assert {slot.review_status for slot in entry.media_slots} == {"needs_review"}
        assert tuple(entry.evidence.unknown_concept_ids) == (
            entry.evidence.target_concept_id,
        )
        mapping = entry.pedagogical_jamo_mapping
        if mapping is not None:
            assert mapping.review_status.value == "needs_review"
            assert mapping.display_glyph != mapping.canonical_jamo
            assert unicodedata.normalize("NFC", mapping.canonical_jamo) == mapping.canonical_jamo

    result = api.validate_korean_foundation_pack(registry=registry, pack=pack)
    assert result.validated_entry_count == len(pack.entries)
    assert result.admitted_target_concept_ids == tuple(
        entry.evidence.target_concept_id for entry in pack.entries
    )


@pytest.mark.parametrize("stage_id", ["H1", "H2", "H3", "H4", "H5", "H6"])
def test_hangul_h1_h6_mutation_adds_a_second_recomputed_unknown(
    stage_id: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    entries = list(pack.entries)
    index = next(index for index, entry in enumerate(entries) if entry.stage_id == stage_id)
    entry = entries[index]
    later_target = entries[index + 1].evidence.target_concept_id
    evidence = entry.evidence.model_copy(
        update={
            "observed_concept_ids": (
                *entry.evidence.observed_concept_ids,
                later_target,
            )
        }
    )
    entries[index] = entry.model_copy(update={"evidence": evidence})
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(registry=registry, pack=mutated)

    assert _reason(exc_info) == "recomputed_unknown_mismatch"


_MODERN_FINAL_DISPLAY_ORDER = tuple(
    "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
)
_COMPLEX_FINAL_DISPLAY_ORDER = tuple("ㄳㄵㄶㄺㄻㄼㄽㄾㄿㅀㅄ")


def test_hangul_h7_h10_exact_stage_inventory_and_machine_only_copy() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()

    assert tuple(
        entry.category_id for entry in _entries_for_stage(pack, "H7")
    ) == _HANGUL_STAGE_CATEGORIES["H7"]
    assert tuple(
        entry.category_id for entry in _entries_for_stage(pack, "H8")
    ) == _HANGUL_STAGE_CATEGORIES["H8"]
    assert tuple(
        entry.category_id for entry in _entries_for_stage(pack, "H9")
    ) == _HANGUL_STAGE_CATEGORIES["H9"]
    assert tuple(
        entry.category_id for entry in _entries_for_stage(pack, "H10")
    ) == _HANGUL_STAGE_CATEGORIES["H10"]
    assert tuple(len(_entries_for_stage(pack, stage)) for stage in ("H7", "H8", "H9", "H10")) == (
        8,
        27,
        3,
        5,
    )
    for stage_id in ("H9", "H10"):
        for entry in _entries_for_stage(pack, stage_id):
            assert entry.canonical_jamo_or_block == entry.evidence.target_concept_id
            for learner_text in (entry.reading_or_name, entry.sound, entry.mnemonic):
                if learner_text is not None:
                    assert learner_text
                    assert unicodedata.normalize("NFC", learner_text) == learner_text


def test_jongseong_h7_has_position_and_exactly_seven_output_categories() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    entries = _entries_for_stage(pack, "H7")
    batchim, *outputs = entries

    assert batchim.category_id == "batchim-position"
    assert batchim.canonical_jamo_or_block == "각"
    assert batchim.pedagogical_jamo_mapping is None
    assert tuple(
        entry.pedagogical_jamo_mapping.display_glyph for entry in outputs
    ) == tuple("ㄱㄴㄷㄹㅁㅂㅇ")
    assert tuple(
        entry.pedagogical_jamo_mapping.canonical_jamo for entry in outputs
    ) == tuple("ᆨᆫᆮᆯᆷᆸᆼ")
    assert {
        entry.pedagogical_jamo_mapping.jamo_position for entry in outputs
    } == {"final"}


def test_jongseong_h8_has_exactly_27_finals_and_11_complex_clusters() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    entries = _entries_for_stage(pack, "H8")
    displays = tuple(
        entry.pedagogical_jamo_mapping.display_glyph for entry in entries
    )
    canonical = tuple(
        entry.pedagogical_jamo_mapping.canonical_jamo for entry in entries
    )

    assert displays == _MODERN_FINAL_DISPLAY_ORDER
    assert len(displays) == len(set(displays)) == 27
    assert canonical == tuple(chr(codepoint) for codepoint in range(0x11A8, 0x11C3))
    assert len(canonical) == len(set(canonical)) == 27
    assert tuple(display for display in displays if display in _COMPLEX_FINAL_DISPLAY_ORDER) == _COMPLEX_FINAL_DISPLAY_ORDER
    assert all(unicodedata.name(value).startswith("HANGUL JONGSEONG ") for value in canonical)


def test_hangul_h9_is_bounded_to_three_orthographic_foundation_concepts() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    entries = _entries_for_stage(pack, "H9")

    assert tuple(entry.category_id for entry in entries) == (
        "morpheme-preserving-spelling",
        "basic-word-spacing",
        "attached-particle-spacing",
    )
    for entry in entries:
        referenced = {
            entry.evidence.target_concept_id,
            *entry.evidence.prerequisite_concept_ids,
            *entry.evidence.observed_concept_ids,
            *entry.active_rule_ids,
        }
        assert all(identifier.startswith("orthography.") for identifier in referenced)
        assert not any(
            identifier.startswith(("grammar.", "lexicon.")) for identifier in referenced
        )


def test_hangul_h10_covers_normalization_keyboard_punctuation_numerals_and_mixed_script() -> None:
    pack = _curriculum().load_korean_hangul_source_pack()
    entries = _entries_for_stage(pack, "H10")

    assert tuple(entry.category_id for entry in entries) == (
        "nfc-nfd-equivalence",
        "keyboard-orientation",
        "punctuation",
        "numerals",
        "bounded-mixed-script",
    )
    assert all(
        unicodedata.normalize("NFC", entry.canonical_jamo_or_block)
        == entry.canonical_jamo_or_block
        for entry in entries
    )


@pytest.mark.parametrize("invalid", [unicodedata.normalize("NFD", "가"), "ㄱ", "ﾡ"])
def test_hangul_h10_rejects_nfd_compatibility_and_halfwidth_machine_values(
    invalid: str,
) -> None:
    api = _curriculum()
    pack = api.load_korean_hangul_source_pack()
    payload = pack.model_dump(mode="json")
    index = next(
        index for index, entry in enumerate(payload["entries"]) if entry["stage_id"] == "H10"
    )
    payload["entries"][index]["canonical_jamo_or_block"] = invalid
    payload["entries"][index]["content_hash"] = _canonical_hash(payload["entries"][index])
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanHangulSourcePack.model_validate(payload)


def test_hangul_complete_has_exact_coverage_hashes_and_strict_recomputation() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()

    assert pack.inventory_status == "complete"
    assert len(pack.entries) == 92
    assert tuple(entry.sequence for entry in pack.entries) == tuple(range(1, 93))
    assert tuple(entry.sort_index for entry in pack.entries) == tuple(range(1, 93))
    for stage_id, required_categories in _HANGUL_STAGE_CATEGORIES.items():
        entries = _entries_for_stage(pack, stage_id)
        assert tuple(entry.category_id for entry in entries) == required_categories
    assert all(entry.content_hash == _canonical_hash(entry.model_dump(mode="json")) for entry in pack.entries)
    assert pack.content_hash == _canonical_hash(pack.model_dump(mode="json"))
    assert set(_all_status_values(pack.model_dump(mode="json"))) == {"needs_review"}

    result = api.validate_korean_foundation_pack(registry=registry, pack=pack)
    assert result.validated_entry_count == 92
    assert result.admitted_target_concept_ids == _expected_concept_ids(
        _HANGUL_STAGE_CATEGORIES
    )
    assert result.known_concept_ids == result.admitted_target_concept_ids


def test_cross_pack_orthography_reuses_completed_h7_h8_registry_identities() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()
    hangul_result = api.validate_korean_foundation_pack(registry=registry, pack=hangul)
    inherited = pronunciation.inherited_orthographic_concept_ids
    shared_coda_ids = {
        entry.evidence.target_concept_id
        for entry in (*_entries_for_stage(hangul, "H7"), *_entries_for_stage(hangul, "H8"))
    }

    assert inherited == hangul_result.known_concept_ids
    assert shared_coda_ids <= set(inherited)
    assert not any(identifier.startswith("phonology.") for identifier in inherited)
    p2_concepts = {
        concept.id: set(concept.prerequisite_ids)
        for concept in registry.concepts
        if concept.id.startswith("phonology.p2.")
    }
    assert p2_concepts
    assert _concept_id("H7", "batchim-position") in p2_concepts[
        _concept_id("P2", "unreleased-coda")
    ]
    assert set(_expected_concept_ids({"H8": _HANGUL_STAGE_CATEGORIES["H8"]})) <= p2_concepts[
        _concept_id("P2", "unreleased-coda")
    ]
    for output in ("kiyeok", "nieun", "tikeut", "rieul", "mieum", "pieup", "ieung"):
        assert _concept_id("H7", f"coda-output-{output}") in p2_concepts[
            _concept_id("P2", f"coda-neutralization-{output}")
        ]

    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pronunciation,
        inherited_known_ids=inherited,
    )
    assert result.validated_entry_count == 47
    assert result.admitted_target_concept_ids == _expected_concept_ids(
        _PRONUNCIATION_STAGE_CATEGORIES
    )
    assert result.known_concept_ids == (
        *inherited,
        *_expected_concept_ids(_PRONUNCIATION_STAGE_CATEGORIES),
    )


@pytest.mark.parametrize("stage_id", ["H0", "H7", "H8", "H9", "H10"])
def test_hangul_complete_mutation_rejects_second_unknown_in_every_remaining_stage(
    stage_id: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    entries = list(pack.entries)
    index = next(index for index, entry in enumerate(entries) if entry.stage_id == stage_id)
    entry = entries[index]
    later_target = entries[index + 1].evidence.target_concept_id
    evidence = entry.evidence.model_copy(
        update={
            "observed_concept_ids": (
                *entry.evidence.observed_concept_ids,
                later_target,
            )
        }
    )
    entries[index] = entry.model_copy(update={"evidence": evidence})
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(registry=registry, pack=mutated)

    assert _reason(exc_info) == "recomputed_unknown_mismatch"


def test_hangul_complete_mutation_rejects_missing_entry_coverage() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    pack = api.load_korean_hangul_source_pack()
    mutated = pack.model_copy(update={"entries": pack.entries[:-1]})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(registry=registry, pack=mutated)

    assert _reason(exc_info) == "coverage_mismatch"


def test_hangul_complete_mutation_rejects_entry_hash_drift() -> None:
    api = _curriculum()
    pack = api.load_korean_hangul_source_pack()
    payload = pack.model_dump(mode="json")
    payload["entries"][-1]["content_hash"] = "0" * 64
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanHangulSourcePack.model_validate(payload)


def _pronunciation_entries_for_stages(
    pack: object,
    stage_ids: tuple[str, ...],
) -> tuple[object, ...]:
    return tuple(
        entry for entry in getattr(pack, "entries") if entry.stage_id in stage_ids
    )


def _pronunciation_nine_field_values(entry: object) -> tuple[str, ...]:
    slots = {
        slot.media_kind: slot.slot_id for slot in getattr(entry, "media_slots")
    }
    return (
        getattr(entry, "spellings"),
        getattr(entry, "sound"),
        slots["letter_audio"],
        getattr(entry, "example_word"),
        slots["word_audio"],
        getattr(entry, "word_translation"),
        getattr(entry, "example_sentence"),
        slots["sentence_audio"],
        getattr(entry, "sentence_translation"),
    )


def _assert_no_compatibility_or_halfwidth_hangul(value: str) -> None:
    assert not any(
        0x3130 <= ord(character) < 0x3190
        or 0xFFA0 <= ord(character) < 0xFFDD
        for character in value
    )


def test_pronunciation_p0_p7_populates_every_atomic_target_in_order() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    stages = tuple(f"P{number}" for number in range(8))
    entries = _pronunciation_entries_for_stages(pack, stages)
    required_categories = tuple(
        category
        for stage_id in stages
        for category in _PRONUNCIATION_STAGE_CATEGORIES[stage_id]
    )
    expected_targets = tuple(
        _concept_id(stage_id, category)
        for stage_id in stages
        for category in _PRONUNCIATION_STAGE_CATEGORIES[stage_id]
    )

    assert len(entries) == len(required_categories) == 31
    assert tuple(entry.sequence for entry in entries) == tuple(range(1, 32))
    assert tuple(entry.item_key for entry in entries) == tuple(
        f"ko-pron-{sequence:04d}" for sequence in range(1, 32)
    )
    assert tuple(entry.category_id for entry in entries) == required_categories
    assert tuple(entry.evidence.target_concept_id for entry in entries) == expected_targets
    assert len(set(expected_targets)) == len(expected_targets)

    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pack,
        inherited_known_ids=tuple(
            entry.evidence.target_concept_id for entry in hangul.entries
        ),
    )
    assert result.admitted_target_concept_ids[:31] == expected_targets


def test_pronunciation_onset_contrast_candidates_are_atomic_without_romanization_authority() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    entries = _entries_for_stage(pack, "P1")

    assert tuple(entry.category_id for entry in entries) == (
        "onset-contrast-pieup",
        "onset-contrast-tikeut",
        "onset-contrast-kiyeok",
        "onset-contrast-cieuc",
        "onset-contrast-sios",
        "onset-hieuh",
    )
    assert tuple(entry.example_word for entry in entries) == (
        "바·빠·파",
        "다·따·타",
        "가·까·카",
        "자·짜·차",
        "사·싸",
        "하",
    )
    serialized = json.dumps(
        [entry.model_dump(mode="json") for entry in entries],
        ensure_ascii=False,
    ).casefold()
    assert "roman" not in serialized
    assert "voiced" not in serialized
    assert "voiceless" not in serialized


def test_pronunciation_batchim_reuses_completed_h7_h8_orthographic_identity() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = _entries_for_stage(pack, "P2")
    concept_by_id = {concept.id: concept for concept in registry.concepts}
    h7_h8_ids = {
        entry.evidence.target_concept_id
        for entry in (
            *_entries_for_stage(hangul, "H7"),
            *_entries_for_stage(hangul, "H8"),
        )
    }

    assert tuple(entry.category_id for entry in entries) == (
        "unreleased-coda",
        "coda-neutralization-kiyeok",
        "coda-neutralization-nieun",
        "coda-neutralization-tikeut",
        "coda-neutralization-rieul",
        "coda-neutralization-mieum",
        "coda-neutralization-pieup",
        "coda-neutralization-ieung",
    )
    assert h7_h8_ids <= set(entries[0].evidence.prerequisite_concept_ids)
    for entry in entries:
        target = concept_by_id[entry.evidence.target_concept_id]
        assert set(target.prerequisite_ids) <= set(
            entry.evidence.prerequisite_concept_ids
        )
        assert set(entry.inherited_orthographic_concept_ids) == set(
            pack.inherited_orthographic_concept_ids
        )
        assert not any(
            concept_id.startswith("phonology.") for concept_id in h7_h8_ids
        )


def test_pronunciation_liaison_tensification_nasalization_aspiration_and_palatalization_seeds_stay_distinct() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    expected = {
        "P3": (("liaison-vowel-initial-morpheme", "옷이", "[오시]"),),
        "P4": (("post-obstruent-tensification", "먹다", "[먹따]"),),
        "P5": (
            ("nasalization-velar", "국물", "[궁물]"),
            ("nasalization-coronal", "받는", "[반는]"),
            ("nasalization-labial", "앞문", "[암문]"),
        ),
        "P6": (
            ("h-aspiration-coda-to-onset", "좋다", "[조타]"),
            ("h-aspiration-onset-from-coda", "입학", "[이팍]"),
        ),
        "P7": (
            ("palatalization-tikeut", "굳이", "[구지]"),
            ("palatalization-thieuth", "같이", "[가치]"),
        ),
    }

    for stage_id, expected_rows in expected.items():
        entries = _entries_for_stage(pack, stage_id)
        assert tuple(
            (
                entry.category_id,
                entry.pronunciation_evidence.canonical_spelling,
                entry.pronunciation_evidence.normative_pronunciation,
            )
            for entry in entries
        ) == expected_rows


def test_pronunciation_p0_p7_keeps_rich_evidence_nine_fields_and_all_human_media_gates_pending() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    entries = _pronunciation_entries_for_stages(
        pack,
        tuple(f"P{number}" for number in range(8)),
    )
    required_roles = {
        "korean-phonetics-specialist",
        "independent-native-speaker",
        "portuguese-reviewer",
        "media-rights-reviewer",
        "audio-playback-reviewer",
    }

    assert len(entries) == 31
    assert pack.learner_field_order == _PRONUNCIATION_FIELD_ORDER
    for entry in entries:
        values = _pronunciation_nine_field_values(entry)
        assert len(values) == len(_PRONUNCIATION_FIELD_ORDER) == 9
        assert all(isinstance(value, str) and value for value in values)
        assert entry.example_word == entry.pronunciation_evidence.canonical_spelling
        assert unicodedata.normalize("NFC", entry.word_translation) == entry.word_translation
        assert (
            unicodedata.normalize("NFC", entry.sentence_translation)
            == entry.sentence_translation
        )
        if entry.pronunciation_evidence.ipa is not None:
            assert unicodedata.normalize("NFC", entry.pronunciation_evidence.ipa) == entry.pronunciation_evidence.ipa
            assert entry.pronunciation_evidence.ipa.startswith("/")
            assert entry.pronunciation_evidence.ipa.endswith("/")
        assert entry.pronunciation_evidence.review_status.value == "needs_review"
        assert entry.register_context
        assert {source.source_id for source in entry.provenance} == {
            "nikl.pronunciation-0002"
        }
        assert {review.status for review in entry.pending_reviews} == {
            "needs_review"
        }
        assert required_roles <= {
            review.required_reviewer_role for review in entry.pending_reviews
        }
        assert {slot.review_status for slot in entry.media_slots} == {
            "needs_review"
        }
        assert tuple(slot.media_kind for slot in entry.media_slots) == (
            "letter_audio",
            "word_audio",
            "sentence_audio",
        )
        for text in (
            entry.spellings,
            entry.sound,
            entry.example_word,
            entry.example_sentence,
            entry.pronunciation_evidence.canonical_spelling,
            entry.pronunciation_evidence.normative_pronunciation,
            entry.pronunciation_evidence.surface_pronunciation,
        ):
            assert unicodedata.normalize("NFC", text) == text
            _assert_no_compatibility_or_halfwidth_hangul(text)


def test_pronunciation_p0_p7_recomputes_one_unknown_and_declares_every_active_non_target_rule() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    inherited = tuple(entry.evidence.target_concept_id for entry in hangul.entries)
    known = set(inherited)

    assert len(pack.entries) >= 31
    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pack,
        inherited_known_ids=inherited,
    )
    assert result.validated_entry_count == len(pack.entries)
    for entry in pack.entries:
        observed = tuple(entry.evidence.observed_concept_ids)
        recomputed_unknown = tuple(
            concept_id for concept_id in observed if concept_id not in known
        )
        assert recomputed_unknown == (entry.evidence.target_concept_id,)
        assert tuple(entry.evidence.unknown_concept_ids) == recomputed_unknown
        active_non_target = set(entry.active_rule_ids) - {
            entry.evidence.target_concept_id
        }
        assert active_non_target <= set(entry.evidence.prerequisite_concept_ids)
        assert active_non_target <= known
        assert active_non_target <= set(observed)
        known.add(entry.evidence.target_concept_id)


@pytest.mark.parametrize("stage_id", [f"P{number}" for number in range(8)])
def test_pronunciation_p0_p7_mutation_rejects_a_second_recomputed_unknown(
    stage_id: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = list(pack.entries)
    index = next(
        index for index, entry in enumerate(entries) if entry.stage_id == stage_id
    )
    entry = entries[index]
    later_target = next(
        concept.id
        for concept in registry.concepts
        if concept.domain == "phonology"
        and concept.id not in {
            candidate.evidence.target_concept_id for candidate in entries[: index + 1]
        }
    )
    evidence = entry.evidence.model_copy(
        update={
            "observed_concept_ids": (
                *entry.evidence.observed_concept_ids,
                later_target,
            )
        }
    )
    entries[index] = entry.model_copy(update={"evidence": evidence})
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=registry,
            pack=mutated,
            inherited_known_ids=tuple(
                hangul_entry.evidence.target_concept_id
                for hangul_entry in hangul.entries
            ),
        )

    assert _reason(exc_info) == "recomputed_unknown_mismatch"


def test_pronunciation_tensification_mutation_rejects_undeclared_active_rule() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = list(pack.entries)
    index = next(index for index, entry in enumerate(entries) if entry.stage_id == "P4")
    entry = entries[index]
    known_active = _concept_id("P3", "liaison-vowel-initial-morpheme")
    evidence = entry.evidence.model_copy(
        update={
            "observed_concept_ids": (
                *entry.evidence.observed_concept_ids,
                known_active,
            )
        }
    )
    entries[index] = entry.model_copy(
        update={
            "evidence": evidence,
            "active_rule_ids": (*entry.active_rule_ids, known_active),
        }
    )
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=registry,
            pack=mutated,
            inherited_known_ids=tuple(
                hangul_entry.evidence.target_concept_id
                for hangul_entry in hangul.entries
            ),
        )

    assert _reason(exc_info) == "active_rule_not_prerequisite"


def test_pronunciation_p8_p13_completes_every_remaining_atomic_target_in_order() -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    expected_targets = _expected_concept_ids(_PRONUNCIATION_STAGE_CATEGORIES)

    assert pack.inventory_status == "complete"
    assert len(pack.entries) == len(expected_targets) == 47
    assert tuple(entry.sequence for entry in pack.entries) == tuple(range(1, 48))
    assert tuple(entry.item_key for entry in pack.entries) == tuple(
        f"ko-pron-{sequence:04d}" for sequence in range(1, 48)
    )
    assert tuple(entry.evidence.target_concept_id for entry in pack.entries) == (
        expected_targets
    )
    for stage_id, required_categories in _PRONUNCIATION_STAGE_CATEGORIES.items():
        assert tuple(
            entry.category_id for entry in _entries_for_stage(pack, stage_id)
        ) == required_categories

    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pack,
        inherited_known_ids=tuple(
            entry.evidence.target_concept_id for entry in hangul.entries
        ),
    )
    assert result.validated_entry_count == 47
    assert result.admitted_target_concept_ids == expected_targets


def test_pronunciation_p8_liquid_processes_and_n_insertion_are_separate_targets() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    entries = _entries_for_stage(pack, "P8")

    assert tuple(
        (
            entry.category_id,
            entry.example_word,
            entry.pronunciation_evidence.normative_pronunciation,
        )
        for entry in entries
    ) == (
        ("liquid-assimilation", "신라", "[실라]"),
        ("rieul-related-process", "설날", "[설랄]"),
        ("n-insertion", "담요", "[담뇨]"),
    )
    assert len({entry.evidence.target_concept_id for entry in entries}) == 3


def test_pronunciation_p9_complex_coda_environments_and_interaction_are_separate() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    entries = {
        entry.category_id: entry for entry in _entries_for_stage(pack, "P9")
    }
    p2_unreleased = _concept_id("P2", "unreleased-coda")
    p3_liaison = _concept_id("P3", "liaison-vowel-initial-morpheme")
    p4_tensification = _concept_id("P4", "post-obstruent-tensification")
    p5_velar = _concept_id("P5", "nasalization-velar")
    before_consonant = _concept_id("P9", "complex-coda-before-consonant")

    assert tuple(entries) == _PRONUNCIATION_STAGE_CATEGORIES["P9"]
    assert (
        entries["complex-coda-before-consonant"].example_word,
        entries[
            "complex-coda-before-consonant"
        ].pronunciation_evidence.normative_pronunciation,
    ) == ("읽다", "[익따]")
    assert (
        entries["complex-coda-before-vowel"].example_word,
        entries[
            "complex-coda-before-vowel"
        ].pronunciation_evidence.normative_pronunciation,
    ) == ("읽어", "[일거]")
    assert (
        entries["complex-coda-rule-interaction"].example_word,
        entries[
            "complex-coda-rule-interaction"
        ].pronunciation_evidence.normative_pronunciation,
    ) == ("읽는", "[잉는]")
    assert {p2_unreleased, p4_tensification} <= set(
        entries["complex-coda-before-consonant"].active_rule_ids
    )
    assert p3_liaison in entries["complex-coda-before-vowel"].active_rule_ids
    assert {p2_unreleased, p5_velar, before_consonant} <= set(
        entries["complex-coda-rule-interaction"].active_rule_ids
    )


def test_pronunciation_p10_contains_each_locked_regular_contraction_family() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    entries = _entries_for_stage(pack, "P10")

    assert tuple((entry.spellings, entry.example_word) for entry in entries) == (
        ("보아요 → 봐요", "봐요"),
        ("주어요 → 줘요", "줘요"),
        ("되어요 → 돼요", "돼요"),
        ("하여요 → 해요", "해요"),
    )
    assert tuple(entry.category_id for entry in entries) == (
        "contraction-boa-bwa",
        "contraction-jueo-jwo",
        "contraction-doeeo-dwae",
        "contraction-hayeo-hae",
    )


def test_pronunciation_p11_p13_keep_unavailable_specialist_auditory_portuguese_and_media_truth_pending() -> None:
    pack = _curriculum().load_korean_pronunciation_source_pack()
    p11 = _entries_for_stage(pack, "P11")
    p12 = _entries_for_stage(pack, "P12")
    p13 = _entries_for_stage(pack, "P13")
    review_pending = (*p11, *p12, *p13)

    assert len(p11) == 1
    assert p11[0].register_context == "optional-colloquial-needs-review"
    assert len(p12) == 4
    assert tuple(entry.category_id for entry in p12) == (
        "phrase-accent",
        "focus",
        "boundary-intonation",
        "rate-conditioned-effects",
    )
    assert len({entry.register_context for entry in p12}) == 4
    assert all("auditory-needs-review" in entry.register_context for entry in p12)
    assert len(p13) == 1
    assert p13[0].register_context == "ordering-atomization-needs-review"
    assert p13[0].example_word == "읽는"
    assert p13[0].pronunciation_evidence.normative_pronunciation == "[잉는]"
    assert {
        _concept_id("P2", "unreleased-coda"),
        _concept_id("P5", "nasalization-velar"),
        _concept_id("P9", "complex-coda-before-consonant"),
    } <= set(p13[0].active_rule_ids)

    for entry in review_pending:
        assert entry.sound != "needs_review"
        assert entry.word_translation != "needs_review"
        assert entry.example_sentence != "needs_review"
        assert entry.sentence_translation != "needs_review"
        assert entry.pronunciation_evidence.surface_pronunciation != "needs_review"
        if entry.pronunciation_evidence.ipa is not None:
            assert entry.pronunciation_evidence.ipa.startswith("/")
            assert entry.pronunciation_evidence.ipa.endswith("/")
        assert entry.pronunciation_evidence.review_status.value == "needs_review"
        assert {review.status for review in entry.pending_reviews} == {
            "needs_review"
        }
        assert {slot.review_status for slot in entry.media_slots} == {
            "needs_review"
        }
        assert "specialist-atomization-review-required" in {
            review.reason_code for review in entry.pending_reviews
        }


def test_pronunciation_full_cross_pack_hash_identity_nine_field_and_pending_audit() -> None:
    api = _curriculum()
    registry_path = Path("data/korean_foundations/korean-concepts-v1.json")
    hangul_path = Path("data/korean_foundations/hangul-v1.json")
    pronunciation_path = Path(
        "data/korean_foundations/pronunciation-i-plus-1-v1.json"
    )
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pronunciation = api.load_korean_pronunciation_source_pack()
    inherited = tuple(entry.evidence.target_concept_id for entry in hangul.entries)

    assert sha256(registry_path.read_bytes()).hexdigest() == (
        "79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625"
    )
    assert sha256(hangul_path.read_bytes()).hexdigest() == (
        "80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1"
    )
    assert pronunciation_path.stat().st_size <= api.KOREAN_MANIFEST_MAX_BYTES
    assert registry.content_hash == _canonical_hash(registry.model_dump(mode="json"))
    assert hangul.content_hash == _canonical_hash(hangul.model_dump(mode="json"))
    assert pronunciation.content_hash == _canonical_hash(
        pronunciation.model_dump(mode="json")
    )
    assert all(
        entry.content_hash == _canonical_hash(entry.model_dump(mode="json"))
        for entry in pronunciation.entries
    )
    assert pronunciation.inherited_orthographic_concept_ids == inherited
    assert set(inherited).isdisjoint(
        entry.evidence.target_concept_id for entry in pronunciation.entries
    )
    assert len(
        {entry.evidence.target_concept_id for entry in pronunciation.entries}
    ) == 47
    assert all(
        len(_pronunciation_nine_field_values(entry)) == 9
        for entry in pronunciation.entries
    )
    assert set(_all_status_values(pronunciation.model_dump(mode="json"))) == {
        "needs_review"
    }

    result = api.validate_korean_foundation_pack(
        registry=registry,
        pack=pronunciation,
        inherited_known_ids=inherited,
    )
    assert result.known_concept_ids == (
        *inherited,
        *_expected_concept_ids(_PRONUNCIATION_STAGE_CATEGORIES),
    )


@pytest.mark.parametrize("mutation", ["cycle", "forward_edge"])
def test_pronunciation_full_cross_pack_mutation_rejects_registry_cycle_or_forward_edge(
    mutation: str,
) -> None:
    api = _curriculum()
    payload = api.load_korean_concept_registry().model_dump(mode="json")
    concepts = {concept["id"]: concept for concept in payload["concepts"]}
    if mutation == "cycle":
        concepts[_concept_id("P0", "syllable-timing")]["prerequisite_ids"].append(
            _concept_id("P0", "vowel-quality")
        )
    else:
        concepts[_concept_id("P10", "contraction-boa-bwa")][
            "prerequisite_ids"
        ].append(_concept_id("P12", "focus"))
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanConceptRegistry.model_validate(payload)


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        ("omitted_category", "coverage_mismatch"),
        ("forged_unknown", "serialized_unknown_mismatch"),
        ("missing_active_prerequisite", "active_rule_not_prerequisite"),
        ("forward_prerequisite", "unknown_prerequisite"),
        ("fused_target", "recomputed_unknown_mismatch"),
    ],
)
def test_pronunciation_full_cross_pack_mutation_rejects_false_curriculum_evidence(
    mutation: str,
    expected_reason: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = list(pack.entries)
    if mutation == "omitted_category":
        entries.pop()
    elif mutation == "forged_unknown":
        entry = entries[-1]
        evidence = entry.evidence.model_copy(
            update={
                "unknown_concept_ids": (
                    _concept_id("P12", "rate-conditioned-effects"),
                )
            }
        )
        entries[-1] = entry.model_copy(update={"evidence": evidence})
    elif mutation == "missing_active_prerequisite":
        index = next(
            index
            for index, entry in enumerate(entries)
            if entry.category_id == "complex-coda-before-consonant"
        )
        entry = entries[index]
        missing = _concept_id("P4", "post-obstruent-tensification")
        evidence = entry.evidence.model_copy(
            update={
                "prerequisite_concept_ids": tuple(
                    concept_id
                    for concept_id in entry.evidence.prerequisite_concept_ids
                    if concept_id != missing
                )
            }
        )
        entries[index] = entry.model_copy(update={"evidence": evidence})
    elif mutation == "forward_prerequisite":
        index = next(
            index for index, entry in enumerate(entries) if entry.stage_id == "P8"
        )
        entry = entries[index]
        future = _concept_id("P12", "focus")
        evidence = entry.evidence.model_copy(
            update={
                "prerequisite_concept_ids": (
                    *entry.evidence.prerequisite_concept_ids,
                    future,
                ),
                "observed_concept_ids": (
                    *entry.evidence.observed_concept_ids,
                    future,
                ),
            }
        )
        entries[index] = entry.model_copy(update={"evidence": evidence})
    else:
        index = next(
            index for index, entry in enumerate(entries) if entry.stage_id == "P8"
        )
        entry = entries[index]
        future = _concept_id("P12", "focus")
        evidence = entry.evidence.model_copy(
            update={
                "observed_concept_ids": (
                    *entry.evidence.observed_concept_ids,
                    future,
                )
            }
        )
        entries[index] = entry.model_copy(update={"evidence": evidence})
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=registry,
            pack=mutated,
            inherited_known_ids=tuple(
                entry.evidence.target_concept_id for entry in hangul.entries
            ),
        )

    assert _reason(exc_info) == expected_reason


def test_pronunciation_full_cross_pack_mutation_rejects_drifted_entry_hash() -> None:
    api = _curriculum()
    payload = api.load_korean_pronunciation_source_pack().model_dump(mode="json")
    payload["entries"][-1]["content_hash"] = "0" * 64
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanPronunciationSourcePack.model_validate(payload)


def test_pronunciation_full_cross_pack_mutation_rejects_unsupported_script() -> None:
    api = _curriculum()
    payload = api.load_korean_pronunciation_source_pack().model_dump(mode="json")
    entry = payload["entries"][0]
    entry["spellings"] = "かな"
    entry["sound"] = "[かな]"
    entry["example_word"] = "かな"
    entry["pronunciation_evidence"]["canonical_spelling"] = "かな"
    entry["pronunciation_evidence"]["normative_pronunciation"] = "[かな]"
    entry["pronunciation_evidence"]["surface_pronunciation"] = "[かな]"
    entry["content_hash"] = _canonical_hash(entry)
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanPronunciationSourcePack.model_validate(payload)


def test_pronunciation_full_cross_pack_mutation_rejects_premature_source_approval() -> None:
    api = _curriculum()
    payload = api.load_korean_pronunciation_source_pack().model_dump(mode="json")
    entry = payload["entries"][0]
    entry["pronunciation_evidence"]["review_status"] = "approved"
    entry["content_hash"] = _canonical_hash(entry)
    payload["content_hash"] = _canonical_hash(payload)

    with pytest.raises(ValidationError):
        api.KoreanPronunciationSourcePack.model_validate(payload)


@pytest.mark.parametrize("stage_id", [f"P{number}" for number in range(8, 14)])
def test_pronunciation_p8_p13_second_pass_mutation_rejects_false_unknown_evidence(
    stage_id: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = list(pack.entries)
    index = next(
        index for index, entry in enumerate(entries) if entry.stage_id == stage_id
    )
    entry = entries[index]
    if stage_id == "P13":
        evidence = entry.evidence.model_copy(
            update={
                "unknown_concept_ids": (
                    _concept_id("P12", "rate-conditioned-effects"),
                )
            }
        )
        expected = "serialized_unknown_mismatch"
    else:
        later_unknown = next(
            concept.id
            for concept in registry.concepts
            if concept.domain == "phonology"
            and concept.id
            not in {
                candidate.evidence.target_concept_id
                for candidate in entries[: index + 1]
            }
        )
        evidence = entry.evidence.model_copy(
            update={
                "observed_concept_ids": (
                    *entry.evidence.observed_concept_ids,
                    later_unknown,
                )
            }
        )
        expected = "recomputed_unknown_mismatch"
    entries[index] = entry.model_copy(update={"evidence": evidence})
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=registry,
            pack=mutated,
            inherited_known_ids=tuple(
                entry.evidence.target_concept_id for entry in hangul.entries
            ),
        )

    assert _reason(exc_info) == expected


@pytest.mark.parametrize("stage_id", [f"P{number}" for number in range(14)])
def test_pronunciation_every_stage_rejects_drifted_inherited_orthography(
    stage_id: str,
) -> None:
    api = _curriculum()
    registry = api.load_korean_concept_registry()
    hangul = api.load_korean_hangul_source_pack()
    pack = api.load_korean_pronunciation_source_pack()
    entries = list(pack.entries)
    index = next(
        index for index, entry in enumerate(entries) if entry.stage_id == stage_id
    )
    entry = entries[index]
    entries[index] = entry.model_copy(
        update={
            "inherited_orthographic_concept_ids": entry.inherited_orthographic_concept_ids[
                :-1
            ]
        }
    )
    mutated = pack.model_copy(update={"entries": tuple(entries)})

    with pytest.raises(api.KoreanCurriculumError) as exc_info:
        api.validate_korean_foundation_pack(
            registry=registry,
            pack=mutated,
            inherited_known_ids=tuple(
                entry.evidence.target_concept_id for entry in hangul.entries
            ),
        )

    assert _reason(exc_info) == "inherited_concepts_mismatch"
