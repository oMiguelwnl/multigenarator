import importlib
import json
import subprocess
import sys
import unicodedata
from hashlib import sha256
from importlib.util import find_spec
from pathlib import Path

import pytest
from pydantic import ValidationError

from multilang.services.korean_curriculum import (
    korean_canonical_json_sha256,
    load_korean_hangul_source_pack,
    load_korean_pronunciation_source_pack,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURATION_SCRIPT = PROJECT_ROOT / "scripts/build_korean_foundation_candidates.py"
HANGUL_SOURCE = PROJECT_ROOT / "data/korean_foundations/hangul-v1.json"
PRONUNCIATION_SOURCE = (
    PROJECT_ROOT / "data/korean_foundations/pronunciation-i-plus-1-v1.json"
)
BATCH_STAGES = {
    "hangul-h0-h3": ("H0", "H1", "H2", "H3"),
    "hangul-h4-h7": ("H4", "H5", "H6", "H7"),
    "hangul-h8-h10": ("H8", "H9", "H10"),
    "pronunciation-p0-p4": ("P0", "P1", "P2", "P3", "P4"),
    "pronunciation-p5-p9": ("P5", "P6", "P7", "P8", "P9"),
    "pronunciation-p10-p13": ("P10", "P11", "P12", "P13"),
}


def _content_hash(payload: dict[str, object]) -> str:
    hash_payload = dict(payload)
    hash_payload.pop("content_hash", None)
    return korean_canonical_json_sha256(hash_payload)


def _source_payload(family: str) -> dict[str, object]:
    if family == "hangul":
        pack = load_korean_hangul_source_pack()
        source = HANGUL_SOURCE
    else:
        pack = load_korean_pronunciation_source_pack()
        source = PRONUNCIATION_SOURCE
    return {
        "family": family,
        "source_file_name": source.name,
        "source_file_sha256": sha256(source.read_bytes()).hexdigest(),
        "source_pack_version": pack.source_pack_version,
        "source_pack_content_hash": pack.content_hash,
        "registry_version": pack.registry_version,
        "registry_content_hash": pack.registry_content_hash,
    }


def _hangul_batch_payload() -> dict[str, object]:
    return _batch_payload("hangul-h0-h3")


def _batch_payload(batch_id: str) -> dict[str, object]:
    stages = BATCH_STAGES[batch_id]
    family = "hangul" if batch_id.startswith("hangul-") else "pronunciation"
    pack = (
        load_korean_hangul_source_pack()
        if family == "hangul"
        else load_korean_pronunciation_source_pack()
    )
    records: list[dict[str, object]] = []
    for entry in pack.entries:
        if entry.stage_id not in stages:
            continue
        grounding = [entry.provenance[0].source_id]
        if family == "hangul":
            proposal_values = {
                "reading_or_name": "기역",
                "sound": "기역",
                "mnemonic": "Forma de memoria proposta.",
            }
        else:
            proposal_values = {
                "spellings": "아기",
                "sound": "아기",
                "example_word": "아기",
                "word_translation": "crianca",
                "example_sentence": "아기가 웃어요.",
                "sentence_translation": "A crianca sorri.",
                "normative_pronunciation": "아기",
                "surface_pronunciation": "아기",
                "ipa": "[a]",
            }
        record: dict[str, object] = {
            "item_key": entry.item_key,
            "sequence": entry.sequence,
            "stage_id": entry.stage_id,
            "source_entry_content_hash": entry.content_hash,
            "proposals": [
                {
                    "field_name": field_name,
                    "value": value,
                    "authorship": "ai-proposed",
                    "grounding_reference_ids": grounding,
                }
                for field_name, value in proposal_values.items()
            ],
            "uncertainties": [],
            "disagreements": [],
        }
        record["content_hash"] = _content_hash(record)
        records.append(record)

    batch: dict[str, object] = {
        "schema_version": 1,
        "batch_id": batch_id,
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "source": _source_payload(family),
        "stages": list(stages),
        "records": records,
    }
    batch["content_hash"] = _content_hash(batch)
    return batch


def _family_payload(family: str) -> dict[str, object]:
    batch_ids = tuple(
        batch_id
        for batch_id in BATCH_STAGES
        if batch_id.startswith(f"{family}-")
    )
    batches = [_batch_payload(batch_id) for batch_id in batch_ids]
    records = [record for batch in batches for record in batch["records"]]
    family_payload: dict[str, object] = {
        "schema_version": 1,
        "family": family,
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "source": _source_payload(family),
        "batch_bindings": [
            {
                "artifact_id": batch["batch_id"],
                "content_hash": batch["content_hash"],
                "record_count": len(batch["records"]),
                "stages": batch["stages"],
                "proposal_count": sum(
                    len(record["proposals"]) for record in batch["records"]
                ),
                "uncertainty_count": sum(
                    len(record["uncertainties"]) for record in batch["records"]
                ),
                "disagreement_count": 0,
            }
            for batch in batches
        ],
        "records": records,
    }
    family_payload["content_hash"] = _content_hash(family_payload)
    return family_payload


def _manifest_payload() -> dict[str, object]:
    families = [_family_payload("hangul"), _family_payload("pronunciation")]
    family_bindings = []
    batch_bindings = []
    for family in families:
        proposal_count = sum(
            len(record["proposals"]) for record in family["records"]
        )
        uncertainty_count = sum(
            len(record["uncertainties"]) for record in family["records"]
        )
        family_bindings.append(
            {
                "artifact_id": (
                    "hangul-v2-draft"
                    if family["family"] == "hangul"
                    else "pronunciation-i-plus-1-v2-draft"
                ),
                "content_hash": family["content_hash"],
                "record_count": len(family["records"]),
                "stages": sorted(
                    {record["stage_id"] for record in family["records"]},
                    key=lambda value: int(value[1:]),
                ),
                "proposal_count": proposal_count,
                "uncertainty_count": uncertainty_count,
                "disagreement_count": 0,
            }
        )
        batch_bindings.extend(family["batch_bindings"])
    manifest: dict[str, object] = {
        "schema_version": 1,
        "manifest_version": "korean-foundations-v2-draft",
        "draft_only": True,
        "review_status": "needs_review",
        "promotion_authority": False,
        "family_bindings": family_bindings,
        "batch_bindings": batch_bindings,
        "total_record_count": 139,
        "proposal_count": sum(item["proposal_count"] for item in family_bindings),
        "uncertainty_count": 0,
        "disagreement_count": 0,
    }
    manifest["content_hash"] = _content_hash(manifest)
    return manifest


def test_ai_curation_contract_module_exists() -> None:
    assert find_spec("multilang.services.korean_foundation_ai_curation") is not None


def test_ai_curation_contract_types_exist() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    required_names = {
        "KoreanFoundationDraftSourceReference",
        "KoreanFoundationFieldProposal",
        "KoreanFoundationDraftUncertainty",
        "KoreanFoundationDraftRecord",
        "KoreanFoundationBatchDraft",
        "KoreanFoundationFamilyDraft",
        "KoreanFoundationDraftManifest",
    }

    assert not required_names.difference(vars(module))


def test_source_reference_is_exact_frozen_and_forbids_authority() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    model_type = module.KoreanFoundationDraftSourceReference
    pack = load_korean_hangul_source_pack()
    payload = {
        "family": "hangul",
        "source_file_name": "hangul-v1.json",
        "source_file_sha256": sha256(HANGUL_SOURCE.read_bytes()).hexdigest(),
        "source_pack_version": pack.source_pack_version,
        "source_pack_content_hash": pack.content_hash,
        "registry_version": pack.registry_version,
        "registry_content_hash": pack.registry_content_hash,
    }

    source = model_type.model_validate(payload)
    with pytest.raises(ValidationError):
        source.family = "pronunciation"
    with pytest.raises(ValidationError):
        model_type.model_validate({**payload, "reviewer": "someone"})
    with pytest.raises(ValidationError):
        model_type.model_validate({**payload, "source_file_sha256": "A" * 64})


def test_field_dispositions_are_bounded_plain_nfc_text_without_placeholders() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    proposal_type = module.KoreanFoundationFieldProposal
    uncertainty_type = module.KoreanFoundationDraftUncertainty
    proposal = {
        "field_name": "example_word",
        "value": "아기",
        "authorship": "ai-proposed",
        "grounding_reference_ids": ["nikl.pronunciation-0002"],
    }

    assert proposal_type.model_validate(proposal).value == "아기"
    assert uncertainty_type.model_validate(
        {
            "field_name": "ipa",
            "code": "optional-ipa-unavailable",
            "grounding_reference_ids": ["nikl.pronunciation-0002"],
        }
    ).code == "optional-ipa-unavailable"

    unsafe_values = (
        None,
        "needs_review",
        "<script>alert(1)</script>",
        unicodedata.normalize("NFD", "아기"),
        "ㄱ",
    )
    for value in unsafe_values:
        with pytest.raises(ValidationError):
            proposal_type.model_validate({**proposal, "value": value})
    with pytest.raises(ValidationError):
        proposal_type.model_validate({**proposal, "approved_by": "reviewer"})


def test_batch_draft_requires_exact_v1_coverage_hashes_and_no_authority() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    model_type = module.KoreanFoundationBatchDraft
    payload = _hangul_batch_payload()

    draft = model_type.model_validate(payload)
    assert draft.draft_only is True
    assert draft.review_status == "needs_review"
    assert draft.promotion_authority is False
    assert draft.content_hash == _content_hash(payload)

    stale_source = _hangul_batch_payload()
    stale_source["source"]["source_file_sha256"] = "0" * 64
    stale_source["content_hash"] = _content_hash(stale_source)
    with pytest.raises(ValidationError):
        model_type.model_validate(stale_source)

    authority_spoof = {**_hangul_batch_payload(), "promotion_authority": True}
    authority_spoof["content_hash"] = _content_hash(authority_spoof)
    with pytest.raises(ValidationError):
        model_type.model_validate(authority_spoof)

    structural_spoof = {**_hangul_batch_payload(), "active_rule_ids": []}
    structural_spoof["content_hash"] = _content_hash(structural_spoof)
    with pytest.raises(ValidationError):
        model_type.model_validate(structural_spoof)

    incomplete = _hangul_batch_payload()
    incomplete["records"] = incomplete["records"][:-1]
    incomplete["content_hash"] = _content_hash(incomplete)
    with pytest.raises(ValidationError):
        model_type.model_validate(incomplete)

    stale_entry = _hangul_batch_payload()
    stale_entry["records"][0]["source_entry_content_hash"] = "0" * 64
    stale_entry["records"][0]["content_hash"] = _content_hash(
        stale_entry["records"][0]
    )
    stale_entry["content_hash"] = _content_hash(stale_entry)
    with pytest.raises(ValidationError):
        model_type.model_validate(stale_entry)


@pytest.mark.parametrize(
    "forbidden_field",
    (
        "approval",
        "reviewer",
        "qualification",
        "timestamp",
        "rights_disposition",
        "redistribution_disposition",
        "media_hash",
        "artifact_hash",
        "playback_verified",
        "production_voice_id",
        "prerequisite_concept_ids",
        "active_rule_ids",
    ),
)
def test_batch_draft_rejects_forbidden_authority_and_structure_fields(
    forbidden_field: str,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    payload = {**_hangul_batch_payload(), forbidden_field: "spoofed"}
    payload["content_hash"] = _content_hash(payload)

    with pytest.raises(ValidationError):
        module.KoreanFoundationBatchDraft.model_validate(payload)


def test_family_and_manifest_require_exact_two_family_coverage() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    family_type = module.KoreanFoundationFamilyDraft
    manifest_type = module.KoreanFoundationDraftManifest

    hangul = family_type.model_validate(_family_payload("hangul"))
    pronunciation = family_type.model_validate(_family_payload("pronunciation"))
    manifest = manifest_type.model_validate(_manifest_payload())

    assert len(hangul.records) == 92
    assert len(pronunciation.records) == 47
    assert manifest.total_record_count == 139
    assert len(manifest.batch_bindings) == 6

    incomplete = _manifest_payload()
    incomplete["family_bindings"] = incomplete["family_bindings"][:1]
    incomplete["content_hash"] = _content_hash(incomplete)
    with pytest.raises(ValidationError):
        manifest_type.model_validate(incomplete)


def test_fixed_curation_script_surface_exists() -> None:
    assert CURATION_SCRIPT.is_file()


def test_compact_projections_have_exact_bounded_stage_coverage() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    build_projection = getattr(
        module,
        "build_korean_foundation_batch_projection",
        None,
    )

    assert callable(build_projection)
    projections = [build_projection(batch_id) for batch_id in BATCH_STAGES]
    assert sum(len(projection.records) for projection in projections) == 139
    for projection in projections:
        assert tuple(projection.stages) == BATCH_STAGES[projection.batch_id]
        assert {record.stage_id for record in projection.records} <= set(
            projection.stages
        )
        raw = projection.model_dump_json().encode("utf-8")
        assert len(raw) <= 120 * 1024
        assert b"inherited_orthographic_concept_ids" not in raw
        assert b"media_slots" not in raw
        assert b"pending_reviews" not in raw


def test_curation_script_exposes_only_fixed_operations_and_enum_targets() -> None:
    help_result = subprocess.run(
        [sys.executable, str(CURATION_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert help_result.returncode == 0
    for operation in (
        "project-batch",
        "validate-batch",
        "assemble-family",
        "assemble",
        "validate-drafts",
        "check-selection",
        "promote",
        "verify-promoted",
        "regenerate-requests",
        "verify-requests",
    ):
        assert operation in help_result.stdout
    for forbidden_option in (
        "--root",
        "--output",
        "--url",
        "--provider",
        "--force",
        "--approve",
        "--repair",
    ):
        assert forbidden_option not in help_result.stdout

    traversal = subprocess.run(
        [sys.executable, str(CURATION_SCRIPT), "project-batch", "../../outside"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert traversal.returncode == 2


def test_fixed_validation_and_assembly_are_deterministic_and_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    batch_type = module.KoreanFoundationBatchDraft
    batches = {
        batch_id: batch_type.model_validate(_batch_payload(batch_id))
        for batch_id in BATCH_STAGES
    }
    hangul = module.assemble_korean_foundation_family_draft(
        "hangul",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[:3]),
    )
    pronunciation = module.assemble_korean_foundation_family_draft(
        "pronunciation",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[3:]),
    )
    manifest = module.assemble_korean_foundation_draft_manifest(
        (hangul, pronunciation),
        tuple(batches.values()),
    )

    assert hangul.content_hash == module.assemble_korean_foundation_family_draft(
        "hangul",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[:3]),
    ).content_hash
    assert manifest.total_record_count == 139

    monkeypatch.setattr(
        module,
        "_load_fixed_batch_draft",
        lambda batch_id: batches[batch_id],
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: (
            hangul
            if str(family) in {"hangul", "KoreanFoundationFamily.HANGUL"}
            else pronunciation
        ),
    )
    monkeypatch.setattr(module, "_load_fixed_draft_manifest", lambda: manifest)

    def reject_write(*args: object, **kwargs: object) -> None:
        raise AssertionError("read-only validation attempted a write")

    monkeypatch.setattr(module, "_atomic_write_json", reject_write)
    report = module.validate_korean_foundation_drafts()
    assert report.validated_record_count == 139
    assert report.validated_batch_count == 6


def test_atomic_writer_rejects_any_unregistered_path() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    projection = module.build_korean_foundation_batch_projection("hangul-h0-h3")
    outside_path = PROJECT_ROOT / "curation-drafts" / "outside.json"

    with pytest.raises(module.KoreanFoundationAICurationError):
        module._atomic_write_json(outside_path, projection)
    assert not outside_path.exists()



def test_read_only_validation_rejects_stale_family_batch_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    batches = {
        batch_id: module.KoreanFoundationBatchDraft.model_validate(
            _batch_payload(batch_id)
        )
        for batch_id in BATCH_STAGES
    }
    stale_hangul_payload = _family_payload("hangul")
    stale_hangul_payload["batch_bindings"][0]["content_hash"] = "0" * 64
    stale_hangul_payload["content_hash"] = _content_hash(stale_hangul_payload)
    stale_hangul = module.KoreanFoundationFamilyDraft.model_validate(
        stale_hangul_payload
    )
    pronunciation = module.assemble_korean_foundation_family_draft(
        "pronunciation",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[3:]),
    )
    manifest = module.assemble_korean_foundation_draft_manifest(
        (stale_hangul, pronunciation),
        tuple(batches.values()),
    )

    monkeypatch.setattr(
        module,
        "_load_fixed_batch_draft",
        lambda batch_id: batches[batch_id],
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: (
            stale_hangul
            if str(family) in {"hangul", "KoreanFoundationFamily.HANGUL"}
            else pronunciation
        ),
    )
    monkeypatch.setattr(module, "_load_fixed_draft_manifest", lambda: manifest)

    with pytest.raises(module.KoreanFoundationAICurationError):
        module.validate_korean_foundation_drafts()


def test_read_only_validation_aggregates_content_free_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    bad_ids = {"hangul-h0-h3", "pronunciation-p0-p4"}
    seen: list[str] = []

    def reject_selected_batches(batch_id: str) -> object:
        seen.append(batch_id)
        if batch_id in bad_ids:
            raise module.KoreanFoundationAICurationError(
                module.KoreanFoundationAICurationReasonCode.ARTIFACT_INVALID
            )
        return module.KoreanFoundationBatchDraft.model_validate(
            _batch_payload(batch_id)
        )

    monkeypatch.setattr(module, "_load_fixed_batch_draft", reject_selected_batches)
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: module.KoreanFoundationFamilyDraft.model_validate(
            _family_payload("hangul" if "HANGUL" in str(family) else "pronunciation")
        ),
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_draft_manifest",
        lambda: module.KoreanFoundationDraftManifest.model_validate(
            _manifest_payload()
        ),
    )

    with pytest.raises(module.KoreanFoundationAICurationError) as exc_info:
        module.validate_korean_foundation_drafts()

    assert tuple(seen) == tuple(BATCH_STAGES)
    assert len(exc_info.value.failures) == 2
    assert all("아기" not in failure for failure in exc_info.value.failures)


def _validated_draft_models(module: object) -> tuple[dict[str, object], object, object, object]:
    batches = {
        batch_id: module.KoreanFoundationBatchDraft.model_validate(
            _batch_payload(batch_id)
        )
        for batch_id in BATCH_STAGES
    }
    hangul = module.assemble_korean_foundation_family_draft(
        "hangul",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[:3]),
    )
    pronunciation = module.assemble_korean_foundation_family_draft(
        "pronunciation",
        tuple(batches[batch_id] for batch_id in tuple(BATCH_STAGES)[3:]),
    )
    manifest = module.assemble_korean_foundation_draft_manifest(
        (hangul, pronunciation),
        tuple(batches.values()),
    )
    return batches, hangul, pronunciation, manifest


def test_promotion_rejects_structural_diff_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    check_selection = getattr(
        module,
        "check_korean_foundation_curation_selection",
        None,
    )
    assert callable(check_selection)
    batches, hangul, pronunciation, manifest = _validated_draft_models(module)
    stale_hangul_payload = hangul.model_dump(mode="json")
    stale_hangul_payload["batch_bindings"][0]["content_hash"] = "0" * 64
    stale_hangul_payload["content_hash"] = _content_hash(stale_hangul_payload)
    stale_hangul = module.KoreanFoundationFamilyDraft.model_validate(
        stale_hangul_payload
    )

    monkeypatch.setattr(
        module,
        "_load_fixed_batch_draft",
        lambda batch_id: batches[batch_id],
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: (
            stale_hangul
            if str(family) in {"hangul", "KoreanFoundationFamily.HANGUL"}
            else pronunciation
        ),
    )
    monkeypatch.setattr(module, "_load_fixed_draft_manifest", lambda: manifest)
    monkeypatch.setattr(
        module,
        "_load_selected_draft_manifest_sha256",
        lambda: manifest.content_hash,
    )

    def reject_write(*args: object, **kwargs: object) -> None:
        raise AssertionError("selection check attempted a write")

    monkeypatch.setattr(module, "_atomic_write_json", reject_write)

    with pytest.raises(module.KoreanFoundationAICurationError) as exc_info:
        check_selection(expected_draft_manifest_sha256=manifest.content_hash)
    assert exc_info.value.reason_code in {
        module.KoreanFoundationAICurationReasonCode.ARTIFACT_BINDING_MISMATCH,
        module.KoreanFoundationAICurationReasonCode.STRUCTURAL_DIFF,
    }


def test_selection_check_defines_fixed_candidate_bundle_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    check_selection = getattr(
        module,
        "check_korean_foundation_curation_selection",
        None,
    )
    assert callable(check_selection)
    batches, hangul, pronunciation, manifest = _validated_draft_models(module)

    monkeypatch.setattr(
        module,
        "_load_fixed_batch_draft",
        lambda batch_id: batches[batch_id],
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: (
            hangul
            if str(family) in {"hangul", "KoreanFoundationFamily.HANGUL"}
            else pronunciation
        ),
    )
    monkeypatch.setattr(module, "_load_fixed_draft_manifest", lambda: manifest)
    monkeypatch.setattr(
        module,
        "_load_selected_draft_manifest_sha256",
        lambda: manifest.content_hash,
    )

    def reject_write(*args: object, **kwargs: object) -> None:
        raise AssertionError("selection check attempted a write")

    monkeypatch.setattr(module, "_atomic_write_json", reject_write)

    plan = check_selection(expected_draft_manifest_sha256=manifest.content_hash)

    assert plan.selected_draft_manifest_sha256 == manifest.content_hash
    assert plan.member_names == (
        "hangul-v2.json",
        "pronunciation-i-plus-1-v2.json",
        "korean-foundations-v2-curation.json",
        "korean-foundations-v2-media.json",
    )
    assert plan.bundle_relpath == f"candidate-bundles/{plan.bundle_sha256}"
    assert plan.pointer_relpath == "current-candidate.json"
    assert plan.hangul_family_sha256 == hangul.content_hash
    assert plan.pronunciation_family_sha256 == pronunciation.content_hash
    assert plan.content_hash == _content_hash(plan.model_dump(mode="json"))


def _install_candidate_paths(
    module: object,
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
) -> None:
    candidate_root = root / "data" / "korean_foundations"
    monkeypatch.setattr(module, "KOREAN_FOUNDATION_CANDIDATE_ROOT", candidate_root)
    monkeypatch.setattr(
        module,
        "KOREAN_FOUNDATION_CANDIDATE_BUNDLE_ROOT",
        candidate_root / "candidate-bundles",
    )
    monkeypatch.setattr(
        module,
        "_CURRENT_CANDIDATE_POINTER_PATH",
        candidate_root / "current-candidate.json",
    )


def _install_valid_selection_fixture(
    module: object,
    monkeypatch: pytest.MonkeyPatch,
) -> object:
    batches, hangul, pronunciation, manifest = _validated_draft_models(module)
    monkeypatch.setattr(
        module,
        "_load_fixed_batch_draft",
        lambda batch_id: batches[batch_id],
    )
    monkeypatch.setattr(
        module,
        "_load_fixed_family_draft",
        lambda family: (
            hangul
            if str(family) in {"hangul", "KoreanFoundationFamily.HANGUL"}
            else pronunciation
        ),
    )
    monkeypatch.setattr(module, "_load_fixed_draft_manifest", lambda: manifest)
    monkeypatch.setattr(
        module,
        "_load_selected_draft_manifest_sha256",
        lambda: manifest.content_hash,
    )
    return manifest


def test_candidate_bundle_publication_is_atomic_for_readers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    promote = getattr(module, "promote_korean_foundation_curation_selection", None)
    verify = getattr(module, "verify_promoted_korean_foundation_candidate", None)
    read_current = getattr(module, "read_current_korean_foundation_candidate", None)
    assert callable(promote)
    assert callable(verify)
    assert callable(read_current)
    manifest = _install_valid_selection_fixture(module, monkeypatch)
    _install_candidate_paths(module, monkeypatch, tmp_path)
    candidate_root = module.KOREAN_FOUNDATION_CANDIDATE_ROOT
    pointer_path = module._CURRENT_CANDIDATE_POINTER_PATH
    original_pointer_replace = module._atomic_replace_candidate_pointer

    def fail_before_pointer(raw: bytes) -> None:
        raise module.KoreanFoundationAICurationError(
            module.KoreanFoundationAICurationReasonCode.ATOMIC_WRITE_FAILED
        )

    monkeypatch.setattr(module, "_atomic_replace_candidate_pointer", fail_before_pointer)
    with pytest.raises(module.KoreanFoundationAICurationError):
        promote(expected_draft_manifest_sha256=manifest.content_hash)
    assert not pointer_path.exists()
    with pytest.raises(module.KoreanFoundationAICurationError):
        read_current()

    monkeypatch.setattr(
        module,
        "_atomic_replace_candidate_pointer",
        original_pointer_replace,
    )
    published = promote(expected_draft_manifest_sha256=manifest.content_hash)
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    assert set(pointer) == {
        "schema_version",
        "bundle_sha256",
        "bundle_relpath",
        "bundle_manifest_sha256",
    }
    assert pointer["bundle_sha256"] == published.bundle_sha256
    assert pointer["bundle_relpath"] == f"candidate-bundles/{published.bundle_sha256}"

    bundle_root = candidate_root / pointer["bundle_relpath"]
    members = sorted(path.name for path in bundle_root.iterdir())
    assert members == [
        "bundle-manifest.json",
        "hangul-v2.json",
        "korean-foundations-v2-curation.json",
        "korean-foundations-v2-media.json",
        "pronunciation-i-plus-1-v2.json",
    ]
    bundle_manifest = json.loads(
        (bundle_root / "bundle-manifest.json").read_text(encoding="utf-8")
    )
    assert [member["name"] for member in bundle_manifest["members"]] == list(
        module._CANDIDATE_MEMBER_NAMES
    )
    assert len(bundle_manifest["members"]) == 4
    assert bundle_manifest["media_slot_count"] == 509
    for member in bundle_manifest["members"]:
        assert set(member) == {"name", "sha256"}
        content = (bundle_root / member["name"]).read_bytes()
        assert member["sha256"] == sha256(content).hexdigest()

    verified = verify(expected_draft_manifest_sha256=manifest.content_hash)
    current = read_current()
    retried = promote(expected_draft_manifest_sha256=manifest.content_hash)
    assert verified.bundle_sha256 == published.bundle_sha256
    assert current.bundle_sha256 == published.bundle_sha256
    assert retried.bundle_sha256 == published.bundle_sha256


def test_candidate_bundle_publication_refuses_conflicting_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    promote = getattr(module, "promote_korean_foundation_curation_selection", None)
    assert callable(promote)
    manifest = _install_valid_selection_fixture(module, monkeypatch)
    _install_candidate_paths(module, monkeypatch, tmp_path)
    pointer_path = module._CURRENT_CANDIDATE_POINTER_PATH
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "bundle_sha256": "0" * 64,
                "bundle_relpath": f"candidate-bundles/{'0' * 64}",
                "bundle_manifest_sha256": "1" * 64,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(module.KoreanFoundationAICurationError) as exc_info:
        promote(expected_draft_manifest_sha256=manifest.content_hash)
    assert (
        exc_info.value.reason_code
        is module.KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_CONFLICT
    )


def test_regenerate_requests_fixed_operation_is_implemented() -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    regenerate = getattr(module, "regenerate_korean_foundation_review_requests", None)
    verify = getattr(module, "verify_korean_foundation_review_requests", None)
    assert callable(regenerate)
    assert callable(verify)

    help_result = subprocess.run(
        [sys.executable, str(CURATION_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    assert "regenerate-requests" in help_result.stdout
    assert "verify-requests" in help_result.stdout


def _install_review_request_paths(
    module: object,
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
) -> tuple[Path, Path]:
    curriculum_path = root / "31-CURRICULUM-REVIEW.md"
    audio_path = root / "31-AUDIO-PLAYBACK-REVIEW.md"
    monkeypatch.setattr(
        module,
        "_CURRICULUM_REVIEW_REQUEST_PATH",
        curriculum_path,
    )
    monkeypatch.setattr(
        module,
        "_AUDIO_PLAYBACK_REVIEW_REQUEST_PATH",
        audio_path,
    )
    return curriculum_path, audio_path


def _extract_request_payload(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.count("```json\n") == 1
    payload_text = text.split("```json\n", maxsplit=1)[1].split(
        "\n```",
        maxsplit=1,
    )[0]
    return json.loads(payload_text)


def test_regenerate_requests_writes_complete_pending_request_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    regenerate = getattr(module, "regenerate_korean_foundation_review_requests", None)
    verify = getattr(module, "verify_korean_foundation_review_requests", None)
    assert callable(regenerate)
    assert callable(verify)
    curriculum_path, audio_path = _install_review_request_paths(
        module,
        monkeypatch,
        tmp_path,
    )

    result = regenerate()
    verified = verify()

    assert result.content_hash == verified.content_hash
    assert curriculum_path.is_file()
    assert audio_path.is_file()
    curriculum = _extract_request_payload(curriculum_path)
    audio = _extract_request_payload(audio_path)
    assert curriculum["request_status"] == "needs_review"
    assert audio["request_status"] == "needs_review"
    assert curriculum["candidate_bindings"] == audio["candidate_bindings"]
    assert curriculum["coverage"]["item_count"] == 139
    assert audio["coverage"]["asset_count"] == 509
    assert audio["coverage"]["audio_asset_count"] == 233
    assert result.curriculum_request_sha256 == sha256(curriculum_path.read_bytes()).hexdigest()
    assert result.audio_playback_request_sha256 == sha256(audio_path.read_bytes()).hexdigest()


def test_regenerate_requests_rejects_candidate_pointer_drift_before_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    regenerate = getattr(module, "regenerate_korean_foundation_review_requests", None)
    assert callable(regenerate)
    curriculum_path, audio_path = _install_review_request_paths(
        module,
        monkeypatch,
        tmp_path,
    )
    monkeypatch.setattr(
        module,
        "read_current_korean_foundation_candidate",
        lambda: (_ for _ in ()).throw(
            module.KoreanFoundationAICurationError(
                module.KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
            )
        ),
    )

    def reject_write(*args: object, **kwargs: object) -> None:
        raise AssertionError("regeneration wrote before candidate validation")

    monkeypatch.setattr(module, "_write_review_request_pair", reject_write)

    with pytest.raises(module.KoreanFoundationAICurationError):
        regenerate()
    assert not curriculum_path.exists()
    assert not audio_path.exists()


def test_regenerate_requests_rejects_symlink_candidate_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    regenerate = getattr(module, "regenerate_korean_foundation_review_requests", None)
    assert callable(regenerate)
    _install_candidate_paths(module, monkeypatch, tmp_path)
    _install_review_request_paths(module, monkeypatch, tmp_path)
    pointer_path = module._CURRENT_CANDIDATE_POINTER_PATH
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-pointer.json"
    outside.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "bundle_sha256": "0" * 64,
                "bundle_relpath": f"candidate-bundles/{'0' * 64}",
                "bundle_manifest_sha256": "1" * 64,
            }
        ),
        encoding="utf-8",
    )
    pointer_path.symlink_to(outside)

    with pytest.raises(module.KoreanFoundationAICurationError) as exc_info:
        regenerate()
    assert (
        exc_info.value.reason_code
        is module.KoreanFoundationAICurationReasonCode.CANDIDATE_POINTER_INVALID
    )


def test_verify_requests_rejects_request_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "multilang.services.korean_foundation_ai_curation"
    )
    regenerate = getattr(module, "regenerate_korean_foundation_review_requests", None)
    verify = getattr(module, "verify_korean_foundation_review_requests", None)
    assert callable(regenerate)
    assert callable(verify)
    curriculum_path, _ = _install_review_request_paths(module, monkeypatch, tmp_path)
    regenerate()
    curriculum_path.write_text(
        curriculum_path.read_text(encoding="utf-8").replace(
            "needs_review",
            "approved",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(module.KoreanFoundationAICurationError) as exc_info:
        verify()
    assert (
        exc_info.value.reason_code
        is module.KoreanFoundationAICurationReasonCode.REVIEW_REQUEST_MISMATCH
    )
