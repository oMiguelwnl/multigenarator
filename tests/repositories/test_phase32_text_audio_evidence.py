"""Repository round trips for Phase 32 text/audio evidence fields."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import LexicalCandidate
from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioReviewStatus,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import raw_bytes_sha256
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    KoreanAdaptiveIPlusOneEvidence,
    KoreanProviderReviewEvidence,
    KoreanTextSelectionEvidence,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.text_repository import TextRepository


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def build_repositories() -> tuple[TextRepository, AudioRepository, LexicalRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return (
        TextRepository(session),
        AudioRepository(session),
        LexicalRepository(session),
        JobRepository(session),
        session,
    )


def _make_job(job_repository: JobRepository):
    return job_repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="frequency", level=1),
        run_key="ko-phase32-evidence",
        source_fingerprint="fixture-source",
        total_items=1,
    )


def _seed_candidate(
    lexical_repository: LexicalRepository,
    session: Session,
    *,
    job_id: str,
    run_key: str,
    item_key: str,
) -> LexicalCandidate:
    lexical_repository.upsert_candidate(
        job_id=job_id,
        run_key=run_key,
        item_key=item_key,
        source_type="frequency",
        normalized_source="학교",
        candidate=LexicalCardCandidate(
            submitted_form="학교",
            display_form="학교",
            lemma="학교",
            lemma_key="ko:school",
            frequency_rank=1,
            frequency_level=1,
            definitions_html="escola",
            definition_language="pt",
            translation_target_language="pt",
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(source="fixture"),
        ),
    )
    return session.query(LexicalCandidate).filter_by(job_id=job_id, item_key=item_key).one()


def _selection() -> KoreanTextSelectionEvidence:
    return KoreanTextSelectionEvidence(
        candidate_set_sha256=_hash("candidate-set"),
        selected_candidate_sha256=_hash("selected-candidate"),
        selected_ordinal=1,
        initial_candidate_count=2,
        repair_attempt_count=0,
        hard_gate_status="passed",
        selector_version="phase32-selector-v1",
    )


def _adaptive() -> KoreanAdaptiveIPlusOneEvidence:
    return KoreanAdaptiveIPlusOneEvidence(
        known_prefix_sha256=_hash("known-prefix"),
        target_concept_id="lexicon:school",
        observed_concept_ids=("orthography:hangul", "lexicon:school"),
        incidental_concept_ids=("grammar:topic",),
        scorer_version="adaptive-i-plus-one-v1",
    )


def _provider_review(decision: str = "needs_review") -> KoreanProviderReviewEvidence:
    return KoreanProviderReviewEvidence(
        reviewer_class="ai_policy_linguistic_review",
        policy_sha256=_hash("policy"),
        review_receipt_sha256=_hash("provider-review"),
        decision=decision,
    )


def _text_record(
    *,
    job_id: str,
    item_key: str,
    lexical_candidate_id: str,
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED,
    text_review_receipt_sha256: str | None = None,
) -> TextQualityRecord:
    return TextQualityRecord(
        job_id=job_id,
        item_key=item_key,
        lexical_candidate_id=lexical_candidate_id,
        example_sentence="학교에 가요.",
        translation_text="Eu vou para a escola.",
        generation_status=TextGenerationStatus.GENERATED,
        validation_status=ValidationStatus.PASSED,
        review_status=review_status,
        confidence_score=0.92,
        confidence_label=ConfidenceLabel.HIGH,
        sentence_provenance=TextProvenance(source="generator", provider="fixture", model="fixture-model"),
        translation_provenance=TextProvenance(source="translator", provider="fixture", model="fixture-model"),
        candidate_selection_evidence=_selection(),
        adaptive_i_plus_one_evidence=_adaptive(),
        provider_review_evidence=_provider_review("accepted" if review_status is ReviewStatus.ACCEPTED else "needs_review"),
        text_review_receipt_sha256=text_review_receipt_sha256,
    )


def _audio_record(
    *,
    job_id: str,
    item_key: str,
    asset_kind: AudioAssetKind,
    text: str,
    review_status: AudioReviewStatus | None = AudioReviewStatus.SYNTHESIZED_PENDING,
    audio_review_receipt_sha256: str | None = None,
    heard_review_receipt_sha256: str | None = None,
    fallback_used: bool = False,
) -> AudioAssetRecord:
    normalized = NormalizedTtsInput(
        display_text=text,
        tts_text=text,
        ssml_text=f"<speak>{text}</speak>",
    )
    return AudioAssetRecord(
        job_id=job_id,
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=text,
        normalized_input=normalized,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id="ko-KR-SunHiNeural",
            locale="ko-KR",
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized.text_hash or "",
            ssml_hash=normalized.ssml_hash or "",
            storage_path=f"audio/{asset_kind.value}/{item_key}.mp3",
            byte_size=2048,
            duration_ms=900,
            status=AudioSynthesisStatus.SYNTHESIZED,
            fallback_used=fallback_used,
            provider_sdk_version="1.49.1",
            voice_profile_sha256=_hash("voice-profile"),
            catalog_receipt_sha256=_hash("catalog-receipt"),
            synthesis_request_sha256=_hash(f"request-{asset_kind.value}"),
            artifact_sha256=_hash(f"artifact-{asset_kind.value}"),
            audio_review_status=review_status,
            audio_review_receipt_sha256=audio_review_receipt_sha256,
            heard_review_receipt_sha256=heard_review_receipt_sha256,
        ),
    )


def test_text_selection_adaptive_and_provider_review_evidence_round_trip() -> None:
    text_repository, _, lexical_repository, job_repository, session = build_repositories()
    job = _make_job(job_repository)
    lexical = _seed_candidate(lexical_repository, session, job_id=job.id, run_key=job.run_key, item_key="rank-0001")

    stored = text_repository.upsert_text_record(
        _text_record(job_id=job.id, item_key="rank-0001", lexical_candidate_id=lexical.id)
    )
    session.expire_all()
    restored = text_repository.get_text_record(job.id, "rank-0001")

    assert restored == stored
    assert restored is not None
    assert restored.candidate_selection_evidence == _selection()
    assert restored.adaptive_i_plus_one_evidence == _adaptive()
    assert restored.provider_review_evidence == _provider_review()
    assert restored.review_status is ReviewStatus.REVIEW_REQUIRED


def test_text_machine_evidence_cannot_self_approve_without_review_receipt() -> None:
    with pytest.raises(ValueError):
        _text_record(
            job_id="job",
            item_key="rank-0001",
            lexical_candidate_id="lexical",
            review_status=ReviewStatus.ACCEPTED,
        )


def test_audio_catalog_profile_artifact_and_review_evidence_round_trip_word_sentence() -> None:
    _, audio_repository, _, job_repository, session = build_repositories()
    job = _make_job(job_repository)
    word = _audio_record(job_id=job.id, item_key="rank-0001", asset_kind=AudioAssetKind.WORD, text="학교")
    sentence = _audio_record(job_id=job.id, item_key="rank-0001", asset_kind=AudioAssetKind.SENTENCE, text="학교에 가요.")

    audio_repository.upsert_audio_asset(word)
    audio_repository.upsert_audio_asset(sentence)
    session.expire_all()

    assets = audio_repository.list_assets_for_job(job.id)
    assert [asset.asset_kind for asset in assets] == [AudioAssetKind.SENTENCE, AudioAssetKind.WORD]
    assert {asset.provenance.synthesis_request_sha256 for asset in assets} == {
        _hash("request-word"),
        _hash("request-sentence"),
    }
    assert all(asset.provenance.audio_review_status is AudioReviewStatus.SYNTHESIZED_PENDING for asset in assets)
    assert not any(asset.ready_for_korean_final_export for asset in assets)


def test_audio_approved_review_requires_exact_heard_receipt_and_legacy_remains_readable() -> None:
    _, audio_repository, _, job_repository, session = build_repositories()
    job = _make_job(job_repository)
    legacy = _audio_record(
        job_id=job.id,
        item_key="legacy",
        asset_kind=AudioAssetKind.WORD,
        text="legacy",
        review_status=None,
    )
    audio_repository.upsert_audio_asset(legacy)

    with pytest.raises(ValueError):
        _audio_record(
            job_id=job.id,
            item_key="rank-0001",
            asset_kind=AudioAssetKind.WORD,
            text="학교",
            review_status=AudioReviewStatus.APPROVED,
            audio_review_receipt_sha256=_hash("audio-review"),
        )
    with pytest.raises(ValueError):
        _audio_record(
            job_id=job.id,
            item_key="rank-0002",
            asset_kind=AudioAssetKind.WORD,
            text="학생",
            review_status=AudioReviewStatus.APPROVED,
            audio_review_receipt_sha256=_hash("audio-review"),
            heard_review_receipt_sha256=_hash("heard-review"),
            fallback_used=True,
        )

    restored = audio_repository.get_asset(job.id, "legacy", AudioAssetKind.WORD)
    assert restored is not None
    assert restored.provenance.audio_review_status is None
    assert restored.ready_for_korean_final_export is False
