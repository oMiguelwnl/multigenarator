"""Phase 32 frequency evidence reload and privacy proofs."""

from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import CardExportModel, DeckExportModel, ProviderCallLogModel
from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportArtifactStatus,
    ExportCardIdentity,
    ExportCardRow,
    ExportDeckArtifact,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import KoreanFrequencyJobAuthority, raw_bytes_sha256
from multilang.repositories.export_repository import ExportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.provider_call_log_repository import (
    ProviderCallLogCreate,
    ProviderCallLogRepository,
)


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def _repositories() -> tuple[ExportRepository, ProviderCallLogRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return (
        ExportRepository(session),
        ProviderCallLogRepository(session),
        JobRepository(session),
        session,
    )


def _authority(stage: str = "full", **overrides: str) -> KoreanFrequencyJobAuthority:
    payload = {
        "stage": stage,
        "phase31_pointer_locator_sha256": _hash("phase31-pointer-locator"),
        "phase31_pointer_content_sha256": _hash("phase31-pointer-content"),
        "phase31_validation_receipt_sha256": _hash("phase31-validation-receipt"),
        "phase31_snapshot_manifest_sha256": _hash("phase31-snapshot-manifest"),
        "phase31_snapshot_root_sha256": _hash("phase31-snapshot-root"),
        "frequency_bundle_locator_sha256": _hash("frequency-bundle-locator"),
        "frequency_bundle_content_sha256": _hash("frequency-bundle-content"),
        "source_retrieval_sha256": _hash("source-retrieval"),
        "source_build_result_sha256": _hash("source-build-result"),
        "source_review_aggregate_sha256": _hash("source-review-aggregate"),
        "provider_policy_sha256": _hash("provider-policy"),
        "pilot_authority_sha256": _hash("pilot-authority"),
        "catalog_locator_sha256": _hash("catalog-locator"),
        "catalog_content_sha256": _hash("catalog-content"),
        "profile_sample_authority_sha256": _hash("profile-sample-authority"),
        "provider_review_authority_sha256": _hash("provider-review-authority"),
        "heard_review_authority_sha256": _hash("heard-review-authority"),
    }
    payload.update(overrides)
    return KoreanFrequencyJobAuthority.model_validate(payload)


def _ko_frequency_job(job_repository: JobRepository) -> str:
    job = job_repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="frequency"),
        run_key="ko-frequency-evidence-reload",
        source_fingerprint="synthetic-frequency-authority",
        total_items=3000,
    )
    return job.id


def _card(job_id: str, *, bundle_hash: str, gate_hash: str) -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.KO,
            source_type="frequency",
            job_id=job_id,
            item_key="level-2-rank-0001",
            lemma_key="ko:synthetic",
            sort_index=1001,
        ),
        word="학교",
        front_of_card="학교",
        ipa="",
        definitions="substantivo: escola",
        example_sentence="저는 학교에 가요.",
        translation="Eu vou para a escola.",
        word_audio="[sound:ko-word.mp3]",
        sentence_audio="[sound:ko-sentence.mp3]",
        frequency_level=2,
        frequency_bundle_sha256=bundle_hash,
        export_gate_receipt_sha256=gate_hash,
    )


def test_export_frequency_level_bundle_gate_and_guid_survive_staged_reload() -> None:
    export_repo, _provider_repo, job_repo, session = _repositories()
    job_id = _ko_frequency_job(job_repo)
    authority = _authority()
    job_repo.bind_audio_authority(job_id, authority)

    first = export_repo.upsert_card_snapshot(
        _card(
            job_id,
            bundle_hash=authority.frequency_bundle_content_sha256 or "",
            gate_hash=_hash("export-gate-a"),
        )
    )
    updated = export_repo.upsert_card_snapshot(
        _card(
            job_id,
            bundle_hash=_hash("updated-frequency-bundle"),
            gate_hash=_hash("export-gate-b"),
        )
    )
    export_repo.upsert_deck_export(
        ExportDeckArtifact(
            job_id=job_id,
            export_format=ExportArtifactFormat.APKG,
            deck_name="Multilang Korean::Frequency::Level 2",
            output_path="exports/ko-frequency.apkg",
            card_count=1000,
            status=ExportArtifactStatus.BLOCKED,
            frequency_bundle_sha256=_hash("updated-frequency-bundle"),
            export_manifest_sha256=_hash("export-manifest"),
            export_gate_receipt_sha256=_hash("export-gate-b"),
        )
    )

    session.expire_all()
    reloaded_card = export_repo.list_card_snapshots(job_id)[0]
    reloaded_artifact = export_repo.list_deck_exports(job_id)[0]
    reloaded_authority = job_repo.load_korean_authority(job_id)

    assert updated.note_guid == first.note_guid == reloaded_card.note_guid
    assert reloaded_card.frequency_level == 2
    assert reloaded_card.frequency_bundle_sha256 == _hash("updated-frequency-bundle")
    assert reloaded_card.export_gate_receipt_sha256 == _hash("export-gate-b")
    assert reloaded_card.ordered_field_mapping()["Image"] == ""
    assert reloaded_artifact.frequency_bundle_sha256 == _hash("updated-frequency-bundle")
    assert reloaded_artifact.export_manifest_sha256 == _hash("export-manifest")
    assert reloaded_artifact.export_gate_receipt_sha256 == _hash("export-gate-b")
    assert reloaded_authority == authority


