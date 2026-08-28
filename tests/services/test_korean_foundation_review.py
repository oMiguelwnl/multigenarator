"""Independent, hash-bound review gates for Korean foundation candidates."""

from __future__ import annotations

import hashlib
import json
from importlib import import_module, util
import inspect
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace

import pytest
from pydantic import ValidationError


def _review() -> ModuleType:
    assert util.find_spec("multilang.services.korean_foundation_review") is not None, (
        "the Korean foundation review service must exist"
    )
    return import_module("multilang.services.korean_foundation_review")


def _curriculum() -> ModuleType:
    return import_module("multilang.services.korean_curriculum")


def _media() -> ModuleType:
    return import_module("multilang.services.korean_foundation_media")


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    reason_code = getattr(exc_info.value, "reason_code")
    return getattr(reason_code, "value", reason_code)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PHASE_ROOT = (
    Path(__file__).resolve().parents[2]
    / ".planning"
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
)


def _approved_gate(api: ModuleType, record: object, gate_name: str) -> object:
    pending = next(
        gate for gate in getattr(record, "gates") if gate.gate_name == gate_name
    )
    payload = pending.model_dump(mode="json")
    payload.update(
        {
            "status": "approved",
            "reason_code": None,
            "reviewer_id": f"test-reviewer-{gate_name}",
            "reviewer_role": api.KOREAN_FOUNDATION_GATE_REVIEWER_ROLES[
                gate_name
            ],
            "reviewed_at": "2026-08-05T00:00:00Z",
            "source_pack_version": getattr(record, "source_pack_version"),
            "source_content_sha256": getattr(record, "source_content_sha256"),
            "reviewed_evidence_sha256": "e" * 64,
        }
    )
    return api.KoreanFoundationReviewGate.model_validate(payload)


def test_review_public_contract_has_fixed_no_path_production_apis() -> None:
    api = _review()

    expected = {
        "DEFAULT_KOREAN_FOUNDATION_CURATION_PATH",
        "KOREAN_FOUNDATION_GATE_REVIEWER_ROLES",
        "KoreanFoundationCurationManifest",
        "KoreanFoundationCurationRecord",
        "KoreanFoundationReviewError",
        "KoreanFoundationReviewGate",
        "KoreanFoundationReviewReasonCode",
        "KoreanFoundationReviewStatus",
        "KoreanFoundationReviewSummary",
        "assert_korean_foundation_review_ready",
        "load_korean_v1_foundation_curation",
        "load_pending_korean_foundation_curation",
        "summarize_korean_foundation_review",
        "update_korean_foundation_review_gate",
        "validate_korean_foundation_curation",
    }
    assert set(api.__all__) == expected
    assert tuple(
        inspect.signature(api.load_pending_korean_foundation_curation).parameters
    ) == ()
    assert tuple(
        inspect.signature(api.load_korean_v1_foundation_curation).parameters
    ) == ()
    assert tuple(inspect.signature(api.assert_korean_foundation_review_ready).parameters) == (
        "snapshot",
    )
    for function_name in (
        "load_pending_korean_foundation_curation",
        "load_korean_v1_foundation_curation",
        "assert_korean_foundation_review_ready",
    ):
        source = inspect.getsource(getattr(api, function_name)).casefold()
        assert "http://" not in source
        assert "https://" not in source
        assert "requests" not in source


