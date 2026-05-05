"""Assemble accepted lexical, text, and audio data into frozen export rows."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re

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
                    source_type=_candidate_source_type(lexical_candidate),
                    job_id=job_id,
                    item_key=text_record.item_key,
                    lemma_key=lexical_candidate.lemma_key,
                    sort_index=sort_index,
                ),
                word=escape(lexical_candidate.lemma),
                front_of_card=escape(lexical_candidate.display_form),
                ipa=self._render_ipa(lexical_candidate.ipa, lexical_candidate.spoken_form),
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
        raw_parts = [part.strip() for part in re.split(r"(?:<br\s*/?>|\n)+", cleaned) if part.strip()]
        parts = [escape(_require_definition_template(candidate, part)) for part in raw_parts]
        if not parts:
            raise AssembleExportCardsError(f"missing definitions for item {candidate.lemma_key}")
        return "<br>".join(parts)

    def _render_ipa(self, ipa: str | None, spoken_form: str | None) -> str:
        if not ipa:
            raise AssembleExportCardsError("missing IPA for export candidate")
        cleaned = " ".join(ipa.split())
        if not cleaned:
            raise AssembleExportCardsError("missing IPA for export candidate")
        if not spoken_form:
            raise AssembleExportCardsError("missing spoken form for export candidate")
        cleaned_spoken_form = " ".join(spoken_form.split())
        if not cleaned_spoken_form:
            raise AssembleExportCardsError("missing spoken form for export candidate")
        escaped_ipa = escape(cleaned)
        return f"{escaped_ipa} ({escape(cleaned_spoken_form)})"

    def _to_sound_tag(self, asset: AudioAssetRecord) -> str:
        return f"[sound:{Path(asset.provenance.storage_path).name}]"


_IPA_HINT_REPLACEMENTS = (
    ("t͡ɕ", "ch"),
    ("d͡ʑ", "j"),
    ("t͡ʃ", "ch"),
    ("d͡ʒ", "j"),
    ("t͡s", "ts"),
    ("ɐ", "uh"),
    ("ə", "uh"),
    ("ɚ", "er"),
    ("ɝ", "er"),
    ("æ", "a"),
    ("ɑ", "a"),
    ("ɒ", "o"),
    ("ɔ", "o"),
    ("ɛ", "e"),
    ("ɜ", "er"),
    ("ɪ", "i"),
    ("ɨ", "y"),
    ("ʊ", "u"),
    ("ʌ", "uh"),
    ("ɡ", "g"),
    ("ɣ", "gh"),
    ("χ", "kh"),
    ("x", "kh"),
    ("ʃ", "sh"),
    ("ʒ", "zh"),
    ("ʂ", "sh"),
    ("ʐ", "zh"),
    ("ɕ", "sh"),
    ("ʑ", "zh"),
    ("θ", "th"),
    ("ð", "th"),
    ("ŋ", "ng"),
    ("ɲ", "ny"),
    ("ʎ", "ly"),
    ("β", "v"),
    ("ɾ", "r"),
    ("ʁ", "r"),
    ("ɫ", "l"),
    ("ʲ", "y"),
    ("ʷ", "w"),
)


def _readable_pronunciation_hint(ipa: str) -> str | None:
    if "(" in ipa or ")" in ipa:
        return None

    first_variant = re.split(r"[,;]", ipa, maxsplit=1)[0]
    hint = first_variant.strip().strip("/[]")
    hint = hint.replace("ˈ", "-").replace("ˌ", "-").replace(".", "-")
    hint = hint.replace("ː", "").replace("ˑ", "")
    for source, replacement in _IPA_HINT_REPLACEMENTS:
        hint = hint.replace(source, replacement)
    hint = re.sub(r"[^A-Za-z-]+", "", hint)
    hint = re.sub(r"-+", "-", hint).strip("-").casefold()
    hint = re.sub(r"^([a-z]{2,})([bcdfghjklmnpqrstvwxyz]uh)$", r"\1-\2", hint)
    if not hint:
        return None
    return hint


def _candidate_source_type(candidate: object) -> str:
    source_type = getattr(candidate, "source_type", None)
    if source_type:
        return str(source_type)
    if getattr(candidate, "frequency_rank", None) is not None:
        return "frequency"
    return "word-list"


_DEFINITION_TEMPLATE_RE = re.compile(r"^[A-Za-z][A-Za-z -]{1,40}:\s+\S")


def _require_definition_template(candidate: LexicalCardCandidate, definition: str) -> str:
    if _DEFINITION_TEMPLATE_RE.match(definition):
        return definition
    raise AssembleExportCardsError(
        f"definition for item {candidate.lemma_key} must use '[part of speech]: [meaning]'"
    )


__all__ = [
    "AssembleExportCardsError",
    "AssembleExportCardsResult",
    "AssembleExportCardsService",
]
