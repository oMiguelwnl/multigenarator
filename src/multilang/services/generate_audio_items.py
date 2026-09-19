"""Coordinate accepted-text audio generation and deterministic reuse."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.exporting import export_field_names_for_language_and_source
from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.services.audio.integrity import (
    AudioIntegrityError,
    assert_sentence_audio_matches_sentence,
    assert_word_audio_matches_word,
)
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.korean_audio import korean_audio_asset_reusable


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
        missing_only: bool = False,
        fallback_only: bool = False,
        max_items: int | None = None,
    ) -> GenerateAudioItemsResult:
        if max_items is not None and max_items < 1:
            raise ValueError("max_items must be greater than or equal to 1")
        result = GenerateAudioItemsResult()
        processed_records = 0

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
            field_names = export_field_names_for_language_and_source(
                language=deck_language,
                source_type=_candidate_source_type(lexical_candidate),
            )
            assets = []
            if "word_audio" in field_names:
                assets.append(prepared_bundle.word_asset)
            if "sentence_audio" in field_names:
                assets.append(prepared_bundle.sentence_asset)
            if missing_only or fallback_only:
                assets = [
                    asset
                    for asset in assets
                    if self._needs_audio_retry(
                        asset,
                        fallback_only=fallback_only,
                    )
                ]
                if not assets:
                    continue
            if max_items is not None and processed_records >= max_items:
                break
            processed_records += 1

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

    def _needs_audio_retry(self, prepared_asset: AudioAssetRecord, *, fallback_only: bool = False) -> bool:
        existing = self.audio_repository.get_asset(prepared_asset.job_id, prepared_asset.item_key, prepared_asset.asset_kind)
        if existing is None:
            return not fallback_only
        if fallback_only:
            return bool(existing.provenance.fallback_used)
        return not _can_reuse_asset(prepared_asset, existing)

    def _materialize_asset(self, prepared_asset: AudioAssetRecord) -> tuple[AudioAssetRecord, bool]:
        reusable = self.audio_repository.get_reusable_asset(
            asset_kind=prepared_asset.asset_kind,
            text_hash=prepared_asset.normalized_input.text_hash or "",
            ssml_hash=prepared_asset.normalized_input.ssml_hash or "",
            voice_id=prepared_asset.provenance.voice_id,
            format=prepared_asset.provenance.format,
        )
        if reusable is not None and _can_reuse_asset(prepared_asset, reusable):
            return reusable.model_copy(
                update={
                    "job_id": prepared_asset.job_id,
                    "item_key": prepared_asset.item_key,
                    "display_text": prepared_asset.display_text,
                }
            ), True

        if prepared_asset.provenance.status is AudioSynthesisStatus.FAILED:
            return prepared_asset, False

        return self.audio_synthesis_service.synthesize_prepared_asset(prepared_asset), False


def _candidate_source_type(candidate: object) -> str:
    source_type = getattr(candidate, "source_type", None)
    if source_type:
        return str(source_type)
    if getattr(candidate, "frequency_rank", None) is not None or getattr(candidate, "frequency_level", None) is not None:
        return "frequency"
    return "word-list"


def _can_reuse_asset(prepared_asset: AudioAssetRecord, reusable: AudioAssetRecord) -> bool:
    requested = prepared_asset.provenance
    stored = reusable.provenance
    if prepared_asset.asset_kind is not reusable.asset_kind:
        return False
    if stored.status is not AudioSynthesisStatus.SYNTHESIZED:
        return False
    if any(getattr(requested, field) != getattr(stored, field) for field in (
        "provider", "voice_id", "locale", "format", "fallback_used", "text_hash", "ssml_hash",
    )):
        return False
    if prepared_asset.normalized_input.tts_text != reusable.normalized_input.tts_text:
        return False
    if prepared_asset.normalized_input.ssml_text != reusable.normalized_input.ssml_text:
        return False
    for asset in (prepared_asset, reusable):
        normalized = asset.normalized_input
        for value, input_hash, provenance_hash in (
            (normalized.tts_text, normalized.text_hash, asset.provenance.text_hash),
            (normalized.ssml_text or normalized.tts_text, normalized.ssml_hash, asset.provenance.ssml_hash),
        ):
            if input_hash != sha256(value.encode("utf-8")).hexdigest() or provenance_hash != input_hash:
                return False
    if requested.locale == "ko-KR" or stored.locale == "ko-KR":
        if not korean_audio_asset_reusable(prepared_asset, reusable):
            return False
    else:
        try:
            if prepared_asset.asset_kind is AudioAssetKind.WORD:
                assert_word_audio_matches_word(reusable, prepared_asset.display_text)
            else:
                assert_sentence_audio_matches_sentence(reusable, prepared_asset.display_text)
        except AudioIntegrityError:
            return False
    media = inspect_local_mp3(
        stored.storage_path, expected_byte_size=stored.byte_size,
        artifact_hash_prefix=b"artifact:"
        if stored.locale == "ko-KR" and stored.audio_review_status is not None else b"",
    )
    return media is not None and (
        stored.artifact_sha256 is None or media.artifact_sha256 == stored.artifact_sha256
    )


__all__ = ["GenerateAudioItemsResult", "GenerateAudioItemsService"]