def test_review_and_media_default_to_exact_v2_bundle_with_all_gates_pending() -> None:
    review_api = _review()
    media_api = _media()
    curriculum = _curriculum()

    bundle = curriculum.load_korean_current_foundation_bundle()
    assert review_api.DEFAULT_KOREAN_FOUNDATION_CURATION_PATH == (
        curriculum.CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH
    )
    assert media_api.DEFAULT_KOREAN_FOUNDATION_MEDIA_MANIFEST_PATH == (
        curriculum.CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH
    )

    curation_load_error = None
    try:
        curation = review_api.load_pending_korean_foundation_curation()
    except review_api.KoreanFoundationReviewError as exc:
        curation = None
        curation_load_error = getattr(exc.reason_code, "value", exc.reason_code)
    media_load_error = None
    try:
        media = media_api.load_pending_korean_foundation_media_manifest()
    except media_api.KoreanFoundationMediaError as exc:
        media = None
        media_load_error = getattr(exc.reason_code, "value", exc.reason_code)

    assert curation_load_error is None
    assert media_load_error is None
    assert curation is not None
    assert media is not None

    bundle_root = Path(bundle.source_root)
    assert bundle.source_kind == "current-candidate"
    assert bundle.bundle_sha256 == (
        "36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0"
    )
    assert bundle.bundle_manifest_sha256 == (
        "2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40"
    )
    assert bundle.member_file_sha256["korean-foundations-v2-curation.json"] == (
        "faa233cdc67f99c28c3f203e1b206f4ad4f631bc34b8e2fbb970db336f1157db"
    )
    assert bundle.member_file_sha256["korean-foundations-v2-media.json"] == (
        "e21c7a11006cf70a0559ec7fff7279b466097cf3bbc1fa092cee84e7b963e938"
    )
    assert _sha256_file(bundle_root / "korean-foundations-v2-curation.json") == (
        "faa233cdc67f99c28c3f203e1b206f4ad4f631bc34b8e2fbb970db336f1157db"
    )
    assert _sha256_file(bundle_root / "korean-foundations-v2-media.json") == (
        "e21c7a11006cf70a0559ec7fff7279b466097cf3bbc1fa092cee84e7b963e938"
    )
    assert _sha256_file(PHASE_ROOT / "31-CURRICULUM-REVIEW.md") == (
        "df52d78f2bcd3a89e9589ea68d645df02841a2f9017394d14c833cb7580b36cc"
    )
    assert _sha256_file(PHASE_ROOT / "31-AUDIO-PLAYBACK-REVIEW.md") == (
        "4e28149921c9602c78f1e15633923b55eaf572993fce506651d6d474acf73035"
    )

    assert curation.manifest_version == "korean-foundations-v2-curation"
    assert curation.hangul_source_pack_version == bundle.hangul.source_pack_version
    assert curation.pronunciation_source_pack_version == (
        bundle.pronunciation.source_pack_version
    )
    assert curation.hangul_source_pack_sha256 == bundle.hangul.content_hash
    assert curation.pronunciation_source_pack_sha256 == (
        bundle.pronunciation.content_hash
    )
    assert curation.content_hash == (
        "08874c6f4c64240d79cbdb982c1aa0d8a886749bc8100da41036b7c1b8ba9b22"
    )
    assert len(curation.records) == 139
    assert sum(record.family == "hangul" for record in curation.records) == 92
    assert sum(record.family == "pronunciation" for record in curation.records) == 47
    assert sum(len(record.gates) for record in curation.records) == 973
    assert {record.source_pack_version for record in curation.records} == {
        "hangul-v2",
        "pronunciation-i-plus-1-v2",
    }
    assert {
        gate.status for record in curation.records for gate in record.gates
    } == {"needs_review"}
    assert all(
        gate.reviewer_id is None
        and gate.reviewer_role is None
        and gate.reviewed_at is None
        and gate.reviewed_evidence_sha256 is None
        for record in curation.records
        for gate in record.gates
    )

    assert media.manifest_version == "korean-foundations-v2-media"
    assert media.hangul_source_pack_version == bundle.hangul.source_pack_version
    assert media.pronunciation_source_pack_version == (
        bundle.pronunciation.source_pack_version
    )
    assert media.hangul_source_pack_sha256 == bundle.hangul.content_hash
    assert media.pronunciation_source_pack_sha256 == bundle.pronunciation.content_hash
    assert media.content_hash == (
        "8d860b5e41738d2322dc63eb220eb23de66f4b68b4ff1f9e3dd8979e90b5b55a"
    )
    assert len(media.slots) == 509
    assert sum(slot.family == "hangul" for slot in media.slots) == 368
    assert sum(slot.family == "pronunciation" for slot in media.slots) == 141
    assert sum(slot.required for slot in media.slots) == 325
    assert {slot.status for slot in media.slots} == {"needs_review"}
    assert all(
        slot.reason_code == "media-evidence-required"
        and slot.artifact_sha256 is None
        and slot.reviewed_artifact_sha256 is None
        and slot.review_receipts == ()
        for slot in media.slots
    )

    summary = review_api.summarize_korean_foundation_review(curation)
    assert summary.learner_ready_records == 0
    assert summary.blocked_records == 139
    review_snapshot = SimpleNamespace(
        concept_registry=bundle.registry,
        hangul_source_pack=bundle.hangul,
        pronunciation_source_pack=bundle.pronunciation,
        curation_manifest=curation,
    )
    with pytest.raises(review_api.KoreanFoundationReviewError) as review_exc:
        review_api.assert_korean_foundation_review_ready(review_snapshot)
    assert _reason(review_exc) == "candidate_manifest_not_active"

    media_snapshot = SimpleNamespace(
        concept_registry=bundle.registry,
        hangul_source_pack=bundle.hangul,
        pronunciation_source_pack=bundle.pronunciation,
        snapshot_root=bundle_root,
        media_root=bundle_root / "media",
        media_manifest_bytes=(
            json.dumps(media.model_dump(mode="json"), ensure_ascii=False) + "\n"
        ).encode("utf-8"),
        media_members=(),
    )
    with pytest.raises(media_api.KoreanFoundationMediaError) as media_exc:
        media_api.assert_korean_foundation_media_ready(media_snapshot)
    assert _reason(media_exc) == "candidate_manifest_not_active"

    history_curation = review_api.load_korean_v1_foundation_curation()
    history_media = media_api.load_korean_v1_foundation_media_manifest()
    assert history_curation.manifest_version == "korean-foundations-v1-curation"
    assert history_media.manifest_version == "korean-foundations-v1-media"
    assert history_curation.hangul_source_pack_version == "hangul-v1"
    assert history_media.pronunciation_source_pack_version == (
        "pronunciation-i-plus-1-v1"
    )