def test_provider_route_cache_denominator_and_redaction_reload_without_content() -> None:
    _export_repo, provider_repo, job_repo, session = _repositories()
    job_id = _ko_frequency_job(job_repo)
    job_repo.bind_audio_authority(job_id, _authority())

    provider_repo.insert(
        ProviderCallLogCreate(
            job_id=job_id,
            item_key="level-1-rank-0001",
            operation="production_text",
            provider="litellm",
            model="openai/test-model",
            attempt=2,
            latency_ms=37,
            status="failure",
            error_code="provider_error",
            error_summary="api_key=secret prompt: raw payload /home/miguel/private/source row reviewer note",
            fallback_from="primary-route",
            prompt_hash=_hash("prompt"),
            response_hash=_hash("response"),
            route_policy_sha256=_hash("route-policy"),
            budget_snapshot_sha256=_hash("budget-snapshot"),
            cache_key_sha256=_hash("cache-key"),
            response_schema_sha256=_hash("response-schema"),
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            estimated_cost=0.0042,
        )
    )
    provider_repo.insert(
        ProviderCallLogCreate(
            job_id=job_id,
            item_key="level-1-rank-0002",
            operation="production_text",
            provider="litellm",
            status="success",
            latency_ms=41,
            route_policy_sha256=_hash("route-policy"),
            budget_snapshot_sha256=_hash("budget-snapshot"),
            cache_key_sha256=_hash("cache-key-2"),
            response_schema_sha256=_hash("response-schema"),
        )
    )

    session.expire_all()
    rows = provider_repo.list_for_job(job_id)
    summaries = provider_repo.summarize_for_job(job_id)

    failed = next(row for row in rows if row.status == "failure")
    assert failed.route_policy_sha256 == _hash("route-policy")
    assert failed.budget_snapshot_sha256 == _hash("budget-snapshot")
    assert failed.cache_key_sha256 == _hash("cache-key")
    assert failed.response_schema_sha256 == _hash("response-schema")
    assert failed.attempt == 2
    assert failed.fallback_from == "primary-route"
    assert failed.total_tokens == 15
    assert failed.estimated_cost == 0.0042

    all_values = _flatten_persisted_values(
        session.scalars(select(ProviderCallLogModel).where(ProviderCallLogModel.job_id == job_id)).all(),
        session.scalars(select(CardExportModel).where(CardExportModel.job_id == job_id)).all(),
        session.scalars(select(DeckExportModel).where(DeckExportModel.job_id == job_id)).all(),
    )
    forbidden = ("/home/", "prompt:", "raw payload", "api_key=secret", "source row", "reviewer note")
    assert all(fragment not in all_values for fragment in forbidden)
    assert {
        (summary["status"], summary["token_value_count"], summary["cost_value_count"])
        for summary in summaries
    } == {("failure", 1, 1), ("success", 0, 0)}
    assert {summary["route_policy_sha256"] for summary in summaries} == {_hash("route-policy")}
    assert {summary["budget_snapshot_sha256"] for summary in summaries} == {_hash("budget-snapshot")}


def _flatten_persisted_values(*rows_by_model: list[object]) -> str:
    values: list[str] = []
    for rows in rows_by_model:
        for row in rows:
            table = getattr(row, "__table__")
            for column in table.columns:
                value = getattr(row, column.name)
                values.append(str(value))
    return "\n".join(values)
