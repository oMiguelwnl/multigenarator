"""End-to-end Phase 16 evidence for local Kindle highlights."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import LexicalCandidate
from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import GenerationRequest, JobStage, SupportedLanguage
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.services.assemble_export_cards import AssembleExportCardsService
from multilang.services.audio_synthesis import AudioSynthesisBundle
from multilang.services.generate_audio_items import GenerateAudioItemsService
from multilang.services.generate_job import GenerateJobService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService


class FakeLookup:
    """Deterministic lexical grounding for the synthetic local fixture."""

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        if language_code == "es" and term == "jardín":
            return KaikkiRecord(
                term="jardín",
                display_form="jardín",
                lemma="jardín",
                definitions=["noun: a cultivated outdoor place with plants"],
                ipa="/xaɾˈðin/",
                source="kaikki-test-fixture",
            )
        return None


def build_ingest_service() -> tuple[IngestLexicalItemsService, LexicalRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    lexical_repo = LexicalRepository(session)
    service = IngestLexicalItemsService(
        job_service=GenerateJobService(JobRepository(session)),
        lexical_repo=lexical_repo,
        grounding_service=LexicalGroundingService(FakeLookup()),
        highlight_import_repo=HighlightImportRepository(session),
    )
    return service, lexical_repo, session


def write_synthetic_kindle_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "synthetic-kindle-export.html"
    fixture_path.write_text(
        """
        <!doctype html><html><body>
        <div class="bookTitle">Synthetic Garden Reader</div>
        <div class="noteHeading">Highlight (<span>Location 7</span>)</div>
        <div class="noteText">El jardín tranquilo tiene flores azules.</div>
        </body></html>
        """,
        encoding="utf-8",
    )
    return fixture_path


def accepted_text_record(*, job_id: str, item_key: str, lexical_candidate_id: str) -> TextQualityRecord:
    return TextQualityRecord(
        job_id=job_id,
        item_key=item_key,
        lexical_candidate_id=lexical_candidate_id,
        example_sentence="El jardín tranquilo recibe la luz de la mañana.",
        translation_text="must stay out of highlight exports",
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=ReviewStatus.ACCEPTED,
        repair_attempt_count=0,
        confidence_score=0.96,
        confidence_label=ConfidenceLabel.HIGH,
        validation_flags=[],
        review_reason=None,
        sentence_provenance=TextProvenance(
            source="phase16-local-fixture",
            provider="deterministic-test",
            metadata={"source_type": "kindle-highlights"},
        ),
        translation_provenance=TextProvenance(source="omitted", provider="deterministic-test"),
    )


@dataclass
class TextRepo:
    record: TextQualityRecord

    def list_accepted_records(self, job_id: str) -> list[TextQualityRecord]:
        return [self.record] if job_id == self.record.job_id else []


@dataclass
class AudioRepo:
    assets: dict[tuple[str, str], AudioAssetRecord] = field(default_factory=dict)

    def get_reusable_asset(self, **kwargs: object) -> None:
        return None

    def upsert_audio_asset(self, record: AudioAssetRecord) -> AudioAssetRecord:
        self.assets[(record.item_key, record.asset_kind.value)] = record
        return record

    def get_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> AudioAssetRecord | None:
        return self.assets.get((item_key, asset_kind.value))


@dataclass
class AudioSynthesis:
    def prepare_item_assets(
        self,
        *,
        language: SupportedLanguage,
        display_word: str,
        text_record: TextQualityRecord,
    ) -> AudioSynthesisBundle:
        return AudioSynthesisBundle(
            word_asset=self._asset(
                job_id=text_record.job_id,
                item_key=text_record.item_key,
                asset_kind=AudioAssetKind.WORD,
                text=display_word,
            ),
            sentence_asset=self._asset(
                job_id=text_record.job_id,
                item_key=text_record.item_key,
                asset_kind=AudioAssetKind.SENTENCE,
                text=text_record.example_sentence,
            ),
        )

    def synthesize_prepared_asset(self, prepared_asset: AudioAssetRecord) -> AudioAssetRecord:
        return prepared_asset.model_copy(
            update={
                "provenance": prepared_asset.provenance.model_copy(
                    update={"status": AudioSynthesisStatus.SYNTHESIZED, "byte_size": 2048, "duration_ms": 700}
                )
            }
        )

    def _asset(self, *, job_id: str, item_key: str, asset_kind: AudioAssetKind, text: str) -> AudioAssetRecord:
        normalized = NormalizedTtsInput(display_text=text, tts_text=text, ssml_text=f"<speak>{text}</speak>")
        return AudioAssetRecord(
            job_id=job_id,
            item_key=item_key,
            asset_kind=asset_kind,
            display_text=text,
            normalized_input=normalized,
            provenance=AudioProvenance(
                provider=AudioProvider.AZURE,
                voice_id="es-ES-ElviraNeural",
                locale="es-ES",
                format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
                text_hash=normalized.text_hash or "",
                ssml_hash=normalized.ssml_hash or "",
                storage_path=f"audio/{asset_kind.value}/jardin-{asset_kind.value}.mp3",
                byte_size=0,
                status=AudioSynthesisStatus.PENDING,
            ),
        )


@dataclass
class AudioJobRepo:
    successes: list[tuple[str, str, JobStage]] = field(default_factory=list)

    def record_item_success(self, job_id: str, *, item_key: str, completed_stage: JobStage) -> None:
        self.successes.append((job_id, item_key, completed_stage))


@dataclass
class ExportRepo:
    rows: list[object] = field(default_factory=list)

    def upsert_card_snapshot(self, record: object) -> object:
        self.rows.append(record)
        return record


def test_local_kindle_fixture_ingests_generates_audio_and_assembles_highlight_card(tmp_path: Path) -> None:
    fixture_path = write_synthetic_kindle_fixture(tmp_path)
    ingest_service, lexical_repo, session = build_ingest_service()

    ingest_result = ingest_service.execute(
        GenerationRequest(language=SupportedLanguage.ES, source_type="kindle-highlights", input_file=fixture_path)
    )
    job_id = ingest_result.report.orchestration.job_id
    candidate_row = session.scalar(select(LexicalCandidate).where(LexicalCandidate.job_id == job_id))
    assert candidate_row is not None

    text_repo = TextRepo(
        accepted_text_record(job_id=job_id, item_key=candidate_row.item_key, lexical_candidate_id=candidate_row.id)
    )
    audio_repo = AudioRepo()
    audio_result = GenerateAudioItemsService(
        job_repository=AudioJobRepo(),
        lexical_repository=lexical_repo,
        text_repository=text_repo,
        audio_repository=audio_repo,
        audio_synthesis_service=AudioSynthesis(),
    ).execute(job_id=job_id, deck_language=SupportedLanguage.ES)
    card_result = AssembleExportCardsService(
        text_repository=text_repo,
        lexical_repository=lexical_repo,
        audio_repository=audio_repo,
        export_repository=ExportRepo(),
    ).execute(job_id=job_id, deck_language=SupportedLanguage.ES)

    row = card_result.cards[0]
    mapping = row.ordered_field_mapping()

    assert ingest_result.imported_highlights == 1
    assert ingest_result.rejected_highlights == 0
    assert ingest_result.extracted_candidates >= 1
    assert ingest_result.planned_cards == 1
    assert str(fixture_path) not in repr(ingest_result.report)
    assert "webdav" not in repr(ingest_result.report).casefold()
    assert audio_result.processed_items == 2
    assert row.identity.source_type == "kindle-highlights"
    assert row.translation == ""
    assert "Translation" not in mapping
    assert mapping["Image"] == ""
    assert mapping["word_audio"].startswith("[sound:")
    assert mapping["sentence_audio"].startswith("[sound:")

    session.close()
