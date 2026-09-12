"""Minimized, revocable learner data isolated from canonical editions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.content import canonical_content_hash


class LearningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class HistoryAlias(LearningModel):
    note_guid: str = Field(min_length=1, max_length=128)
    template_ordinal: int = Field(ge=0, le=10000)
    model_id: int = Field(gt=0)
    semantic_card_id: str = Field(min_length=1, max_length=255)
    parent_lexical_identity_id: str = Field(min_length=1, max_length=255)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    confidence: Literal["verified_one_to_one"] = "verified_one_to_one"


class HistoryLimits(LearningModel):
    max_archive_bytes: int = Field(
        default=128 * 1024 * 1024, ge=1, le=512 * 1024 * 1024
    )
    max_member_bytes: int = Field(default=128 * 1024 * 1024, ge=1, le=256 * 1024 * 1024)
    max_total_uncompressed_bytes: int = Field(
        default=512 * 1024 * 1024, ge=1, le=1024 * 1024 * 1024
    )
    max_members: int = Field(default=10000, ge=1, le=100000)
    max_compression_ratio: float = Field(default=100, ge=1, le=1000)
    max_cards: int = Field(default=100000, ge=1, le=1000000)
    max_reviews: int = Field(default=1000000, ge=1, le=5000000)
    max_seconds: float = Field(default=10, gt=0, le=60)
    max_sqlite_operations: int = Field(default=20000000, ge=1000, le=100000000)


class MappedLearnerState(LearningModel):
    semantic_card_id: str
    parent_lexical_identity_id: str
    repetitions: int = Field(ge=0)
    lapses: int = Field(ge=0)
    interval_days: int = Field(ge=0)
    review_count: int = Field(ge=0)
    last_review_ms: int | None = Field(default=None, ge=0)
    mapping_evidence_sha256: str


class HistoryImport(LearningModel):
    namespace: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mapping_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    states: tuple[MappedLearnerState, ...]
    quarantined_count: int = Field(ge=0)
    raw_copy_retained: Literal[False] = False

    @property
    def import_id(self) -> str:
        return "history:1:" + canonical_content_hash(
            {
                "namespace": self.namespace,
                "input": self.input_sha256,
                "mapping": self.mapping_sha256,
            }
        )


class LearnerState(LearningModel):
    namespace: str
    known_card_ids: tuple[str, ...] = ()
    reading_card_ids: tuple[str, ...] = ()
    history: tuple[HistoryImport, ...] = ()
    overrides: dict[str, int] = Field(default_factory=dict)
    expansion_enabled: bool = False
    revision: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def isolated_history(self) -> LearnerState:
        if not self.namespace.startswith("user:") or len(self.namespace) <= 5:
            raise ValueError("learner state requires explicit user namespace")
        if any(item.namespace != self.namespace for item in self.history):
            raise ValueError("history belongs to another user namespace")
        if len(self.overrides) > 100000 or any(
            abs(value) > 10000 for value in self.overrides.values()
        ):
            raise ValueError("adaptive override limit exceeded")
        return self


class AdaptivePolicy(LearningModel):
    version: str = "1"
    mode: Literal["core_first", "balanced", "reading_first"] = "core_first"
    module_size: int = Field(default=100, ge=50, le=200)
    require_ready_content: bool = False
    max_cards: int = Field(default=200000, ge=1, le=1000000)


class QueueEntry(LearningModel):
    card_id: str
    score: int
    components: dict[str, int]
    module: int
    destination: str


class DeferredCard(LearningModel):
    card_id: str
    reason: Literal[
        "known",
        "prerequisite",
        "expansion_disabled",
        "content_not_ready",
        "private_namespace",
    ]


class AdaptiveQueueResult(LearningModel):
    namespace: str
    policy_sha256: str
    source_snapshot_sha256: str
    queue_sha256: str
    eligible: tuple[QueueEntry, ...]
    deferred: tuple[DeferredCard, ...]
    counts: dict[str, dict[str, int]]
