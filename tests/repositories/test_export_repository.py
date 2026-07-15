"""Repository tests for persisted export snapshots and artifacts."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportArtifactStatus,
    ExportCardIdentity,
    ExportCardRow,
    ExportDeckArtifact,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.export_repository import ExportRepository
from multilang.repositories.job_repository import JobRepository


def build_repositories() -> tuple[ExportRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return ExportRepository(session), JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="word-list", input_file=None)


def make_card_row(*, item_key: str, sort_index: int, translation: str = "Eu corro.") -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.EN,
            source_type="word-list",
            job_id="placeholder",
            item_key=item_key,
            lemma_key=f"en:{item_key}",
            sort_index=sort_index,
        ),
        word=item_key,
        front_of_card=item_key,
        ipa=f"/{item_key}/",
        definitions=f"definition for {item_key}",
        example_sentence=f"I can use {item_key} in a sentence.",
        translation=translation,
        word_audio=f"[sound:{item_key}.mp3]",
        sentence_audio=f"[sound:{item_key}-sentence.mp3]",
    )


def make_artifact(*, job_id: str, export_format: ExportArtifactFormat) -> ExportDeckArtifact:
    return ExportDeckArtifact(
        job_id=job_id,
        export_format=export_format,
        deck_name="English::Level 1",
        output_path=f"exports/{job_id}.{export_format.value}",
        card_count=2,
        status=ExportArtifactStatus.COMPLETED,
    )


def test_upsert_card_snapshot_updates_existing_job_item_row() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-export-upsert",
        source_fingerprint="list-a",
        total_items=1,
    )

    first = make_card_row(item_key="line-1", sort_index=1)
    repository.upsert_card_snapshot(
        first.model_copy(update={"identity": first.identity.model_copy(update={"job_id": job.id})})
    )

    updated = repository.upsert_card_snapshot(
        make_card_row(item_key="line-1", sort_index=1, translation="Eu corro mais rápido.").model_copy(
            update={
                "identity": make_card_row(item_key="line-1", sort_index=1).identity.model_copy(
                    update={"job_id": job.id}
                )
            }
        )
    )

    assert session.execute(
        text("SELECT COUNT(*) FROM card_exports WHERE job_id = :job_id AND item_key = :item_key"),
        {"job_id": job.id, "item_key": "line-1"},
    ).scalar_one() == 1
    assert updated.translation == "Eu corro mais rápido."


def test_upsert_card_snapshots_persists_batch_with_single_job_scope() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-export-bulk-upsert",
        source_fingerprint="list-bulk",
        total_items=2,
    )

    first = make_card_row(item_key="line-1", sort_index=1)
    second = make_card_row(item_key="line-2", sort_index=2)
    stored = repository.upsert_card_snapshots(
        [
            first.model_copy(update={"identity": first.identity.model_copy(update={"job_id": job.id})}),
            second.model_copy(update={"identity": second.identity.model_copy(update={"job_id": job.id})}),
        ]
    )

    assert [row.identity.item_key for row in stored] == ["line-1", "line-2"]
    assert session.execute(
        text("SELECT COUNT(*) FROM card_exports WHERE job_id = :job_id"),
        {"job_id": job.id},
    ).scalar_one() == 2

    updated = make_card_row(item_key="line-2", sort_index=2, translation="Linha dois atualizada.")
    repository.upsert_card_snapshots(
        [updated.model_copy(update={"identity": updated.identity.model_copy(update={"job_id": job.id})})]
    )

    assert session.execute(
        text("SELECT COUNT(*) FROM card_exports WHERE job_id = :job_id AND item_key = :item_key"),
        {"job_id": job.id, "item_key": "line-2"},
    ).scalar_one() == 1
    assert repository.list_card_snapshots(job.id)[1].translation == "Linha dois atualizada."


def test_card_snapshot_round_trip_preserves_gramatica() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-export-gramatica",
        source_fingerprint="list-la",
        total_items=1,
    )

    grammar = "vir: subst masc, 2a declinacao, Nominativus singularis, Suj."
    row = make_card_row(item_key="vir", sort_index=1).model_copy(update={"gramatica": grammar})
    stored = repository.upsert_card_snapshot(
        row.model_copy(update={"identity": row.identity.model_copy(update={"job_id": job.id})})
    )

    # The value must survive the upsert return path...
    assert stored.gramatica == grammar
    # ...and a fresh read from the persisted row (not just the in-memory object).
    session.expire_all()
    reloaded = repository.list_card_snapshots(job.id)
    assert reloaded[0].gramatica == grammar


def test_card_snapshot_round_trip_keeps_gramatica_null_when_absent() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-export-no-gramatica",
        source_fingerprint="list-plain",
        total_items=1,
    )

    row = make_card_row(item_key="run", sort_index=1)
    repository.upsert_card_snapshot(
        row.model_copy(update={"identity": row.identity.model_copy(update={"job_id": job.id})})
    )

    session.expire_all()
    assert repository.list_card_snapshots(job.id)[0].gramatica is None


def test_artifacts_and_card_queries_are_job_scoped_and_sorted() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-export-list",
        source_fingerprint="list-b",
        total_items=3,
    )

    line_2 = make_card_row(item_key="line-2", sort_index=2)
    line_1b = make_card_row(item_key="line-1b", sort_index=1)
    line_1a = make_card_row(item_key="line-1a", sort_index=1)

    for row in (line_2, line_1b, line_1a):
        repository.upsert_card_snapshot(
            row.model_copy(update={"identity": row.identity.model_copy(update={"job_id": job.id})})
        )

    repository.upsert_deck_export(make_artifact(job_id=job.id, export_format=ExportArtifactFormat.CSV))
    repository.upsert_deck_export(make_artifact(job_id=job.id, export_format=ExportArtifactFormat.TSV))

    cards = repository.list_card_snapshots(job.id)
    artifacts = repository.list_deck_exports(job.id)

    assert [(card.sort_index, card.identity.item_key) for card in cards] == [
        (1, "line-1a"),
        (1, "line-1b"),
        (2, "line-2"),
    ]
    assert [artifact.export_format for artifact in artifacts] == [
        ExportArtifactFormat.CSV,
        ExportArtifactFormat.TSV,
    ]
