"""Content-free Korean frequency source-review receipt aggregation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import (
    KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
    KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
    KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT,
    KoreanFrequencyBuildResult,
    KoreanFrequencyBundleManifest,
    canonical_json_sha256,
    raw_bytes_sha256,
)
from multilang.services.korean_frequency import validate_korean_source_build_result


_BATCH_SCHEMA_VERSION = "korean-source-review-batch-v1"
_RECEIPT_SCHEMA_VERSION = "korean-source-review-receipt-v1"
_POLICY_ID = "multilang-ai-linguistic-review-v1"
_REVIEWER_CLASS = "ai_policy_source_review"
_REVIEWER_ROLE = "source-curation"
_MAX_BATCH_SIZE = 100
_HEX = frozenset("0123456789abcdef")
_BUNDLE_MANIFEST_PATH = "manifest.json"
_INVENTORY_PATH = "curated-inventory.jsonl"
_REJECTIONS_PATH = "rejections.jsonl"
_SUBJECT_CACHE_LIMIT = 4
_SUBJECT_CACHE: dict[tuple[str, str], dict[int, tuple[str, str]]] = {}


@dataclass(frozen=True, slots=True)
class KoreanSourceReviewBatchReceipt:
    batch_id: str
    build_result_sha256: str
    bundle_sha256: str
    decision_count: int
    accepted_count: int
    rejected_count: int
    source_ranks: tuple[int, ...]
    decision_set_sha256: str
    receipt_sha256: str
    reviewer_class: str
    reviewer_role: str


@dataclass(frozen=True, slots=True)
class KoreanSourceReviewAggregate:
    status: Literal["complete"]
    total_dispositions: int
    accepted_count: int
    rejected_count: int
    max_batch_size: int
    receipt_count: int
    aggregate_sha256: str


@dataclass(frozen=True, slots=True)
class _BuildContext:
    build_result_sha256: str
    bundle_sha256: str
    subjects: dict[int, tuple[str, str]]


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def _sha256(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in _HEX for ch in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_identifier(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 128
        or not value[0].isalnum()
        or any(not ch.isascii() or not (ch.isalnum() or ch in "._:-") for ch in value)
    ):
        raise ValueError(f"{field_name} must be a safe identifier")
    return value


class _ReviewDecision(_FrozenModel):
    source_rank: int = Field(ge=1, le=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT)
    disposition: Literal["accepted", "rejected"]
    subject_sha256: str = Field(min_length=64, max_length=64)
    risk_codes: tuple[str, ...] = Field(min_length=1, max_length=16)

    @field_validator("subject_sha256")
    @classmethod
    def subject_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256(value, field_name="subject_sha256")

    @field_validator("risk_codes")
    @classmethod
    def risk_codes_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_safe_identifier(item, field_name="risk code") for item in value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("risk codes must be unique")
        return normalized


class _ReviewBatchPayload(_FrozenModel):
    schema_version: Literal["korean-source-review-batch-v1"]
    batch_id: str = Field(min_length=1, max_length=128)
    reviewer_class: Literal["ai_policy_source_review"]
    reviewer_role: Literal["source-curation"]
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    build_result_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    decisions: tuple[_ReviewDecision, ...] = Field(min_length=1, max_length=_MAX_BATCH_SIZE)

    @field_validator("batch_id")
    @classmethod
    def batch_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="batch_id")

    @field_validator("build_result_sha256", "bundle_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def decisions_must_be_disjoint(self) -> Self:
        ranks = tuple(decision.source_rank for decision in self.decisions)
        if len(ranks) != len(set(ranks)):
            raise ValueError("review batch source ranks must be disjoint")
        return self


class _ReviewReceiptFile(_FrozenModel):
    schema_version: Literal["korean-source-review-receipt-v1"]
    batch_id: str
    reviewer_class: Literal["ai_policy_source_review"]
    reviewer_role: Literal["source-curation"]
    policy_id: Literal["multilang-ai-linguistic-review-v1"]
    build_result_sha256: str
    bundle_sha256: str
    decisions: tuple[_ReviewDecision, ...]
    decision_count: int = Field(ge=1, le=_MAX_BATCH_SIZE)
    accepted_count: int = Field(ge=0, le=_MAX_BATCH_SIZE)
    rejected_count: int = Field(ge=0, le=_MAX_BATCH_SIZE)
    source_ranks: tuple[int, ...] = Field(min_length=1, max_length=_MAX_BATCH_SIZE)
    decision_set_sha256: str
    receipt_sha256: str

    @field_validator("batch_id")
    @classmethod
    def batch_id_must_be_safe(cls, value: str) -> str:
        return _safe_identifier(value, field_name="batch_id")

    @field_validator("build_result_sha256", "bundle_sha256", "decision_set_sha256", "receipt_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256(value, field_name=getattr(info, "field_name", "hash"))

    @model_validator(mode="after")
    def counts_must_match_decisions(self) -> Self:
        accepted = sum(1 for decision in self.decisions if decision.disposition == "accepted")
        rejected = sum(1 for decision in self.decisions if decision.disposition == "rejected")
        ranks = tuple(decision.source_rank for decision in self.decisions)
        if self.source_ranks != ranks:
            raise ValueError("receipt source ranks drift")
        if self.decision_count != len(self.decisions):
            raise ValueError("receipt decision count drift")
        if self.accepted_count != accepted or self.rejected_count != rejected:
            raise ValueError("receipt disposition count drift")
        if self.decision_set_sha256 != canonical_json_sha256(
            [decision.model_dump(mode="json") for decision in self.decisions]
        ):
            raise ValueError("receipt decision hash drift")
        return self


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _safe_receipt_dir(receipt_dir: Path) -> Path:
    path = Path(receipt_dir)
    if path.exists() and (not path.is_dir() or path.is_symlink()):
        raise ValueError("source-review receipt directory is unsafe")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("source-review receipt directory is unsafe")
    return path


def _atomic_write_receipt(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ValueError("source-review receipt target is unsafe")
        if path.read_bytes() == payload:
            return
        raise ValueError("source-review receipt collision")
    with NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise


def _load_batch(path: Path) -> _ReviewBatchPayload:
    try:
        return _ReviewBatchPayload.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("source-review batch is invalid") from exc


def _load_receipt(path: Path) -> _ReviewReceiptFile:
    try:
        receipt = _ReviewReceiptFile.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("source-review receipt is invalid") from exc
    payload = receipt.model_dump(mode="json", exclude={"receipt_sha256"})
    if receipt.receipt_sha256 != canonical_json_sha256(payload):
        raise ValueError("source-review receipt hash drift")
    return receipt


def _load_json_model(path: Path, model: type[BaseModel], *, error: str) -> BaseModel:
    try:
        return model.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(error) from exc


def _safe_bundle_child(bundle_dir: Path, relative_path: str) -> Path:
    child = Path(bundle_dir) / relative_path
    try:
        metadata = child.lstat()
    except OSError as exc:
        raise ValueError("source-review bundle member is unavailable") from exc
    if child.parent != Path(bundle_dir) or child.is_symlink() or not child.is_file() or metadata.st_size <= 0:
        raise ValueError("source-review bundle member is unsafe")
    return child


def _expected_manifest_bundle_sha256(manifest: KoreanFrequencyBundleManifest) -> str:
    return canonical_json_sha256(manifest.model_dump(mode="json", exclude={"bundle_sha256"}))


def _bundle_subjects_from_payloads(
    inventory_payload: bytes,
    rejection_payload: bytes,
    *,
    inventory_sha256: str,
    rejection_sha256: str,
) -> dict[int, tuple[str, str]]:
    cache_key = (inventory_sha256, rejection_sha256)
    cached = _SUBJECT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    subjects: dict[int, tuple[str, str]] = {}
    for line in inventory_payload.splitlines():
        row = json.loads(line.decode("utf-8"))
        subjects[int(row["source_rank"])] = (
            "accepted",
            canonical_json_sha256(row["lexical_identity"]),
        )
    for line in rejection_payload.splitlines():
        row = json.loads(line.decode("utf-8"))
        subjects[int(row["source_rank"])] = ("rejected", row["source_form_sha256"])
    if set(subjects) != set(range(1, KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT + 1)):
        raise ValueError("source-review bundle subjects are incomplete")
    if len(_SUBJECT_CACHE) >= _SUBJECT_CACHE_LIMIT:
        _SUBJECT_CACHE.clear()
    _SUBJECT_CACHE[cache_key] = subjects
    return subjects


def _load_build_context(build_result_file: Path, bundle_dir: Path) -> _BuildContext:
    root = Path(bundle_dir)
    try:
        metadata = root.lstat()
    except OSError as exc:
        raise ValueError("source-review bundle root is unavailable") from exc
    if root.is_symlink() or not root.is_dir() or metadata.st_size < 0:
        raise ValueError("source-review bundle root is unsafe")
    try:
        build_result_payload = Path(build_result_file).read_bytes()
    except OSError as exc:
        raise ValueError("source-review build result is unavailable") from exc
    try:
        result = KoreanFrequencyBuildResult.model_validate_json(build_result_payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("source-review build result is invalid") from exc
    manifest = _load_json_model(
        _safe_bundle_child(root, _BUNDLE_MANIFEST_PATH),
        KoreanFrequencyBundleManifest,
        error="source-review bundle manifest is invalid",
    )
    assert isinstance(manifest, KoreanFrequencyBundleManifest)
    if _expected_manifest_bundle_sha256(manifest) != manifest.bundle_sha256:
        raise ValueError("source-review bundle manifest hash drift")
    if result.bundle_sha256 != manifest.bundle_sha256:
        raise ValueError("source-review build result bundle hash drift")
    if result.inventory_sha256 != manifest.inventory_sha256:
        raise ValueError("source-review inventory hash drift")
    if result.rejection_sha256 != manifest.rejection_sha256:
        raise ValueError("source-review rejection hash drift")
    inventory_payload = _safe_bundle_child(root, _INVENTORY_PATH).read_bytes()
    rejection_payload = _safe_bundle_child(root, _REJECTIONS_PATH).read_bytes()
    inventory_sha256 = raw_bytes_sha256(inventory_payload)
    rejection_sha256 = raw_bytes_sha256(rejection_payload)
    if inventory_sha256 != result.inventory_sha256:
        raise ValueError("source-review inventory bytes drift")
    if rejection_sha256 != result.rejection_sha256:
        raise ValueError("source-review rejection bytes drift")
    return _BuildContext(
        build_result_sha256=raw_bytes_sha256(build_result_payload),
        bundle_sha256=result.bundle_sha256,
        subjects=_bundle_subjects_from_payloads(
            inventory_payload,
            rejection_payload,
            inventory_sha256=inventory_sha256,
            rejection_sha256=rejection_sha256,
        ),
    )


def _validate_batch_against_build(
    batch: _ReviewBatchPayload,
    *,
    build_result_file: Path,
    bundle_dir: Path,
) -> None:
    context = _load_build_context(build_result_file, bundle_dir)
    if batch.build_result_sha256 != context.build_result_sha256:
        raise ValueError("source-review build result hash drift")
    if batch.bundle_sha256 != context.bundle_sha256:
        raise ValueError("source-review bundle hash drift")
    for decision in batch.decisions:
        expected_disposition, expected_subject_hash = context.subjects[decision.source_rank]
        if decision.disposition != expected_disposition:
            raise ValueError("source-review disposition drift")
        if decision.subject_sha256 != expected_subject_hash:
            raise ValueError("source-review subject hash drift")


def _receipt_file_payload(batch: _ReviewBatchPayload) -> dict[str, object]:
    decisions = [decision.model_dump(mode="json") for decision in batch.decisions]
    payload = {
        "schema_version": _RECEIPT_SCHEMA_VERSION,
        "batch_id": batch.batch_id,
        "reviewer_class": batch.reviewer_class,
        "reviewer_role": batch.reviewer_role,
        "policy_id": batch.policy_id,
        "build_result_sha256": batch.build_result_sha256,
        "bundle_sha256": batch.bundle_sha256,
        "decisions": decisions,
        "decision_count": len(batch.decisions),
        "accepted_count": sum(1 for decision in batch.decisions if decision.disposition == "accepted"),
        "rejected_count": sum(1 for decision in batch.decisions if decision.disposition == "rejected"),
        "source_ranks": [decision.source_rank for decision in batch.decisions],
        "decision_set_sha256": canonical_json_sha256(decisions),
    }
    payload["receipt_sha256"] = canonical_json_sha256(payload)
    return payload


def _to_receipt(receipt: _ReviewReceiptFile) -> KoreanSourceReviewBatchReceipt:
    return KoreanSourceReviewBatchReceipt(
        batch_id=receipt.batch_id,
        build_result_sha256=receipt.build_result_sha256,
        bundle_sha256=receipt.bundle_sha256,
        decision_count=receipt.decision_count,
        accepted_count=receipt.accepted_count,
        rejected_count=receipt.rejected_count,
        source_ranks=receipt.source_ranks,
        decision_set_sha256=receipt.decision_set_sha256,
        receipt_sha256=receipt.receipt_sha256,
        reviewer_class=receipt.reviewer_class,
        reviewer_role=receipt.reviewer_role,
    )


def import_korean_bundle_review_batch(
    batch_file: Path,
    *,
    build_result_file: Path,
    bundle_dir: Path,
    receipt_dir: Path,
) -> KoreanSourceReviewBatchReceipt:
    """Import one at-most-100-row source-review batch as an immutable receipt."""

    batch = _load_batch(batch_file)
    _validate_batch_against_build(
        batch,
        build_result_file=build_result_file,
        bundle_dir=bundle_dir,
    )
    root = _safe_receipt_dir(receipt_dir)
    payload = _receipt_file_payload(batch)
    receipt_path = root / f"{batch.batch_id}.json"
    raw = _canonical_bytes(payload)
    _atomic_write_receipt(receipt_path, raw)
    return _to_receipt(_load_receipt(receipt_path))


def validate_korean_bundle_review_batches(
    receipt_dir: Path,
    *,
    build_result_file: Path,
    bundle_dir: Path,
) -> KoreanSourceReviewAggregate:
    """Aggregate exact source-review coverage without exposing source content."""

    result = validate_korean_source_build_result(build_result_file, bundle_dir=bundle_dir)
    build_result_hash = raw_bytes_sha256(Path(build_result_file).read_bytes())
    root = Path(receipt_dir)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("source-review receipt directory is unavailable")
    receipts: list[_ReviewReceiptFile] = []
    for child in sorted(root.iterdir()):
        if child.is_symlink() or not child.is_file() or child.suffix != ".json":
            raise ValueError("source-review receipt directory contains unsafe member")
        receipt = _load_receipt(child)
        if child.name != f"{receipt.batch_id}.json":
            raise ValueError("source-review receipt filename drift")
        if receipt.build_result_sha256 != build_result_hash:
            raise ValueError("source-review receipt build hash drift")
        if receipt.bundle_sha256 != result.bundle_sha256:
            raise ValueError("source-review receipt bundle hash drift")
        receipts.append(receipt)
    if not receipts:
        raise ValueError("source-review receipts are missing")
    seen: set[int] = set()
    accepted = 0
    rejected = 0
    max_batch_size = 0
    for receipt in receipts:
        max_batch_size = max(max_batch_size, receipt.decision_count)
        accepted += receipt.accepted_count
        rejected += receipt.rejected_count
        for decision in receipt.decisions:
            if decision.source_rank in seen:
                raise ValueError("source-review source ranks overlap")
            seen.add(decision.source_rank)
    if seen != set(range(1, KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT + 1)):
        raise ValueError("source-review source ranks are incomplete")
    if accepted != KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT:
        raise ValueError("source-review accepted count drift")
    if rejected != KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT:
        raise ValueError("source-review rejected count drift")
    payload = {
        "accepted_count": accepted,
        "build_result_sha256": build_result_hash,
        "bundle_sha256": result.bundle_sha256,
        "max_batch_size": max_batch_size,
        "receipt_sha256s": [receipt.receipt_sha256 for receipt in receipts],
        "rejected_count": rejected,
        "total_dispositions": len(seen),
    }
    return KoreanSourceReviewAggregate(
        status="complete",
        total_dispositions=len(seen),
        accepted_count=accepted,
        rejected_count=rejected,
        max_batch_size=max_batch_size,
        receipt_count=len(receipts),
        aggregate_sha256=canonical_json_sha256(payload),
    )


__all__ = [
    "KoreanSourceReviewAggregate",
    "KoreanSourceReviewBatchReceipt",
    "import_korean_bundle_review_batch",
    "validate_korean_bundle_review_batches",
]