@pytest.mark.parametrize("status", ["needs_review", "rejected"])
def test_blocking_gate_requires_its_controlled_actionable_reason(status: str) -> None:
    api = _review()

    with pytest.raises(ValidationError):
        api.KoreanFoundationReviewGate(
            gate_name="source_content",
            status=status,
            reason_code=None,
            scope_ids=("source-claim",),
        )
    with pytest.raises(ValidationError):
        api.KoreanFoundationReviewGate(
            gate_name="source_content",
            status=status,
            reason_code="free-form-reviewer-note",
            scope_ids=("source-claim",),
        )


def test_approved_gate_requires_exact_identity_role_time_version_and_hashes() -> None:
    api = _review()
    base = {
        "gate_name": "korean_phonetics",
        "status": "approved",
        "reason_code": None,
        "scope_ids": ("normative-pronunciation",),
        "reviewer_id": "test-phonetics-reviewer",
        "reviewer_role": "korean-phonetics-specialist",
        "reviewed_at": "2026-08-05T00:00:00Z",
        "source_pack_version": "pronunciation-i-plus-1-v1",
        "source_content_sha256": "a" * 64,
        "reviewed_evidence_sha256": "b" * 64,
    }

    gate = api.KoreanFoundationReviewGate(**base)
    assert gate.status == "approved"
    for field_name in (
        "reviewer_id",
        "reviewer_role",
        "reviewed_at",
        "source_pack_version",
        "source_content_sha256",
        "reviewed_evidence_sha256",
    ):
        payload = dict(base)
        payload[field_name] = None
        with pytest.raises(ValidationError):
            api.KoreanFoundationReviewGate(**payload)

    for field_name, invalid_value in (
        ("reviewer_role", "audio-playback-reviewer"),
        ("reviewed_at", "2026-08-05"),
        ("source_content_sha256", "A" * 64),
        ("reviewed_evidence_sha256", "not-a-hash"),
    ):
        payload = dict(base)
        payload[field_name] = invalid_value
        with pytest.raises(ValidationError):
            api.KoreanFoundationReviewGate(**payload)


