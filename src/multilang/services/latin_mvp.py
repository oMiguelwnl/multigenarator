"""Deterministic start service for the isolated Classical Latin MVP path."""

from __future__ import annotations

from pydantic import BaseModel, Field

from multilang.domain.latin import LATIN_MVP_CARD_COUNT, LatinDeckMetadata, LatinGenerationRequest


class LatinMvpStartResult(BaseModel):
    """Machine-readable result for starting a Latin MVP generation run."""

    metadata: LatinDeckMetadata
    source_type: str = "latin-mvp"
    item_keys: list[str] = Field(default_factory=list)


class LatinMvpGenerationService:
    """Build the fixed Latin MVP run contract without modern frequency paths."""

    def start(self, request: LatinGenerationRequest) -> LatinMvpStartResult:
        metadata = request.metadata()
        return LatinMvpStartResult(
            metadata=metadata,
            source_type=request.source_type,
            item_keys=[f"latin-mvp-{index:04d}" for index in range(1, LATIN_MVP_CARD_COUNT + 1)],
        )


__all__ = ["LatinMvpGenerationService", "LatinMvpStartResult"]
