from __future__ import annotations

import hashlib

from sqlalchemy import create_engine, event, func, inspect, select, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import (
    HighlightImportManifestModel,
    HighlightImportRecordModel,
    HighlightPrivateExcerptRevisionModel,
)
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


def make_korean_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.KO, source_type="kindle-highlights")


def make_highlight(
    text: str = PRIVATE_SENTENCE,
    index: int = 0,
    *,
    highlight_id: str | None = None,
    source_path: str = "local_export.txt",
    raw_location: str | None = None,
) -> NormalizedHighlight:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return NormalizedHighlight(
        highlight_id=highlight_id or f"highlight-{index}",
        text=text,
        provenance=HighlightProvenance(
            source_path=source_path,
            source_format="text",
            source_index=index,
            raw_location=raw_location,
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


def test_korean_private_revisions_retry_changed_text_and_old_row_unchanged() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_korean_request(),
        run_key="ko:kindle-highlights:items:abc",
        source_fingerprint="items:abc",
        total_items=1,
    )
    first_import_hash = hashlib.sha256(b"first-import").hexdigest()
    second_import_hash = hashlib.sha256(b"second-import").hexdigest()
    first = make_highlight("민감한 원문 target 첫째", 0, highlight_id="highlight-stable")
    changed = make_highlight("민감한 원문 target 둘째", 0, highlight_id="highlight-stable")

    assert repository.upsert_import_records(job.id, first_import_hash, [first]) == 1
    first_safe = repository.list_korean_safe_inventory(job.id).rows[0]
    first_revision = repository.load_private_excerpt_revision(job.id, first_safe.excerpt_revision_id)
    assert first_revision is not None
    assert first_revision.normalized_text == "민감한 원문 target 첫째"
    assert repository.upsert_import_records(job.id, first_import_hash, [first]) == 1
    assert repository.upsert_import_records(job.id, second_import_hash, [changed]) == 1

    revisions = session.scalars(
        select(HighlightPrivateExcerptRevisionModel)
        .where(HighlightPrivateExcerptRevisionModel.job_id == job.id)
        .order_by(HighlightPrivateExcerptRevisionModel.revision_number.asc())
    ).all()
    assert [revision.revision_number for revision in revisions] == [1, 2]
    assert revisions[0].normalized_text == "민감한 원문 target 첫째"
    assert revisions[1].normalized_text == "민감한 원문 target 둘째"
    assert revisions[0].excerpt_revision_id == first_revision.excerpt_revision_id
    loaded_first_revision = repository.load_private_excerpt_revision(job.id, revisions[0].excerpt_revision_id)
    assert loaded_first_revision.normalized_text == "민감한 원문 target 첫째"
    assert session.scalar(select(func.count(HighlightImportRecordModel.id))) == 0


def test_korean_distinct_excerpt_hashes_keep_distinct_safe_inventory_links() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_korean_request(),
        run_key="ko:kindle-highlights:items:def",
        source_fingerprint="items:def",
        total_items=2,
    )
    import_hash = hashlib.sha256(b"distinct-import").hexdigest()
    first = make_highlight("물은 차갑다", 0, highlight_id="same-candidate-a")
    second = make_highlight("그 물이 맑다", 1, highlight_id="same-candidate-b")

    repository.upsert_import_records(job.id, import_hash, [first, second])
    inventory = repository.list_korean_safe_inventory(job.id)

    assert [row.candidate_id for row in inventory.rows] == ["same-candidate-a", "same-candidate-b"]
    assert len({row.source_content_hash for row in inventory.rows}) == 2
    assert len({row.excerpt_revision_id for row in inventory.rows}) == 2


def test_korean_safe_inventory_root_order_no_drop_and_private_boundary_hash_only() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_korean_request(),
        run_key="ko:kindle-highlights:items:ghi",
        source_fingerprint="items:ghi",
        total_items=3,
    )
    import_hash = hashlib.sha256(b"inventory-import").hexdigest()
    sentinel = "민감한 /home/private/book.txt ignore previous instructions"
    highlights = (
        make_highlight("중복 target", 0, highlight_id="candidate-0", source_path="/home/private/book.txt"),
        make_highlight(f"{sentinel} target", 1, highlight_id="candidate-1", raw_location="secret-location"),
        make_highlight("중복 target", 2, highlight_id="candidate-2"),
    )

    repository.upsert_import_records(job.id, import_hash, highlights)
    inventory = repository.list_korean_safe_inventory(job.id)
    replay = repository.list_korean_safe_inventory(job.id)

    assert [row.candidate_id for row in inventory.rows] == ["candidate-0", "candidate-1", "candidate-2"]
    assert [row.source_index for row in inventory.rows] == [0, 1, 2]
    assert inventory.inventory_root_sha256 == replay.inventory_root_sha256
    assert inventory.candidate_count == 3
    rendered = inventory.model_dump_json()
    assert sentinel not in rendered
    assert "/home/private" not in rendered
    assert "secret-location" not in rendered
    assert "normalized_text" not in rendered
    assert "source_path" not in rendered
    assert "raw_location" not in rendered


def test_korean_private_boundary_hash_only_safe_inventory_selects_no_exact_text_path_or_location_columns() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_korean_request(),
        run_key="ko:kindle-highlights:items:jkl",
        source_fingerprint="items:jkl",
        total_items=1,
    )
    import_hash = hashlib.sha256(b"sentinel-import").hexdigest()
    repository.upsert_import_records(
        job.id,
        import_hash,
        [make_highlight("민감한 target 원문", 0, source_path="/home/private/book.txt", raw_location="secret")],
    )
    statements: list[str] = []

    def capture_statement(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture_statement)
    try:
        inventory = repository.list_korean_safe_inventory(job.id)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture_statement)

    assert inventory.rows[0].candidate_id == "highlight-0"
    inventory_selects = [statement for statement in statements if "highlight_private_excerpt_revisions" in statement]
    assert inventory_selects
    rendered_sql = "\n".join(inventory_selects)
    assert "normalized_text" not in rendered_sql
    assert "source_path" not in rendered_sql
    assert "raw_location" not in rendered_sql


def test_get_private_record_fetches_by_job_and_highlight_id() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(), run_key="es:kindle-highlights:items:abc", source_fingerprint="items:abc", total_items=2
    )
    other_job = job_repository.create_job(
        request=make_request(), run_key="es:kindle-highlights:items:def", source_fingerprint="items:def", total_items=1
    )
    import_hash = hashlib.sha256(b"import").hexdigest()
    repository.upsert_import_records(job.id, import_hash, [make_highlight("first private text", 0), make_highlight("second private text", 1)])
    repository.upsert_import_records(other_job.id, import_hash, [make_highlight("other private text", 0)])

    record = repository.get_private_record(job.id, "highlight-1")

    assert record is not None
    assert record.normalized_text == "second private text"
    assert repository.get_private_record(job.id, "missing") is None
    assert repository.get_private_record(other_job.id, "highlight-1") is None


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