def test_committed_candidate_is_complete_aligned_pending_and_non_ready() -> None:
    api = _review()
    curriculum = _curriculum()
    registry = curriculum.load_korean_concept_registry()
    hangul = curriculum.load_korean_hangul_source_pack()
    pronunciation = curriculum.load_korean_pronunciation_source_pack()

    manifest = api.load_pending_korean_foundation_curation()
    api.validate_korean_foundation_curation(
        manifest,
        registry=registry,
        hangul_pack=hangul,
        pronunciation_pack=pronunciation,
    )

    expected_sources = (*hangul.entries, *pronunciation.entries)
    assert manifest.candidate_only is True
    assert len(manifest.records) == 139
    assert tuple(record.item_key for record in manifest.records) == tuple(
        entry.item_key for entry in expected_sources
    )
    assert tuple(record.source_content_sha256 for record in manifest.records) == tuple(
        entry.content_hash for entry in expected_sources
    )

    hangul_gate_names = {
        "source_content",
        "curriculum_atomicity",
        "korean_orthography",
        "portuguese",
        "media_license",
        "media_integrity",
        "audio_playback",
    }
    pronunciation_gate_names = {
        "source_content",
        "curriculum_atomicity",
        "korean_phonetics",
        "portuguese",
        "media_license",
        "media_integrity",
        "audio_playback",
    }
    for record in manifest.records:
        expected_names = (
            hangul_gate_names
            if record.family == "hangul"
            else pronunciation_gate_names
        )
        assert {gate.gate_name for gate in record.gates} == expected_names
        assert {gate.status for gate in record.gates} == {"needs_review"}
        assert all(gate.reason_code is not None for gate in record.gates)
        assert all(gate.reviewer_id is None for gate in record.gates)
        assert all(gate.reviewer_role is None for gate in record.gates)
        assert all(gate.reviewed_at is None for gate in record.gates)

    summary = api.summarize_korean_foundation_review(manifest)
    assert summary.total_records == 139
    assert summary.learner_ready_records == 0
    assert summary.blocked_records == 139
    assert summary.family_counts == {"hangul": 92, "pronunciation": 47}
    assert all(
        counts["approved"] == 0 and counts["rejected"] == 0
        for counts in summary.gate_counts.values()
    )


def test_source_or_curriculum_invalidity_precedes_approved_gate_state() -> None:
    api = _review()
    curriculum = _curriculum()
    registry = curriculum.load_korean_concept_registry()
    hangul = curriculum.load_korean_hangul_source_pack()
    pronunciation = curriculum.load_korean_pronunciation_source_pack()
    manifest = api.load_pending_korean_foundation_curation()

    first = hangul.entries[0]
    forged_evidence = first.evidence.model_copy(
        update={"unknown_concept_ids": ("orthography.block.unit",)}
    )
    forged_entry = first.model_copy(update={"evidence": forged_evidence})
    forged_hangul = hangul.model_copy(
        update={"entries": (forged_entry, *hangul.entries[1:])}
    )
    with pytest.raises(api.KoreanFoundationReviewError) as exc_info:
        api.validate_korean_foundation_curation(
            manifest,
            registry=registry,
            hangul_pack=forged_hangul,
            pronunciation_pack=pronunciation,
        )
    assert _reason(exc_info) == "source_invalid"
    assert str(exc_info.value) == "source_invalid"


@pytest.mark.parametrize(
    ("field_name", "value", "expected_reason"),
    [
        ("source_pack_version", "hangul-v1", "source_identity_mismatch"),
        ("source_content_sha256", "f" * 64, "source_identity_mismatch"),
    ],
)
def test_copied_source_version_or_hash_drift_blocks_content_free(
    field_name: str,
    value: str,
    expected_reason: str,
) -> None:
    api = _review()
    curriculum = _curriculum()
    manifest = api.load_pending_korean_foundation_curation()
    changed_record = manifest.records[0].model_copy(update={field_name: value})
    changed_manifest = manifest.model_copy(
        update={"records": (changed_record, *manifest.records[1:])}
    )

    with pytest.raises(api.KoreanFoundationReviewError) as exc_info:
        api.validate_korean_foundation_curation(
            changed_manifest,
            registry=curriculum.load_korean_concept_registry(),
            hangul_pack=curriculum.load_korean_hangul_source_pack(),
            pronunciation_pack=curriculum.load_korean_pronunciation_source_pack(),
        )
    assert _reason(exc_info) == expected_reason
    assert value not in str(exc_info.value)


