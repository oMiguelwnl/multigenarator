"""Azure-first audio synthesis, normalization, and integrity validation."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from typing import Protocol

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.text_quality import ReviewStatus, TextQualityRecord, ValidationStatus
from multilang.services.audio_voice_registry import VoiceSelectionError, select_voice
from multilang.settings import Settings

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class AudioSynthesisResponse:
    storage_path: Path
    byte_size: int
    duration_ms: int | None


class AudioSynthesisAdapter(Protocol):
    def available_voice_ids(self) -> set[str] | None: ...

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse: ...


@dataclass(frozen=True, slots=True)
class AudioSynthesisBundle:
    word_asset: AudioAssetRecord
    sentence_asset: AudioAssetRecord


class AudioSynthesisService:
    """Build and validate separate word and sentence audio assets."""

    def __init__(self, *, adapter: AudioSynthesisAdapter, settings: Settings | None = None) -> None:
        self.adapter = adapter
        self.settings = settings or Settings()

    def synthesize_item(
        self,
        *,
        language: SupportedLanguage,
        display_word: str,
        text_record: TextQualityRecord,
    ) -> AudioSynthesisBundle:
        prepared = self.prepare_item_assets(
            language=language,
            display_word=display_word,
            text_record=text_record,
        )
        word_asset = self.synthesize_prepared_asset(prepared.word_asset)
        sentence_asset = self.synthesize_prepared_asset(prepared.sentence_asset)
        return AudioSynthesisBundle(word_asset=word_asset, sentence_asset=sentence_asset)

    def prepare_item_assets(
        self,
        *,
        language: SupportedLanguage,
        display_word: str,
        text_record: TextQualityRecord,
    ) -> AudioSynthesisBundle:
        if not self._is_accepted(text_record):
            return AudioSynthesisBundle(
                word_asset=self._failed_asset(
                    job_id=text_record.job_id,
                    item_key=text_record.item_key,
                    asset_kind=AudioAssetKind.WORD,
                    display_text=display_word,
                    reason_text=display_word,
                ),
                sentence_asset=self._failed_asset(
                    job_id=text_record.job_id,
                    item_key=text_record.item_key,
                    asset_kind=AudioAssetKind.SENTENCE,
                    display_text=text_record.example_sentence or "",
                    reason_text=text_record.example_sentence or "",
                ),
            )

        return AudioSynthesisBundle(
            word_asset=self._prepare_asset(
                language=language,
                job_id=text_record.job_id,
                item_key=text_record.item_key,
                asset_kind=AudioAssetKind.WORD,
                display_text=display_word,
            ),
            sentence_asset=self._prepare_asset(
                language=language,
                job_id=text_record.job_id,
                item_key=text_record.item_key,
                asset_kind=AudioAssetKind.SENTENCE,
                display_text=text_record.example_sentence or "",
            ),
        )

    def synthesize_prepared_asset(self, prepared_asset: AudioAssetRecord) -> AudioAssetRecord:
        if prepared_asset.provenance.status is AudioSynthesisStatus.FAILED:
            return prepared_asset

        output_path = Path(prepared_asset.provenance.storage_path)
        try:
            response = self.adapter.synthesize(
                ssml_text=prepared_asset.normalized_input.ssml_text or prepared_asset.normalized_input.tts_text,
                voice_id=prepared_asset.provenance.voice_id,
                locale=prepared_asset.provenance.locale,
                output_path=output_path,
                audio_format=self.settings.azure_speech_output_format,
            )
        except Exception:
            return self._build_record(
                job_id=prepared_asset.job_id,
                item_key=prepared_asset.item_key,
                asset_kind=prepared_asset.asset_kind,
                display_text=prepared_asset.display_text,
                normalized_input=prepared_asset.normalized_input,
                voice_id=prepared_asset.provenance.voice_id,
                locale=prepared_asset.provenance.locale,
                storage_path=str(output_path),
                byte_size=0,
                duration_ms=None,
                status=AudioSynthesisStatus.FAILED,
                fallback_used=prepared_asset.provenance.fallback_used,
            )

        if not self._is_valid_media(expected_path=output_path, response=response):
            return self._build_record(
                job_id=prepared_asset.job_id,
                item_key=prepared_asset.item_key,
                asset_kind=prepared_asset.asset_kind,
                display_text=prepared_asset.display_text,
                normalized_input=prepared_asset.normalized_input,
                voice_id=prepared_asset.provenance.voice_id,
                locale=prepared_asset.provenance.locale,
                storage_path=str(output_path),
                byte_size=0,
                duration_ms=None,
                status=AudioSynthesisStatus.FAILED,
                fallback_used=prepared_asset.provenance.fallback_used,
            )

        return self._build_record(
            job_id=prepared_asset.job_id,
            item_key=prepared_asset.item_key,
            asset_kind=prepared_asset.asset_kind,
            display_text=prepared_asset.display_text,
            normalized_input=prepared_asset.normalized_input,
            voice_id=prepared_asset.provenance.voice_id,
            locale=prepared_asset.provenance.locale,
            storage_path=str(response.storage_path),
            byte_size=response.byte_size,
            duration_ms=response.duration_ms,
            status=AudioSynthesisStatus.SYNTHESIZED,
            fallback_used=prepared_asset.provenance.fallback_used,
        )

    def _prepare_asset(
        self,
        *,
        language: SupportedLanguage,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
        display_text: str,
        ) -> AudioAssetRecord:
        normalized_input = self._normalize_input(display_text, asset_kind=asset_kind)
        try:
            voice = select_voice(
                language,
                available_voice_ids=self.adapter.available_voice_ids(),
            )
        except VoiceSelectionError:
            return self._failed_asset(
                job_id=job_id,
                item_key=item_key,
                asset_kind=asset_kind,
                display_text=display_text,
                reason_text=display_text,
            )

        output_path = self._build_storage_path(
            asset_kind=asset_kind,
            normalized_input=normalized_input,
            voice_id=voice.voice_id,
            locale=voice.locale,
            registry_version=voice.registry_version,
        )

        return self._build_record(
            job_id=job_id,
            item_key=item_key,
            asset_kind=asset_kind,
            display_text=display_text,
            normalized_input=normalized_input,
            voice_id=voice.voice_id,
            locale=voice.locale,
            storage_path=str(output_path),
            byte_size=0,
            duration_ms=None,
            status=AudioSynthesisStatus.PENDING,
            fallback_used=voice.fallback_used,
        )

    def _failed_asset(
        self,
        *,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
        display_text: str,
        reason_text: str,
    ) -> AudioAssetRecord:
        display = display_text or reason_text or asset_kind.value
        normalized_input = self._normalize_input(display, asset_kind=asset_kind)
        return self._build_record(
            job_id=job_id,
            item_key=item_key,
            asset_kind=asset_kind,
            display_text=display,
            normalized_input=normalized_input,
            voice_id="unresolved",
            locale="unresolved",
            storage_path=str(self._build_storage_path(
                asset_kind=asset_kind,
                normalized_input=normalized_input,
                voice_id="unresolved",
                locale="unresolved",
                registry_version="unresolved",
            )),
            byte_size=0,
            duration_ms=None,
            status=AudioSynthesisStatus.FAILED,
            fallback_used=False,
        )

    def _build_record(
        self,
        *,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
        display_text: str,
        normalized_input: NormalizedTtsInput,
        voice_id: str,
        locale: str,
        storage_path: str,
        byte_size: int,
        duration_ms: int | None,
        status: AudioSynthesisStatus,
        fallback_used: bool,
    ) -> AudioAssetRecord:
        return AudioAssetRecord(
            job_id=job_id,
            item_key=item_key,
            asset_kind=asset_kind,
            display_text=display_text,
            normalized_input=normalized_input,
            provenance=AudioProvenance(
                provider=AudioProvider.AZURE,
                voice_id=voice_id,
                locale=locale,
                format=AudioFormat(self.settings.azure_speech_output_format),
                text_hash=normalized_input.text_hash or "",
                ssml_hash=normalized_input.ssml_hash or "",
                storage_path=storage_path,
                byte_size=byte_size,
                duration_ms=duration_ms,
                status=status,
                fallback_used=fallback_used,
            ),
        )

    def _normalize_input(self, display_text: str, *, asset_kind: AudioAssetKind) -> NormalizedTtsInput:
        normalized = _WHITESPACE_RE.sub(" ", display_text.replace("’", "'").strip())
        escaped = escape(normalized, quote=True)
        if asset_kind is AudioAssetKind.WORD:
            ssml_text = (
                '<speak version="1.0"><prosody rate="-10%" pitch="+8%" volume="+20%">'
                f"{escaped}"
                "</prosody></speak>"
            )
        else:
            ssml_text = f'<speak version="1.0">{escaped}</speak>'
        return NormalizedTtsInput(
            display_text=display_text,
            tts_text=normalized,
            ssml_text=ssml_text,
        )

    def _build_storage_path(
        self,
        *,
        asset_kind: AudioAssetKind,
        normalized_input: NormalizedTtsInput,
        voice_id: str,
        locale: str,
        registry_version: str,
    ) -> Path:
        return (
            self.settings.audio_storage_dir
            / asset_kind.value
            / registry_version
            / locale
            / f"{voice_id}-{normalized_input.text_hash}-{normalized_input.ssml_hash}.mp3"
        )

    def _is_valid_media(self, *, expected_path: Path, response: AudioSynthesisResponse) -> bool:
        if response.storage_path != expected_path:
            return False
        if not response.storage_path.exists():
            return False
        if response.byte_size <= 0:
            return False
        return response.storage_path.stat().st_size > 0

    def _is_accepted(self, text_record: TextQualityRecord) -> bool:
        return (
            text_record.review_status is ReviewStatus.ACCEPTED
            and text_record.validation_status is ValidationStatus.PASSED
            and bool(text_record.example_sentence)
        )


__all__ = [
    "AudioSynthesisAdapter",
    "AudioSynthesisBundle",
    "AudioSynthesisResponse",
    "AudioSynthesisService",
]
