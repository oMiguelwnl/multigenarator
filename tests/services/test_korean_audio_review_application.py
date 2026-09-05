"""Korean audio-review import and exact authority application tests."""

from __future__ import annotations

from hashlib import sha256

import pytest
from pydantic import ValidationError

from multilang.domain.audio import AudioAssetKind, AudioReviewStatus
from multilang.services.korean_audio import (
    KoreanAzureCatalogVoice,
    KoreanVoiceProfile,
    build_korean_audio_asset,
    build_korean_tts_input,
)
from multilang.services.korean_audio_review import (
    KoreanAudioReviewAggregate,
    KoreanAudioReviewApplicationAuthority,
    KoreanAudioReviewApplicationService,
    KoreanAudioReviewBatch,
    KoreanAudioReviewBatchDecision,
    KoreanAudioReviewImportLedger,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _profile() -> KoreanVoiceProfile:
    return KoreanVoiceProfile.from_catalog_voice(
        KoreanAzureCatalogVoice(
            short_name="ko-KR-SunHiNeural",
            locale="ko-KR",
            region="koreacentral",
            status="available",
            voice_type="Neural",
            provider_sdk_version="1.49.1",
        ),
        catalog_receipt_sha256=_hash("catalog-receipt"),
        profile_authority_sha256=_hash("profile-authority"),
    )


def _asset(kind: AudioAssetKind, item_key: str = "item-1"):
    profile = _profile()
    text = "학교" if kind is AudioAssetKind.WORD else "저는 학교에 가요."
    normalized = build_korean_tts_input(text, asset_kind=kind, profile=profile)
    return build_korean_audio_asset(
        job_id="job-ko",
        item_key=item_key,
        asset_kind=kind,
        normalized_input=normalized,
        profile=profile,
        storage_path=f"audio/{item_key}-{kind.value}.mp3",
        media_bytes=f"{item_key}-{kind.value}".encode("utf-8"),
        duration_ms=100,
        fallback_used=False,
    )


def _decision(asset, *, outcome: str = "rejected") -> KoreanAudioReviewBatchDecision:
    return KoreanAudioReviewBatchDecision(
        job_id=asset.job_id,
        item_key=asset.item_key,
        asset_kind=asset.asset_kind,
        synthesis_request_sha256=asset.provenance.synthesis_request_sha256 or "",
        artifact_sha256=asset.provenance.artifact_sha256 or "",
        outcome=outcome,
        rejection_codes=("noisy_audio",) if outcome == "rejected" else (),
    )


class _FakeAudioRepository:
    def __init__(self, assets) -> None:
        self.assets = {(asset.item_key, asset.asset_kind): asset for asset in assets}
        self.upserts = []

    def get_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind):
        asset = self.assets.get((item_key, asset_kind))
        if asset is None or asset.job_id != job_id:
            return None
        return asset

    def upsert_audio_asset(self, asset):
        self.upserts.append(asset)
        self.assets[(asset.item_key, asset.asset_kind)] = asset
        return asset


def test_audio_review_batch_import_is_bounded_content_free_and_exact_retry() -> None:
    asset = _asset(AudioAssetKind.WORD)
    with pytest.raises(ValidationError):
        KoreanAudioReviewBatchDecision.model_validate(
            {**_decision(asset).model_dump(mode="json"), "raw_note": "private heard note"}
        )
    with pytest.raises(ValidationError):
        KoreanAudioReviewBatch(
            job_id="job-ko",
            production_run_sha256=_hash("production"),
            review_receipt_sha256=_hash("receipt-too-large"),
            decisions=tuple(_decision(_asset(AudioAssetKind.WORD, f"item-{index}")) for index in range(101)),
        )

    ledger = KoreanAudioReviewImportLedger()
    batch = KoreanAudioReviewBatch(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        review_receipt_sha256=_hash("receipt"),
        decisions=(_decision(asset),),
    )

    first = ledger.import_batch(batch, current_assets={(asset.item_key, asset.asset_kind): asset})
    second = ledger.import_batch(batch, current_assets={(asset.item_key, asset.asset_kind): asset})

    assert first.replayed is False
    assert second.replayed is True
    assert ledger.write_count == 1
    assert first.rejected_count == 1


