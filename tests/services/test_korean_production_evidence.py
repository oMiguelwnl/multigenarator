"""Read-only Korean production evidence reconciliation tests."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from uuid import uuid4
import zipfile

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.models import (
    AudioAssetModel,
    CardExportModel,
    DeckExportModel,
    GenerationJob,
    LexicalCandidate,
    ProviderCallLogModel,
    TextQualityRecordModel,
)
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.exporting import FREQUENCY_EXPORT_CARD_FIELD_NAMES, ExportCardIdentity, build_export_note_guid
from multilang.domain.jobs import SupportedLanguage
from multilang.services.korean_production_evidence import (
    KoreanProductionEvidenceAuthority,
    KoreanProductionEvidenceRows,
    build_korean_production_audit_payload,
    korean_production_review_identity_hash,
    load_korean_production_evidence_rows,
    render_korean_production_audit_markdown,
    validate_korean_production_review_batches,
    validate_korean_production_final_evidence,
    validate_korean_production_run_result,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


HASHES_FOR_FINAL = {
    "content_promotion": _hash("content-promotion"),
    "text_review_aggregate": _hash("text-review-aggregate"),
    "text_review_application": _hash("text-review-application"),
    "audio_review_aggregate": _hash("audio-review-aggregate"),
    "audio_review_application": _hash("audio-review-application"),
}
KOREAN_FREQUENCY_MODEL_ID = 1_762_801_101
KOREAN_FREQUENCY_PARENT_DECK_ID = 1_762_801_102
KOREAN_FREQUENCY_LEVEL_DECK_IDS = {1: 1_762_801_103, 2: 1_762_801_104, 3: 1_762_801_105}


def _authority(**overrides: str) -> KoreanProductionEvidenceAuthority:
    payload = {
        "job_id": "job-ko-production",
        "phase31_pointer_locator_sha256": _hash("phase31-pointer-locator"),
        "phase31_pointer_content_sha256": _hash("phase31-pointer-content"),
        "phase31_validation_receipt_sha256": _hash("phase31-validation"),
        "phase31_snapshot_manifest_sha256": _hash("phase31-manifest"),
        "phase31_snapshot_root_sha256": _hash("phase31-root"),
        "frequency_bundle_locator_sha256": _hash("frequency-manifest"),
        "frequency_bundle_content_sha256": _hash("frequency-content"),
        "source_access_authority_sha256": _hash("source-access"),
        "source_retrieval_sha256": _hash("source-retrieval"),
        "source_transformation_sha256": _hash("source-transformation"),
        "source_build_result_sha256": _hash("source-build"),
        "source_review_aggregate_sha256": _hash("source-review-aggregate"),
        "final_bundle_authority_sha256": _hash("final-bundle-authority"),
        "provider_policy_sha256": _hash("provider-policy"),
        "provider_review_authority_sha256": _hash("provider-review-authority"),
        "budget_authority_sha256": _hash("budget-authority"),
        "retry_policy_sha256": _hash("retry-policy"),
        "full_run_authority_sha256": _hash("full-run-authority"),
        "catalog_locator_sha256": _hash("catalog-locator"),
        "catalog_content_sha256": _hash("catalog-content"),
        "profile_sample_authority_sha256": _hash("profile-sample-authority"),
        "heard_review_authority_sha256": _hash("heard-review-authority"),
        "full_binding_receipt_sha256": _hash("full-binding-receipt"),
    }
    payload.update(overrides)
    return KoreanProductionEvidenceAuthority(**payload)


def _phase31_report(authority: KoreanProductionEvidenceAuthority) -> SimpleNamespace:
    return SimpleNamespace(
        receipt_sha256=authority.phase31_validation_receipt_sha256,
        snapshot_manifest_sha256=authority.phase31_snapshot_manifest_sha256,
        snapshot_root_sha256=authority.phase31_snapshot_root_sha256,
    )


def _insert_fake_production_run_database(
    tmp_path: Path,
    *,
    text_repair_attempt_count: int = 1,
    text_review_status: str = "review_required",
    text_review_receipt_sha256: str | None = None,
    provider_fallback: bool = False,
    audio_review_status: str = "synthesized_pending",
    audio_review_receipt_sha256: str | None = None,
    heard_review_receipt_sha256: str | None = None,
    include_export_rows: bool = False,
) -> tuple[str, KoreanProductionEvidenceAuthority]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    authority = _authority()
    database_url = f"sqlite+pysqlite:///{tmp_path / 'production-run.db'}"
    engine = create_engine(database_url)
    ensure_database_schema(engine, database_url)
    session = Session(engine)
    try:
        session.add(
            GenerationJob(
                id=authority.job_id,
                run_key="ko-production-run",
                language="ko",
                source_type="frequency",
                source_fingerprint=authority.frequency_bundle_content_sha256,
                status="running",
                current_stage="production_audio_pending_review",
                last_completed_stage="production_audio",
                total_items=3000,
                completed_items=3000,
                failed_items=0,
                retrying_items=0,
                skipped_duplicates=0,
                resume_state={},
                korean_phase31_pointer_locator_sha256=authority.phase31_pointer_locator_sha256,
                korean_phase31_pointer_content_sha256=authority.phase31_pointer_content_sha256,
                korean_phase31_validation_receipt_sha256=authority.phase31_validation_receipt_sha256,
                korean_phase31_snapshot_manifest_sha256=authority.phase31_snapshot_manifest_sha256,
                korean_phase31_snapshot_root_sha256=authority.phase31_snapshot_root_sha256,
                korean_frequency_bundle_locator_sha256=authority.frequency_bundle_locator_sha256,
                korean_frequency_bundle_content_sha256=authority.frequency_bundle_content_sha256,
                korean_frequency_authority=authority.model_dump(mode="json"),
                korean_provider_policy_sha256=authority.provider_policy_sha256,
                korean_provider_policy={"policy_sha256": authority.provider_policy_sha256},
            )
        )
        lexical_rows: list[LexicalCandidate] = []
        text_rows: list[TextQualityRecordModel] = []
        audio_rows: list[AudioAssetModel] = []
        export_rows: list[CardExportModel] = []
        for rank in range(1, 3001):
            level = ((rank - 1) // 1000) + 1
            item_key = f"ko-production-{rank:04d}"
            candidate_id = str(uuid4())
            lexical_rows.append(
                LexicalCandidate(
                    id=candidate_id,
                    job_id=authority.job_id,
                    run_key="ko-production-run",
                    item_key=item_key,
                    source_type="frequency",
                    submitted_form=f"term-{rank:04d}",
                    normalized_source=f"term-{rank:04d}",
                    display_form=f"term-{rank:04d}",
                    lemma=f"lemma-{rank:04d}",
                    lemma_key=f"ko:lemma:{rank:04d}",
                    frequency_rank=rank,
                    frequency_level=level,
                    definitions_html="substantivo: fixture synthetic only",
                    definition_language="pt",
                    ipa=f"/fixture-{rank:04d}/",
                    spoken_form=f"spoken-{rank:04d}",
                    translation_target_language="pt",
                    grounding_status="grounded",
                    warning_code=None,
                    warning_detail=None,
                    provenance={"source": "synthetic-production-fixture"},
                    korean_identity={"pos": "NNG", "sense_id_sha256": _hash(f"sense-{rank}")},
                    frequency_bundle_sha256=authority.frequency_bundle_content_sha256,
                    frequency_source_sha256=authority.source_retrieval_sha256,
                    source_review_receipt_sha256=authority.source_review_aggregate_sha256,
                    source_review_aggregate_sha256=authority.source_review_aggregate_sha256,
                    lexical_evidence={
                        "source_access_authority_sha256": authority.source_access_authority_sha256,
                        "source_transformation_sha256": authority.source_transformation_sha256,
                        "source_build_result_sha256": authority.source_build_result_sha256,
                        "final_bundle_authority_sha256": authority.final_bundle_authority_sha256,
                    },
                )
            )
            text_rows.append(
                TextQualityRecordModel(
                    id=str(uuid4()),
                    job_id=authority.job_id,
                    lexical_candidate_id=candidate_id,
                    run_key="ko-production-run",
                    item_key=item_key,
                    example_sentence="LEAK-SYNTHETIC-KOREAN-SENTENCE",
                    translation_text="LEAK-SYNTHETIC-PORTUGUESE-TRANSLATION",
                    generation_status="repaired",
                    validation_status="passed",
                    review_status=text_review_status,
                    repair_attempt_count=text_repair_attempt_count,
                    confidence_score=0.99,
                    confidence_label="high",
                    validation_flags=[],
                    review_reason=None,
                    sentence_provenance={"provider": "fixture"},
                    translation_provenance={"provider": "fixture"},
                    candidate_selection_evidence={
                        "candidate_set_sha256": _hash(f"candidate-set-{rank}"),
                        "selected_candidate_sha256": _hash(f"selected-candidate-{rank}"),
                        "initial_candidate_count": 2,
                        "repair_attempt_count": text_repair_attempt_count,
                        "hard_gate_status": "passed",
                    },
                    adaptive_i_plus_one_evidence={
                        "known_prefix_sha256": _hash(f"known-prefix-{rank}"),
                        "known_concept_count": 2,
                        "phase31_pointer_locator_sha256": authority.phase31_pointer_locator_sha256,
                        "phase31_pointer_content_sha256": authority.phase31_pointer_content_sha256,
                        "phase31_validation_receipt_sha256": authority.phase31_validation_receipt_sha256,
                        "phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                        "phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
                        "frequency_bundle_locator_sha256": authority.frequency_bundle_locator_sha256,
                        "frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
                        "candidate_sha256": _hash(f"lexical-candidate-{rank}"),
                        "hard_gate_codes": [],
                        "target_concept_id": f"lexicon:ko:{rank:04d}",
                        "observed_concept_ids": [f"lexicon:ko:{rank:04d}", "foundation:hangul"],
                        "incidental_concept_ids": ["foundation:hangul"],
                        "scorer_version": "synthetic-scorer-v1",
                    },
                    provider_review_evidence={
                        "review_receipt_sha256": authority.provider_review_authority_sha256,
                        "decision": "accepted" if text_review_status == "accepted" else "needs_review",
                    },
                    text_review_receipt_sha256=text_review_receipt_sha256,
                )
            )
            for kind in ("word", "sentence"):
                audio_rows.append(
                    AudioAssetModel(
                        id=str(uuid4()),
                        job_id=authority.job_id,
                        run_key="ko-production-run",
                        item_key=item_key,
                        asset_kind=kind,
                        display_text=f"{kind}-{rank:04d}-LEAK-AUDIO-TEXT",
                        tts_text=f"{kind}-{rank:04d}-LEAK-AUDIO-TEXT",
                        ssml_text=f"<speak>{kind}-{rank:04d}</speak>",
                        provider="azure",
                        voice_id="ko-KR-SunHiNeural",
                        locale="ko-KR",
                        format="audio-24khz-48kbitrate-mono-mp3",
                        text_hash=_hash(f"{kind}-text-{rank}"),
                        ssml_hash=_hash(f"{kind}-ssml-{rank}"),
                        storage_path=f"private/audio/{item_key}-{kind}.mp3",
                        byte_size=2048,
                        duration_ms=800,
                        status="synthesized",
                        fallback_used=False,
                        provider_sdk_version="1.49.1",
                        voice_profile_sha256=authority.profile_sample_authority_sha256,
                        catalog_receipt_sha256=authority.catalog_content_sha256,
                        synthesis_request_sha256=_hash(f"{kind}-request-{rank}"),
                        artifact_sha256=_hash(f"{kind}-artifact-{rank}"),
                        audio_review_status=audio_review_status,
                        audio_review_receipt_sha256=audio_review_receipt_sha256,
                        heard_review_receipt_sha256=heard_review_receipt_sha256,
                        fallback_origin=None,
                        rejection_reason_code=None,
                    )
                )
            if include_export_rows:
                identity = ExportCardIdentity(
                    language=SupportedLanguage.KO,
                    source_type="frequency",
                    job_id=authority.job_id,
                    item_key=item_key,
                    lemma_key=f"ko:lemma:{rank:04d}",
                    sort_index=rank,
                )
                export_rows.append(
                    CardExportModel(
                        id=str(uuid4()),
                        job_id=authority.job_id,
                        run_key="ko-production-run",
                        item_key=item_key,
                        lemma_key=f"ko:lemma:{rank:04d}",
                        note_guid=build_export_note_guid(identity),
                        sort_index=rank,
                        frequency_level=level,
                        frequency_bundle_sha256=authority.frequency_bundle_content_sha256,
                        export_gate_receipt_sha256=HASHES_FOR_FINAL["content_promotion"],
                        word=f"term-{rank:04d}",
                        front_of_card=f"term-{rank:04d}",
                        ipa=f"/fixture-{rank:04d}/",
                        definitions="substantivo: fixture synthetic only",
                        example_sentence="LEAK-SYNTHETIC-KOREAN-SENTENCE",
                        translation="LEAK-SYNTHETIC-PORTUGUESE-TRANSLATION",
                        word_audio=f"[sound:{item_key}-word.mp3]",
                        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
                        image="",
                    )
                )
        session.add_all(lexical_rows)
        session.add_all(text_rows)
        session.add_all(audio_rows)
        if export_rows:
            session.add_all(export_rows)
            session.add(
                DeckExportModel(
                    id=str(uuid4()),
                    job_id=authority.job_id,
                    run_key="ko-production-run",
                    export_format="apkg",
                    deck_name="Multilang Korean::Frequency",
                    output_path=str(tmp_path / "korean-frequency.apkg"),
                    card_count=3000,
                    status="completed",
                    frequency_bundle_sha256=authority.frequency_bundle_content_sha256,
                    export_manifest_sha256=authority.frequency_bundle_locator_sha256,
                    export_gate_receipt_sha256=HASHES_FOR_FINAL["content_promotion"],
                )
            )
        session.add_all(
            [
                _provider_row(authority, operation="definition", item_key="provider-definition"),
                _provider_row(authority, operation="sentence_generation", item_key="provider-sentence", attempt=2),
                _provider_row(authority, operation="translation", item_key="provider-translation"),
                _provider_row(
                    authority,
                    operation="audio_synthesis",
                    item_key="provider-audio",
                    fallback_from="forbidden" if provider_fallback else None,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()
        engine.dispose()
    return database_url, authority


def _provider_row(
    authority: KoreanProductionEvidenceAuthority,
    *,
    operation: str,
    item_key: str,
    attempt: int = 1,
    fallback_from: str | None = None,
) -> ProviderCallLogModel:
    return ProviderCallLogModel(
        id=str(uuid4()),
        job_id=authority.job_id,
        item_key=item_key,
        operation=operation,
        provider="azure" if operation == "audio_synthesis" else "openai",
        model="fixture-model",
        voice_id="ko-KR-SunHiNeural" if operation == "audio_synthesis" else None,
        attempt=attempt,
        latency_ms=120,
        status="success",
        error_code=None,
        error_summary=None,
        fallback_from=fallback_from,
        prompt_hash=_hash(f"prompt-{operation}"),
        response_hash=_hash(f"response-{operation}"),
        route_policy_sha256=authority.provider_policy_sha256,
        budget_snapshot_sha256=authority.budget_authority_sha256,
        cache_key_sha256=_hash(f"cache-{operation}"),
        response_schema_sha256=_hash(f"schema-{operation}"),
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        estimated_cost=0.01,
    )


def _table_counts(database_url: str) -> dict[str, int]:
    engine = create_engine(database_url)
    session = Session(engine)
    try:
        return {
            "jobs": int(session.scalar(select(func.count()).select_from(GenerationJob)) or 0),
            "lexical": int(session.scalar(select(func.count()).select_from(LexicalCandidate)) or 0),
            "text": int(session.scalar(select(func.count()).select_from(TextQualityRecordModel)) or 0),
            "audio": int(session.scalar(select(func.count()).select_from(AudioAssetModel)) or 0),
            "provider": int(session.scalar(select(func.count()).select_from(ProviderCallLogModel)) or 0),
            "cards": int(session.scalar(select(func.count()).select_from(CardExportModel)) or 0),
            "decks": int(session.scalar(select(func.count()).select_from(DeckExportModel)) or 0),
        }
    finally:
        session.close()
        engine.dispose()


def _write_fake_korean_frequency_apkg(
    tmp_path: Path,
    authority: KoreanProductionEvidenceAuthority,
    *,
    bad_level_count: bool = False,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    model_id = KOREAN_FREQUENCY_MODEL_ID
    parent_deck_id = KOREAN_FREQUENCY_PARENT_DECK_ID
    level_deck_ids = KOREAN_FREQUENCY_LEVEL_DECK_IDS
    collection_path = tmp_path / "collection.anki2"
    if collection_path.exists():
        collection_path.unlink()
    with sqlite3.connect(collection_path) as connection:
        connection.execute("create table col(models text not null, decks text not null)")
        connection.execute("create table notes(id integer primary key, guid text not null, mid integer not null, flds text not null)")
        connection.execute("create table cards(id integer primary key, nid integer not null, did integer not null)")
        models = {str(model_id): {"name": "Multilang::Card", "flds": [{"name": name} for name in FREQUENCY_EXPORT_CARD_FIELD_NAMES]}}
        decks = {
            str(parent_deck_id): {"name": "Multilang Korean::Frequency"},
            **{
                str(deck_id): {"name": f"Multilang Korean::Frequency::Level {level}"}
                for level, deck_id in level_deck_ids.items()
            },
        }
        connection.execute("insert into col(models, decks) values (?, ?)", (json.dumps(models), json.dumps(decks)))
        for rank in range(1, 3001):
            level = ((rank - 1) // 1000) + 1
            if bad_level_count and rank == 3000:
                level = 2
            item_key = f"ko-production-{rank:04d}"
            identity = ExportCardIdentity(
                language=SupportedLanguage.KO,
                source_type="frequency",
                job_id=authority.job_id,
                item_key=item_key,
                lemma_key=f"ko:lemma:{rank:04d}",
                sort_index=rank,
            )
            fields = "\x1f".join(
                (
                    str(rank),
                    f"term-{rank:04d}",
                    f"/fixture-{rank:04d}/",
                    "substantivo: fixture synthetic only",
                    "LEAK-SYNTHETIC-KOREAN-SENTENCE",
                    "LEAK-SYNTHETIC-PORTUGUESE-TRANSLATION",
                    f"[sound:{item_key}-word.mp3]",
                    f"[sound:{item_key}-sentence.mp3]",
                    "",
                )
            )
            connection.execute(
                "insert into notes(id, guid, mid, flds) values (?, ?, ?, ?)",
                (rank, build_export_note_guid(identity), model_id, fields),
            )
            connection.execute(
                "insert into cards(id, nid, did) values (?, ?, ?)",
                (rank, rank, level_deck_ids[level]),
            )
        connection.commit()

    media_manifest: dict[str, str] = {}
    for rank in range(1, 3001):
        item_key = f"ko-production-{rank:04d}"
        media_manifest[str((rank - 1) * 2)] = f"{item_key}-word.mp3"
        media_manifest[str((rank - 1) * 2 + 1)] = f"{item_key}-sentence.mp3"
    apkg_path = tmp_path / "korean-frequency.apkg"
    with zipfile.ZipFile(apkg_path, "w") as archive:
        archive.write(collection_path, "collection.anki2")
        archive.writestr("media", json.dumps(media_manifest, sort_keys=True))
        for index in range(6000):
            archive.writestr(str(index), b"ID3")
    return apkg_path


def _write_generation_reports(
    tmp_path: Path,
    authority: KoreanProductionEvidenceAuthority,
    apkg_path: Path,
    *,
    bad_card_count: bool = False,
) -> tuple[Path, Path, str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    apkg_sha256 = _sha256_file(apkg_path)
    payload = {
        "report_schema": "korean-frequency-export-report-v1",
        "job": {"id": authority.job_id, "language": "ko", "source_type": "frequency", "total_items": 3000},
        "frequency_bundle": {
            "content_sha256": authority.frequency_bundle_content_sha256,
            "manifest_sha256": authority.frequency_bundle_locator_sha256,
            "binding_receipt_sha256": authority.full_binding_receipt_sha256,
        },
        "export": {
            "format": "apkg",
            "apkg_sha256": apkg_sha256,
            "card_count": 2999 if bad_card_count else 3000,
            "expected_items": 3000,
            "cards_per_level": 1000,
        },
        "level_counts": {"1": 1000, "2": 1000, "3": 1000},
        "text": {"total": 3000, "accepted": 3000, "review_required": 0, "review_receipt_count": 3000},
        "audio": {
            "word": {"expected": 3000, "total": 3000, "approved": 3000, "missing": 0},
            "sentence": {"expected": 3000, "total": 3000, "approved": 3000, "missing": 0},
            "fallback_count": 0,
            "artifact_hash_count": 6000,
        },
        "denominators": {"provider_call_records": 4, "token_values": 4, "cost_values": 4},
        "private": "LEAK-CONTENT",
    }
    json_path = tmp_path / "generation-report.json"
    markdown_path = tmp_path / "generation-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(
        f"exact_apkg_sha256={apkg_sha256}\ncard_count={payload['export']['card_count']}\nLEAK-CONTENT\n",
        encoding="utf-8",
    )
    return json_path, markdown_path, apkg_sha256


def test_run_result_reconciles_exact_db_rows_phase31_denominators_and_pending_audio_read_only(tmp_path: Path) -> None:
    database_url, authority = _insert_fake_production_run_database(tmp_path)
    before_counts = _table_counts(database_url)

    rows = load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id)
    evidence = validate_korean_production_run_result(
        authority=authority,
        rows=rows,
        expected_item_count=3000,
        protected_hashes={"frequency_manifest": (_hash("protected"), _hash("protected"))},
        phase31_verifier=lambda **_: _phase31_report(authority),
    )

    assert _table_counts(database_url) == before_counts
    assert evidence.mode == "run_result"
    assert evidence.job_id == authority.job_id
    assert evidence.lexical_candidate_count == 3000
    assert evidence.level_counts == {1: 1000, 2: 1000, 3: 1000}
    assert evidence.text_record_count == 3000
    assert evidence.text_histories_with_two_initial_candidates == 3000
    assert evidence.text_histories_with_single_repair_or_less == 3000
    assert evidence.hard_gate_passed_count == 3000
    assert evidence.adaptive_evidence_count == 3000
    assert evidence.word_pending_audio_review_count == 3000
    assert evidence.sentence_pending_audio_review_count == 3000
    assert evidence.provider_call_count == 4
    assert evidence.provider_attempt_count == 4
    assert evidence.retry_attempt_count == 1
    assert evidence.cache_hit_count == 0
    assert evidence.missing_token_denominator_count == 0
    assert evidence.missing_cost_denominator_count == 0
    assert evidence.fallback_attempt_count == 0
    assert evidence.grants_review_application_authority is False
    assert evidence.grants_content_promotion_authority is False
    assert evidence.grants_release_authority is False
    serialized = evidence.model_dump_json()
    assert "LEAK-" not in serialized
    assert "private/audio" not in serialized
    assert len(evidence.evidence_sha256) == 64


def test_run_result_rejects_one_fact_drift_without_mutating_rows(tmp_path: Path) -> None:
    database_url, authority = _insert_fake_production_run_database(tmp_path, text_repair_attempt_count=2)
    before_counts = _table_counts(database_url)
    rows = load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id)

    with pytest.raises(ValueError, match="text history"):
        validate_korean_production_run_result(
            authority=authority,
            rows=rows,
            expected_item_count=3000,
            protected_hashes={"frequency_manifest": (_hash("protected"), _hash("protected"))},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )
    assert _table_counts(database_url) == before_counts

    with pytest.raises(ValueError, match="protected input drift"):
        validate_korean_production_run_result(
            authority=authority,
            rows=rows,
            expected_item_count=3000,
            protected_hashes={"frequency_manifest": (_hash("before"), _hash("after"))},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )


def test_run_result_blocks_phase31_provider_fallback_and_audio_review_drift(tmp_path: Path) -> None:
    database_url, authority = _insert_fake_production_run_database(tmp_path, provider_fallback=True)
    rows = load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id)

    with pytest.raises(ValueError, match="Phase 31"):
        validate_korean_production_run_result(
            authority=authority,
            rows=rows,
            expected_item_count=3000,
            protected_hashes={},
            phase31_verifier=lambda **_: SimpleNamespace(
                receipt_sha256=authority.phase31_validation_receipt_sha256,
                snapshot_manifest_sha256=_hash("wrong-manifest"),
                snapshot_root_sha256=authority.phase31_snapshot_root_sha256,
            ),
        )

    with pytest.raises(ValueError, match="fallback"):
        validate_korean_production_run_result(
            authority=authority,
            rows=rows,
            expected_item_count=3000,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )

    other_database_url, other_authority = _insert_fake_production_run_database(
        tmp_path / "other",
        audio_review_status="approved",
    )
    other_rows = load_korean_production_evidence_rows(database_url=other_database_url, job_id=other_authority.job_id)
    with pytest.raises(ValueError, match="pending-review audio"):
        validate_korean_production_run_result(
            authority=other_authority,
            rows=other_rows,
            expected_item_count=3000,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(other_authority),
        )


def test_final_evidence_reconciles_review_apkg_report_and_hash_only_audits_read_only(tmp_path: Path) -> None:
    authority_heard = _hash("heard-review-authority")
    database_url, authority = _insert_fake_production_run_database(
        tmp_path,
        text_review_status="accepted",
        text_review_receipt_sha256=HASHES_FOR_FINAL["text_review_application"],
        audio_review_status="approved",
        audio_review_receipt_sha256=HASHES_FOR_FINAL["audio_review_application"],
        heard_review_receipt_sha256=authority_heard,
        include_export_rows=True,
    )
    authority = _authority(heard_review_authority_sha256=authority_heard)
    apkg_path = _write_fake_korean_frequency_apkg(tmp_path, authority)
    report_json, report_markdown, apkg_sha256 = _write_generation_reports(tmp_path, authority, apkg_path)
    before_counts = _table_counts(database_url)

    rows = load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id)
    evidence = validate_korean_production_final_evidence(
        authority=authority,
        rows=rows,
        expected_item_count=3000,
        expected_word_assets=3000,
        expected_sentence_assets=3000,
        cards_per_level=1000,
        content_promotion_authority_sha256=HASHES_FOR_FINAL["content_promotion"],
        text_review_aggregate_sha256=HASHES_FOR_FINAL["text_review_aggregate"],
        text_review_application_sha256=HASHES_FOR_FINAL["text_review_application"],
        audio_review_aggregate_sha256=HASHES_FOR_FINAL["audio_review_aggregate"],
        audio_review_application_sha256=HASHES_FOR_FINAL["audio_review_application"],
        apkg_file=apkg_path,
        generation_report_json=report_json,
        generation_report_markdown=report_markdown,
        protected_hashes={"generation_report_json": (_hash("protected"), _hash("protected"))},
        phase31_verifier=lambda **_: _phase31_report(authority),
    )

    assert _table_counts(database_url) == before_counts
    assert evidence.mode == "final_result"
    assert evidence.text_accepted_count == 3000
    assert evidence.text_review_required_count == 0
    assert evidence.word_reviewed_audio_count == 3000
    assert evidence.sentence_reviewed_audio_count == 3000
    assert evidence.word_pending_audio_review_count == 0
    assert evidence.sentence_pending_audio_review_count == 0
    assert evidence.card_export_count == 3000
    assert evidence.deck_export_count == 1
    assert evidence.apkg_card_count == 3000
    assert evidence.apkg_media_count == 6000
    assert evidence.apkg_sha256 == apkg_sha256
    assert evidence.generation_report_json_sha256 == _sha256_file(report_json)
    assert evidence.generation_report_markdown_sha256 == _sha256_file(report_markdown)
    assert evidence.grants_content_promotion_authority is False
    assert evidence.grants_release_authority is False
    audit_payload = build_korean_production_audit_payload(evidence)
    audit_markdown = render_korean_production_audit_markdown(audit_payload)
    serialized = json.dumps(audit_payload, ensure_ascii=False) + audit_markdown + evidence.model_dump_json()
    assert "LEAK-" not in serialized
    assert "private/audio" not in serialized
    assert audit_payload["final"]["apkg_card_count"] == 3000
    assert f"apkg_sha256={apkg_sha256}" in audit_markdown


def test_final_evidence_one_fact_mutations_fail_read_only_for_review_apkg_and_report(tmp_path: Path) -> None:
    database_url, authority = _insert_fake_production_run_database(
        tmp_path,
        text_review_status="accepted",
        text_review_receipt_sha256=HASHES_FOR_FINAL["text_review_application"],
        audio_review_status="approved",
        audio_review_receipt_sha256=HASHES_FOR_FINAL["audio_review_application"],
        heard_review_receipt_sha256=_hash("heard-review-authority"),
        include_export_rows=True,
    )
    apkg_path = _write_fake_korean_frequency_apkg(tmp_path, authority)
    report_json, report_markdown, _apkg_sha256 = _write_generation_reports(tmp_path, authority, apkg_path)
    before_counts = _table_counts(database_url)

    rows = load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id)
    text_mutation = rows.text_records[0]
    text_mutation.review_status = "review_required"
    with pytest.raises(ValueError, match="reviewed text"):
        validate_korean_production_final_evidence(
            authority=authority,
            rows=replace(rows, text_records=(text_mutation, *rows.text_records[1:])),
            expected_item_count=3000,
            expected_word_assets=3000,
            expected_sentence_assets=3000,
            cards_per_level=1000,
            content_promotion_authority_sha256=HASHES_FOR_FINAL["content_promotion"],
            text_review_aggregate_sha256=HASHES_FOR_FINAL["text_review_aggregate"],
            text_review_application_sha256=HASHES_FOR_FINAL["text_review_application"],
            audio_review_aggregate_sha256=HASHES_FOR_FINAL["audio_review_aggregate"],
            audio_review_application_sha256=HASHES_FOR_FINAL["audio_review_application"],
            apkg_file=apkg_path,
            generation_report_json=report_json,
            generation_report_markdown=report_markdown,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )

    bad_apkg = _write_fake_korean_frequency_apkg(tmp_path / "bad-apkg", authority, bad_level_count=True)
    bad_report_json, bad_report_markdown, _ = _write_generation_reports(tmp_path / "bad-apkg", authority, bad_apkg)
    with pytest.raises(ValueError, match="APKG"):
        validate_korean_production_final_evidence(
            authority=authority,
            rows=load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id),
            expected_item_count=3000,
            expected_word_assets=3000,
            expected_sentence_assets=3000,
            cards_per_level=1000,
            content_promotion_authority_sha256=HASHES_FOR_FINAL["content_promotion"],
            text_review_aggregate_sha256=HASHES_FOR_FINAL["text_review_aggregate"],
            text_review_application_sha256=HASHES_FOR_FINAL["text_review_application"],
            audio_review_aggregate_sha256=HASHES_FOR_FINAL["audio_review_aggregate"],
            audio_review_application_sha256=HASHES_FOR_FINAL["audio_review_application"],
            apkg_file=bad_apkg,
            generation_report_json=bad_report_json,
            generation_report_markdown=bad_report_markdown,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )

    bad_report_json, bad_report_markdown, _ = _write_generation_reports(
        tmp_path / "bad-report",
        authority,
        apkg_path,
        bad_card_count=True,
    )
    with pytest.raises(ValueError, match="report"):
        validate_korean_production_final_evidence(
            authority=authority,
            rows=load_korean_production_evidence_rows(database_url=database_url, job_id=authority.job_id),
            expected_item_count=3000,
            expected_word_assets=3000,
            expected_sentence_assets=3000,
            cards_per_level=1000,
            content_promotion_authority_sha256=HASHES_FOR_FINAL["content_promotion"],
            text_review_aggregate_sha256=HASHES_FOR_FINAL["text_review_aggregate"],
            text_review_application_sha256=HASHES_FOR_FINAL["text_review_application"],
            audio_review_aggregate_sha256=HASHES_FOR_FINAL["audio_review_aggregate"],
            audio_review_application_sha256=HASHES_FOR_FINAL["audio_review_application"],
            apkg_file=apkg_path,
            generation_report_json=bad_report_json,
            generation_report_markdown=bad_report_markdown,
            protected_hashes={},
            phase31_verifier=lambda **_: _phase31_report(authority),
        )
    assert _table_counts(database_url) == before_counts


def _simple_review_rows(authority: KoreanProductionEvidenceAuthority, *, count: int = 3) -> KoreanProductionEvidenceRows:
    text_records = []
    audio_assets = []
    for rank in range(1, count + 1):
        item_key = f"ko-production-{rank:04d}"
        text_records.append(
            SimpleNamespace(
                job_id=authority.job_id,
                item_key=item_key,
                validation_status="passed",
                review_status="accepted",
                repair_attempt_count=1 if rank == 1 else 0,
                validation_flags=["risk"] if rank == 2 else [],
                text_review_receipt_sha256=HASHES_FOR_FINAL["text_review_application"],
            )
        )
        for kind in ("word", "sentence"):
            audio_assets.append(
                SimpleNamespace(
                    job_id=authority.job_id,
                    item_key=item_key,
                    asset_kind=kind,
                    status="synthesized",
                    audio_review_status="approved",
                    synthesis_request_sha256=_hash(f"{kind}-request-{rank}"),
                    artifact_sha256=_hash(f"{kind}-artifact-{rank}"),
                    byte_size=2048,
                    audio_review_receipt_sha256=HASHES_FOR_FINAL["audio_review_application"],
                    heard_review_receipt_sha256=authority.heard_review_authority_sha256,
                )
            )
    return KoreanProductionEvidenceRows(
        job=SimpleNamespace(id=authority.job_id),
        lexical_candidates=(),
        text_records=tuple(text_records),
        audio_assets=tuple(audio_assets),
        provider_call_records=(),
        card_exports=(),
        deck_exports=(),
    )


def _write_review_receipt(
    directory: Path,
    name: str,
    *,
    authority: KoreanProductionEvidenceAuthority,
    coverage_kind: str,
    identity_hashes: list[str],
    reviewer_role: str = "qualified-reviewer",
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "korean-production-review-receipt-batch",
        "job_id": authority.job_id,
        "coverage_kind": coverage_kind,
        "reviewer_role": reviewer_role,
        "decision": "approved",
        "authority": {
            "full_binding_receipt_sha256": authority.full_binding_receipt_sha256,
            "frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
            "profile_sample_authority_sha256": authority.profile_sample_authority_sha256,
            "heard_review_authority_sha256": authority.heard_review_authority_sha256,
        },
        "identity_hashes": identity_hashes,
    }
    path = directory / name
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def test_review_aggregate_recomputes_complete_bounded_receipts_read_only_and_content_free(tmp_path: Path) -> None:
    authority = _authority()
    rows = _simple_review_rows(authority)
    receipt_dir = tmp_path / "receipts"
    text_hashes = [
        korean_production_review_identity_hash("text", job_id=authority.job_id, item_key=f"ko-production-{rank:04d}")
        for rank in range(1, 4)
    ]
    word_hashes = [
        korean_production_review_identity_hash(
            "word_integrity",
            job_id=authority.job_id,
            item_key=f"ko-production-{rank:04d}",
            request_sha256=_hash(f"word-request-{rank}"),
            artifact_sha256=_hash(f"word-artifact-{rank}"),
        )
        for rank in range(1, 4)
    ]
    sentence_hashes = [
        korean_production_review_identity_hash(
            "sentence_integrity",
            job_id=authority.job_id,
            item_key=f"ko-production-{rank:04d}",
            request_sha256=_hash(f"sentence-request-{rank}"),
            artifact_sha256=_hash(f"sentence-artifact-{rank}"),
        )
        for rank in range(1, 4)
    ]
    receipt_files = [
        _write_review_receipt(receipt_dir, "text.json", authority=authority, coverage_kind="text", identity_hashes=text_hashes),
        _write_review_receipt(receipt_dir, "word.json", authority=authority, coverage_kind="word_integrity", identity_hashes=word_hashes),
        _write_review_receipt(receipt_dir, "sentence.json", authority=authority, coverage_kind="sentence_integrity", identity_hashes=sentence_hashes),
        _write_review_receipt(receipt_dir, "heard-word.json", authority=authority, coverage_kind="heard_word", identity_hashes=word_hashes[:1]),
        _write_review_receipt(receipt_dir, "heard-sentence.json", authority=authority, coverage_kind="heard_sentence", identity_hashes=sentence_hashes[:1]),
        _write_review_receipt(receipt_dir, "risk.json", authority=authority, coverage_kind="risk", identity_hashes=text_hashes[:2]),
    ]

    aggregate = validate_korean_production_review_batches(
        authority=authority,
        rows=rows,
        receipt_files=receipt_files,
        expected_item_count=3,
        expected_heard_sample_count=1,
    )

    assert aggregate.text_receipt_count == 3
    assert aggregate.word_integrity_receipt_count == 3
    assert aggregate.sentence_integrity_receipt_count == 3
    assert aggregate.heard_word_sample_count == 1
    assert aggregate.risk_case_count == 2
    assert aggregate.grants_review_application_authority is False
    dumped = aggregate.model_dump_json()
    assert "LEAK" not in dumped
    assert "private/audio" not in dumped

    duplicate = _write_review_receipt(
        tmp_path / "bad",
        "duplicate.json",
        authority=authority,
        coverage_kind="text",
        identity_hashes=[text_hashes[0], text_hashes[0]],
    )
    with pytest.raises(ValueError, match="overlap"):
        validate_korean_production_review_batches(
            authority=authority,
            rows=rows,
            receipt_files=[duplicate],
            expected_item_count=3,
            expected_heard_sample_count=1,
        )
