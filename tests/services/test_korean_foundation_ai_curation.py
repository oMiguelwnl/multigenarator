import importlib
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