def test_audio_review_reject_and_final_promote_require_exact_authority_request_and_bytes() -> None:
    rejected = _asset(AudioAssetKind.WORD, "item-1")
    promoted_word = _asset(AudioAssetKind.WORD, "item-2")
    promoted_sentence = _asset(AudioAssetKind.SENTENCE, "item-2")
    repository = _FakeAudioRepository([rejected, promoted_word, promoted_sentence])
    service = KoreanAudioReviewApplicationService(repository)

    reject_aggregate = KoreanAudioReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(_decision(rejected),),
        expected_word_count=1,
        expected_sentence_count=0,
    )
    reject_prestate = service.prestate_sha256("job-ko", reject_aggregate.asset_keys)

    with pytest.raises(ValueError, match="remediation"):
        service.apply(
            reject_aggregate,
            KoreanAudioReviewApplicationAuthority(
                mode="reject_only",
                power="final_content_promotion",
                aggregate_sha256=reject_aggregate.aggregate_sha256,
                prestate_sha256=reject_prestate,
            ),
        )
    assert repository.upserts == []

    service.apply(
        reject_aggregate,
        KoreanAudioReviewApplicationAuthority(
            mode="reject_only",
            power="remediation",
            aggregate_sha256=reject_aggregate.aggregate_sha256,
            prestate_sha256=reject_prestate,
        ),
    )
    assert repository.assets[("item-1", AudioAssetKind.WORD)].provenance.audio_review_status is AudioReviewStatus.REJECTED

    promote_aggregate = KoreanAudioReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(_decision(promoted_word, outcome="accepted"), _decision(promoted_sentence, outcome="accepted")),
        expected_word_count=1,
        expected_sentence_count=1,
    )
    promote_prestate = service.prestate_sha256("job-ko", promote_aggregate.asset_keys)
    result = service.apply(
        promote_aggregate,
        KoreanAudioReviewApplicationAuthority(
            mode="promote",
            power="final_content_promotion",
            aggregate_sha256=promote_aggregate.aggregate_sha256,
            prestate_sha256=promote_prestate,
            audio_review_receipt_sha256=_hash("audio-review"),
            heard_review_receipt_sha256=_hash("heard-review"),
        ),
    )

    assert result.mutated_count == 2
    assert repository.assets[("item-2", AudioAssetKind.WORD)].provenance.audio_review_status is AudioReviewStatus.APPROVED
    assert repository.assets[("item-2", AudioAssetKind.SENTENCE)].provenance.audio_review_status is AudioReviewStatus.APPROVED


def test_audio_review_blocks_stale_request_or_byte_without_mutation() -> None:
    asset = _asset(AudioAssetKind.WORD)
    repository = _FakeAudioRepository([asset])
    service = KoreanAudioReviewApplicationService(repository)
    stale = KoreanAudioReviewBatchDecision(
        job_id="job-ko",
        item_key="item-1",
        asset_kind=AudioAssetKind.WORD,
        synthesis_request_sha256=_hash("stale-request"),
        artifact_sha256=asset.provenance.artifact_sha256 or "",
        outcome="rejected",
        rejection_codes=("stale",),
    )
    aggregate = KoreanAudioReviewAggregate.from_decisions(
        job_id="job-ko",
        production_run_sha256=_hash("production"),
        decisions=(stale,),
        expected_word_count=1,
        expected_sentence_count=0,
    )

    with pytest.raises(ValueError, match="stale Korean audio review request"):
        service.apply(
            aggregate,
            KoreanAudioReviewApplicationAuthority(
                mode="reject_only",
                power="remediation",
                aggregate_sha256=aggregate.aggregate_sha256,
                prestate_sha256=service.prestate_sha256("job-ko", aggregate.asset_keys),
            ),
        )
    assert repository.upserts == []
