"""Assemble accepted lexical, text, and audio data into frozen export rows."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow, export_field_names_for_source_type
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import LexicalCardCandidate
from multilang.domain.source_profiles import get_source_profile
from multilang.domain.text_quality import TextQualityRecord
from multilang.services.audio_integrity import AudioIntegrityError, assert_word_audio_matches_word
from multilang.services.text_field_remediation import validate_definition_html


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
        audio_index = self._preload_audio_assets(job_id)
        for sort_index, text_record in enumerate(accepted_records, start=1):
            lexical_candidate = self.lexical_repository.get_candidate_for_item(job_id, text_record.item_key)
            if lexical_candidate is None:
                raise AssembleExportCardsError(
                    f"missing lexical candidate for item {text_record.item_key} in job {job_id}"
                )

            source_type = _candidate_source_type(lexical_candidate)
            source_profile = get_source_profile(source_type)
            field_names = export_field_names_for_source_type(source_type)
            word_audio = (
                self._require_audio(
                    job_id=job_id,
                    item_key=text_record.item_key,
                    asset_kind=AudioAssetKind.WORD,
                    audio_index=audio_index,
                )
                if "word_audio" in field_names
                else None
            )
            if word_audio is not None:
                try:
                    assert_word_audio_matches_word(
                        word_audio,
                        lexical_candidate.lemma,
                        item_key=text_record.item_key,
                    )
                except AudioIntegrityError as exc:
                    raise AssembleExportCardsError(str(exc)) from exc
            sentence_audio = self._require_audio(
                job_id=job_id,
                item_key=text_record.item_key,
                asset_kind=AudioAssetKind.SENTENCE,
                audio_index=audio_index,
            )
            row = ExportCardRow(
                identity=ExportCardIdentity(
                    language=deck_language,
                    source_type=source_type,
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
                translation=escape(text_record.translation_text or "") if source_profile.exports_translation_field else "",
                word_audio=self._to_sound_tag(word_audio) if word_audio is not None else "",
                sentence_audio=self._to_sound_tag(sentence_audio),
                gramatica=self._render_gramatica(text_record),
            )
            cards.append(row)

        return AssembleExportCardsResult(cards=self._persist_cards(cards))

    def _preload_audio_assets(self, job_id: str) -> dict[tuple[str, str], AudioAssetRecord] | None:
        if not hasattr(self.audio_repository, "list_assets_for_job"):
            return None
        return {
            (asset.item_key, asset.asset_kind.value): asset
            for asset in self.audio_repository.list_assets_for_job(job_id)
        }

    def _require_audio(
        self,
        *,
        job_id: str,
        item_key: str,
        asset_kind: AudioAssetKind,
        audio_index: dict[tuple[str, str], AudioAssetRecord] | None = None,
    ) -> AudioAssetRecord:
        asset = (
            audio_index.get((item_key, asset_kind.value))
            if audio_index is not None
            else self.audio_repository.get_asset(job_id, item_key, asset_kind)
        )
        if asset is None:
            raise AssembleExportCardsError(
                f"missing required {asset_kind.value} audio for item {item_key} in job {job_id}"
            )
        if asset.provenance.status is not AudioSynthesisStatus.SYNTHESIZED or asset.provenance.byte_size <= 0:
            raise AssembleExportCardsError(
                f"missing required {asset_kind.value} audio for item {item_key} in job {job_id}"
            )
        return asset

    def _persist_cards(self, cards: list[ExportCardRow]) -> list[ExportCardRow]:
        bulk_upsert = getattr(self.export_repository, "upsert_card_snapshots", None)
        if callable(bulk_upsert):
            return list(bulk_upsert(cards))
        return [self.export_repository.upsert_card_snapshot(row) for row in cards]

    def _render_definitions(self, candidate: LexicalCardCandidate) -> str:
        raw = candidate.definitions_html or ""
        cleaned = raw.replace("</ul>", "").replace("<ul>", "\n").replace("</li>", "\n").replace("<li>", "")
        raw_parts = [part.strip() for part in re.split(r"(?:<br\s*/?>|\n)+", cleaned) if part.strip()]
        parts = []
        for part in raw_parts:
            try:
                validate_definition_html(lemma_key=candidate.lemma_key, definitions_html=part)
            except ValueError as exc:
                raise AssembleExportCardsError(str(exc)) from exc
            parts.append(escape(_require_definition_template(candidate, part)))
        if not parts:
            raise AssembleExportCardsError(f"missing definitions for item {candidate.lemma_key}")
        # Multiple senses stay on a single line (no <br> line breaks), joined with
        # a semicolon in the standard dictionary style. Consecutive senses that
        # share the same part-of-speech label drop the repeated label, e.g.
        # "verb: to run; to operate" instead of "verb: to run; verb: to operate".
        return _join_definition_senses(parts)

    def _render_gramatica(self, text_record: TextQualityRecord) -> str | None:
        provenance = getattr(text_record, "sentence_provenance", None)
        metadata = getattr(provenance, "metadata", None) or {}
        gramatica = metadata.get("gramatica")
        if not gramatica:
            return None
        cleaned = " ".join(str(gramatica).split())
        return escape(cleaned) if cleaned else None

    def _render_ipa(self, ipa: str | None, spoken_form: str | None) -> str:
        if not ipa:
            raise AssembleExportCardsError("missing IPA for export candidate")
        cleaned = " ".join(ipa.split())
        if not cleaned:
            raise AssembleExportCardsError("missing IPA for export candidate")
        return escape(_strip_trailing_ipa_word_hint(cleaned))

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


_TRAILING_IPA_WORD_HINT_RE = re.compile(r"^(?P<ipa>.+(?:/|\]|⟩))\s+\([^()]+\)$")


def _strip_trailing_ipa_word_hint(ipa: str) -> str:
    match = _TRAILING_IPA_WORD_HINT_RE.match(ipa)
    if match is None:
        return ipa
    return match.group("ipa").strip()


def _candidate_source_type(candidate: object) -> str:
    source_type = getattr(candidate, "source_type", None)
    if source_type:
        return str(source_type)
    if getattr(candidate, "frequency_rank", None) is not None:
        return "frequency"
    return "word-list"


_DEFINITION_SENSE_SEPARATOR = "; "
_DEFINITION_TEMPLATE_RE = re.compile(r"^[^\W\d_](?:[^\W\d_]|[ -]){1,40}:\s+\S")


def _join_definition_senses(parts: list[str]) -> str:
    """Join senses on one line, dropping a repeated part-of-speech label.

    Each part is validated as ``[label]: [meaning]`` upstream. When a sense
    repeats the label of the previously shown sense, only its meaning is kept
    so the label appears once: ``verb: to run; to operate``. A sense with a
    different label keeps it: ``verb: to run; noun: a jog``.
    """

    rendered: list[str] = []
    last_label: str | None = None
    for part in parts:
        label, separator, meaning = part.partition(":")
        label = label.strip()
        meaning = meaning.strip()
        if separator and meaning:
            if last_label is not None and label.casefold() == last_label.casefold():
                rendered.append(meaning)
            else:
                rendered.append(f"{label}: {meaning}")
                last_label = label
        else:
            rendered.append(part)
            last_label = None
    return _DEFINITION_SENSE_SEPARATOR.join(rendered)


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
