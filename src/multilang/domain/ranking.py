"""Corpus allocation and reproducible RANK-01 result contracts."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import UnitDecimal, canonical_sha256

PositiveDecimal = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class CorpusManifest(NativeContract):
    corpus_id: Identifier
    sha256: Sha256
    language: SupportedLanguage
    version: Identifier
    token_count: int = Field(ge=1)
    document_count: int = Field(ge=1)
    weight: UnitDecimal
    source_id: Identifier
    license_id: Identifier
    redistribution_approved: bool = False
    privacy_class: Literal["public", "private"] = "public"
    domain: Identifier
    period: Identifier
    variant: Identifier
    held_out: bool = False

    @model_validator(mode="after")
    def private_corpus_cannot_be_published(self) -> Self:
        if self.privacy_class == "private" and self.redistribution_approved:
            raise ValueError("private corpus cannot authorize shared redistribution")
        return self


class Allocation(NativeContract):
    lexical_identity_id: Identifier
    share: Annotated[Decimal, Field(gt=0, le=1, allow_inf_nan=False)]
    confidence: UnitDecimal


class CorpusObservation(NativeContract):
    corpus_id: Identifier
    document_id: Identifier
    occurrence_id: Identifier
    token_start: int = Field(ge=0)
    token_end: int = Field(ge=1)
    surface: str = Field(min_length=1, max_length=512)
    occurrence_count: PositiveDecimal = Decimal(1)
    allocations: tuple[Allocation, ...] = ()
    counting_channel: Identifier = "lexical"
    is_mwe: bool = False

    @model_validator(mode="after")
    def validate_allocation(self) -> Self:
        if self.token_end <= self.token_start:
            raise ValueError("occurrence must have a positive token span")
        if self.token_end - self.token_start > 4096:
            raise ValueError("occurrence exceeds maximum token span")
        ids = [item.lexical_identity_id for item in self.allocations]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate identity allocation in occurrence")
        if self.allocations and sum(
            (item.share for item in self.allocations), Decimal(0)
        ) != Decimal(1):
            raise ValueError("accepted allocation shares must sum exactly to 1")
        if self.is_mwe and self.token_end - self.token_start < 2:
            raise ValueError("MWE must have an explicitly segmented multi-token span")
        return self


class RankingPolicy(NativeContract):
    version: Identifier
    normalizer_version: Identifier
    analyzer_version: Identifier
    tokenizer_version: Identifier
    tagset_version: Identifier
    allocation_policy_version: Identifier
    mwe_policy_version: Identifier
    confidence_threshold: UnitDecimal
    rank_precision: int = Field(default=8, ge=0, le=18)
    intermediate_precision: int = Field(default=50, ge=28, le=100)
    formula_version: Literal["RANK-01-ln-ppm-dispersion-1"] = (
        "RANK-01-ln-ppm-dispersion-1"
    )
    rounding: Literal["ROUND_HALF_EVEN"] = "ROUND_HALF_EVEN"
    allowed_counting_channels: tuple[Identifier, ...] = ("lexical",)
    overlap_approval_sha256: Sha256 | None = None
    quality_version: Literal["frequency-confidence-coverage-validation-1"] = (
        "frequency-confidence-coverage-validation-1"
    )
    quality_weights: dict[str, UnitDecimal] = Field(
        default_factory=lambda: {
            "frequency": Decimal("0.25"),
            "confidence": Decimal("0.25"),
            "coverage": Decimal("0.25"),
            "validation": Decimal("0.25"),
        }
    )

    @model_validator(mode="after")
    def policies_are_complete(self) -> Self:
        if set(self.quality_weights) != {
            "frequency",
            "confidence",
            "coverage",
            "validation",
        }:
            raise ValueError("quality score requires all four evidence dimensions")
        if sum(self.quality_weights.values(), Decimal(0)) != Decimal(1):
            raise ValueError("quality weights must sum exactly to 1")
        if not self.allowed_counting_channels or len(
            set(self.allowed_counting_channels)
        ) != len(self.allowed_counting_channels):
            raise ValueError("counting channels must be nonempty and unique")
        if len(self.allowed_counting_channels) > 1 and not self.overlap_approval_sha256:
            raise ValueError(
                "overlap across counting channels requires explicit approval"
            )
        return self

    @computed_field
    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude_computed_fields=True)
        )


class CorpusContribution(NativeContract):
    corpus_id: Identifier
    allocated_count: PositiveDecimal
    document_frequency: int = Field(ge=1)
    frequency_ppm: PositiveDecimal
    dispersion: UnitDecimal
    occurrence_ids: tuple[Identifier, ...]


class RankingEntry(NativeContract):
    lexical_identity_id: Identifier
    rank: int = Field(ge=1)
    score: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
    aggregate_allocated_frequency: PositiveDecimal
    quality_score: UnitDecimal
    contributions: tuple[CorpusContribution, ...]

    @computed_field
    @property
    def level(self) -> int | None:
        return ((self.rank - 1) // 1000) + 1 if self.rank <= 3000 else None


class QuarantinedOccurrence(NativeContract):
    corpus_id: Identifier
    occurrence_id: Identifier
    reason: Literal[
        "unresolved_allocation",
        "allocation_confidence_below_threshold",
        "ambiguous_span",
    ]


class RankingResult(NativeContract):
    language: SupportedLanguage
    policy: RankingPolicy
    corpora: tuple[CorpusManifest, ...]
    observations_sha256: Sha256
    entries: tuple[RankingEntry, ...]
    quarantine: tuple[QuarantinedOccurrence, ...] = ()
    suppressed_occurrence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def ranking_is_reconciled(self) -> Self:
        ids = [entry.lexical_identity_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate lexical identity in ranking")
        if [entry.rank for entry in self.entries] != list(
            range(1, len(self.entries) + 1)
        ):
            raise ValueError("ranking positions must be contiguous")
        return self

    @computed_field
    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="json", exclude_computed_fields=True)
        )

    def diff(self, other: RankingResult) -> tuple[dict[str, object], ...]:
        before = {item.lexical_identity_id: item for item in self.entries}
        after = {item.lexical_identity_id: item for item in other.entries}
        return tuple(
            {
                "lexical_identity_id": identity_id,
                "before": before[identity_id].model_dump(mode="json")
                if identity_id in before
                else None,
                "after": after[identity_id].model_dump(mode="json")
                if identity_id in after
                else None,
            }
            for identity_id in sorted(before.keys() | after.keys())
            if before.get(identity_id) != after.get(identity_id)
        )


def validate_core_ranking(result: RankingResult) -> None:
    """Validate Core size; software accounting does not approve linguistic quality."""
    if result.language is SupportedLanguage.LA:
        raise ValueError("Latin is excluded from modern Core")
    if len(result.entries) != 3000:
        raise ValueError("Core requires exactly 3000 unique lexical identities")
    if any(
        sum(entry.level == level for entry in result.entries) != 1000
        for level in (1, 2, 3)
    ):
        raise ValueError("Core requires exactly 1000 identities per level")


class RankingContract(Protocol):
    def calculate(
        self,
        *,
        corpora: Iterable[CorpusManifest],
        observations: Iterable[CorpusObservation],
        policy: RankingPolicy,
    ) -> RankingResult: ...
