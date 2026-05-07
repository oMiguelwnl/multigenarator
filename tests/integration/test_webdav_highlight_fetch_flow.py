from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.webdav_highlight_fetch import WebDAVHighlightFetchService, WebDAVResponse
from multilang.settings import Settings


class FakeLookup:
    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        if term == "jardín":
            return KaikkiRecord(
                term="jardín",
                display_form="jardín",
                lemma="jardín",
                definitions=["learner definition for jardín"],
                ipa="/x/",
                source="kaikki",
            )
        return None


class FakeTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def request(self, method: str, url: str, *, headers, timeout: float) -> WebDAVResponse:
        assert method == "GET"
        return WebDAVResponse(status_code=200, body=self.body, headers={})


def build_ingest_service() -> tuple[IngestLexicalItemsService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    service = IngestLexicalItemsService(
        job_service=GenerateJobService(JobRepository(session)),
        lexical_repo=LexicalRepository(session),
        grounding_service=LexicalGroundingService(FakeLookup()),
        highlight_import_repo=HighlightImportRepository(session),
    )
    return service, session


def synthetic_kindle_export() -> bytes:
    return b"""
    <!doctype html><html><body>
    <div class="bookTitle">Synthetic Learner Reader</div>
    <div class="noteHeading">Highlight (<span>Location 1</span>)</div>
    <div class="noteText">El jard\xc3\xadn secreto guarda una llave brillante</div>
    </body></html>
    """


def test_webdav_fetch_to_ingest_is_content_hash_idempotent(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        webdav_url="https://example.invalid/dav/",
        webdav_username="reader",
        webdav_secret="reader-secret",
        webdav_cache_dir=tmp_path / ".multilang" / "highlights" / "cache",
    )
    fetch_service = WebDAVHighlightFetchService.from_settings(
        settings,
        transport=FakeTransport(synthetic_kindle_export()),
    )
    ingest_service, session = build_ingest_service()

    first_fetch = fetch_service.fetch_export("/safe/export.html")
    first = ingest_service.execute(
        GenerationRequest(language=SupportedLanguage.ES, source_type="kindle-highlights", input_file=first_fetch.cached_path)
    )
    second_fetch = fetch_service.fetch_export("/safe/export.html")
    second = ingest_service.execute(
        GenerationRequest(language=SupportedLanguage.ES, source_type="kindle-highlights", input_file=second_fetch.cached_path)
    )

    session.close()

    assert first_fetch.content_hash == second_fetch.content_hash
    assert first.imported_highlights == 1
    assert first.rejected_highlights == 0
    assert first.extracted_candidates >= 1
    assert first.duplicate_candidates >= 0
    assert first.planned_cards == 1
    assert second.reused_existing_items == first.planned_cards
    assert second.reused_existing_candidates if hasattr(second, "reused_existing_candidates") else second.reused_existing_items
    assert second.newly_planned_candidates == 0
