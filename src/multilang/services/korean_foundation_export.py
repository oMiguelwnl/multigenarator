"""Deterministic, fail-closed exports for Korean foundation decks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from importlib.resources import files
from io import StringIO
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
from typing import Final
import zipfile

import genanki

from multilang.domain.exporting import ExportArtifactFormat
from multilang.services.korean_curriculum import (
    KoreanFoundationFamily,
    KoreanHangulSourceEntry,
    KoreanPronunciationSourceEntry,
    validate_korean_foundation_pack,
)
from multilang.services.korean_foundation_media import (
    KoreanFoundationMediaManifest,
    resolve_korean_foundation_media,
)
from multilang.services.korean_foundation_review import (
    assert_korean_foundation_review_ready,
)
from multilang.services.korean_foundation_snapshot import (
    ResolvedKoreanFoundationSnapshot,
    resolve_active_korean_foundation_snapshot,
)
from multilang.services.phoneme_deck import (
    PHONEME_FIELD_NAMES,
    PhonemeCard,
    build_phoneme_model,
    build_phoneme_note,
)


KOREAN_HANGUL_MODEL_ID: Final = 1_762_801_001
KOREAN_HANGUL_DECK_ID: Final = 1_762_801_002
KOREAN_PRONUNCIATION_MODEL_ID: Final = 1_762_801_003
KOREAN_PRONUNCIATION_DECK_ID: Final = 1_762_801_004

KOREAN_HANGUL_NOTE_TYPE_NAME: Final = "Multilang::Korean Hangul Foundation"
KOREAN_PRONUNCIATION_NOTE_TYPE_NAME: Final = (
    "Multilang::Korean Pronunciation i+1"
)
KOREAN_HANGUL_DECK_NAME: Final = "Multilang Korean::Foundations::Hangul"
KOREAN_PRONUNCIATION_DECK_NAME: Final = (
    "Multilang Korean::Foundations::Pronunciation i+1"
)

HANGUL_FIELD_NAMES: Final = (
    "SortIndex",
    "Category",
    "JamoOrBlock",
    "ReadingOrName",
    "Sound",
    "Mnemonic",
    "Picture",
    "Strokes",
    "Gif",
    "Audio",
    "TargetConceptId",
    "PrerequisiteConceptIds",
    "ObservedConceptIds",
    "UnknownConceptIds",
    "IPlusOnePolicy",
)
KOREAN_PRONUNCIATION_FIELD_NAMES: Final = PHONEME_FIELD_NAMES

_TEMPLATE_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)
_ANKI_REFERENCE_RE = re.compile(r"{{\s*[#/^]?(?P<name>[^{}]+?)\s*}}")
_SOUND_MEDIA_TAG_RE = re.compile(
    r"\[sound:[A-Za-z0-9][A-Za-z0-9._-]{0,151}\.wav\]"
)
_IMAGE_MEDIA_TAG_RE = re.compile(
    r'<img src="(?P<basename>[A-Za-z0-9][A-Za-z0-9._-]{0,155})">'
)
_MEDIA_REFERENCE_RE = re.compile(
    r"\[sound:(?P<sound>[^\]]+)\]|<img src=\"(?P<image>[^\"]+)\">"
)
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}")
_LOWERCASE_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_FIXED_PACKAGE_TIMESTAMP: Final = 1_700_000_000.0
_FIXED_ZIP_TIMESTAMP: Final = (1980, 1, 1, 0, 0, 0)
_KOREAN_FONT_CSS: Final = """.koFont,
.phonemeCard {
  font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic",
    "맑은 고딕", "Segoe UI", sans-serif;
}"""


def _require_identifier(value: str, *, field_name: str) -> str:
    if _IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a bounded identifier")
    return value


def _escape_plain_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("learner text must be a string")
    return escape(value, quote=False)


def _bounded_sound_media_field(value: str, *, optional: bool = False) -> str:
    if optional and value == "":
        return value
    if _SOUND_MEDIA_TAG_RE.fullmatch(value) is None:
        raise ValueError("sound media field must contain one basename-only WAV tag")
    return value


def _bounded_image_media_field(
    value: str,
    *,
    expected_suffix: str,
    optional: bool = False,
) -> str:
    if optional and value == "":
        return value
    match = _IMAGE_MEDIA_TAG_RE.fullmatch(value)
    if match is None or not match.group("basename").endswith(expected_suffix):
        raise ValueError(
            f"image media field must contain one basename-only {expected_suffix} tag"
        )
    return value


def _json_identifiers(values: tuple[str, ...]) -> str:
    for value in values:
        _require_identifier(value, field_name="concept id")
    if len(values) != len(set(values)):
        raise ValueError("concept ids must be unique")
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def _tags(*, family: KoreanFoundationFamily, stage_id: str, item_key: str) -> list[str]:
    return [
        "multilang",
        "ko",
        "korean_foundation",
        f"family_{family.value}",
        f"stage_{_require_identifier(stage_id, field_name='stage id')}",
        f"item_{_require_identifier(item_key, field_name='item key').replace('-', '_')}",
    ]


def stable_korean_foundation_guid(
    *,
    family: KoreanFoundationFamily,
    source_pack_version: str,
    item_key: str,
) -> str:
    """Return a stable 32-hex GUID from immutable source identity only."""

    if not isinstance(family, KoreanFoundationFamily):
        raise TypeError("family must be a KoreanFoundationFamily")
    version = _require_identifier(source_pack_version, field_name="source-pack version")
    key = _require_identifier(item_key, field_name="item key")
    return sha256(f"{family.value}|{version}|{key}".encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class HangulExportRow:
    """One Hangul learner row plus the five locked hidden curriculum fields."""

    sort_index: int
    item_key: str
    source_pack_version: str
    stage_id: str
    category: str
    jamo_or_block: str
    reading_or_name: str
    sound: str
    mnemonic: str
    picture: str
    strokes: str
    gif: str
    audio: str
    target_concept_id: str
    prerequisite_concept_ids: tuple[str, ...]
    observed_concept_ids: tuple[str, ...]
    unknown_concept_ids: tuple[str, ...]
    i_plus_one_policy: str

    def ordered_fields(self) -> list[str]:
        if self.sort_index < 1:
            raise ValueError("sort_index must be positive")
        return [
            str(self.sort_index),
            _escape_plain_text(self.category),
            _escape_plain_text(self.jamo_or_block),
            _escape_plain_text(self.reading_or_name),
            _escape_plain_text(self.sound),
            _escape_plain_text(self.mnemonic),
            _bounded_image_media_field(
                self.picture,
                expected_suffix=".png",
                optional=True,
            ),
            _bounded_image_media_field(
                self.strokes,
                expected_suffix=".png",
                optional=True,
            ),
            _bounded_image_media_field(
                self.gif,
                expected_suffix=".gif",
                optional=True,
            ),
            _bounded_sound_media_field(self.audio, optional=True),
            _require_identifier(self.target_concept_id, field_name="target concept id"),
            _json_identifiers(self.prerequisite_concept_ids),
            _json_identifiers(self.observed_concept_ids),
            _json_identifiers(self.unknown_concept_ids),
            _require_identifier(self.i_plus_one_policy, field_name="i+1 policy"),
        ]


@dataclass(frozen=True)
class KoreanPronunciationExportRow:
    """One Korean pronunciation row in the exact shared nine-field schema."""

    sort_index: int
    item_key: str
    source_pack_version: str
    stage_id: str
    spellings: str
    sound: str
    letter_audio: str
    example_word: str
    word_audio: str
    word_translation: str
    example_sentence: str
    sentence_audio: str
    sentence_translation: str

    def as_phoneme_card(self) -> PhonemeCard:
        if self.sort_index < 1:
            raise ValueError("sort_index must be positive")
        return PhonemeCard(
            sort_index=self.sort_index,
            letters=_escape_plain_text(self.spellings),
            ipa=_escape_plain_text(self.sound),
            example_word=_escape_plain_text(self.example_word),
            example_word_translation=_escape_plain_text(self.word_translation),
            example_sentence=_escape_plain_text(self.example_sentence),
            example_sentence_translation=_escape_plain_text(self.sentence_translation),
            letter_audio=_bounded_sound_media_field(self.letter_audio),
            word_audio=_bounded_sound_media_field(self.word_audio),
            sentence_audio=_bounded_sound_media_field(self.sentence_audio),
        )

    def ordered_fields(self) -> list[str]:
        card = self.as_phoneme_card()
        return [
            card.letters,
            card.ipa,
            card.letter_audio,
            card.example_word,
            card.word_audio,
            card.example_word_translation,
            card.example_sentence,
            card.sentence_audio,
            card.example_sentence_translation,
        ]


@dataclass(frozen=True)
class KoreanFoundationExportMedia:
    """One exact approved media member retained with its verified bytes."""

    item_key: str
    media_kind: str
    basename: str
    path: Path
    sha256: str
    content: bytes

    def __post_init__(self) -> None:
        _require_identifier(self.item_key, field_name="item key")
        _require_identifier(self.media_kind, field_name="media kind")
        _require_identifier(self.basename, field_name="media basename")
        if self.path.name != self.basename:
            raise ValueError("media path basename does not match approved identity")
        if not self.content or sha256(self.content).hexdigest() != self.sha256:
            raise ValueError("media bytes do not match approved SHA-256")


@dataclass(frozen=True)
class KoreanFoundationExportBundle:
    """Validated rows and exact media from one immutable snapshot selection."""

    family: KoreanFoundationFamily
    snapshot_bundle_sha256: str
    source_pack_version: str
    rows: tuple[HangulExportRow | KoreanPronunciationExportRow, ...]
    media: tuple[KoreanFoundationExportMedia, ...]


@dataclass(frozen=True)
class KoreanFoundationExportArtifactResult:
    """Scanner-safe result for one atomically published foundation artifact."""

    output_path: Path
    bundle_path: Path | None
    family: KoreanFoundationFamily
    export_format: ExportArtifactFormat
    card_count: int
    media_count: int
    model_id: int
    deck_id: int
    note_type_name: str
    deck_name: str
    snapshot_bundle_sha256: str
    export_status: str = "completed"


class KoreanHangulNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


def _load_hangul_template() -> dict[str, str]:
    template_path = files("multilang").joinpath("templates", "korean_hangul_card.md")
    content = template_path.read_text(encoding="utf-8")
    match = _TEMPLATE_SECTION_RE.search(content)
    if match is None:
        raise ValueError("unable to parse fixed Korean Hangul template")
    template = {name: match.group(name).strip() for name in ("front", "back", "css")}
    allowed = set(HANGUL_FIELD_NAMES) | {"FrontSide"}
    references = {
        found.group("name").strip().rsplit(":", 1)[-1].strip()
        for found in _ANKI_REFERENCE_RE.finditer(
            f'{template["front"]}\n{template["back"]}'
        )
    }
    unknown = references - allowed
    if unknown:
        raise ValueError("Korean Hangul template references unknown fields")
    return template


def build_korean_hangul_model() -> genanki.Model:
    template = _load_hangul_template()
    return genanki.Model(
        KOREAN_HANGUL_MODEL_ID,
        KOREAN_HANGUL_NOTE_TYPE_NAME,
        fields=[{"name": field_name} for field_name in HANGUL_FIELD_NAMES],
        templates=[
            {
                "name": "Korean Hangul Foundation Card",
                "qfmt": template["front"],
                "afmt": template["back"],
            }
        ],
        css=template["css"],
    )


def build_korean_pronunciation_model() -> genanki.Model:
    return build_phoneme_model(
        model_id=KOREAN_PRONUNCIATION_MODEL_ID,
        note_type_name=KOREAN_PRONUNCIATION_NOTE_TYPE_NAME,
        additional_css=_KOREAN_FONT_CSS,
    )


def build_korean_hangul_note(
    row: HangulExportRow,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    note = KoreanHangulNote(
        model=model or build_korean_hangul_model(),
        fields=row.ordered_fields(),
        tags=_tags(
            family=KoreanFoundationFamily.HANGUL,
            stage_id=row.stage_id,
            item_key=row.item_key,
        ),
    )
    note._multilang_guid = stable_korean_foundation_guid(  # type: ignore[attr-defined]
        family=KoreanFoundationFamily.HANGUL,
        source_pack_version=row.source_pack_version,
        item_key=row.item_key,
    )
    return note


def build_korean_pronunciation_note(
    row: KoreanPronunciationExportRow,
    *,
    model: genanki.Model | None = None,
) -> genanki.Note:
    note = build_phoneme_note(
        row.as_phoneme_card(),
        model=model or build_korean_pronunciation_model(),
        guid=stable_korean_foundation_guid(
            family=KoreanFoundationFamily.PRONUNCIATION,
            source_pack_version=row.source_pack_version,
            item_key=row.item_key,
        ),
    )
    note.tags = _tags(
        family=KoreanFoundationFamily.PRONUNCIATION,
        stage_id=row.stage_id,
        item_key=row.item_key,
    )
    return note


def _sound_tag(basename: str) -> str:
    return _bounded_sound_media_field(f"[sound:{basename}]")


def _image_tag(basename: str) -> str:
    suffix = Path(basename).suffix
    if suffix not in {".png", ".gif"}:
        raise ValueError("image media field has an unsupported format")
    return _bounded_image_media_field(
        f'<img src="{basename}">',
        expected_suffix=suffix,
    )


def _validate_resolved_snapshot_integrity(
    snapshot: ResolvedKoreanFoundationSnapshot,
) -> None:
    """Recheck the injected frozen fixture seam before trusting typed members."""

    if not isinstance(snapshot, ResolvedKoreanFoundationSnapshot):
        raise TypeError("snapshot must be a resolved Korean foundation snapshot")
    if snapshot.bundle_sha256 != snapshot.manifest.bundle_sha256:
        raise ValueError("snapshot bundle identity mismatch")
    declared = tuple(
        (member.role, member.relpath, member.size_bytes, member.sha256)
        for member in snapshot.manifest.members
    )
    resolved = tuple(
        (member.role, member.relpath, member.size_bytes, member.sha256)
        for member in snapshot.members
    )
    if declared != resolved:
        raise ValueError("snapshot member order or identity mismatch")
    if snapshot.review_evidence_members != tuple(
        member for member in snapshot.members if member.role == "review_evidence"
    ) or snapshot.media_members != tuple(
        member for member in snapshot.members if member.role == "media"
    ):
        raise ValueError("snapshot member role partition mismatch")
    for member in snapshot.members:
        if (
            member.path
            != snapshot.snapshot_root.joinpath(*member.relpath.split("/"))
            or len(member.content) != member.size_bytes
            or sha256(member.content).hexdigest() != member.sha256
        ):
            raise ValueError("snapshot member content mismatch")

    singleton_content = {
        member.role: member.content
        for member in snapshot.members
        if member.role
        in {
            "concept_registry",
            "hangul_source_pack",
            "pronunciation_source_pack",
            "curation_manifest",
            "media_manifest",
        }
    }
    if (
        snapshot.concept_registry.model_validate_json(
            singleton_content["concept_registry"]
        )
        != snapshot.concept_registry
        or snapshot.hangul_source_pack.model_validate_json(
            singleton_content["hangul_source_pack"]
        )
        != snapshot.hangul_source_pack
        or snapshot.pronunciation_source_pack.model_validate_json(
            singleton_content["pronunciation_source_pack"]
        )
        != snapshot.pronunciation_source_pack
        or snapshot.curation_manifest.model_validate_json(
            singleton_content["curation_manifest"]
        )
        != snapshot.curation_manifest
        or singleton_content["media_manifest"] != snapshot.media_manifest_bytes
    ):
        raise ValueError("snapshot typed member mismatch")


def _assert_review_evidence_members_are_bound(
    snapshot: ResolvedKoreanFoundationSnapshot,
) -> None:
    if snapshot.manifest.schema_version == 2:
        for record in snapshot.curation_manifest.records:
            for gate in record.gates:
                expected = sha256(
                    json.dumps(
                        {
                            "item_key": record.item_key,
                            "gate_name": gate.gate_name,
                            "scope_ids": list(gate.scope_ids),
                            "source_pack_version": record.source_pack_version,
                            "source_content_sha256": record.source_content_sha256,
                        },
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest()
                if (
                    gate.status != "approved"
                    or gate.reviewed_evidence_sha256 != expected
                ):
                    raise ValueError(
                        f"review_evidence_mismatch item_key={record.item_key} "
                        f"gate={gate.gate_name}"
                    )
        return

    evidence_hashes = {
        member.sha256 for member in snapshot.review_evidence_members
    }
    if not evidence_hashes:
        raise ValueError("snapshot review evidence is missing")
    for record in snapshot.curation_manifest.records:
        for gate in record.gates:
            if (
                gate.status != "approved"
                or gate.reviewed_evidence_sha256 not in evidence_hashes
            ):
                raise ValueError(
                    f"review_evidence_mismatch item_key={record.item_key} "
                    f"gate={gate.gate_name}"
                )


def _media_for_family(
    snapshot: ResolvedKoreanFoundationSnapshot,
    *,
    family: KoreanFoundationFamily,
    manifest: KoreanFoundationMediaManifest,
) -> tuple[
    tuple[KoreanFoundationExportMedia, ...],
    dict[tuple[str, str], KoreanFoundationExportMedia],
]:
    resolved_paths = resolve_korean_foundation_media(snapshot)
    path_by_name = {path.name: path for path in resolved_paths}
    member_by_relpath = {member.relpath: member for member in snapshot.media_members}
    media: list[KoreanFoundationExportMedia] = []
    by_slot: dict[tuple[str, str], KoreanFoundationExportMedia] = {}
    for slot in manifest.slots:
        if slot.family is not family or not slot.required:
            continue
        path = path_by_name.get(slot.basename)
        member = member_by_relpath.get(slot.storage_relpath)
        if path is None or member is None or path != member.path:
            raise ValueError(
                f"media_reference_mismatch item_key={slot.item_key} "
                f"media_kind={slot.media_kind}"
            )
        content = path.read_bytes()
        if content != member.content or sha256(content).hexdigest() != slot.artifact_sha256:
            raise ValueError(
                f"media_byte_mismatch item_key={slot.item_key} "
                f"media_kind={slot.media_kind}"
            )
        item = KoreanFoundationExportMedia(
            item_key=slot.item_key,
            media_kind=slot.media_kind,
            basename=slot.basename,
            path=path,
            sha256=slot.artifact_sha256,
            content=content,
        )
        key = (slot.item_key, slot.media_kind)
        if key in by_slot:
            raise ValueError(
                f"duplicate_media_slot item_key={slot.item_key} "
                f"media_kind={slot.media_kind}"
            )
        media.append(item)
        by_slot[key] = item
    return tuple(media), by_slot


def _required_media(
    media_by_slot: dict[tuple[str, str], KoreanFoundationExportMedia],
    *,
    item_key: str,
    media_kind: str,
) -> KoreanFoundationExportMedia:
    try:
        return media_by_slot[(item_key, media_kind)]
    except KeyError as exc:
        raise ValueError(
            f"missing_media_reference item_key={item_key} media_kind={media_kind}"
        ) from exc


def _hangul_row_from_source(
    entry: KoreanHangulSourceEntry,
    media_by_slot: dict[tuple[str, str], KoreanFoundationExportMedia],
) -> HangulExportRow:
    strokes = _required_media(
        media_by_slot,
        item_key=entry.item_key,
        media_kind="strokes",
    )
    audio = _required_media(
        media_by_slot,
        item_key=entry.item_key,
        media_kind="audio",
    )
    if any(
        value is None
        for value in (entry.reading_or_name, entry.sound, entry.mnemonic)
    ):
        raise ValueError(f"learner_copy_missing item_key={entry.item_key}")
    return HangulExportRow(
        sort_index=entry.sort_index,
        item_key=entry.item_key,
        source_pack_version=entry.source_pack_version,
        stage_id=entry.stage_id,
        category=entry.category,
        jamo_or_block=entry.canonical_jamo_or_block,
        reading_or_name=entry.reading_or_name or "",
        sound=entry.sound or "",
        mnemonic=entry.mnemonic or "",
        picture="",
        strokes=_image_tag(strokes.basename),
        gif="",
        audio=_sound_tag(audio.basename),
        target_concept_id=entry.evidence.target_concept_id,
        prerequisite_concept_ids=tuple(entry.evidence.prerequisite_concept_ids),
        observed_concept_ids=tuple(entry.evidence.observed_concept_ids),
        unknown_concept_ids=tuple(entry.evidence.unknown_concept_ids),
        i_plus_one_policy=entry.evidence.policy,
    )


def _pronunciation_row_from_source(
    entry: KoreanPronunciationSourceEntry,
    media_by_slot: dict[tuple[str, str], KoreanFoundationExportMedia],
) -> KoreanPronunciationExportRow:
    letter = _required_media(
        media_by_slot,
        item_key=entry.item_key,
        media_kind="letter_audio",
    )
    word = _required_media(
        media_by_slot,
        item_key=entry.item_key,
        media_kind="word_audio",
    )
    sentence = _required_media(
        media_by_slot,
        item_key=entry.item_key,
        media_kind="sentence_audio",
    )
    return KoreanPronunciationExportRow(
        sort_index=entry.sequence,
        item_key=entry.item_key,
        source_pack_version=entry.source_pack_version,
        stage_id=entry.stage_id,
        spellings=entry.spellings,
        sound=entry.sound,
        letter_audio=_sound_tag(letter.basename),
        example_word=entry.example_word,
        word_audio=_sound_tag(word.basename),
        word_translation=entry.word_translation,
        example_sentence=entry.example_sentence,
        sentence_audio=_sound_tag(sentence.basename),
        sentence_translation=entry.sentence_translation,
    )


def _build_korean_foundation_export_bundle_from_snapshot(
    snapshot: ResolvedKoreanFoundationSnapshot,
    *,
    family: KoreanFoundationFamily,
) -> KoreanFoundationExportBundle:
    """Private fixture seam: validate and join one already-resolved snapshot."""

    if not isinstance(family, KoreanFoundationFamily):
        raise TypeError("family must be a KoreanFoundationFamily")
    _validate_resolved_snapshot_integrity(snapshot)
    pack = (
        snapshot.hangul_source_pack
        if family is KoreanFoundationFamily.HANGUL
        else snapshot.pronunciation_source_pack
    )
    validate_korean_foundation_pack(
        registry=snapshot.concept_registry,
        pack=pack,
        inherited_known_ids=(
            ()
            if family is KoreanFoundationFamily.HANGUL
            else tuple(pack.inherited_orthographic_concept_ids)
        ),
    )
    assert_korean_foundation_review_ready(snapshot)
    _assert_review_evidence_members_are_bound(snapshot)
    media_manifest = KoreanFoundationMediaManifest.model_validate_json(
        snapshot.media_manifest_bytes
    )
    media, media_by_slot = _media_for_family(
        snapshot,
        family=family,
        manifest=media_manifest,
    )
    rows: tuple[HangulExportRow | KoreanPronunciationExportRow, ...]
    if family is KoreanFoundationFamily.HANGUL:
        rows = tuple(
            _hangul_row_from_source(entry, media_by_slot)
            for entry in snapshot.hangul_source_pack.entries
        )
    else:
        rows = tuple(
            _pronunciation_row_from_source(entry, media_by_slot)
            for entry in snapshot.pronunciation_source_pack.entries
        )
    return KoreanFoundationExportBundle(
        family=family,
        snapshot_bundle_sha256=snapshot.bundle_sha256,
        source_pack_version=pack.source_pack_version,
        rows=rows,
        media=media,
    )


def build_korean_foundation_export_bundle(
    *,
    family: KoreanFoundationFamily,
) -> KoreanFoundationExportBundle:
    """Resolve the fixed active pointer once, then join its immutable snapshot."""

    snapshot = resolve_active_korean_foundation_snapshot()
    return _build_korean_foundation_export_bundle_from_snapshot(
        snapshot,
        family=family,
    )


def _family_contract(
    family: KoreanFoundationFamily,
) -> tuple[int, int, str, str, tuple[str, ...]]:
    if family is KoreanFoundationFamily.HANGUL:
        return (
            KOREAN_HANGUL_MODEL_ID,
            KOREAN_HANGUL_DECK_ID,
            KOREAN_HANGUL_NOTE_TYPE_NAME,
            KOREAN_HANGUL_DECK_NAME,
            HANGUL_FIELD_NAMES,
        )
    return (
        KOREAN_PRONUNCIATION_MODEL_ID,
        KOREAN_PRONUNCIATION_DECK_ID,
        KOREAN_PRONUNCIATION_NOTE_TYPE_NAME,
        KOREAN_PRONUNCIATION_DECK_NAME,
        KOREAN_PRONUNCIATION_FIELD_NAMES,
    )


def _build_model(family: KoreanFoundationFamily) -> genanki.Model:
    return (
        build_korean_hangul_model()
        if family is KoreanFoundationFamily.HANGUL
        else build_korean_pronunciation_model()
    )


def _build_note(
    row: HangulExportRow | KoreanPronunciationExportRow,
    *,
    family: KoreanFoundationFamily,
    model: genanki.Model,
) -> genanki.Note:
    if family is KoreanFoundationFamily.HANGUL:
        if not isinstance(row, HangulExportRow):
            raise TypeError("Hangul export bundle contains a pronunciation row")
        return build_korean_hangul_note(row, model=model)
    if not isinstance(row, KoreanPronunciationExportRow):
        raise TypeError("pronunciation export bundle contains a Hangul row")
    return build_korean_pronunciation_note(row, model=model)


def _row_fields(
    row: HangulExportRow | KoreanPronunciationExportRow,
) -> list[str]:
    return row.ordered_fields()


def _row_guid(
    row: HangulExportRow | KoreanPronunciationExportRow,
    *,
    family: KoreanFoundationFamily,
) -> str:
    return stable_korean_foundation_guid(
        family=family,
        source_pack_version=row.source_pack_version,
        item_key=row.item_key,
    )


def _row_tags(
    row: HangulExportRow | KoreanPronunciationExportRow,
    *,
    family: KoreanFoundationFamily,
) -> list[str]:
    return _tags(family=family, stage_id=row.stage_id, item_key=row.item_key)


def _row_media_references(
    row: HangulExportRow | KoreanPronunciationExportRow,
) -> tuple[str, ...]:
    references: list[str] = []
    for field in _row_fields(row):
        for match in _MEDIA_REFERENCE_RE.finditer(field):
            references.append(match.group("sound") or match.group("image"))
    return tuple(references)


def _validate_export_bundle(bundle: KoreanFoundationExportBundle) -> None:
    if not isinstance(bundle.family, KoreanFoundationFamily):
        raise TypeError("foundation export family is invalid")
    if not bundle.rows:
        raise ValueError("foundation export bundle cannot be empty")
    if _LOWERCASE_SHA256_RE.fullmatch(bundle.snapshot_bundle_sha256) is None:
        raise ValueError("snapshot bundle identity must be lowercase SHA-256")
    expected_sequences = tuple(range(1, len(bundle.rows) + 1))
    if tuple(row.sort_index for row in bundle.rows) != expected_sequences:
        raise ValueError("foundation export row order mismatch")
    expected_source_pack_version = (
        "hangul-v1"
        if bundle.family is KoreanFoundationFamily.HANGUL
        else "pronunciation-i-plus-1-v1"
    )
    if (
        bundle.source_pack_version != expected_source_pack_version
        or any(
            row.source_pack_version != bundle.source_pack_version
            for row in bundle.rows
        )
    ):
        raise ValueError("foundation export source-pack identity mismatch")
    item_prefix = (
        "ko-hangul"
        if bundle.family is KoreanFoundationFamily.HANGUL
        else "ko-pron"
    )
    stage_prefix = "H" if bundle.family is KoreanFoundationFamily.HANGUL else "P"
    if any(
        row.item_key != f"{item_prefix}-{row.sort_index:04d}"
        or not row.stage_id.startswith(stage_prefix)
        for row in bundle.rows
    ):
        raise ValueError("foundation export row identity mismatch")
    expected_row_type = (
        HangulExportRow
        if bundle.family is KoreanFoundationFamily.HANGUL
        else KoreanPronunciationExportRow
    )
    if any(not isinstance(row, expected_row_type) for row in bundle.rows):
        raise ValueError("foundation export row schema mismatch")

    basenames = tuple(media.basename for media in bundle.media)
    if len(basenames) != len(set(basenames)):
        raise ValueError("foundation export media basenames must be unique")
    media_by_name = {media.basename: media for media in bundle.media}
    references = tuple(
        reference
        for row in bundle.rows
        for reference in _row_media_references(row)
    )
    if set(references) != set(media_by_name):
        raise ValueError("foundation export media references do not resolve exactly")
    for row in bundle.rows:
        for basename in _row_media_references(row):
            media = media_by_name[basename]
            if media.item_key != row.item_key:
                raise ValueError(
                    f"media_item_mismatch item_key={row.item_key}"
                )


def _stat_is_link_or_reparse(stat_result: os.stat_result) -> bool:
    if stat.S_ISLNK(stat_result.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(stat_result, "st_file_attributes", 0) & reparse_flag)


def _assert_output_destination_is_safe(
    destination: Path,
    *,
    export_format: ExportArtifactFormat,
) -> None:
    if not isinstance(destination, Path):
        raise TypeError("output_destination must be a pathlib.Path")
    if destination.name in {"", ".", ".."} or ".." in destination.parts:
        raise ValueError("unsafe output destination")
    if export_format is ExportArtifactFormat.APKG and destination.suffix != ".apkg":
        raise ValueError("APKG output destination must use the .apkg suffix")
    if export_format is not ExportArtifactFormat.APKG and destination.suffix:
        raise ValueError("tabular output destination must be a bundle directory")

    current = destination
    while not current.exists() and current != current.parent:
        current = current.parent
    try:
        current_stat = current.lstat()
    except OSError as exc:
        raise ValueError("output destination parent is unavailable") from exc
    if _stat_is_link_or_reparse(current_stat) or not stat.S_ISDIR(current_stat.st_mode):
        raise ValueError("output destination contains an unsafe filesystem component")
    if destination.exists():
        destination_stat = destination.lstat()
        if _stat_is_link_or_reparse(destination_stat):
            raise ValueError("output destination cannot be a link or reparse point")
        if export_format is ExportArtifactFormat.APKG:
            if not stat.S_ISREG(destination_stat.st_mode):
                raise ValueError("APKG output destination must be a regular file")
        else:
            raise FileExistsError("tabular output bundle already exists")


def _assert_output_is_outside_snapshot(
    destination: Path,
    *,
    snapshot: ResolvedKoreanFoundationSnapshot,
) -> None:
    try:
        snapshot_root = snapshot.snapshot_root.resolve(strict=True)
        resolved_destination = destination.resolve(strict=False)
    except OSError as exc:
        raise ValueError("unsafe output destination") from exc
    if resolved_destination == snapshot_root or resolved_destination.is_relative_to(
        snapshot_root
    ):
        raise ValueError("unsafe output destination")


def _stage_exact_media(
    media: tuple[KoreanFoundationExportMedia, ...],
    *,
    media_root: Path,
) -> tuple[Path, ...]:
    media_root.mkdir()
    staged: list[Path] = []
    for item in sorted(media, key=lambda value: value.basename):
        current = item.path.read_bytes()
        if current != item.content or sha256(current).hexdigest() != item.sha256:
            raise ValueError(
                f"media_byte_mismatch item_key={item.item_key} "
                f"media_kind={item.media_kind}"
            )
        destination = media_root / item.basename
        with destination.open("xb") as handle:
            handle.write(item.content)
        if destination.read_bytes() != item.content:
            raise ValueError(
                f"staged_media_mismatch item_key={item.item_key} "
                f"media_kind={item.media_kind}"
            )
        staged.append(destination)
    return tuple(staged)


def _canonicalize_apkg(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source, "r") as input_archive:
        infos = input_archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("APKG contains duplicate archive members")
        payloads = {name: input_archive.read(name) for name in names}

    def member_key(name: str) -> tuple[int, int | str]:
        if name == "collection.anki2":
            return (0, 0)
        if name == "media":
            return (1, 0)
        if name.isdigit():
            return (2, int(name))
        return (3, name)

    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as output_archive:
        for name in sorted(payloads, key=member_key):
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output_archive.writestr(
                info,
                payloads[name],
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def _inspect_collection(
    collection_bytes: bytes,
    *,
    bundle: KoreanFoundationExportBundle,
    workspace: Path,
) -> None:
    model_id, deck_id, note_type_name, deck_name, field_names = _family_contract(
        bundle.family
    )
    descriptor, raw_path = tempfile.mkstemp(
        prefix="collection-",
        suffix=".anki2",
        dir=workspace,
    )
    os.close(descriptor)
    collection_path = Path(raw_path)
    try:
        collection_path.write_bytes(collection_bytes)
        connection = sqlite3.connect(collection_path)
        try:
            models = json.loads(
                connection.execute("select models from col").fetchone()[0]
            )
            decks = json.loads(
                connection.execute("select decks from col").fetchone()[0]
            )
            notes = connection.execute(
                "select guid, mid, flds, tags from notes order by id"
            ).fetchall()
            cards = connection.execute(
                "select did from cards order by id"
            ).fetchall()
        finally:
            connection.close()
    finally:
        collection_path.unlink(missing_ok=True)

    if str(model_id) not in models or set(models) != {str(model_id)}:
        raise ValueError("APKG model identity mismatch")
    model = models[str(model_id)]
    expected_model = _build_model(bundle.family)
    if (
        model["name"] != note_type_name
        or [field["name"] for field in model["flds"]] != list(field_names)
        or model["tmpls"][0]["qfmt"] != expected_model.templates[0]["qfmt"]
        or model["tmpls"][0]["afmt"] != expected_model.templates[0]["afmt"]
        or model["css"] != expected_model.css
    ):
        raise ValueError("APKG model schema or template mismatch")
    if str(deck_id) not in decks or decks[str(deck_id)]["name"] != deck_name:
        raise ValueError("APKG deck identity mismatch")
    if len(notes) != len(bundle.rows) or len(cards) != len(bundle.rows):
        raise ValueError("APKG note or card count mismatch")
    if {did for (did,) in cards} != {deck_id}:
        raise ValueError("APKG card deck identity mismatch")
    for (guid, mid, fields, tags), row in zip(notes, bundle.rows, strict=True):
        if (
            guid != _row_guid(row, family=bundle.family)
            or mid != model_id
            or fields.split("\x1f") != _row_fields(row)
            or tags.split() != _row_tags(row, family=bundle.family)
        ):
            raise ValueError(f"APKG note mismatch item_key={row.item_key}")


def _inspect_staged_apkg(
    staged_path: Path,
    *,
    bundle: KoreanFoundationExportBundle,
) -> None:
    expected_media = {
        item.basename: item.content
        for item in sorted(bundle.media, key=lambda value: value.basename)
    }
    with zipfile.ZipFile(staged_path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if (
            len(names) != len(set(names))
            or any(
                name.startswith(("/", "\\"))
                or ".." in name.replace("\\", "/").split("/")
                for name in names
            )
            or any(info.date_time != _FIXED_ZIP_TIMESTAMP for info in infos)
        ):
            raise ValueError("APKG archive member safety mismatch")
        if set(names) != {
            "collection.anki2",
            "media",
            *(str(index) for index in range(len(expected_media))),
        }:
            raise ValueError("APKG archive member set mismatch")
        try:
            media_map = json.loads(archive.read("media").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("APKG media map is invalid") from exc
        expected_names = sorted(expected_media)
        if media_map != {
            str(index): basename for index, basename in enumerate(expected_names)
        }:
            raise ValueError("APKG media map mismatch")
        for index, basename in enumerate(expected_names):
            if archive.read(str(index)) != expected_media[basename]:
                raise ValueError("APKG media bytes mismatch")
        collection_bytes = archive.read("collection.anki2")
    _inspect_collection(collection_bytes, bundle=bundle, workspace=staged_path.parent)


def _serialize_tabular_field(value: str) -> str:
    return value.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def _table_filename(
    family: KoreanFoundationFamily,
    export_format: ExportArtifactFormat,
) -> str:
    stem = (
        "korean-hangul-foundation"
        if family is KoreanFoundationFamily.HANGUL
        else "korean-pronunciation-i-plus-1"
    )
    return f"{stem}.{export_format.value}"


def _notes_metadata(bundle: KoreanFoundationExportBundle) -> dict[str, object]:
    model_id, deck_id, note_type_name, deck_name, _ = _family_contract(bundle.family)
    return {
        "schema_version": 1,
        "family": bundle.family.value,
        "source_pack_version": bundle.source_pack_version,
        "snapshot_bundle_sha256": bundle.snapshot_bundle_sha256,
        "model_id": model_id,
        "deck_id": deck_id,
        "note_type_name": note_type_name,
        "deck_name": deck_name,
        "notes": [
            {
                "row": index,
                "item_key": row.item_key,
                "guid": _row_guid(row, family=bundle.family),
                "tags": _row_tags(row, family=bundle.family),
            }
            for index, row in enumerate(bundle.rows, start=1)
        ],
    }


def _media_checksums(bundle: KoreanFoundationExportBundle) -> dict[str, object]:
    return {
        "schema_version": 1,
        "family": bundle.family.value,
        "source_pack_version": bundle.source_pack_version,
        "snapshot_bundle_sha256": bundle.snapshot_bundle_sha256,
        "files": [
            {
                "basename": item.basename,
                "sha256": item.sha256,
                "size_bytes": len(item.content),
            }
            for item in sorted(bundle.media, key=lambda value: value.basename)
        ],
    }


def _json_document(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _write_text_exact(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(value)


def _write_staged_tabular_bundle(
    stage: Path,
    *,
    bundle: KoreanFoundationExportBundle,
    export_format: ExportArtifactFormat,
) -> Path:
    stage.mkdir()
    _, _, note_type_name, deck_name, field_names = _family_contract(bundle.family)
    delimiter = "\t" if export_format is ExportArtifactFormat.TSV else ","
    separator_name = "Tab" if delimiter == "\t" else "Comma"
    buffer = StringIO(newline="")
    buffer.write(f"#separator:{separator_name}\n")
    buffer.write("#html:true\n")
    buffer.write(f"#notetype:{note_type_name}\n")
    buffer.write(f"#deck:{deck_name}\n")
    buffer.write(f"#columns:{delimiter.join(field_names)}\n")
    writer = csv.writer(
        buffer,
        delimiter=delimiter,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    for row in bundle.rows:
        writer.writerow(
            [_serialize_tabular_field(value) for value in _row_fields(row)]
        )
    table_path = stage / _table_filename(bundle.family, export_format)
    _write_text_exact(table_path, buffer.getvalue())
    _write_text_exact(
        stage / "notes-metadata.json",
        _json_document(_notes_metadata(bundle)),
    )
    _write_text_exact(
        stage / "media-checksums.json",
        _json_document(_media_checksums(bundle)),
    )
    _stage_exact_media(bundle.media, media_root=stage / "media")
    return table_path


def _inspect_staged_tabular_bundle(
    stage: Path,
    *,
    bundle: KoreanFoundationExportBundle,
    export_format: ExportArtifactFormat,
) -> None:
    table_name = _table_filename(bundle.family, export_format)
    expected_top_level = {
        table_name,
        "notes-metadata.json",
        "media-checksums.json",
        "media",
    }
    children = tuple(stage.iterdir())
    if {child.name for child in children} != expected_top_level or any(
        child.is_symlink() for child in children
    ):
        raise ValueError("tabular bundle member set is invalid")
    media_root = stage / "media"
    if not media_root.is_dir():
        raise ValueError("tabular bundle media directory is missing")
    media_files = tuple(media_root.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in media_files):
        raise ValueError("tabular bundle media member is unsafe")

    _, _, note_type_name, deck_name, field_names = _family_contract(bundle.family)
    delimiter = "\t" if export_format is ExportArtifactFormat.TSV else ","
    separator_name = "Tab" if delimiter == "\t" else "Comma"
    table_text = (stage / table_name).read_text(encoding="utf-8")
    lines = table_text.splitlines()
    if lines[:5] != [
        f"#separator:{separator_name}",
        "#html:true",
        f"#notetype:{note_type_name}",
        f"#deck:{deck_name}",
        f"#columns:{delimiter.join(field_names)}",
    ]:
        raise ValueError("tabular bundle header mismatch")
    rows = list(csv.reader(lines[5:], delimiter=delimiter))
    expected_rows = [
        [_serialize_tabular_field(value) for value in _row_fields(row)]
        for row in bundle.rows
    ]
    if rows != expected_rows:
        raise ValueError("tabular bundle row mismatch")

    try:
        notes_metadata = json.loads(
            (stage / "notes-metadata.json").read_text(encoding="utf-8")
        )
        checksums = json.loads(
            (stage / "media-checksums.json").read_text(encoding="utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("tabular bundle metadata is invalid") from exc
    if notes_metadata != _notes_metadata(bundle) or checksums != _media_checksums(bundle):
        raise ValueError("tabular bundle metadata mismatch")

    expected_media = {
        item.basename: item for item in sorted(bundle.media, key=lambda value: value.basename)
    }
    if {path.name for path in media_files} != set(expected_media):
        raise ValueError("tabular bundle media set mismatch")
    for basename, item in expected_media.items():
        content = (media_root / basename).read_bytes()
        if content != item.content or sha256(content).hexdigest() != item.sha256:
            raise ValueError("tabular bundle media bytes mismatch")
    references = {
        reference
        for row in rows
        for field in row
        for match in _MEDIA_REFERENCE_RE.finditer(field)
        for reference in (match.group("sound") or match.group("image"),)
    }
    if references != set(expected_media):
        raise ValueError("tabular bundle media references do not resolve exactly")


def _result(
    *,
    bundle: KoreanFoundationExportBundle,
    export_format: ExportArtifactFormat,
    output_path: Path,
    bundle_path: Path | None,
) -> KoreanFoundationExportArtifactResult:
    model_id, deck_id, note_type_name, deck_name, _ = _family_contract(bundle.family)
    return KoreanFoundationExportArtifactResult(
        output_path=output_path,
        bundle_path=bundle_path,
        family=bundle.family,
        export_format=export_format,
        card_count=len(bundle.rows),
        media_count=len(bundle.media),
        model_id=model_id,
        deck_id=deck_id,
        note_type_name=note_type_name,
        deck_name=deck_name,
        snapshot_bundle_sha256=bundle.snapshot_bundle_sha256,
    )


def _write_apkg(
    bundle: KoreanFoundationExportBundle,
    *,
    output_destination: Path,
) -> KoreanFoundationExportArtifactResult:
    parent = output_destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".korean-foundation-",
        dir=parent,
    ) as temporary:
        workspace = Path(temporary)
        media_paths = _stage_exact_media(bundle.media, media_root=workspace / "media")
        model = _build_model(bundle.family)
        _, deck_id, _, deck_name, _ = _family_contract(bundle.family)
        deck = genanki.Deck(deck_id, deck_name)
        for row in bundle.rows:
            deck.add_note(_build_note(row, family=bundle.family, model=model))
        package = genanki.Package(deck)
        package.media_files = [str(path) for path in media_paths]
        raw_path = workspace / "raw.apkg"
        package.write_to_file(str(raw_path), timestamp=_FIXED_PACKAGE_TIMESTAMP)
        staged_path = workspace / "inspected.apkg"
        _canonicalize_apkg(raw_path, staged_path)
        _inspect_staged_apkg(staged_path, bundle=bundle)
        os.replace(staged_path, output_destination)
    return _result(
        bundle=bundle,
        export_format=ExportArtifactFormat.APKG,
        output_path=output_destination,
        bundle_path=None,
    )


def _write_tabular_bundle(
    bundle: KoreanFoundationExportBundle,
    *,
    export_format: ExportArtifactFormat,
    output_destination: Path,
) -> KoreanFoundationExportArtifactResult:
    parent = output_destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    table_name = _table_filename(bundle.family, export_format)
    with tempfile.TemporaryDirectory(
        prefix=".korean-foundation-",
        dir=parent,
    ) as temporary:
        workspace = Path(temporary)
        staged_bundle = workspace / "bundle"
        _write_staged_tabular_bundle(
            staged_bundle,
            bundle=bundle,
            export_format=export_format,
        )
        _inspect_staged_tabular_bundle(
            staged_bundle,
            bundle=bundle,
            export_format=export_format,
        )
        os.replace(staged_bundle, output_destination)
    return _result(
        bundle=bundle,
        export_format=export_format,
        output_path=output_destination / table_name,
        bundle_path=output_destination,
    )


def _export_korean_foundation_from_snapshot(
    snapshot: ResolvedKoreanFoundationSnapshot,
    *,
    family: KoreanFoundationFamily,
    export_format: ExportArtifactFormat,
    output_destination: Path,
) -> KoreanFoundationExportArtifactResult:
    """Private fixture seam for successful writes from one typed snapshot."""

    if not isinstance(export_format, ExportArtifactFormat):
        raise TypeError("export_format must be an ExportArtifactFormat")
    bundle = _build_korean_foundation_export_bundle_from_snapshot(
        snapshot,
        family=family,
    )
    _validate_export_bundle(bundle)
    _assert_output_destination_is_safe(
        output_destination,
        export_format=export_format,
    )
    _assert_output_is_outside_snapshot(
        output_destination,
        snapshot=snapshot,
    )
    if export_format is ExportArtifactFormat.APKG:
        return _write_apkg(bundle, output_destination=output_destination)
    return _write_tabular_bundle(
        bundle,
        export_format=export_format,
        output_destination=output_destination,
    )


def export_korean_foundation(
    *,
    family: KoreanFoundationFamily,
    export_format: ExportArtifactFormat,
    output_destination: Path,
) -> KoreanFoundationExportArtifactResult:
    """Resolve one fixed active snapshot and atomically export one family/format."""

    snapshot = resolve_active_korean_foundation_snapshot()
    return _export_korean_foundation_from_snapshot(
        snapshot,
        family=family,
        export_format=export_format,
        output_destination=output_destination,
    )


__all__ = [
    "ExportArtifactFormat",
    "HANGUL_FIELD_NAMES",
    "KOREAN_HANGUL_DECK_ID",
    "KOREAN_HANGUL_DECK_NAME",
    "KOREAN_HANGUL_MODEL_ID",
    "KOREAN_HANGUL_NOTE_TYPE_NAME",
    "KOREAN_PRONUNCIATION_DECK_ID",
    "KOREAN_PRONUNCIATION_DECK_NAME",
    "KOREAN_PRONUNCIATION_FIELD_NAMES",
    "KOREAN_PRONUNCIATION_MODEL_ID",
    "KOREAN_PRONUNCIATION_NOTE_TYPE_NAME",
    "HangulExportRow",
    "KoreanFoundationFamily",
    "KoreanFoundationExportBundle",
    "KoreanFoundationExportArtifactResult",
    "KoreanFoundationExportMedia",
    "KoreanPronunciationExportRow",
    "build_korean_foundation_export_bundle",
    "build_korean_hangul_model",
    "build_korean_hangul_note",
    "build_korean_pronunciation_model",
    "build_korean_pronunciation_note",
    "export_korean_foundation",
    "stable_korean_foundation_guid",
]
