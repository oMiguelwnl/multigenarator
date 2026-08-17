from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import LexicalCandidate
from multilang.domain.highlights import HighlightCandidate
from multilang.domain.jobs import GenerationRequest, JobStage, SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalysisAlternative,
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMorphemeEvidence,
    KoreanMorphologyResult,
    KoreanMorphologyStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
    KoreanWordAnalysis,
    canonicalize_korean,
)
from multilang.domain.lexicon import GroundingStatus
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.lexical_lookup import LexicalRecord
from multilang.services.lexical_grounding import LexicalGroundingService


PRIVATE_SENTENCE = "El jardín secreto guarda una llave brillante"


class FakeLookup:
    def __init__(self, records: dict[str, LexicalRecord] | None = None) -> None:
        self.records = records or {}

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        return self.records.get(term)


def build_service(
    records: dict[str, LexicalRecord] | None = None,
    *,
    grounding_service: LexicalGroundingService | None = None,
) -> tuple[IngestLexicalItemsService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    job_repository = JobRepository(session)
    service = IngestLexicalItemsService(
        job_service=GenerateJobService(job_repository),
        lexical_repo=LexicalRepository(session),
        grounding_service=grounding_service or LexicalGroundingService(FakeLookup(records)),
        highlight_import_repo=HighlightImportRepository(session),
    )
    return service, session


def record(term: str) -> LexicalRecord:
    return LexicalRecord(
        term=term,
        display_form=term,
        lemma=term,
        definitions=[f"a learner definition for {term}"],
        part_of_speech="noun",
        ipa="/x/",
        source="manual",
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
    manifest = HighlightImportRepository(session).get_manifest(result.report.job_id)
    assert manifest is not None
    assert set(manifest.counts) == {
        "imported_highlights",
        "rejected_highlights",
        "extracted_candidates",
        "duplicate_candidates",
    }
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


def _korean_fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _korean_analysis(
    *,
    words: tuple[tuple[str, int, tuple[tuple[str, str], ...]], ...],
    fingerprint: KoreanAnalyzerFingerprint,
) -> KoreanMorphologyResult:
    alternatives: list[KoreanAnalysisAlternative] = []
    for rank in (1, 2):
        projected_words: list[KoreanWordAnalysis] = []
        for surface_form, word_position, signature in words:
            morphemes = tuple(
                KoreanMorphemeEvidence(
                    form=form,
                    lemma=form,
                    pos=pos,
                    raw_pos=pos,
                    oov=False,
                )
                for form, pos in signature
            )
            projected_words.append(
                KoreanWordAnalysis(
                    surface_form=surface_form,
                    word_position=word_position,
                    morphemes=morphemes,
                    lexical_signature=tuple(
                        KoreanSignatureItem(form=form, pos=pos)
                        for form, pos in signature
                    ),
                )
            )
        alternatives.append(
            KoreanAnalysisAlternative(
                rank=rank,
                score=-float(rank),
                words=tuple(projected_words),
                has_oov=False,
            )
        )
    return KoreanMorphologyResult(
        status=KoreanMorphologyStatus.RESOLVED,
        analyzer_fingerprint=fingerprint,
        alternatives=tuple(alternatives),
        reason_code=KoreanReasonCode.ANALYSIS_RESOLVED,
    )


class _KoreanLookup:
    def __init__(self, records: tuple[LexicalRecord, ...]) -> None:
        self.records = records

    def iter_candidates(self, *, language_code: str) -> tuple[LexicalRecord, ...]:
        assert language_code == "ko"
        return self.records

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        raise AssertionError("Korean ingestion must use source inventory selection")


class _KoreanMorphology:
    def __init__(
        self,
        analyses: dict[str, KoreanMorphologyResult],
        fingerprint: KoreanAnalyzerFingerprint,
    ) -> None:
        self.analyses = {
            canonicalize_korean(text): analysis for text, analysis in analyses.items()
        }
        self._fingerprint = fingerprint
        self.calls: list[str] = []

    @property
    def fingerprint(self) -> KoreanAnalyzerFingerprint:
        return self._fingerprint

    def analyze(self, text: str) -> KoreanMorphologyResult:
        canonical = canonicalize_korean(text)
        self.calls.append(canonical)
        return self.analyses[canonical]


def _korean_record(
    lemma: str,
    *,
    part_of_speech: str,
    sense_id: str,
) -> LexicalRecord:
    return LexicalRecord(
        term=lemma,
        display_form=lemma,
        lemma=lemma,
        definitions=["synthetic fixture only"],
        part_of_speech=part_of_speech,
        sense_id=sense_id,
        register="standard",
        source="reviewed_test_fixture",
    )


def _korean_request(input_file: Path) -> GenerationRequest:
    return GenerationRequest(
        language=SupportedLanguage.KO,
        source_type="kindle-highlights",
        input_file=input_file,
    )


def test_korean_highlight_ingestion_persists_exact_identity_without_reanalysis(
    tmp_path: Path,
) -> None:
    private_sentence = "물은 학교에서 공부해요"
    export_path = tmp_path / "Private Korean Reader.txt"
    write_export(export_path, private_sentence)
    fingerprint = _korean_fingerprint()
    water = (("물", "NNG"),)
    school = (("학교", "NNG"),)
    study = (("공부", "NNG"), ("하", "XSV"))
    morphology = _KoreanMorphology(
        {
            "물": _korean_analysis(
                words=(("물", 0, water),),
                fingerprint=fingerprint,
            ),
            "학교": _korean_analysis(
                words=(("학교", 0, school),),
                fingerprint=fingerprint,
            ),
            "공부하다": _korean_analysis(
                words=(("공부하다", 0, study),),
                fingerprint=fingerprint,
            ),
            private_sentence: _korean_analysis(
                words=(
                    ("물은", 0, water),
                    ("학교에서", 1, school),
                    ("공부해요", 2, study),
                ),
                fingerprint=fingerprint,
            ),
        },
        fingerprint,
    )
    grounding = LexicalGroundingService(
        _KoreanLookup(
            (
                _korean_record(
                    "공부하다",
                    part_of_speech="verb",
                    sense_id="fixture:study:1",
                ),
                _korean_record(
                    "물",
                    part_of_speech="noun",
                    sense_id="fixture:water:1",
                ),
                _korean_record(
                    "학교",
                    part_of_speech="noun",
                    sense_id="fixture:school:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )
    service, session = build_service(grounding_service=grounding)

    result = service.execute(_korean_request(export_path))

    assert result.imported_highlights == 1
    assert result.extracted_candidates == 3
    assert result.newly_planned_candidates == 3
    assert result.blocked_candidates == 0
    assert morphology.calls == ["공부하다", "물", "학교", private_sentence]

    private_records = HighlightImportRepository(session).list_private_records(
        result.report.job_id
    )
    assert private_records[0].normalized_text == private_sentence
    assert not hasattr(private_records[0], "source_path")
    assert export_path.name not in str(private_records[0].__dict__)

    session.expire_all()
    persisted = LexicalRepository(session).list_candidates(result.report.job_id)
    assert {candidate.lemma for candidate in persisted} == {"공부하다", "학교", "물"}
    assert all(candidate.korean_identity is not None for candidate in persisted)
    assert {
        candidate.korean_identity.sense_id for candidate in persisted
    } == {
        "fixture:study:1",
        "fixture:school:1",
        "fixture:water:1",
    }
    assert all(
        candidate.lemma_key == candidate.korean_identity.lexical_key
        for candidate in persisted
    )
    assert morphology.calls == ["공부하다", "물", "학교", private_sentence]

    manifest = HighlightImportRepository(session).get_manifest(result.report.job_id)
    assert manifest is not None
    public_rows = session.query(LexicalCandidate).all()
    public_dump = str(
        {
            "manifest": manifest.model_dump(),
            "rows": [
                {
                    "normalized_source": row.normalized_source,
                    "submitted_form": row.submitted_form,
                    "display_form": row.display_form,
                    "lemma": row.lemma,
                    "provenance": row.provenance,
                    "korean_identity": row.korean_identity,
                }
                for row in public_rows
            ],
        }
    )
    assert private_sentence not in public_dump
    assert str(export_path) not in public_dump
    assert export_path.name not in public_dump
    assert "prompt" not in public_dump
    assert "traceback" not in public_dump
    assert all(len(row.normalized_source) == 64 for row in public_rows)


def test_unresolved_korean_highlight_is_blocked_but_private_record_stays_private(
    tmp_path: Path,
) -> None:
    private_sentence = "비밀원문"
    export_path = tmp_path / "Secret Korean Reader.txt"
    write_export(export_path, private_sentence)
    fingerprint = _korean_fingerprint()
    unknown = (("비밀원문", "NNG"),)
    morphology = _KoreanMorphology(
        {
            private_sentence: _korean_analysis(
                words=((private_sentence, 0, unknown),),
                fingerprint=fingerprint,
            )
        },
        fingerprint,
    )
    grounding = LexicalGroundingService(
        _KoreanLookup(()),
        korean_morphology=morphology,
    )
    service, session = build_service(grounding_service=grounding)

    result = service.execute(_korean_request(export_path))

    assert result.imported_highlights == 1
    assert result.extracted_candidates == 0
    assert result.blocked_candidates == 1
    assert result.planned_cards == 0
    assert LexicalRepository(session).list_candidates(result.report.job_id) == []
    private_records = HighlightImportRepository(session).list_private_records(
        result.report.job_id
    )
    assert private_records[0].normalized_text == private_sentence
    manifest = HighlightImportRepository(session).get_manifest(result.report.job_id)
    assert manifest is not None
    manifest_dump = manifest.model_dump_json()
    assert manifest.counts["resolution_errors"] == 1
    assert private_sentence not in manifest_dump
    assert str(export_path) not in manifest_dump


def test_korean_highlight_candidate_identity_must_still_match_source_inventory() -> None:
    fingerprint = _korean_fingerprint()
    water = (("물", "NNG"),)
    morphology = _KoreanMorphology(
        {
            "물": _korean_analysis(
                words=(("물", 0, water),),
                fingerprint=fingerprint,
            ),
        },
        fingerprint,
    )
    service = LexicalGroundingService(
        _KoreanLookup(
            (
                _korean_record(
                    "물",
                    part_of_speech="noun",
                    sense_id="fixture:water:1",
                ),
            )
        ),
        korean_morphology=morphology,
    )
    forged_identity = KoreanLexicalIdentity(
        submitted_form=None,
        canonical_nfc="물은",
        lemma="물",
        part_of_speech="NNG",
        sense_id="fixture:forged:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="물", pos="NNG"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )
    candidate = HighlightCandidate(
        item_key="highlight-ko-safe-forged",
        source_content_hash="c" * 64,
        display_form="물",
        lemma_key=forged_identity.lexical_key,
        first_highlight_id="safe-id",
        first_source_index=0,
        occurrence_count=1,
        korean_identity=forged_identity,
    )

    grounded = service.ground_highlight_candidate(
        language=SupportedLanguage.KO,
        candidate=candidate,
    )

    assert grounded.grounding_status is GroundingStatus.INSUFFICIENT
    assert grounded.korean_identity is None
    assert grounded.warning_detail == "source_identity_mismatch"
    assert morphology.calls == ["물"]
