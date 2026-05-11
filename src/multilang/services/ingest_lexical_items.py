"""Coordinate lexical ingestion for frequency decks and custom word lists."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from multilang.domain.highlights import HighlightImportManifest
from multilang.domain.jobs import GenerationRequest, JobStage, SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.services.execution_report import JobExecutionReport
from multilang.services.frequency_decks import LEVEL_WINDOWS, build_frequency_level
from multilang.services.generate_job import GenerateJobService
from multilang.services.highlight_candidate_extraction import extract_highlight_candidates
from multilang.services.kindle_highlight_parser import parse_kindle_highlight_export
from multilang.services.lexical_grounding import (
    LexicalGroundingService,
    build_lexical_grounding_service,
)
from multilang.services.word_list_parser import parse_word_list
from multilang.settings import Settings


@dataclass(slots=True)
class IngestLexicalItemsResult:
    """Combined lexical-ingestion counts and lifecycle report."""

    report: JobExecutionReport
    grounded_candidates: int
    pending_groundings: int
    rejected_rows: int
    backfilled_candidates: int
    level_counts: dict[int, int]
    imported_highlights: int = 0
    rejected_highlights: int = 0
    extracted_candidates: int = 0
    duplicate_candidates: int = 0
    reused_existing_items: int = 0
    newly_planned_candidates: int = 0
    blocked_candidates: int = 0
    planned_cards: int = 0


class IngestLexicalItemsService:
    """Coordinate lexical ingestion for both frequency and custom-list sources."""

    def __init__(
        self,
        job_service: GenerateJobService,
        lexical_repo: LexicalRepository,
        settings: Settings | None = None,
        grounding_service: LexicalGroundingService | None = None,
        highlight_import_repo: HighlightImportRepository | None = None,
    ) -> None:
        self.job_service = job_service
        self.repository = job_service.repository
        self.lexical_repo = lexical_repo
        self.settings = settings or Settings()
        self.grounding_service = grounding_service or build_lexical_grounding_service(
            self.settings.lexicon_data_dir
        )
        self.highlight_import_repo = highlight_import_repo

    def execute(self, request: GenerationRequest) -> IngestLexicalItemsResult:
        """Execute lexical ingestion for the shipped runtime path."""

        if request.source_type == "frequency":
            return self._ingest_frequency_deck(request)
        if request.source_type == "word-list":
            return self._ingest_word_list(request)
        if request.source_type == "kindle-highlights":
            return self._ingest_highlights(request)
        raise ValueError(f"Unsupported source type: {request.source_type}")

    def _ingest_highlights(self, request: GenerationRequest) -> IngestLexicalItemsResult:
        if request.input_file is None:
            raise ValueError("kindle-highlights requests require an input file")
        if self.highlight_import_repo is None:
            raise ValueError("kindle-highlights requests require a highlight import repository")

        parsed = parse_kindle_highlight_export(request.input_file)
        extraction = extract_highlight_candidates(parsed.highlights, language=request.language)
        candidates_by_key = {candidate.item_key: candidate for candidate in extraction.candidates}
        candidate_keys = [candidate.item_key for candidate in extraction.candidates]
        import_content_hash = sha256(
            "\n".join(sorted(highlight.provenance.content_hash for highlight in parsed.highlights)).encode("utf-8")
        ).hexdigest()
        orchestration = self.job_service.orchestrate(request, requested_item_keys=candidate_keys)
        report = JobExecutionReport(
            orchestration=orchestration,
            progress_updates=[],
            retried_item_keys=[],
            failed_item_keys=[],
        )
        if orchestration.diagnostic is not None:
            return IngestLexicalItemsResult(
                report=report,
                grounded_candidates=0,
                pending_groundings=0,
                rejected_rows=len(parsed.rejected),
                backfilled_candidates=0,
                level_counts={1: 0, 2: 0, 3: 0},
                imported_highlights=len(parsed.highlights),
                rejected_highlights=len(parsed.rejected),
                extracted_candidates=len(extraction.candidates),
                duplicate_candidates=extraction.duplicate_count,
            )

        self.highlight_import_repo.upsert_import_records(
            orchestration.job_id,
            import_content_hash,
            parsed.highlights,
        )
        self.highlight_import_repo.upsert_import_manifest(
            orchestration.job_id,
            HighlightImportManifest(
                import_content_hash=import_content_hash,
                candidate_keys=candidate_keys,
                counts={
                    "imported_highlights": len(parsed.highlights),
                    "rejected_highlights": len(parsed.rejected),
                    "extracted_candidates": len(extraction.candidates),
                    "duplicate_candidates": extraction.duplicate_count,
                },
            ),
        )

        candidate_rows: list[tuple[str, str, LexicalCardCandidate]] = []
        grounded_item_keys: list[str] = []
        blocked_candidates = 0
        for item_key in orchestration.pending_item_keys:
            highlight_candidate = candidates_by_key[item_key]
            grounded = self.grounding_service.ground_highlight_candidate(
                language=request.language,
                candidate=highlight_candidate,
            )
            if grounded.grounding_status is not GroundingStatus.GROUNDED:
                blocked_candidates += 1
                continue
            safe_provenance = grounded.provenance.model_copy(
                update={
                    "notes": [
                        *grounded.provenance.notes,
                        f"first_highlight_id={highlight_candidate.first_highlight_id}",
                        f"source_content_hash={highlight_candidate.source_content_hash}",
                        f"first_source_index={highlight_candidate.first_source_index}",
                        f"occurrence_count={highlight_candidate.occurrence_count}",
                    ]
                }
            )
            grounded = grounded.model_copy(update={"provenance": safe_provenance})
            candidate_rows.append((item_key, highlight_candidate.source_content_hash, grounded))
            grounded_item_keys.append(item_key)

        self.lexical_repo.upsert_candidates(
            job_id=orchestration.job_id,
            run_key=orchestration.run_key,
            source_type="kindle-highlights",
            candidates=candidate_rows,
        )
        if grounded_item_keys:
            self.repository.record_item_successes(
                orchestration.job_id,
                item_keys=grounded_item_keys,
                completed_stage=JobStage.INGEST,
            )
        if grounded_item_keys or orchestration.skipped_item_keys:
            self.repository.advance_job_to_stage(orchestration.job_id, JobStage.GENERATE_TEXT)

        result = self._result_from_persisted_candidates(report=report)
        result.imported_highlights = len(parsed.highlights)
        result.rejected_highlights = len(parsed.rejected)
        result.extracted_candidates = len(extraction.candidates)
        result.duplicate_candidates = extraction.duplicate_count
        result.reused_existing_items = len(orchestration.skipped_item_keys)
        result.newly_planned_candidates = len(grounded_item_keys)
        result.blocked_candidates = blocked_candidates
        result.planned_cards = len(grounded_item_keys) + len(orchestration.skipped_item_keys)
        return result

    def _ingest_frequency_deck(self, request: GenerationRequest) -> IngestLexicalItemsResult:
        """Ingest lexical items from a frequency deck with lexical backfill."""

        language = request.language
        levels = [request.level] if request.level is not None else [1, 2, 3]
        cards_per_level = request.resolved_cards_per_level()
        requested_item_keys = [
            self._frequency_item_key(level, position)
            for level in levels
            for position in range(1, cards_per_level + 1)
        ]
        orchestration = self.job_service.orchestrate(
            request,
            requested_item_keys=requested_item_keys,
        )
        report = JobExecutionReport(
            orchestration=orchestration,
            progress_updates=[],
            retried_item_keys=[],
            failed_item_keys=[],
        )
        if orchestration.diagnostic is not None:
            return IngestLexicalItemsResult(
                report=report,
                grounded_candidates=0,
                pending_groundings=0,
                rejected_rows=0,
                backfilled_candidates=0,
                level_counts={1: 0, 2: 0, 3: 0},
            )

        if not orchestration.pending_item_keys and not (request.overwrite and request.yes_overwrite):
            return self._result_from_persisted_candidates(report=report)

        level_counts = {1: 0, 2: 0, 3: 0}
        total_backfilled = 0
        for level in levels:
            grounded_candidates, backfilled_count = self._build_grounded_frequency_level(
                language=language,
                level=level,
                required_count_per_level=cards_per_level,
            )
            total_backfilled += backfilled_count
            level_counts[level] = len(grounded_candidates)
            candidate_rows: list[tuple[str, str, LexicalCardCandidate]] = []
            item_keys: list[str] = []
            for position, candidate in enumerate(grounded_candidates, start=1):
                item_key = self._frequency_item_key(level, position)
                candidate_rows.append((item_key, candidate.lemma_key, candidate))
                item_keys.append(item_key)
            self.lexical_repo.upsert_candidates(
                job_id=orchestration.job_id,
                run_key=orchestration.run_key,
                source_type="frequency",
                candidates=candidate_rows,
            )
            self.repository.record_item_successes(
                orchestration.job_id,
                item_keys=item_keys,
                completed_stage=JobStage.INGEST,
            )

        result = self._result_from_persisted_candidates(report=report)
        result.backfilled_candidates = total_backfilled
        result.level_counts.update(level_counts)
        self.repository.advance_job_to_stage(orchestration.job_id, JobStage.GENERATE_TEXT)
        return result

    def _ingest_word_list(self, request: GenerationRequest) -> IngestLexicalItemsResult:
        """Ingest lexical items from a custom word list, preserving pending items."""

        if request.input_file is None:
            raise ValueError("word-list requests require an input file")

        parsed = parse_word_list(request.input_file)
        items_by_key = {item.item_key: item for item in parsed.items}
        orchestration = self.job_service.orchestrate(
            request,
            requested_item_keys=[item.item_key for item in parsed.items],
        )
        report = JobExecutionReport(
            orchestration=orchestration,
            progress_updates=[],
            retried_item_keys=[],
            failed_item_keys=[],
        )
        if orchestration.diagnostic is not None:
            return IngestLexicalItemsResult(
                report=report,
                grounded_candidates=0,
                pending_groundings=0,
                rejected_rows=len(parsed.warnings),
                backfilled_candidates=0,
                level_counts={1: 0, 2: 0, 3: 0},
            )

        for item_key in orchestration.pending_item_keys:
            item = items_by_key[item_key]
            candidate = self.grounding_service.ground_word_list_item(
                language=request.language,
                item=item,
            )
            self.lexical_repo.upsert_candidate(
                job_id=orchestration.job_id,
                run_key=orchestration.run_key,
                item_key=item.item_key,
                source_type="word-list",
                normalized_source=item.item_key,
                candidate=candidate,
            )
            if candidate.grounding_status is GroundingStatus.GROUNDED:
                self.repository.record_item_success(
                    orchestration.job_id,
                    item_key=item.item_key,
                    completed_stage=JobStage.INGEST,
                )

        result = self._result_from_persisted_candidates(report=report)
        result.rejected_rows = len(parsed.warnings)
        self.repository.advance_job_to_stage(orchestration.job_id, JobStage.GENERATE_TEXT)
        return result

    def _result_from_persisted_candidates(
        self,
        *,
        report: JobExecutionReport,
    ) -> IngestLexicalItemsResult:
        candidates = self.lexical_repo.list_candidates(report.job_id)
        level_counts = {1: 0, 2: 0, 3: 0}
        grounded_candidates = 0
        for candidate in candidates:
            if candidate.grounding_status is GroundingStatus.GROUNDED:
                grounded_candidates += 1
                if candidate.frequency_level in level_counts:
                    level_counts[candidate.frequency_level] += 1

        return IngestLexicalItemsResult(
            report=report,
            grounded_candidates=grounded_candidates,
            pending_groundings=self.lexical_repo.count_pending_candidates(report.job_id),
            rejected_rows=0,
            backfilled_candidates=sum(
                1
                for candidate in candidates
                if candidate.grounding_status is GroundingStatus.GROUNDED
                and candidate.frequency_level in LEVEL_WINDOWS
                and candidate.frequency_rank is not None
                and candidate.frequency_rank > LEVEL_WINDOWS[candidate.frequency_level][1]
            ),
            level_counts=level_counts,
        )

    def _build_grounded_frequency_level(
        self,
        *,
        language: SupportedLanguage,
        level: int,
        required_count_per_level: int = 1000,
    ) -> tuple[list[LexicalCardCandidate], int]:
        rejected_lemmas: set[str] = set()

        for _ in range(20):
            candidates = build_frequency_level(
                language,
                level=level,
                required_count_per_level=required_count_per_level,
                rejected_lemmas=rejected_lemmas,
            )
            grounded_candidates: list[LexicalCardCandidate] = []
            backfill_required: set[str] = set()
            for candidate in candidates:
                grounded_candidate = self.grounding_service.ground_frequency_candidate(
                    language=language,
                    candidate=candidate,
                )
                if grounded_candidate.grounding_status is GroundingStatus.GROUNDED:
                    grounded_candidates.append(grounded_candidate)
                    continue
                backfill_required.add(candidate.lemma_key)

            if len(grounded_candidates) == required_count_per_level:
                _, window_end = LEVEL_WINDOWS[level]
                backfilled_count = sum(
                    1
                    for candidate in grounded_candidates
                    if candidate.frequency_rank is not None and candidate.frequency_rank > window_end
                )
                return grounded_candidates, backfilled_count

            if not backfill_required or backfill_required.issubset(rejected_lemmas):
                break
            rejected_lemmas.update(backfill_required)

        raise ValueError(f"unable to ground {required_count_per_level} candidates for level {level}")

    @staticmethod
    def _frequency_item_key(level: int, position: int) -> str:
        return f"level-{level}-rank-{position:04d}"
