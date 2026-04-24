"""Coordinate accepted-text audio generation and deterministic reuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from multilang.domain.audio import AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.jobs import JobStage, SupportedLanguage


@dataclass(slots=True)
class GenerateAudioItemsResult:
    processed_items: int = 0
    reused_items: int = 0
    fallback_items: int = 0
    failed_items: int = 0


class GenerateAudioItemsService:
    """Turn accepted text rows into reusable word and sentence audio assets."""

    def __init__(
        self,
        *,
        job_repository: Any,
        lexical_repository: Any,
        text_repository: Any,
        audio_repository: Any,
        audio_synthesis_service: Any,
    ) -> None:
        self.job_repository = job_repository
        self.lexical_repository = lexical_repository
        self.text_repository = text_repository
        self.audio_repository = audio_repository
        self.audio_synthesis_service = audio_synthesis_service

    def execute(
        self,
        *,
        job_id: str,
        deck_language: SupportedLanguage,
        item_keys: set[str] | None = None,
    ) -> GenerateAudioItemsResult:
        result = GenerateAudioItemsResult()

        for text_record in self.text_repository.list_accepted_records(job_id):
            if item_keys is not None and text_record.item_key not in item_keys:
                continue
            lexical_candidate = self.lexical_repository.get_candidate_for_item(job_id, text_record.item_key)
            if lexical_candidate is None:
                continue

            prepared_bundle = self.audio_synthesis_service.prepare_item_assets(
                language=deck_language,
                display_word=getattr(lexical_candidate, "display_form"),
                text_record=text_record,
            )
            assets = [prepared_bundle.word_asset, prepared_bundle.sentence_asset]

            for prepared_asset in assets:
                final_asset, reused = self._materialize_asset(prepared_asset)
                self.audio_repository.upsert_audio_asset(final_asset)
                result.processed_items += 1
                if reused:
                    result.reused_items += 1
                if final_asset.provenance.fallback_used:
                    result.fallback_items += 1
                if final_asset.provenance.status is AudioSynthesisStatus.FAILED:
                    result.failed_items += 1

            self.job_repository.record_item_success(
                job_id,
                item_key=text_record.item_key,
                completed_stage=JobStage.SYNTHESIZE_AUDIO,
            )

        return result

    def _materialize_asset(self, prepared_asset: AudioAssetRecord) -> tuple[AudioAssetRecord, bool]:
        reusable = self.audio_repository.get_reusable_asset(
            asset_kind=prepared_asset.asset_kind,
            text_hash=prepared_asset.normalized_input.text_hash or "",
            ssml_hash=prepared_asset.normalized_input.ssml_hash or "",
            voice_id=prepared_asset.provenance.voice_id,
            format=prepared_asset.provenance.format,
        )
        if reusable is not None:
            return reusable, True

        if prepared_asset.provenance.status is AudioSynthesisStatus.FAILED:
            return prepared_asset, False

        return self.audio_synthesis_service.synthesize_prepared_asset(prepared_asset), False


__all__ = ["GenerateAudioItemsResult", "GenerateAudioItemsService"]