def test_approved_gate_update_is_isolated_hash_bound_and_force_protected() -> None:
    api = _review()
    manifest = api.load_pending_korean_foundation_curation()
    record = manifest.records[0]
    approved = _approved_gate(api, record, "source_content")

    updated = api.update_korean_foundation_review_gate(
        manifest,
        item_key=record.item_key,
        gate_name="source_content",
        gate=approved,
    )
    updated_record = updated.records[0]
    assert updated.content_hash != manifest.content_hash
    assert next(
        gate for gate in updated_record.gates if gate.gate_name == "source_content"
    ).status == "approved"
    assert tuple(
        gate for gate in updated_record.gates if gate.gate_name != "source_content"
    ) == tuple(
        gate for gate in record.gates if gate.gate_name != "source_content"
    )

    rejected_payload = approved.model_dump(mode="json")
    rejected_payload.update(
        {
            "status": "rejected",
            "reason_code": "source-content-rejected",
            "reviewer_id": None,
            "reviewer_role": None,
            "reviewed_at": None,
            "source_pack_version": None,
            "source_content_sha256": None,
            "reviewed_evidence_sha256": None,
        }
    )
    rejected = api.KoreanFoundationReviewGate.model_validate(rejected_payload)
    with pytest.raises(api.KoreanFoundationReviewError) as exc_info:
        api.update_korean_foundation_review_gate(
            updated,
            item_key=record.item_key,
            gate_name="source_content",
            gate=rejected,
        )
    assert _reason(exc_info) == "approved_gate_overwrite_requires_force"

    forced = api.update_korean_foundation_review_gate(
        updated,
        item_key=record.item_key,
        gate_name="source_content",
        gate=rejected,
        force=True,
    )
    assert next(
        gate
        for gate in forced.records[0].gates
        if gate.gate_name == "source_content"
    ).status == "rejected"


def test_gate_binding_drift_and_candidate_state_can_never_be_ready() -> None:
    api = _review()
    curriculum = _curriculum()
    manifest = api.load_pending_korean_foundation_curation()
    record = manifest.records[0]
    approved = _approved_gate(api, record, "source_content")
    forged_payload = approved.model_dump(mode="json")
    forged_payload["source_content_sha256"] = "0" * 64
    forged_gate = api.KoreanFoundationReviewGate.model_validate(forged_payload)
    forged_record = record.model_copy(
        update={
            "gates": (
                forged_gate,
                *(gate for gate in record.gates if gate.gate_name != "source_content"),
            )
        }
    )
    forged_manifest = manifest.model_copy(
        update={"records": (forged_record, *manifest.records[1:])}
    )

    with pytest.raises(api.KoreanFoundationReviewError) as exc_info:
        api.validate_korean_foundation_curation(
            forged_manifest,
            registry=curriculum.load_korean_concept_registry(),
            hangul_pack=curriculum.load_korean_hangul_source_pack(),
            pronunciation_pack=curriculum.load_korean_pronunciation_source_pack(),
        )
    assert _reason(exc_info) == "gate_binding_mismatch"

    class CandidateSnapshot:
        concept_registry = curriculum.load_korean_concept_registry()
        hangul_source_pack = curriculum.load_korean_hangul_source_pack()
        pronunciation_source_pack = curriculum.load_korean_pronunciation_source_pack()
        curation_manifest = manifest

    with pytest.raises(api.KoreanFoundationReviewError) as exc_info:
        api.assert_korean_foundation_review_ready(CandidateSnapshot())
    assert _reason(exc_info) == "candidate_manifest_not_active"
    diagnostic = str(exc_info.value)
    assert "아기" not in diagnostic
    assert "C:\\" not in diagnostic


def test_ai_review_passed_is_explicit_and_cannot_populate_human_reviewer_fields() -> None:
    api = _review()
    pending = api.load_pending_korean_foundation_curation().records[0].gates[0]
    payload = pending.model_dump(mode="json")
    payload.update(
        status="ai_review_passed",
        reason_code=None,
        reviewed_at="2026-08-27T15:00:00Z",
        source_pack_version="hangul-v2",
        source_content_sha256="a" * 64,
        reviewed_evidence_sha256="b" * 64,
    )
    gate = api.KoreanFoundationReviewGate.model_validate(payload)
    assert gate.status == "ai_review_passed"
    assert gate.reviewer_id is None
    assert gate.reviewer_role is None

    for field_name, value in (
        ("reviewer_id", "ai-agent"),
        ("reviewer_role", "korean-foundation-content-reviewer"),
    ):
        forged = dict(payload)
        forged[field_name] = value
        with pytest.raises(ValidationError):
            api.KoreanFoundationReviewGate.model_validate(forged)
