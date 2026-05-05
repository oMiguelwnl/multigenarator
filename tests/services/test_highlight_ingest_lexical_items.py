from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.highlights import HighlightCandidate
from multilang.domain.jobs import GenerationRequest, JobStage, SupportedLanguage
from multilang.domain.lexicon import GroundingStatus
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService


PRIVATE_SENTENCE = "El jardín secreto guarda una llave brillante"


class FakeLookup:
    def __init__(self, records: dict[str, KaikkiRecord] | None = None) -> None:
        self.records = records or {}

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        return self.records.get(term)


def build_service(records: dict[str, KaikkiRecord] | None = None) -> tuple[IngestLexicalItemsService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    job_repository = JobRepository(session)
    service = IngestLexicalItemsService(
        job_service=GenerateJobService(job_repository),
        lexical_repo=LexicalRepository(session),
        grounding_service=LexicalGroundingService(FakeLookup(records)),
        highlight_import_repo=HighlightImportRepository(session),
    )
    return service, session


def record(term: str) -> KaikkiRecord:
    return KaikkiRecord(
        term=term,
        display_form=term,
        lemma=term,
        definitions=[f"a learner definition for {term}"],
        part_of_speech="noun",
        ipa="/x/",
        source="kaikki",
    )


def request(input_file: Path) -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.ES, source_type="kindle-highlights", input_file=input_file)


def write_export(path: Path, text: str = PRIVATE_SENTENCE) -> None:
    path.write_text(f"Synthetic Learner Reader\n- Your Highlight at Location 1\n{text}\n==========", encoding="utf-8")


def test_missing_highlight_grounding_is_insufficient_not_backfill() -> None:
    service = LexicalGroundingService(FakeLookup())
    source_hash = "a" * 64
    candidate = HighlightCandidate(
        item_key="highlight-es-aaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb",
        source_content_hash=source_hash,
        display_form="jardín",
        lemma_key="jardín",
        first_highlight_id="highlight-1",
        first_source_index=0,
        occurrence_count=1,
    )

    grounded = service.ground_highlight_candidate(language=SupportedLanguage.ES, candidate=candidate)

    assert grounded.grounding_status is GroundingStatus.INSUFFICIENT
    assert grounded.grounding_status is not GroundingStatus.BACKFILL_REQUIRED
    assert grounded.warning_code == "highlight_grounding_missing"
    assert PRIVATE_SENTENCE not in str(grounded.model_dump())


def test_highlight_ingestion_persists_private_records_and_safe_candidates(tmp_path: Path) -> None:
    service, session = build_service({"jardín": record("jardín")})
    export_path = tmp_path / "export.txt"
    write_export(export_path)

    result = service.execute(request(export_path))

    assert result.imported_highlights == 1
    assert result.extracted_candidates >= 1
    assert result.planned_cards == 1
    assert result.blocked_candidates >= 0
    private_records = HighlightImportRepository(session).list_private_records(result.report.job_id)
    assert private_records[0].normalized_text == PRIVATE_SENTENCE
    candidate_rows = LexicalRepository(session).list_candidates(result.report.job_id)
    assert len(candidate_rows) == 1
    assert candidate_rows[0].grounding_status is GroundingStatus.GROUNDED
    assert PRIVATE_SENTENCE not in str(candidate_rows[0].provenance.model_dump())
    job = JobRepository(session).get_job(result.report.job_id)
    assert job is not None
    assert job.current_stage == JobStage.GENERATE_TEXT.value


def test_highlight_rerun_reuses_completed_items_without_duplicate_rows(tmp_path: Path) -> None:
    service, session = build_service({"jardín": record("jardín")})
    export_path = tmp_path / "export.txt"
    write_export(export_path)

    first = service.execute(request(export_path))
    second = service.execute(request(export_path))

    assert second.reused_existing_items == first.planned_cards
    assert second.newly_planned_candidates == 0
    assert len(LexicalRepository(session).list_candidates(first.report.job_id)) == 1
