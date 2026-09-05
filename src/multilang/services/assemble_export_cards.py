"""Assemble accepted lexical, text, and audio data into frozen export rows."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from hashlib import sha256
import json
from pathlib import Path
import re

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.exporting import (
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
    ExportCardIdentity,
    ExportCardRow,
    export_field_names_for_language_and_source,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import LexicalCardCandidate
from multilang.domain.text_quality import ReviewStatus, TextQualityRecord, ValidationStatus
from multilang.services.audio_integrity import AudioIntegrityError, assert_word_audio_matches_word
from multilang.services.japanese_furigana import JapaneseFuriganaError, format_japanese_furigana
from multilang.services.japanese_romaji import JapaneseRomajiError, romanize_japanese
from multilang.services.mandarin_orthography import (
    MandarinOrthography,
    MandarinOrthographyError,
    MandarinOrthographyService,
)
from multilang.services.part_of_speech import CANONICAL_PART_OF_SPEECH_LABELS
from multilang.services.text_field_remediation import validate_definition_html


class AssembleExportCardsError(ValueError):
    """Raised when accepted rows cannot be assembled into safe export cards."""


@dataclass(frozen=True)
class AssembleExportCardsResult:
    cards: list[ExportCardRow]


class AssembleExportCardsService:
    """Deterministically freeze accepted cards into export rows."""

    def __init__(
        self,
        *,
        text_repository: object,
        lexical_repository: object,
        audio_repository: object,
        export_repository: object,
        mandarin_orthography_service: object | None = None,
    ) -> None:
        self.text_repository = text_repository
        self.lexical_repository = lexical_repository
        self.audio_repository = audio_repository
        self.export_repository = export_repository
        self.mandarin_orthography_service = mandarin_orthography_service or MandarinOrthographyService()

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
            korean_final = _uses_korean_frequency_final(deck_language=deck_language, source_type=source_type)
            row_sort_index = self._row_sort_index(
                fallback_sort_index=sort_index,
                lexical_candidate=lexical_candidate,
                korean_final=korean_final,
            )
            field_names = export_field_names_for_language_and_source(
                language=deck_language,
                source_type=source_type,
            )
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
            japanese_readings = self._japanese_readings(
                item_key=text_record.item_key,
                display_word=lexical_candidate.display_form,
                sentence=text_record.example_sentence or "",
                enabled=_uses_japanese_frequency_fields(deck_language=deck_language, source_type=source_type),
            )
            mandarin_orthography = self._mandarin_orthography(
                item_key=text_record.item_key,
                display_word=lexical_candidate.display_form,
                sentence=text_record.example_sentence or "",
                enabled=field_names == MANDARIN_EXPORT_CARD_FIELD_NAMES,
            )
            korean_metadata = self._korean_final_metadata(
                job_id=job_id,
                text_record=text_record,
                lexical_candidate=lexical_candidate,
                word_audio=word_audio,
                sentence_audio=sentence_audio,
                enabled=korean_final,
            )
            row = ExportCardRow(
                identity=ExportCardIdentity(
                    language=deck_language,
                    source_type=source_type,
                    job_id=job_id,
                    item_key=text_record.item_key,
                    lemma_key=lexical_candidate.lemma_key,
                    sort_index=row_sort_index,
                ),
                frequency_level=korean_metadata.get("frequency_level"),
                frequency_bundle_sha256=korean_metadata.get("frequency_bundle_sha256"),
                export_gate_receipt_sha256=korean_metadata.get("export_gate_receipt_sha256"),
                text_review_receipt_sha256=korean_metadata.get("text_review_receipt_sha256"),
                word_audio_artifact_sha256=korean_metadata.get("word_audio_artifact_sha256"),
                sentence_audio_artifact_sha256=korean_metadata.get("sentence_audio_artifact_sha256"),
                word=escape(lexical_candidate.lemma),
                front_of_card=escape(lexical_candidate.display_form),
                ipa=self._render_ipa(lexical_candidate.ipa, lexical_candidate.spoken_form) if "IPA" in field_names else None,
                definitions=self._render_definitions(lexical_candidate, deck_language=deck_language),
                example_sentence=escape(text_record.example_sentence or ""),
                translation=(
                    escape(text_record.translation_text or "")
                    if "Translation" in field_names or "Sentence Translation" in field_names
                    else ""
                ),
                word_audio=self._to_sound_tag(word_audio) if word_audio is not None else "",
                sentence_audio=self._to_sound_tag(sentence_audio),
                word_reading=escape(japanese_readings[0]) if japanese_readings is not None else None,
                word_romaji=escape(japanese_readings[1]) if japanese_readings is not None else None,
                sentence_furigana=escape(japanese_readings[2]) if japanese_readings is not None else None,
                sentence_romaji=escape(japanese_readings[3]) if japanese_readings is not None else None,
                gramatica=self._render_gramatica(text_record),
                mandarin_word_pinyin=(escape(mandarin_orthography.word_pinyin) if mandarin_orthography else None),
                mandarin_word_traditional=(escape(mandarin_orthography.word_traditional) if mandarin_orthography else None),
                mandarin_sentence_pinyin=(escape(mandarin_orthography.sentence_pinyin) if mandarin_orthography else None),
                mandarin_sentence_traditional=(
                    escape(mandarin_orthography.sentence_traditional) if mandarin_orthography else None
                ),
            )
            cards.append(row)

        if _all_korean_frequency_rows(cards):
            self._require_one_korean_frequency_bundle(cards)
            cards = sorted(cards, key=lambda row: (row.sort_index or 0, row.identity.item_key))
        return AssembleExportCardsResult(cards=self._persist_cards(cards))

    def _row_sort_index(
        self,
        *,
        fallback_sort_index: int,
        lexical_candidate: object,
        korean_final: bool,
    ) -> int:
        if not korean_final:
            return fallback_sort_index
        rank = getattr(lexical_candidate, "frequency_rank", None)
        if not isinstance(rank, int) or rank < 1:
            raise AssembleExportCardsError("Korean final export requires an explicit frequency rank")
        return rank

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

    def _render_definitions(self, candidate: LexicalCardCandidate, *, deck_language: SupportedLanguage) -> str:
        raw = candidate.definitions_html or ""
        cleaned = raw.replace("</ul>", "").replace("<ul>", "\n").replace("</li>", "\n").replace("<li>", "")
        raw_parts = [part.strip() for part in re.split(r"(?:<br\s*/?>|\n)+", cleaned) if part.strip()]
        parts = []
        for part in raw_parts:
            try:
                validate_definition_html(lemma_key=candidate.lemma_key, definitions_html=part)
            except ValueError as exc:
                raise AssembleExportCardsError(str(exc)) from exc
            parts.append(escape(_require_definition_template(candidate, part, deck_language=deck_language)))
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

    def _japanese_readings(
        self,
        *,
        item_key: str,
        display_word: str,
        sentence: str,
        enabled: bool,
    ) -> tuple[str, str, str, str] | None:
        if not enabled:
            return None
        try:
            return (
                format_japanese_furigana(display_word),
                romanize_japanese(display_word),
                format_japanese_furigana(sentence),
                romanize_japanese(sentence),
            )
        except (JapaneseFuriganaError, JapaneseRomajiError) as exc:
            raise AssembleExportCardsError(
                f"unable to generate Japanese readings for item {item_key}: {exc}"
            ) from exc

    def _mandarin_orthography(
        self,
        *,
        item_key: str,
        display_word: str,
        sentence: str,
        enabled: bool,
    ) -> MandarinOrthography | None:
        if not enabled:
            return None
        try:
            return self.mandarin_orthography_service.derive(word=display_word, sentence=sentence)
        except MandarinOrthographyError as exc:
            raise AssembleExportCardsError(f"unable to derive Mandarin orthography for item {item_key}: {exc}") from exc

    def _to_sound_tag(self, asset: AudioAssetRecord) -> str:
        return f"[sound:{Path(asset.provenance.storage_path).name}]"

    def _korean_final_metadata(
        self,
        *,
        job_id: str,
        text_record: TextQualityRecord,
        lexical_candidate: object,
        word_audio: AudioAssetRecord | None,
        sentence_audio: AudioAssetRecord,
        enabled: bool,
    ) -> dict[str, object]:
        if not enabled:
            return {}
        evidence = getattr(lexical_candidate, "korean_frequency_evidence", None)
        if evidence is None:
            raise AssembleExportCardsError("Korean final export requires source-backed frequency evidence")
        rank = getattr(lexical_candidate, "frequency_rank", None)
        level = getattr(lexical_candidate, "frequency_level", None)
        if rank != evidence.final_rank:
            raise AssembleExportCardsError("Korean final export frequency rank drift")
        if level != evidence.level:
            raise AssembleExportCardsError("Korean final export frequency level drift")
        if text_record.validation_status is not ValidationStatus.PASSED or text_record.review_status is not ReviewStatus.ACCEPTED:
            raise AssembleExportCardsError("Korean final export requires current approved text")
        if text_record.text_review_receipt_sha256 is None:
            raise AssembleExportCardsError("Korean final export requires text review receipt")
        adaptive_evidence = text_record.adaptive_i_plus_one_evidence
        if adaptive_evidence is None:
            raise AssembleExportCardsError("Korean final export requires adaptive i+1 evidence")
        if adaptive_evidence.frequency_bundle_content_sha256 != evidence.bundle_sha256:
            raise AssembleExportCardsError("Korean final export frequency bundle drift")
        if word_audio is None:
            raise AssembleExportCardsError("Korean final export requires reviewed non-fallback word audio")
        self._require_korean_final_audio(
            asset=word_audio,
            asset_kind=AudioAssetKind.WORD,
            expected_text=lexical_candidate.lemma,
        )
        self._require_korean_final_audio(
            asset=sentence_audio,
            asset_kind=AudioAssetKind.SENTENCE,
            expected_text=text_record.example_sentence or "",
        )
        word_artifact = word_audio.provenance.artifact_sha256
        sentence_artifact = sentence_audio.provenance.artifact_sha256
        assert word_artifact is not None
        assert sentence_artifact is not None
        metadata = {
            "frequency_level": evidence.level,
            "frequency_bundle_sha256": evidence.bundle_sha256,
            "text_review_receipt_sha256": text_record.text_review_receipt_sha256,
            "word_audio_artifact_sha256": word_artifact,
            "sentence_audio_artifact_sha256": sentence_artifact,
        }
        metadata["export_gate_receipt_sha256"] = _korean_export_gate_receipt_sha256(
            job_id=job_id,
            item_key=text_record.item_key,
            lemma_key=lexical_candidate.lemma_key,
            rank=evidence.final_rank,
            metadata=metadata,
        )
        return metadata

    def _require_korean_final_audio(
        self,
        *,
        asset: AudioAssetRecord,
        asset_kind: AudioAssetKind,
        expected_text: str,
    ) -> None:
        if not asset.ready_for_korean_final_export:
            raise AssembleExportCardsError(
                f"Korean final export requires reviewed non-fallback {asset_kind.value} audio"
            )
        if asset.display_text != expected_text or asset.normalized_input.display_text != expected_text:
            raise AssembleExportCardsError(f"Korean final export {asset_kind.value} audio text drift")
        if asset.provenance.text_hash != asset.normalized_input.text_hash:
            raise AssembleExportCardsError(f"Korean final export {asset_kind.value} audio hash drift")
        if asset.provenance.synthesis_request_sha256 != asset.normalized_input.synthesis_request_sha256:
            raise AssembleExportCardsError(f"Korean final export {asset_kind.value} audio request drift")

    def _require_one_korean_frequency_bundle(self, cards: list[ExportCardRow]) -> None:
        bundles = {row.frequency_bundle_sha256 for row in cards}
        if len(bundles) != 1 or None in bundles:
            raise AssembleExportCardsError("Korean final export requires one immutable frequency bundle")


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


def _uses_japanese_frequency_fields(*, deck_language: SupportedLanguage, source_type: str) -> bool:
    return deck_language is SupportedLanguage.JA and source_type == "frequency"


def _uses_korean_frequency_final(*, deck_language: SupportedLanguage, source_type: str) -> bool:
    return deck_language is SupportedLanguage.KO and source_type == "frequency"


def _all_korean_frequency_rows(cards: list[ExportCardRow]) -> bool:
    return bool(cards) and all(
        card.identity.language is SupportedLanguage.KO and card.identity.source_type == "frequency"
        for card in cards
    )


def _korean_export_gate_receipt_sha256(
    *,
    job_id: str,
    item_key: str,
    lemma_key: str,
    rank: int,
    metadata: dict[str, object],
) -> str:
    payload = {
        "job_id": job_id,
        "item_key": item_key,
        "lemma_key": lemma_key,
        "rank": rank,
        **metadata,
    }
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


_DEFINITION_SENSE_SEPARATOR = "; "
_LEGACY_DEFINITION_TEMPLATE_RE = re.compile(r"^[^\W\d_](?:[^\W\d_]|[ -]){1,40}:\s+\S")
_ENGLISH_DEFINITION_LABELS = (*CANONICAL_PART_OF_SPEECH_LABELS, "term")
_ENGLISH_DEFINITION_TEMPLATE_RE = re.compile(
    rf"^(?:{'|'.join(re.escape(label) for label in _ENGLISH_DEFINITION_LABELS)}):\s+\S",
    re.IGNORECASE,
)


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


def _require_definition_template(candidate: LexicalCardCandidate, definition: str, *, deck_language: SupportedLanguage) -> str:
    pattern = _ENGLISH_DEFINITION_TEMPLATE_RE if deck_language is SupportedLanguage.JA else _LEGACY_DEFINITION_TEMPLATE_RE
    if pattern.match(definition):
        return definition
    raise AssembleExportCardsError(
        f"definition for item {candidate.lemma_key} must use '[part of speech]: [meaning]'"
    )


__all__ = [
    "AssembleExportCardsError",
    "AssembleExportCardsResult",
    "AssembleExportCardsService",
]
