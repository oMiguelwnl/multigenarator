"""Bounded Korean audio-review import and authority-gated application."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.audio import AudioAssetKind, AudioReviewStatus


_HEX = frozenset("0123456789abcdef")


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanAudioReviewBatchDecision(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    item_key: str = Field(min_length=1, max_length=255)
    asset_kind: AudioAssetKind
    synthesis_request_sha256: str = Field(min_length=64, max_length=64)
    artifact_sha256: str = Field(min_length=64, max_length=64)
    outcome: Literal["accepted", "rejected"]
    rejection_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=16)

    @field_validator("synthesis_request_sha256", "artifact_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("rejection_codes")
    @classmethod
    def rejection_codes_must_be_controlled(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value)
        if normalized != value or len(normalized) != len(set(normalized)):
            raise ValueError("rejection_codes must be controlled")
        return value

    @model_validator(mode="after")
    def decision_must_match_outcome(self) -> "KoreanAudioReviewBatchDecision":
        if self.outcome == "accepted" and self.rejection_codes:
            raise ValueError("accepted audio decision cannot carry rejection codes")
        if self.outcome == "rejected" and not self.rejection_codes:
            raise ValueError("rejected audio decision requires rejection codes")
        return self


class KoreanAudioReviewBatch(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    production_run_sha256: str = Field(min_length=64, max_length=64)
    review_receipt_sha256: str = Field(min_length=64, max_length=64)
    decisions: tuple[KoreanAudioReviewBatchDecision, ...] = Field(min_length=1, max_length=100)

    @field_validator("production_run_sha256", "review_receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanAudioReviewImportResult(_FrozenModel):
    receipt_sha256: str = Field(min_length=64, max_length=64)
    batch_sha256: str = Field(min_length=64, max_length=64)
    job_id: str = Field(min_length=1, max_length=128)
    decision_count: int = Field(ge=0, le=100)
    accepted_count: int = Field(ge=0, le=100)
    rejected_count: int = Field(ge=0, le=100)
    replayed: bool = False


class KoreanAudioReviewImportLedger:
    def __init__(self) -> None:
        self._receipts: dict[str, KoreanAudioReviewImportResult] = {}
        self.write_count = 0

    def import_batch(
        self,
        batch: KoreanAudioReviewBatch,
        *,
        current_assets: dict[tuple[str, AudioAssetKind], object] | None = None,
    ) -> KoreanAudioReviewImportResult:
        if batch.review_receipt_sha256 in self._receipts:
            return self._receipts[batch.review_receipt_sha256].model_copy(update={"replayed": True})
        if current_assets is not None:
            for decision in batch.decisions:
                asset = current_assets.get((decision.item_key, decision.asset_kind))
                if asset is None:
                    raise ValueError("unknown Korean audio-review asset")
                _assert_decision_matches_asset(decision, asset)
        payload = {
            "job_id": batch.job_id,
            "production_run_sha256": batch.production_run_sha256,
            "review_receipt_sha256": batch.review_receipt_sha256,
            "decisions": [decision.model_dump(mode="json") for decision in batch.decisions],
        }
        result = KoreanAudioReviewImportResult(
            receipt_sha256=batch.review_receipt_sha256,
            batch_sha256=_canonical_sha256(payload),
            job_id=batch.job_id,
            decision_count=len(batch.decisions),
            accepted_count=sum(1 for decision in batch.decisions if decision.outcome == "accepted"),
            rejected_count=sum(1 for decision in batch.decisions if decision.outcome == "rejected"),
        )
        self._receipts[batch.review_receipt_sha256] = result
        self.write_count += 1
        return result


class KoreanAudioReviewAggregate(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    production_run_sha256: str = Field(min_length=64, max_length=64)
    aggregate_sha256: str = Field(min_length=64, max_length=64)
    decisions: tuple[KoreanAudioReviewBatchDecision, ...] = Field(min_length=1)
    expected_word_count: int = Field(ge=0)
    expected_sentence_count: int = Field(ge=0)

    @classmethod
    def from_decisions(
        cls,
        *,
        job_id: str,
        production_run_sha256: str,
        decisions: tuple[KoreanAudioReviewBatchDecision, ...],
        expected_word_count: int,
        expected_sentence_count: int,
    ) -> "KoreanAudioReviewAggregate":
        payload = {
            "job_id": job_id,
            "production_run_sha256": production_run_sha256,
            "decisions": [decision.model_dump(mode="json") for decision in decisions],
            "expected_word_count": expected_word_count,
            "expected_sentence_count": expected_sentence_count,
        }
        return cls(
            job_id=job_id,
            production_run_sha256=production_run_sha256,
            aggregate_sha256=_canonical_sha256(payload),
            decisions=decisions,
            expected_word_count=expected_word_count,
            expected_sentence_count=expected_sentence_count,
        )

    @property
    def asset_keys(self) -> tuple[tuple[str, AudioAssetKind], ...]:
        return tuple((decision.item_key, decision.asset_kind) for decision in self.decisions)

    @property
    def rejected_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.outcome == "rejected")


class KoreanAudioReviewApplicationAuthority(_FrozenModel):
    mode: Literal["reject_only", "promote"]
    power: Literal["remediation", "initial_content_promotion", "final_content_promotion"]
    aggregate_sha256: str = Field(min_length=64, max_length=64)
    prestate_sha256: str = Field(min_length=64, max_length=64)
    audio_review_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    heard_review_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)

    @field_validator("aggregate_sha256", "prestate_sha256", "audio_review_receipt_sha256", "heard_review_receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return value
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanAudioReviewApplicationResult(_FrozenModel):
    mode: Literal["reject_only", "promote"]
    mutated_count: int = Field(ge=0)
    aggregate_sha256: str = Field(min_length=64, max_length=64)


class KoreanAudioReviewApplicationService:
    def __init__(self, audio_repository: object) -> None:
        self.audio_repository = audio_repository

    def prestate_sha256(self, job_id: str, asset_keys: tuple[tuple[str, AudioAssetKind], ...]) -> str:
        payload = []
        for item_key, asset_kind in sorted(asset_keys, key=lambda key: (key[0], key[1].value)):
            asset = self._require_asset(job_id, item_key, asset_kind)
            payload.append(
                {
                    "job_id": asset.job_id,
                    "item_key": asset.item_key,
                    "asset_kind": asset.asset_kind.value,
                    "synthesis_request_sha256": asset.provenance.synthesis_request_sha256,
                    "artifact_sha256": asset.provenance.artifact_sha256,
                    "audio_review_status": asset.provenance.audio_review_status.value
                    if asset.provenance.audio_review_status is not None
                    else None,
                }
            )
        return _canonical_sha256(payload)

    def apply(
        self,
        aggregate: KoreanAudioReviewAggregate,
        authority: KoreanAudioReviewApplicationAuthority,
    ) -> KoreanAudioReviewApplicationResult:
        if aggregate.aggregate_sha256 != authority.aggregate_sha256:
            raise ValueError("Korean audio-review aggregate drift")
        if authority.mode == "reject_only" and authority.power != "remediation":
            raise ValueError("reject-only audio review requires remediation authority")
        if authority.mode == "promote" and authority.power not in {"initial_content_promotion", "final_content_promotion"}:
            raise ValueError("audio review promotion requires content-promotion authority")
        if authority.mode == "promote" and aggregate.rejected_count:
            raise ValueError("audio review promotion requires zero rejections")
        if authority.mode == "promote" and (authority.audio_review_receipt_sha256 is None or authority.heard_review_receipt_sha256 is None):
            raise ValueError("audio review promotion requires review receipts")
        if self.prestate_sha256(aggregate.job_id, aggregate.asset_keys) != authority.prestate_sha256:
            raise ValueError("Korean audio-review prestate drift")

        mutations = []
        for decision in aggregate.decisions:
            asset = self._require_asset(aggregate.job_id, decision.item_key, decision.asset_kind)
            _assert_decision_matches_asset(decision, asset)
            if authority.mode == "reject_only" and decision.outcome == "rejected":
                mutations.append(
                    asset.model_copy(
                        update={
                            "provenance": asset.provenance.model_copy(
                                update={
                                    "audio_review_status": AudioReviewStatus.REJECTED,
                                    "rejection_reason_code": decision.rejection_codes[0],
                                }
                            )
                        }
                    )
                )
            elif authority.mode == "promote" and decision.outcome == "accepted":
                mutations.append(
                    asset.model_copy(
                        update={
                            "provenance": asset.provenance.model_copy(
                                update={
                                    "audio_review_status": AudioReviewStatus.APPROVED,
                                    "audio_review_receipt_sha256": authority.audio_review_receipt_sha256,
                                    "heard_review_receipt_sha256": authority.heard_review_receipt_sha256,
                                }
                            )
                        }
                    )
                )
        for asset in mutations:
            self.audio_repository.upsert_audio_asset(asset)
        return KoreanAudioReviewApplicationResult(
            mode=authority.mode,
            mutated_count=len(mutations),
            aggregate_sha256=aggregate.aggregate_sha256,
        )

    def _require_asset(self, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> object:
        getter = getattr(self.audio_repository, "get_asset", None)
        if not callable(getter):
            raise ValueError("audio repository cannot load review assets")
        asset = getter(job_id, item_key, asset_kind)
        if asset is None:
            raise ValueError("unknown Korean audio-review asset")
        return asset


def _assert_decision_matches_asset(decision: KoreanAudioReviewBatchDecision, asset: object) -> None:
    provenance = getattr(asset, "provenance", None)
    if getattr(provenance, "synthesis_request_sha256", None) != decision.synthesis_request_sha256:
        raise ValueError("stale Korean audio review request")
    if getattr(provenance, "artifact_sha256", None) != decision.artifact_sha256:
        raise ValueError("stale Korean audio review bytes")


__all__ = [
    "KoreanAudioReviewAggregate",
    "KoreanAudioReviewApplicationAuthority",
    "KoreanAudioReviewApplicationResult",
    "KoreanAudioReviewApplicationService",
    "KoreanAudioReviewBatch",
    "KoreanAudioReviewBatchDecision",
    "KoreanAudioReviewImportLedger",
    "KoreanAudioReviewImportResult",
]
