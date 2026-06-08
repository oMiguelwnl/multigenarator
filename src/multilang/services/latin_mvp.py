"""Deterministic start service for the isolated Classical Latin MVP path."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, Field

from multilang.domain.latin import LatinDeckMetadata, LatinGenerationRequest
from multilang.services.latin_audio import (
    DEFAULT_LATIN_AUDIO_MANIFEST_PATH,
    LatinAudioManifest,
    load_latin_audio_manifest,
    summarize_latin_audio_manifest,
)
from multilang.services.latin_source_pack import (
    APPROVED_LATIN_CASE_LABELS,
    DEFAULT_LATIN_MVP_SOURCE_PACK_PATH,
    LatinMvpSourcePack,
    load_latin_mvp_source_pack,
)
from multilang.services.latin_translation_quality import (
    DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH,
    LatinPortugueseTranslationPack,
    LatinPortugueseTranslationQaService,
    load_latin_portuguese_translation_pack,
)

LatinSourcePackLoader = Callable[[Path | None], LatinMvpSourcePack]
LatinPortugueseTranslationPackLoader = Callable[[Path | None], LatinPortugueseTranslationPack]
LatinAudioManifestLoader = Callable[[Path | None], LatinAudioManifest]


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
    grammar_gate_status: str
    grammar_evidence_count: int
    gramatica_count: int
    required_case_labels: list[str] = Field(default_factory=list)
    portuguese_translation_summary: dict[str, object] | None = None
    audio_summary: dict[str, object] | None = None

    def manifest_summary(self) -> dict[str, object]:
        """Return a scanner-friendly public summary of the loaded source pack."""

        summary: dict[str, object] = {
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
            "grammar_gate_status": self.grammar_gate_status,
            "grammar_evidence_count": self.grammar_evidence_count,
            "gramatica_count": self.gramatica_count,
            "required_case_labels": self.required_case_labels,
        }
        if self.portuguese_translation_summary is not None:
            summary["portuguese_translation_summary"] = self.portuguese_translation_summary
        if self.audio_summary is not None:
            summary["audio_summary"] = self.audio_summary
        return summary


def _public_audio_summary(manifest: LatinAudioManifest) -> dict[str, object]:
    """Return aggregate-only Latin audio readiness suitable for CLI JSON output."""

    readiness_summary = summarize_latin_audio_manifest(manifest)
    provider_counts: dict[str, int] = {}
    playback_status_counts: dict[str, int] = {}
    word_count = 0
    sentence_count = 0
    approved_item_count = 0

    for pair in manifest.artifacts:
        pair_approved = True
        for artifact in (pair.word, pair.sentence):
            if artifact is None:
                pair_approved = False
                continue
            if artifact.audio_kind == "word":
                word_count += 1
            if artifact.audio_kind == "sentence":
                sentence_count += 1
            provider_counts[artifact.provider] = provider_counts.get(artifact.provider, 0) + 1
            playback_status_counts[artifact.playback_review_status] = (
                playback_status_counts.get(artifact.playback_review_status, 0) + 1
            )
            if artifact.playback_review_status != "approved":
                pair_approved = False
        if pair_approved and pair.word is not None and pair.sentence is not None:
            approved_item_count += 1

    readiness_status = "approved" if readiness_summary.blocked_items == 0 else "blocked"
    return {
        "source_pack_version": manifest.source_pack_version,
        "manifest_version": manifest.source_pack_version,
        "entry_count": readiness_summary.total_items,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "approved_count": approved_item_count,
        "blocked_count": readiness_summary.blocked_items,
        "provider_counts": provider_counts,
        "playback_status_counts": playback_status_counts,
        "readiness_status": readiness_status,
    }


class LatinMvpGenerationService:
    """Build the fixed Latin MVP run contract without modern frequency paths."""

    def __init__(
        self,
        *,
        source_pack_path: Path | None = None,
        source_pack_loader: LatinSourcePackLoader = load_latin_mvp_source_pack,
        portuguese_translation_pack_path: Path | None = None,
        portuguese_translation_pack_loader: LatinPortugueseTranslationPackLoader = load_latin_portuguese_translation_pack,
        portuguese_translation_qa_service: LatinPortugueseTranslationQaService | None = None,
        audio_manifest_path: Path | None = None,
        audio_manifest_loader: LatinAudioManifestLoader = load_latin_audio_manifest,
    ) -> None:
        self.source_pack_path = source_pack_path
        self.source_pack_loader = source_pack_loader
        self.portuguese_translation_pack_path = portuguese_translation_pack_path
        self.portuguese_translation_pack_loader = portuguese_translation_pack_loader
        self.portuguese_translation_qa_service = portuguese_translation_qa_service or LatinPortugueseTranslationQaService()
        self.audio_manifest_path = audio_manifest_path
        self.audio_manifest_loader = audio_manifest_loader

    def start(
        self,
        request: LatinGenerationRequest,
        *,
        include_portuguese_translation_summary: bool = False,
        include_audio_summary: bool = False,
    ) -> LatinMvpStartResult:
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
        grammar_evidence_count = sum(
            1 for entry in pack.entries if entry.morphology_evidence.grammar_review_status == "approved"
        )
        gramatica_count = sum(1 for entry in pack.entries if bool(entry.gramatica.strip()))
        grammar_gate_status = (
            "approved"
            if grammar_evidence_count == len(pack.entries) == gramatica_count == metadata.card_count
            else "blocked"
        )
        portuguese_translation_summary: dict[str, object] | None = None
        if include_portuguese_translation_summary:
            translation_pack = self.portuguese_translation_pack_loader(
                self.portuguese_translation_pack_path or DEFAULT_LATIN_PORTUGUESE_TRANSLATION_PACK_PATH
            )
            portuguese_translation_summary = self.portuguese_translation_qa_service.validate_pack(
                translation_pack,
                pack,
            ).qa_summary()
        audio_summary: dict[str, object] | None = None
        if include_audio_summary:
            audio_manifest = self.audio_manifest_loader(
                self.audio_manifest_path or DEFAULT_LATIN_AUDIO_MANIFEST_PATH
            )
            if audio_manifest.source_pack_version != pack.source_pack_version:
                raise ValueError(
                    "audio source_pack_version mismatch: "
                    f"audio={audio_manifest.source_pack_version} manifest={pack.source_pack_version}"
                )
            audio_summary = _public_audio_summary(audio_manifest)
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
            grammar_gate_status=grammar_gate_status,
            grammar_evidence_count=grammar_evidence_count,
            gramatica_count=gramatica_count,
            required_case_labels=list(APPROVED_LATIN_CASE_LABELS),
            portuguese_translation_summary=portuguese_translation_summary,
            audio_summary=audio_summary,
        )


__all__ = ["LatinMvpGenerationService", "LatinMvpStartResult"]
