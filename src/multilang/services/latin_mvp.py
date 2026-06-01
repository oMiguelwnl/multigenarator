"""Deterministic start service for the isolated Classical Latin MVP path."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, Field

from multilang.domain.latin import LatinDeckMetadata, LatinGenerationRequest
from multilang.services.latin_source_pack import (
    DEFAULT_LATIN_MVP_SOURCE_PACK_PATH,
    LatinMvpSourcePack,
    load_latin_mvp_source_pack,
)

LatinSourcePackLoader = Callable[[Path | None], LatinMvpSourcePack]


class LatinMvpStartResult(BaseModel):
    """Machine-readable result for starting a Latin MVP generation run."""

    metadata: LatinDeckMetadata
    source_type: str = "latin-mvp"
    item_keys: list[str] = Field(default_factory=list)
    manifest_path: str
    first_item_key: str
    last_item_key: str
    license_gate_status: str
    source_type_counts: dict[str, int] = Field(default_factory=dict)
    frequency_source_count: int
    didactic_sequence_summary: str

    def manifest_summary(self) -> dict[str, object]:
        """Return a scanner-friendly public summary of the loaded source pack."""

        return {
            "language_code": self.metadata.language_code,
            "variant": self.metadata.variant.value,
            "source_type": self.source_type,
            "source_pack_version": self.metadata.source_pack_version,
            "card_count": self.metadata.card_count,
            "item_count": len(self.item_keys),
            "manifest_path": self.manifest_path,
            "first_item_key": self.first_item_key,
            "last_item_key": self.last_item_key,
            "license_gate_status": self.license_gate_status,
            "source_type_counts": self.source_type_counts,
            "frequency_source_count": self.frequency_source_count,
            "didactic_sequence_summary": self.didactic_sequence_summary,
        }


class LatinMvpGenerationService:
    """Build the fixed Latin MVP run contract without modern frequency paths."""

    def __init__(
        self,
        *,
        source_pack_path: Path | None = None,
        source_pack_loader: LatinSourcePackLoader = load_latin_mvp_source_pack,
    ) -> None:
        self.source_pack_path = source_pack_path
        self.source_pack_loader = source_pack_loader

    def start(self, request: LatinGenerationRequest) -> LatinMvpStartResult:
        pack = self.source_pack_loader(self.source_pack_path)
        if request.source_pack_version != pack.source_pack_version:
            raise ValueError(
                "source_pack_version mismatch: "
                f"request={request.source_pack_version} manifest={pack.source_pack_version}"
            )
        metadata = request.metadata()
        item_keys = [entry.item_key for entry in pack.entries]
        source_type_counts: dict[str, int] = {}
        for entry in pack.entries:
            source_type_counts[entry.source_type] = source_type_counts.get(entry.source_type, 0) + 1
        license_gate_status = "approved" if all(entry.license_gate == "approved" for entry in pack.entries) else "blocked"
        return LatinMvpStartResult(
            metadata=metadata,
            source_type=request.source_type,
            item_keys=item_keys,
            manifest_path=str(self.source_pack_path or DEFAULT_LATIN_MVP_SOURCE_PACK_PATH).replace("\\", "/"),
            first_item_key=item_keys[0],
            last_item_key=item_keys[-1],
            license_gate_status=license_gate_status,
            source_type_counts=source_type_counts,
            frequency_source_count=len({entry.frequency_source for entry in pack.entries}),
            didactic_sequence_summary=(
                f"50 entries loaded from {pack.source_pack_version}; didactic sequence preserves frequency ranks "
                "while ordering clear beginner contexts first."
            ),
        )


__all__ = ["LatinMvpGenerationService", "LatinMvpStartResult"]
