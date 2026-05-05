from __future__ import annotations

import hashlib

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import HighlightImportManifestModel
from multilang.domain.highlights import HighlightImportManifest, HighlightProvenance, NormalizedHighlight
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository


PRIVATE_SENTENCE = "La frase privada solo vive en registros internos"


def build_repositories() -> tuple[HighlightImportRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return HighlightImportRepository(session), JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.ES, source_type="kindle-highlights")


def make_highlight(text: str = PRIVATE_SENTENCE, index: int = 0) -> NormalizedHighlight:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return NormalizedHighlight(
        highlight_id=f"highlight-{index}",
        text=text,
        provenance=HighlightProvenance(
            source_path="local_export.txt",
            source_format="text",
            source_index=index,
            content_hash=content_hash,
        ),
    )


def test_metadata_defines_private_records_and_safe_manifest_tables() -> None:
    table_names = set(Base.metadata.tables)
    manifest_columns = {column.name for column in HighlightImportManifestModel.__table__.columns}

    assert "highlight_import_records" in table_names
    assert "highlight_import_manifests" in table_names
    assert {"import_content_hash", "candidate_keys", "counts"}.issubset(manifest_columns)
    assert "normalized_text" not in manifest_columns
    assert "source_path" not in manifest_columns
    assert "raw_location" not in manifest_columns
    assert "book_title" not in manifest_columns
    assert "author" not in manifest_columns


def test_upsert_import_records_stores_private_text_idempotently() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(), run_key="es:kindle-highlights:items:abc", source_fingerprint="items:abc", total_items=1
    )
    import_hash = hashlib.sha256(b"import").hexdigest()
    highlight = make_highlight()

    assert repository.upsert_import_records(job.id, import_hash, [highlight]) == 1
    assert repository.upsert_import_records(job.id, import_hash, [highlight]) == 1

    records = repository.list_private_records(job.id)
    assert len(records) == 1
    assert records[0].normalized_text == PRIVATE_SENTENCE
    assert session.execute(text("SELECT COUNT(*) FROM highlight_import_records")).scalar_one() == 1


def test_upsert_import_manifest_is_safe_and_idempotent() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(), run_key="es:kindle-highlights:items:def", source_fingerprint="items:def", total_items=1
    )
    import_hash = hashlib.sha256(b"import").hexdigest()
    manifest = HighlightImportManifest(
        import_content_hash=import_hash,
        candidate_keys=["highlight-es-abc-def"],
        counts={"imported_highlights": 1},
    )

    repository.upsert_import_manifest(job.id, manifest)
    repository.upsert_import_manifest(
        job.id,
        manifest.model_copy(update={"counts": {"imported_highlights": 1, "extracted_candidates": 1}}),
    )

    stored = repository.get_manifest(job.id)

    assert stored is not None
    assert stored.import_content_hash == import_hash
    assert stored.counts["extracted_candidates"] == 1
    assert PRIVATE_SENTENCE not in str(stored.model_dump())


def test_created_tables_are_inspectable_without_private_manifest_columns() -> None:
    _, _, session = build_repositories()
    inspector = inspect(session.bind)

    assert "highlight_import_records" in inspector.get_table_names()
    assert "highlight_import_manifests" in inspector.get_table_names()
    manifest_columns = {column["name"] for column in inspector.get_columns("highlight_import_manifests")}
    assert "normalized_text" not in manifest_columns
