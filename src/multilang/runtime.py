"""Runtime bootstrap for the shipped CLI path."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from html import unescape
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.provisioning import ensure_database_schema
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.export_repository import ExportRepository
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.repositories.text_repository import TextRepository
from multilang.services.provider_response_cache import ProviderResponseCacheService
from multilang.domain.audio import AudioAssetKind
from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportArtifactStatus,
    ExportDeckArtifact,
    evaluate_export_quality_gate,
    export_field_names_for_language_and_source,
)
from multilang.domain.jobs import JobStage, JobStatus
from multilang.domain.korean import KoreanFrequencyEntry, KoreanFrequencyJobAuthority
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.elevenlabs_speech_adapter import ElevenLabsSpeechAdapter
from multilang.services.fallback_audio_adapter import FallbackAudioAdapter
from multilang.services.google_translate_speech_adapter import GoogleTranslateSpeechAdapter
from multilang.services.audio_synthesis import (
    AudioSynthesisAdapter,
    AudioSynthesisService,
)
from multilang.services.anki_id_registry import assert_anki_id_registry_clean
from multilang.services.assemble_export_cards import AssembleExportCardsService
from multilang.services.audio_integrity import assert_word_audio_matches_word
from multilang.services.export_anki_package import MANDARIN_NOTE_TYPE_NAME, export_anki_package
from multilang.services.export_tabular_bundle import ExportTabularBundleResult, write_export_tabular_bundle
from multilang.services.frequency_decks import build_frequency_level
from multilang.services.generate_job import GenerateJobService
from multilang.services.generate_audio_items import GenerateAudioItemsService
from multilang.services.generate_text_items import GenerateTextItemsService, GenerateTextProgress
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.korean_frequency import load_korean_final_frequency_entries
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance
from multilang.services.lexical_lookup import LexicalLookup
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.rate_limit import RateLimiter
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.library_pronunciation_adapters import (
    FallbackPronunciationAdapter,
    LibraryPronunciationAdapter,
)
from multilang.services.provider_text_adapters import (
    DeepLTranslationAdapter,
    GoogleTranslateAdapter,
    LiteLLMSentenceAdapter,
    can_use_deepl,
    can_use_google_translate,
    can_use_litellm,
)
from multilang.services.generation_report import (
    build_korean_frequency_export_evidence,
    write_generation_report,
    write_korean_frequency_generation_report,
)
from multilang.services.provider_pronunciation_adapters import LiteLLMPronunciationAdapter
from multilang.services.provider_retry import ProviderCircuitBreaker
from multilang.services.regenerate_text_item import RegenerateTextItemService
from multilang.services.tatoeba_sentence_source import (
    StaticTatoebaCandidateProvider,
    TatoebaApiCandidateProvider,
    TatoebaSentenceSource,
)
from multilang.services.text_generation import TextGenerationService
from multilang.services.text_review import ReviewReport, TextReviewService
from multilang.services.text_validation import TextValidationService, looks_like_invalid_translation
from multilang.settings import Settings
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.source_profiles import get_source_profile

_LANGUAGE_NAMES = {
    SupportedLanguage.PT: "Portuguese",
    SupportedLanguage.ES: "Spanish",
    SupportedLanguage.EN: "English",
    SupportedLanguage.FR: "French",
    SupportedLanguage.DE: "German",
    SupportedLanguage.EL: "Greek",
    SupportedLanguage.IT: "Italian",
    SupportedLanguage.PL: "Polish",
    SupportedLanguage.TR: "Turkish",
    SupportedLanguage.RO: "Romanian",
    SupportedLanguage.RU: "Russian",
    SupportedLanguage.NL: "Dutch",
    SupportedLanguage.DA: "Danish",
    SupportedLanguage.NB: "Norwegian Bokmal",
    SupportedLanguage.SV: "Swedish",
    SupportedLanguage.FI: "Finnish",
    SupportedLanguage.HU: "Hungarian",
    SupportedLanguage.CS: "Czech",
    SupportedLanguage.HR: "Croatian",
    SupportedLanguage.LA: "Latin",
    SupportedLanguage.JA: "Japanese",
    SupportedLanguage.ZH: "Mandarin Chinese",
    SupportedLanguage.KO: "Korean",
}


@dataclass(slots=True)
class RuntimeTextResult:
    processed_items: int
    accepted_items: int
    review_required_items: int
    audio_processed_items: int = 0
    audio_reused_items: int = 0
    fallback_audio_items: int = 0
    failed_audio_items: int = 0


@dataclass(slots=True)
class RuntimeExportResult:
    output_path: Path
    card_count: int
    report_json_path: Path | None = None
    report_markdown_path: Path | None = None
    partial: bool = False


@dataclass(frozen=True, slots=True)
class KoreanFrequencyTextRuntimeAuthority:
    """Explicit authority tuple required before Korean final text runtime construction."""

    job_id: str
    bundle_root: Path
    binding_receipt_sha256: str
    authority: KoreanFrequencyJobAuthority


@dataclass(frozen=True, slots=True)
class KoreanFrequencySyntheticExportContract:
    """Count contract for synthetic Korean APKG gates, not production evidence."""

    cards_per_level: int
    exact_scale: bool = False

    @property
    def level_counts(self) -> dict[int, int]:
        return {level: self.cards_per_level for level in (1, 2, 3)}

    @property
    def expected_items(self) -> int:
        return self.cards_per_level * 3

    @property
    def expected_word_assets(self) -> int:
        return self.expected_items

    @property
    def expected_sentence_assets(self) -> int:
        return self.expected_items

    @property
    def expected_media_files(self) -> int:
        return self.expected_word_assets + self.expected_sentence_assets

    @property
    def exact_scale_evidence(self) -> bool:
        return self.exact_scale

    @property
    def production_count_evidence(self) -> bool:
        return False

    @property
    def claim_limit(self) -> str:
        return "synthetic-exact-scale-only" if self.exact_scale else "fast-representative-only"


def build_korean_frequency_synthetic_export_contract(
    *,
    cards_per_level: int,
    exact_scale: bool,
) -> KoreanFrequencySyntheticExportContract:
    if cards_per_level < 1:
        raise ValueError("Korean synthetic export contract requires a positive level size")
    if exact_scale and cards_per_level != 1000:
        raise ValueError("Korean exact-scale synthetic export contract requires 1000 cards per level")
    return KoreanFrequencySyntheticExportContract(cards_per_level=cards_per_level, exact_scale=exact_scale)


@dataclass(frozen=True, slots=True)
class KoreanFrequencySyntheticManifestItem:
    level: int
    ordinal: int
    rank: int
    item_key: str
    lemma_key: str
    word_audio_name: str
    sentence_audio_name: str


@dataclass(frozen=True, slots=True)
class KoreanFrequencySyntheticManifestShape:
    contract: KoreanFrequencySyntheticExportContract
    items: tuple[KoreanFrequencySyntheticManifestItem, ...]
    blocked_mutation_fields: tuple[str, ...]

    @property
    def level_counts(self) -> dict[int, int]:
        return self.contract.level_counts


def build_korean_frequency_synthetic_manifest_shape(
    *,
    cards_per_level: int,
) -> KoreanFrequencySyntheticManifestShape:
    contract = build_korean_frequency_synthetic_export_contract(
        cards_per_level=cards_per_level,
        exact_scale=True,
    )
    items: list[KoreanFrequencySyntheticManifestItem] = []
    for level in (1, 2, 3):
        for ordinal in range(1, cards_per_level + 1):
            rank = ((level - 1) * cards_per_level) + ordinal
            item_key = f"synthetic-ko-exact-{rank:04d}"
            items.append(
                KoreanFrequencySyntheticManifestItem(
                    level=level,
                    ordinal=ordinal,
                    rank=rank,
                    item_key=item_key,
                    lemma_key=f"ko:synthetic:exact:{rank:04d}",
                    word_audio_name=f"{item_key}-word.mp3",
                    sentence_audio_name=f"{item_key}-sentence.mp3",
                )
            )
    return KoreanFrequencySyntheticManifestShape(
        contract=contract,
        items=tuple(items),
        blocked_mutation_fields=(
            "frequency_level",
            "frequency_bundle_sha256",
            "export_gate_receipt_sha256",
            "text_review_receipt_sha256",
            "word_audio_artifact_sha256",
            "sentence_audio_artifact_sha256",
            "word_audio",
            "sentence_audio",
        ),
    )


class RuntimeGenerateService(IngestLexicalItemsService):
    """Repository-backed shipped runtime that composes lexical and Phase 3 text work."""

    def __init__(
        self,
        *,
        text_repository: TextRepository,
        audio_repository: AudioRepository,
        export_repository: ExportRepository,
        provider_call_log_repository: ProviderCallLogRepository,
        generate_text_items_service: GenerateTextItemsService,
        regenerate_text_item_service: RegenerateTextItemService,
        text_review_service: TextReviewService,
        generate_audio_items_service: GenerateAudioItemsService,
        assemble_export_cards_service: AssembleExportCardsService,
        runtime_settings: Settings,
        korean_final_frequency_entries: Iterable[KoreanFrequencyEntry] | None = None,
        korean_source_review_receipt_sha256: str | None = None,
        korean_source_review_aggregate_sha256: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.text_repository = text_repository
        self.audio_repository = audio_repository
        self.export_repository = export_repository
        self.provider_call_log_repository = provider_call_log_repository
        self.generate_text_items_service = generate_text_items_service
        self.regenerate_text_item_service = regenerate_text_item_service
        self.text_review_service = text_review_service
        self.generate_audio_items_service = generate_audio_items_service
        self.assemble_export_cards_service = assemble_export_cards_service
        self.settings = runtime_settings
        self._korean_final_frequency_entries = (
            tuple(korean_final_frequency_entries)
            if korean_final_frequency_entries is not None
            else None
        )
        self._korean_source_review_receipt_sha256 = korean_source_review_receipt_sha256
        self._korean_source_review_aggregate_sha256 = korean_source_review_aggregate_sha256

    def _build_grounded_frequency_level(
        self,
        *,
        language: SupportedLanguage,
        level: int,
        required_count_per_level: int = 1000,
        initially_rejected_lemmas: set[str] | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> tuple[list[LexicalCardCandidate], int]:
        if language is not SupportedLanguage.KO:
            return super()._build_grounded_frequency_level(
                language=language,
                level=level,
                required_count_per_level=required_count_per_level,
                initially_rejected_lemmas=initially_rejected_lemmas,
                rate_limiter=rate_limiter,
            )
        if self._korean_final_frequency_entries is None:
            raise ValueError("Korean final frequency runtime requires explicit final entries")
        if (
            self._korean_source_review_receipt_sha256 is None
            or self._korean_source_review_aggregate_sha256 is None
        ):
            raise ValueError("Korean final frequency runtime requires source review receipts")

        rejected_lemmas = {lemma.casefold() for lemma in (initially_rejected_lemmas or set())}
        candidates = build_frequency_level(
            language,
            level=level,
            required_count_per_level=required_count_per_level,
            rejected_lemmas=rejected_lemmas,
            korean_final_entries=self._korean_final_frequency_entries,
            source_review_receipt_sha256=self._korean_source_review_receipt_sha256,
            source_review_aggregate_sha256=self._korean_source_review_aggregate_sha256,
        )
        grounded_candidates: list[LexicalCardCandidate] = []
        for candidate in candidates:
            grounded_candidate = self.grounding_service.ground_frequency_candidate(
                language=language,
                candidate=candidate,
                rate_limiter=rate_limiter,
            )
            if grounded_candidate.grounding_status is not GroundingStatus.GROUNDED:
                raise ValueError("unable to ground Korean final frequency candidate")
            grounded_candidates.append(grounded_candidate)
        return grounded_candidates, 0

    def generate_text(
        self,
        *,
        job_id: str,
        deck_language: object,
        missing_only: bool = False,
        max_items: int | None = None,
        progress_callback: Callable[[GenerateTextProgress], None] | None = None,
        rate_limiter: RateLimiter | None = None,
        repair_only: bool = False,
        synthesize_audio: bool = True,
        concurrency: int = 1,
    ) -> RuntimeTextResult:
        result = self.generate_text_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
            missing_only=missing_only,
            max_items=max_items,
            progress_callback=progress_callback,
            rate_limiter=rate_limiter,
            repair_only=repair_only,
            concurrency=concurrency,
        )
        if not synthesize_audio:
            return RuntimeTextResult(
                processed_items=result.processed_items,
                accepted_items=result.accepted_items,
                review_required_items=result.review_required_items,
            )
        audio_item_keys = set(result.processed_item_keys) if missing_only or max_items is not None else None
        audio_result = self.generate_audio_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
            item_keys=audio_item_keys,
        )
        return RuntimeTextResult(
            processed_items=result.processed_items,
            accepted_items=result.accepted_items,
            review_required_items=result.review_required_items,
            audio_processed_items=audio_result.processed_items,
            audio_reused_items=audio_result.reused_items,
            fallback_audio_items=audio_result.fallback_items,
            failed_audio_items=audio_result.failed_items,
        )

    def synthesize_audio(
        self,
        *,
        job_id: str,
        deck_language: object,
        missing_only: bool = False,
        fallback_only: bool = False,
        max_items: int | None = None,
    ) -> RuntimeTextResult:
        audio_result = self.generate_audio_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
            missing_only=missing_only,
            fallback_only=fallback_only,
            max_items=max_items,
        )
        return RuntimeTextResult(
            processed_items=0,
            accepted_items=0,
            review_required_items=0,
            audio_processed_items=audio_result.processed_items,
            audio_reused_items=audio_result.reused_items,
            fallback_audio_items=audio_result.fallback_items,
            failed_audio_items=audio_result.failed_items,
        )

    def regenerate_text_item(self, *, job_id: str, item_key: str, deck_language: object) -> RuntimeTextResult:
        record = self.regenerate_text_item_service.execute(
            job_id=job_id,
            item_key=item_key,
            deck_language=deck_language,
        )
        audio_result = self.generate_audio_items_service.execute(
            job_id=job_id,
            deck_language=deck_language,
            item_keys={item_key},
        )
        return RuntimeTextResult(
            processed_items=1,
            accepted_items=1 if record.review_status.value == "accepted" else 0,
            review_required_items=1 if record.review_status.value == "review_required" else 0,
            audio_processed_items=audio_result.processed_items,
            audio_reused_items=audio_result.reused_items,
            fallback_audio_items=audio_result.fallback_items,
            failed_audio_items=audio_result.failed_items,
        )

    def build_review_report(self, *, job_id: str, output_path: object) -> ReviewReport:
        return self.text_review_service.build_review_report(job_id=job_id, output_path=output_path)

    def export_job(
        self,
        *,
        job_id: str,
        export_format: ExportArtifactFormat,
        output_dir: Path,
        deck_name: str | None = None,
        refresh_snapshots: bool = False,
        allow_partial: bool = False,
    ) -> RuntimeExportResult:
        assert_anki_id_registry_clean(production_roots=True)
        job = self.job_service.repository.get_job(job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")

        rows = [] if refresh_snapshots else self.export_repository.list_card_snapshots(job_id)
        if not rows:
            rows = self.assemble_export_cards_service.execute(
                job_id=job_id,
                deck_language=SupportedLanguage(job.language),
            ).cards

        text_records = self.text_repository.list_records_for_job(job_id)
        review_required_count = sum(1 for record in text_records if record.review_status.value == "review_required")
        invalid_translation_count = sum(
            1
            for record in text_records
            if record.review_status.value == "accepted"
            and looks_like_invalid_translation(record.translation_text or "")
        )
        audio_assets = (
            self.audio_repository.list_assets_for_job(job_id)
            if hasattr(self.audio_repository, "list_assets_for_job")
            else []
        )
        missing_audio_count, non_synthesized_audio_count, fallback_audio_count = _audio_gate_counts(rows, audio_assets)
        gate_result = evaluate_export_quality_gate(
            source_type=job.source_type,
            rows=rows,
            review_required_count=review_required_count,
            invalid_translation_count=invalid_translation_count,
            missing_audio_count=missing_audio_count,
            non_synthesized_audio_count=non_synthesized_audio_count,
            fallback_audio_count=fallback_audio_count,
            allow_partial=allow_partial,
        )
        if not gate_result.passed:
            self.job_service.repository.update_job_status(
                job_id,
                status=JobStatus.BLOCKED,
                current_stage=JobStage.EXPORT,
                failed_items=review_required_count + invalid_translation_count + missing_audio_count + non_synthesized_audio_count + fallback_audio_count,
            )
            raise ValueError(f"export quality gate failed: {gate_result.message()}")

        resolved_deck_name = _sanitize_deck_name(deck_name or _default_deck_name(SupportedLanguage(job.language)))
        output_path = output_dir / f"{job_id}.{export_format.value}"
        media_index = self._build_media_index(rows)
        if export_format is ExportArtifactFormat.APKG:
            package_result = export_anki_package(
                rows=rows,
                media_index=media_index,
                output_path=output_path,
                deck_name=resolved_deck_name,
            )
            card_count = package_result.card_count
        else:
            tabular_result = write_export_tabular_bundle(
                rows=rows,
                export_format=export_format,
                output_dir=output_dir,
                deck_name=resolved_deck_name,
                note_type_name=_note_type_name_for_rows(rows),
            )
            if tabular_result.output_path != output_path:
                tabular_result.output_path.replace(output_path)
            card_count = tabular_result.card_count

        export_status = ExportArtifactStatus.PARTIAL if gate_result.partial else ExportArtifactStatus.COMPLETED
        artifact = self.export_repository.upsert_deck_export(
            ExportDeckArtifact(
                job_id=job_id,
                export_format=export_format,
                deck_name=resolved_deck_name,
                output_path=str(output_path),
                card_count=card_count,
                status=export_status,
            )
        )
        self.job_service.repository.update_job_status(
            job_id,
            status=JobStatus.PARTIAL if gate_result.partial else JobStatus.COMPLETED,
            current_stage=JobStage.EXPORT,
            failed_items=review_required_count if gate_result.partial else 0,
        )
        report = write_generation_report(
            job=self.job_service.repository.get_job(job_id),
            export_artifact=artifact,
            rows=rows,
            text_records=text_records,
            audio_assets=audio_assets,
            gate_result=gate_result,
            output_dir=output_path.parent,
            provider_call_records=self.provider_call_log_repository.list_for_job(job_id),
        )
        return RuntimeExportResult(
            output_path=output_path,
            card_count=card_count,
            report_json_path=report.json_path,
            report_markdown_path=report.markdown_path,
            partial=gate_result.partial,
        )

    def export_korean_frequency_apkg(
        self,
        *,
        job_id: str,
        binding_receipt_file: Path,
        bundle_root: Path,
        manifest_file: Path,
        output_path: Path,
        generation_report_json_path: Path,
        generation_report_markdown_path: Path,
        cards_per_level: int,
        expected_items: int,
        expected_word_assets: int,
        expected_sentence_assets: int,
        no_partial: bool,
    ) -> RuntimeExportResult:
        assert_anki_id_registry_clean(production_roots=True)
        if not no_partial:
            raise ValueError("Korean frequency export requires --no-partial")
        _validate_korean_frequency_export_inputs(
            database_url=self.settings.database_url,
            binding_receipt_file=binding_receipt_file,
            bundle_root=bundle_root,
            manifest_file=manifest_file,
            output_path=output_path,
            generation_report_json_path=generation_report_json_path,
            generation_report_markdown_path=generation_report_markdown_path,
            cards_per_level=cards_per_level,
            expected_items=expected_items,
            expected_word_assets=expected_word_assets,
            expected_sentence_assets=expected_sentence_assets,
        )
        job = self.job_service.repository.get_job(job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")
        if job.language != SupportedLanguage.KO.value or job.source_type != "frequency":
            raise ValueError("job is not a Korean frequency job")

        rows = self.assemble_export_cards_service.execute(
            job_id=job_id,
            deck_language=SupportedLanguage.KO,
        ).cards
        text_records = self.text_repository.list_records_for_job(job_id)
        audio_assets = self.audio_repository.list_assets_for_job(job_id)
        missing_audio_count, non_synthesized_audio_count, fallback_audio_count = _audio_gate_counts(rows, audio_assets)
        gate_result = evaluate_export_quality_gate(
            source_type="frequency",
            rows=rows,
            review_required_count=sum(1 for record in text_records if record.review_status.value == "review_required"),
            invalid_translation_count=sum(
                1
                for record in text_records
                if record.review_status.value == "accepted" and looks_like_invalid_translation(record.translation_text or "")
            ),
            missing_audio_count=missing_audio_count,
            non_synthesized_audio_count=non_synthesized_audio_count,
            fallback_audio_count=fallback_audio_count,
            allow_partial=False,
            cards_per_level=cards_per_level,
            expected_items=expected_items,
        )
        if not gate_result.passed:
            raise ValueError(f"export quality gate failed: {gate_result.message()}")
        _require_korean_frequency_audio_counts(
            audio_assets,
            expected_word_assets=expected_word_assets,
            expected_sentence_assets=expected_sentence_assets,
        )

        media_index = self._build_media_index(rows)
        binding_receipt_sha256 = _sha256_file(binding_receipt_file)
        manifest_sha256 = _sha256_file(manifest_file)
        resolved_deck_name = _sanitize_deck_name("Multilang Korean::Frequency")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generation_report_json_path.parent.mkdir(parents=True, exist_ok=True)
        generation_report_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="multilang-ko-export-") as directory:
            stage_root = Path(directory)
            staged_apkg = stage_root / output_path.name
            staged_json = stage_root / generation_report_json_path.name
            staged_markdown = stage_root / generation_report_markdown_path.name
            export_anki_package(
                rows=rows,
                media_index=media_index,
                output_path=staged_apkg,
                deck_name=resolved_deck_name,
                cards_per_level=cards_per_level,
                expected_items=expected_items,
            )
            apkg_sha256 = _sha256_file(staged_apkg)
            evidence = build_korean_frequency_export_evidence(
                job=job,
                rows=rows,
                text_records=text_records,
                audio_assets=audio_assets,
                provider_call_records=self.provider_call_log_repository.list_for_job(job_id),
                apkg_sha256=apkg_sha256,
                binding_receipt_sha256=binding_receipt_sha256,
                manifest_sha256=manifest_sha256,
                cards_per_level=cards_per_level,
                expected_items=expected_items,
                expected_word_assets=expected_word_assets,
                expected_sentence_assets=expected_sentence_assets,
            )
            write_korean_frequency_generation_report(
                evidence,
                json_path=staged_json,
                markdown_path=staged_markdown,
            )
            _replace_staged_outputs(
                (staged_apkg, output_path),
                (staged_json, generation_report_json_path),
                (staged_markdown, generation_report_markdown_path),
            )

        artifact = self.export_repository.upsert_deck_export(
            ExportDeckArtifact(
                job_id=job_id,
                export_format=ExportArtifactFormat.APKG,
                deck_name=resolved_deck_name,
                output_path=str(output_path),
                card_count=len(rows),
                status=ExportArtifactStatus.COMPLETED,
                frequency_bundle_sha256=rows[0].frequency_bundle_sha256 if rows else None,
                export_manifest_sha256=manifest_sha256,
                export_gate_receipt_sha256=rows[0].export_gate_receipt_sha256 if rows else None,
            )
        )
        self.job_service.repository.update_job_status(
            job_id,
            status=JobStatus.COMPLETED,
            current_stage=JobStage.EXPORT,
            failed_items=0,
        )
        return RuntimeExportResult(
            output_path=Path(artifact.output_path),
            card_count=artifact.card_count,
            report_json_path=generation_report_json_path,
            report_markdown_path=generation_report_markdown_path,
            partial=False,
        )

    def _build_media_index(self, rows: list[object]) -> dict[str, Path]:
        media_index: dict[str, Path] = {}
        asset_index = self._preload_audio_assets(rows)
        for row in rows:
            field_names = export_field_names_for_language_and_source(
                language=row.identity.language,
                source_type=row.identity.source_type,
            )
            if "word_audio" in field_names:
                word_asset = self._get_audio_asset(
                    asset_index=asset_index,
                    job_id=row.identity.job_id,
                    item_key=row.identity.item_key,
                    asset_kind=AudioAssetKind.WORD,
                )
                if word_asset is None:
                    raise ValueError(f"missing required word audio for item {row.identity.item_key}")
                assert_word_audio_matches_word(
                    word_asset,
                    unescape(row.word),
                    item_key=row.identity.item_key,
                )
                word_path = Path(word_asset.provenance.storage_path)
                _validate_media_reference(sound_tag=row.word_audio, media_path=word_path)
                _add_media_reference(media_index, sound_tag=row.word_audio, media_path=word_path)
            if "sentence_audio" in field_names:
                sentence_asset = self._get_audio_asset(
                    asset_index=asset_index,
                    job_id=row.identity.job_id,
                    item_key=row.identity.item_key,
                    asset_kind=AudioAssetKind.SENTENCE,
                )
                if sentence_asset is None:
                    raise ValueError(f"missing required sentence audio for item {row.identity.item_key}")
                sentence_path = Path(sentence_asset.provenance.storage_path)
                _validate_media_reference(sound_tag=row.sentence_audio, media_path=sentence_path)
                _add_media_reference(media_index, sound_tag=row.sentence_audio, media_path=sentence_path)
        return media_index

    def _preload_audio_assets(self, rows: list[object]) -> dict[tuple[str, str], object] | None:
        job_ids = {row.identity.job_id for row in rows}
        if len(job_ids) != 1 or not hasattr(self.audio_repository, "list_assets_for_job"):
            return None

        job_id = next(iter(job_ids))
        session = getattr(self.audio_repository, "session", None)
        expire_all = getattr(session, "expire_all", None)
        if callable(expire_all):
            expire_all()
        return {
            (asset.item_key, asset.asset_kind.value): asset
            for asset in self.audio_repository.list_assets_for_job(job_id)
        }

    def _get_audio_asset(
        self,
        *,
        asset_index: dict[tuple[str, str], object] | None,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
    ) -> object | None:
        if asset_index is not None:
            return asset_index.get((item_key, asset_kind.value))
        return self.audio_repository.get_asset(job_id, item_key, asset_kind)


def _validate_media_reference(*, sound_tag: str, media_path: Path) -> None:
    expected_sound_tag = f"[sound:{media_path.name}]"
    if sound_tag != expected_sound_tag:
        raise ValueError(f"media basename mismatch for {media_path.name}")
    if not media_path.exists():
        raise ValueError(f"missing media file for {media_path.name}")


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_korean_frequency_export_inputs(
    *,
    database_url: str,
    binding_receipt_file: Path,
    bundle_root: Path,
    manifest_file: Path,
    output_path: Path,
    generation_report_json_path: Path,
    generation_report_markdown_path: Path,
    cards_per_level: int,
    expected_items: int,
    expected_word_assets: int,
    expected_sentence_assets: int,
) -> None:
    if database_url.strip() != database_url or not database_url.strip():
        raise ValueError("database URL is required")
    for label, path in {
        "binding receipt": binding_receipt_file,
        "manifest file": manifest_file,
    }.items():
        if not path.is_file():
            raise ValueError(f"Korean frequency export requires explicit {label}")
    if not bundle_root.is_dir():
        raise ValueError("Korean frequency export requires explicit bundle root")
    if cards_per_level < 1 or expected_items < 1:
        raise ValueError("Korean frequency export counts must be positive")
    if expected_items != cards_per_level * 3:
        raise ValueError("Korean frequency export expected_items must equal three exact levels")
    if expected_word_assets != expected_items or expected_sentence_assets != expected_items:
        raise ValueError("Korean frequency export expected audio counts must match expected_items")
    outputs = (output_path, generation_report_json_path, generation_report_markdown_path)
    if any(path.is_dir() for path in outputs):
        raise ValueError("Korean frequency export output paths must be files")
    resolved_outputs = {path.resolve() for path in outputs}
    if len(resolved_outputs) != len(outputs):
        raise ValueError("Korean frequency export output paths must be distinct")


def _require_korean_frequency_audio_counts(
    audio_assets: list[object],
    *,
    expected_word_assets: int,
    expected_sentence_assets: int,
) -> None:
    counts = {AudioAssetKind.WORD.value: 0, AudioAssetKind.SENTENCE.value: 0}
    for asset in audio_assets:
        kind = getattr(getattr(asset, "asset_kind", ""), "value", getattr(asset, "asset_kind", ""))
        if kind in counts and getattr(asset, "ready_for_korean_final_export", False):
            counts[str(kind)] += 1
    if counts[AudioAssetKind.WORD.value] != expected_word_assets:
        raise ValueError(
            f"Korean frequency export approved word audio count {counts[AudioAssetKind.WORD.value]}/{expected_word_assets}"
        )
    if counts[AudioAssetKind.SENTENCE.value] != expected_sentence_assets:
        raise ValueError(
            "Korean frequency export approved sentence audio count "
            f"{counts[AudioAssetKind.SENTENCE.value]}/{expected_sentence_assets}"
        )


def _replace_staged_outputs(*pairs: tuple[Path, Path]) -> None:
    backups: list[tuple[Path | None, Path]] = []
    written: list[Path] = []
    try:
        for staged, destination in pairs:
            if not staged.is_file():
                raise ValueError(f"missing staged output: {staged.name}")
            backup = None
            if destination.exists():
                backup = destination.with_name(
                    f".{destination.name}.multilang-backup-{sha256(str(destination.resolve()).encode('utf-8')).hexdigest()[:12]}"
                )
                if backup.exists():
                    raise ValueError(f"existing backup blocks atomic replace: {backup}")
                destination.replace(backup)
            staged.replace(destination)
            backups.append((backup, destination))
            written.append(destination)
    except Exception:
        for destination in reversed(written):
            if destination.exists():
                destination.unlink()
        for backup, destination in reversed(backups):
            if backup is not None and backup.exists():
                backup.replace(destination)
        raise
    for backup, _destination in backups:
        if backup is not None and backup.exists():
            backup.unlink()


def _audio_gate_counts(rows: list[object], audio_assets: list[object]) -> tuple[int, int, int]:
    from multilang.domain.audio import AudioAssetKind, AudioSynthesisStatus

    asset_index = {(asset.item_key, asset.asset_kind.value): asset for asset in audio_assets}
    missing = 0
    non_synthesized = 0
    fallback = 0
    for row in rows:
        required = [AudioAssetKind.SENTENCE]
        if "word_audio" in export_field_names_for_language_and_source(
            language=row.identity.language,
            source_type=row.identity.source_type,
        ):
            required.append(AudioAssetKind.WORD)
        for kind in required:
            asset = asset_index.get((row.identity.item_key, kind.value))
            if asset is None:
                missing += 1
            elif asset.provenance.status is not AudioSynthesisStatus.SYNTHESIZED or asset.provenance.byte_size <= 0:
                non_synthesized += 1
            elif asset.provenance.fallback_used:
                fallback += 1
    return missing, non_synthesized, fallback


def _add_media_reference(media_index: dict[str, Path], *, sound_tag: str, media_path: Path) -> None:
    existing_path = media_index.get(sound_tag)
    if existing_path is not None and existing_path != media_path:
        raise ValueError(f"conflicting media file for {sound_tag}")
    media_index[sound_tag] = media_path


def _build_translation_adapter(runtime_settings: Settings) -> object:
    if runtime_settings.translation_provider == "local":
        return LocalTranslationAdapter()
    if can_use_deepl(runtime_settings):
        return DeepLTranslationAdapter(runtime_settings)
    if can_use_google_translate(runtime_settings):
        return GoogleTranslateAdapter()
    if runtime_settings.translation_provider == "deepl":
        raise ValueError("DeepL translation requires MULTILANG_DEEPL_API_KEY or DEEPL_API_KEY")
    raise ValueError(f"unsupported translation provider: {runtime_settings.translation_provider}")


def _build_sentence_adapter(runtime_settings: Settings) -> object:
    if runtime_settings.text_generation_provider == "local":
        return LocalSentenceAdapter()
    if can_use_litellm(runtime_settings):
        return LiteLLMSentenceAdapter(runtime_settings)
    if runtime_settings.text_generation_provider == "litellm":
        raise ValueError(
            "LiteLLM sentence generation requires MULTILANG_LITELLM_API_KEY, "
            "MULTILANG_OPENAI_API_KEY, or MULTILANG_OPENROUTER_API_KEY"
        )
    raise ValueError(f"unsupported text generation provider: {runtime_settings.text_generation_provider}")


def _build_pronunciation_adapter(runtime_settings: Settings) -> object:
    adapters: list[object] = [LibraryPronunciationAdapter()]
    if can_use_litellm(runtime_settings):
        adapters.append(LiteLLMPronunciationAdapter(runtime_settings))
    if len(adapters) == 1:
        return adapters[0]
    return FallbackPronunciationAdapter(adapters)


def _build_audio_adapter(runtime_settings: Settings) -> AudioSynthesisAdapter:
    providers = [runtime_settings.audio_provider, *runtime_settings.audio_fallback_providers]
    adapters = [_build_single_audio_adapter(runtime_settings, provider) for provider in dict.fromkeys(providers)]
    if len(adapters) == 1:
        return adapters[0]
    return FallbackAudioAdapter(adapters)


def _build_single_audio_adapter(runtime_settings: Settings, provider: str) -> AudioSynthesisAdapter:
    if provider == "azure":
        return AzureSpeechAdapter(runtime_settings)
    if provider == "elevenlabs":
        return ElevenLabsSpeechAdapter(runtime_settings)
    if provider == "google_translate":
        return GoogleTranslateSpeechAdapter(runtime_settings)
    raise ValueError(f"unsupported audio provider: {provider}")


def build_runtime_service(
    settings: Settings | None = None,
    *,
    audio_adapter: AudioSynthesisAdapter | None = None,
    korean_morphology_service: KiwiKoreanMorphologyService | None = None,
    korean_final_frequency_entries: Iterable[KoreanFrequencyEntry] | None = None,
    korean_source_review_receipt_sha256: str | None = None,
    korean_source_review_aggregate_sha256: str | None = None,
) -> IngestLexicalItemsService:
    """Construct the repository-backed orchestration service from runtime settings."""

    runtime_settings = settings or Settings()
    engine = create_engine(runtime_settings.database_url)
    # SQLite (dev/tests) is created in-place; Postgres is migrated with Alembic
    # so the migrations remain the single source of truth for the schema.
    ensure_database_schema(engine, runtime_settings.database_url)
    session = Session(engine)
    job_repository = JobRepository(session)
    lexical_repository = LexicalRepository(session)
    text_repository = TextRepository(session)
    audio_repository = AudioRepository(session)
    export_repository = ExportRepository(session)
    provider_call_log_repository = ProviderCallLogRepository(session)
    circuit_breaker = ProviderCircuitBreaker(
        failure_threshold=runtime_settings.provider_circuit_failure_threshold,
        cooldown_seconds=runtime_settings.provider_circuit_cooldown_seconds,
    )
    highlight_import_repository = HighlightImportRepository(session)
    generate_job_service = GenerateJobService(job_repository)
    translation_adapter = _build_translation_adapter(runtime_settings)
    sentence_adapter = _build_sentence_adapter(runtime_settings)
    text_generation_service = TextGenerationService(
        sentence_adapter=sentence_adapter,
        translation_adapter=translation_adapter,
        provider_cache=ProviderResponseCacheService(text_repository),
        provider_call_logger=provider_call_log_repository,
        circuit_breaker=circuit_breaker,
        retry_attempts=runtime_settings.default_retry_attempts,
        retry_base_delay_seconds=runtime_settings.provider_retry_base_delay_seconds,
        retry_max_delay_seconds=runtime_settings.provider_retry_max_delay_seconds,
        retry_jitter_ratio=runtime_settings.provider_retry_jitter_ratio,
    )

    # Latin structured generation service (uses the model for gramatica, definition etc. in dynamic flow)
    latin_card_service = None
    if hasattr(sentence_adapter, "generate_latin_cards"):
        try:
            from multilang.services.latin_card_generation import LatinCardGenerationService
            latin_card_service = LatinCardGenerationService(
                generator=lambda seeds: sentence_adapter.generate_latin_cards(seeds)
            )
        except Exception:
            latin_card_service = None
    korean_morphology = (
        korean_morphology_service
        if korean_morphology_service is not None
        else KiwiKoreanMorphologyService()
    )
    text_validation_service = TextValidationService(
        korean_matcher=korean_morphology
    )
    tatoeba_sentence_source = TatoebaSentenceSource(
        candidate_provider=(
            TatoebaApiCandidateProvider()
            if runtime_settings.tatoeba_enabled
            else StaticTatoebaCandidateProvider()
        )
    )
    audio_synthesis_service = AudioSynthesisService(
        adapter=audio_adapter or _build_audio_adapter(runtime_settings),
        settings=runtime_settings,
        provider_call_logger=provider_call_log_repository,
        circuit_breaker=circuit_breaker,
    )
    return RuntimeGenerateService(
        job_service=generate_job_service,
        lexical_repo=lexical_repository,
        highlight_import_repo=highlight_import_repository,
        settings=runtime_settings,
        grounding_service=LexicalGroundingService(
            lookup=LexicalLookup(data_dir=runtime_settings.lexicon_data_dir),
            pronunciation_generator=_build_pronunciation_adapter(runtime_settings),
            definition_generator=sentence_adapter,
            allow_frequency_seed_fallback=True,
            korean_morphology=korean_morphology,
        ),
        text_repository=text_repository,
        audio_repository=audio_repository,
        export_repository=export_repository,
        provider_call_log_repository=provider_call_log_repository,
        generate_text_items_service=GenerateTextItemsService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            text_generation_service=text_generation_service,
            text_validation_service=text_validation_service,
            tatoeba_sentence_source=tatoeba_sentence_source,
            highlight_import_repository=highlight_import_repository,
            latin_card_service=latin_card_service,
        ),
        regenerate_text_item_service=RegenerateTextItemService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            text_generation_service=text_generation_service,
            text_validation_service=text_validation_service,
        ),
        text_review_service=TextReviewService(text_repository=text_repository),
        generate_audio_items_service=GenerateAudioItemsService(
            job_repository=job_repository,
            lexical_repository=lexical_repository,
            text_repository=text_repository,
            audio_repository=audio_repository,
            audio_synthesis_service=audio_synthesis_service,
        ),
        assemble_export_cards_service=AssembleExportCardsService(
            text_repository=text_repository,
            lexical_repository=lexical_repository,
            audio_repository=audio_repository,
            export_repository=export_repository,
        ),
        runtime_settings=runtime_settings,
        korean_final_frequency_entries=korean_final_frequency_entries,
        korean_source_review_receipt_sha256=korean_source_review_receipt_sha256,
        korean_source_review_aggregate_sha256=korean_source_review_aggregate_sha256,
    )


def build_korean_frequency_text_runtime_service(
    *,
    settings: Settings,
    runtime_authority: KoreanFrequencyTextRuntimeAuthority,
    korean_morphology_service: KiwiKoreanMorphologyService | None = None,
    phase31_provenance_verifier: Callable[..., object] = verify_active_korean_foundation_snapshot_provenance,
    entry_loader: Callable[..., tuple[KoreanFrequencyEntry, ...]] = load_korean_final_frequency_entries,
    runtime_builder: Callable[..., object] = build_runtime_service,
) -> object:
    """Revalidate Phase 31 and bundle authority immediately before runtime adapters."""

    authority = runtime_authority.authority
    if authority.stage not in {"pilot_base", "pilot_audio", "full"}:
        raise ValueError("Korean frequency text authority stage is invalid")
    if runtime_authority.binding_receipt_sha256 != authority.source_review_aggregate_sha256:
        raise ValueError("Korean frequency binding receipt drift")

    report = phase31_provenance_verifier(
        expected_receipt_sha256=authority.phase31_validation_receipt_sha256,
    )
    expected_report_hashes = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, expected in expected_report_hashes.items():
        if getattr(report, field, None) != expected:
            raise ValueError("Phase 31 active authority drift")

    entries = entry_loader(
        job_id=runtime_authority.job_id,
        bundle_root=runtime_authority.bundle_root,
        binding_receipt_sha256=runtime_authority.binding_receipt_sha256,
        authority=authority,
        repo_root=Path.cwd(),
    )
    return runtime_builder(
        settings=settings,
        korean_morphology_service=korean_morphology_service,
        korean_final_frequency_entries=entries,
        korean_source_review_receipt_sha256=runtime_authority.binding_receipt_sha256,
        korean_source_review_aggregate_sha256=authority.source_review_aggregate_sha256,
    )


def _sanitize_deck_name(deck_name: str) -> str:
    return " ".join(deck_name.replace("::", " - ").split())


def _default_deck_name(language: SupportedLanguage) -> str:
    return f"Multilang {_LANGUAGE_NAMES[language]}"


def _note_type_name_for_rows(rows: list[object]) -> str:
    source_types = {row.identity.source_type for row in rows}
    if len(source_types) > 1:
        raise ValueError("cannot export mixed source types in one note model")
    source_type = next(iter(source_types), "frequency")
    languages = {row.identity.language for row in rows}
    if len(languages) > 1:
        raise ValueError("cannot export mixed languages in one note model")
    # For Latin (la), prefer the dedicated template that includes Definition + Grammar
    # even in dynamic flows (non frozen). This keeps Latin card style.
    # If using legacy latin-mvp source, it already maps to it.
    deck_language = getattr(rows[0].identity, 'language', None) if rows else None
    if deck_language == "zh" or (hasattr(deck_language, 'value') and deck_language.value == "zh"):
        if source_type in {"frequency", "word-list"}:
            return MANDARIN_NOTE_TYPE_NAME
    if deck_language == "ja" or (hasattr(deck_language, 'value') and deck_language.value == "ja"):
        if source_type == "frequency":
            return "Multilang::Japanese Card"
    if deck_language == "la" or (hasattr(deck_language, 'value') and deck_language.value == "la"):
        return "Multilang::Classical Latin MVP"
    return get_source_profile(source_type).note_type_name
