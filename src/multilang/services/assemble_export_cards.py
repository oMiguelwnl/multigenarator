"""Assemble accepted lexical, text, and audio data into frozen export rows."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from re import split

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import LexicalCardCandidate
from multilang.domain.text_quality import TextQualityRecord


class AssembleExportCardsError(ValueError):
    """Raised when accepted rows cannot be assembled into safe export cards."""


@dataclass(frozen=True)
class AssembleExportCardsResult:
    cards: list[ExportCardRow]


class AssembleExportCardsService:
    """Deterministically freeze accepted cards into export rows."""

    def __init__(self, *, text_repository: object, lexical_repository: object, audio_repository: object, export_repository: object) -> None:
        self.text_repository = text_repository
        self.lexical_repository = lexical_repository
        self.audio_repository = audio_repository
        self.export_repository = export_repository

    def execute(self, *, job_id: str, deck_language: SupportedLanguage) -> AssembleExportCardsResult:
        accepted_records = list(self.text_repository.list_accepted_records(job_id))
        if not accepted_records:
            raise AssembleExportCardsError(f"no accepted text records for job {job_id}")

        cards: list[ExportCardRow] = []
        for sort_index, text_record in enumerate(accepted_records, start=1):
            lexical_candidate = self.lexical_repository.get_candidate_for_item(job_id, text_record.item_key)
            if lexical_candidate is None:
                raise AssembleExportCardsError(
                    f"missing lexical candidate for item {text_record.item_key} in job {job_id}"
                )

            word_audio = self._require_audio(job_id=job_id, item_key=text_record.item_key, asset_kind=AudioAssetKind.WORD)
            sentence_audio = self._require_audio(job_id=job_id, item_key=text_record.item_key, asset_kind=AudioAssetKind.SENTENCE)

            row = ExportCardRow(
                identity=ExportCardIdentity(
                    language=deck_language,
                    source_type="word-list",
                    job_id=job_id,
                    item_key=text_record.item_key,
                    lemma_key=lexical_candidate.lemma_key,
                    sort_index=sort_index,
                ),
                word=escape(lexical_candidate.lemma),
                front_of_card=escape(lexical_candidate.display_form),
                ipa=escape(lexical_candidate.ipa) if lexical_candidate.ipa else None,
                definitions=self._render_definitions(lexical_candidate),
                example_sentence=escape(text_record.example_sentence or ""),
                translation=escape(text_record.translation_text or ""),
                word_audio=self._to_sound_tag(word_audio),
                sentence_audio=self._to_sound_tag(sentence_audio),
            )
            cards.append(self.export_repository.upsert_card_snapshot(row))

        return AssembleExportCardsResult(cards=cards)

    def _require_audio(self, *, job_id: str, item_key: str, asset_kind: AudioAssetKind) -> AudioAssetRecord:
        asset = self.audio_repository.get_asset(job_id, item_key, asset_kind)
        if asset is None:
            raise AssembleExportCardsError(
                f"missing required {asset_kind.value} audio for item {item_key} in job {job_id}"
            )
        if asset.provenance.status is not AudioSynthesisStatus.SYNTHESIZED or asset.provenance.byte_size <= 0:
            raise AssembleExportCardsError(
                f"missing required {asset_kind.value} audio for item {item_key} in job {job_id}"
            )
        return asset

    def _render_definitions(self, candidate: LexicalCardCandidate) -> str:
        raw = candidate.definitions_html or ""
        cleaned = raw.replace("</ul>", "").replace("<ul>", "\n").replace("</li>", "\n").replace("<li>", "")
        parts = [escape(part.strip()) for part in split(r"\n+", cleaned) if part.strip()]
        if not parts:
            raise AssembleExportCardsError(f"missing definitions for item {candidate.lemma_key}")
        return "<br>".join(parts)

    def _to_sound_tag(self, asset: AudioAssetRecord) -> str:
        return f"[sound:{Path(asset.provenance.storage_path).name}]"


__all__ = [
    "AssembleExportCardsError",
    "AssembleExportCardsResult",
    "AssembleExportCardsService",
]
