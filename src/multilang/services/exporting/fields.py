"""Map semantic content to established language/source fields without metadata."""

from __future__ import annotations

import re
from pathlib import Path

import genanki

from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.services.anki_id_registry import native_anki_model_id
from multilang.services.card_template_loader import load_card_template
from multilang.services.native_audio import reusable_audio_version
from multilang.services.native_content import render_plain_content as _render_plain_content
from multilang.services.native_content import validate_target_span


def render_plain_content(value: str) -> str:
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        raise ValueError("Anki content cannot contain control characters or field separators")
    return _render_plain_content(value)


def semantic_source_type(card: SemanticCard) -> str:
    if card.inventory == "foundation":
        raise ValueError("foundation cards require their dedicated field contract/exporter")
    return {"custom": "word-list", "highlight": "kindle-highlights"}.get(
        card.inventory, "frequency"
    )


def semantic_field_note(
    card: SemanticCard, *, prototype: bool
) -> tuple[genanki.Model, list[str], list[Path]]:
    """One exact field-compatible note; optional roles use the same field schema."""
    source = semantic_source_type(card)
    names = ExportCardRow.field_names(source_type=source, language=card.language)
    template = load_card_template(source_type=source, language=card.language)
    if card.content is None and not prototype:
        raise ValueError("production card requires approved content")
    if card.content is not None and not prototype and card.content.review_status != "approved":
        raise ValueError("production card requires independently approved content")
    content = card.content.content if card.content else None
    media = []
    sounds = {}
    for kind, asset in (("word", card.word_audio), ("sentence", card.sentence_audio)):
        if asset is None:
            if not prototype:
                raise ValueError("production card requires exact word and sentence audio")
            sounds[kind] = ""
            continue
        if not reusable_audio_version(asset.signature, asset, namespace=card.namespace):
            raise ValueError("audio artifact integrity failed")
        if not prototype and asset.review_status != "approved":
            raise ValueError("production audio requires approved review/license evidence")
        path = Path(asset.storage_path)
        if not re.fullmatch(r"[\w. -]+", path.name, flags=re.UNICODE):
            raise ValueError("unsafe audio media basename")
        media.append(path)
        sounds[kind] = f"[sound:{path.name}]"
    definition = render_plain_content(
        content.definition if content else "Prototype only; content not approved."
    )
    if content and content.explanation:
        definition += "<br>" + render_plain_content(content.explanation)
    if card.role == "important_form":
        if not prototype and (content is None or not content.explanation.strip()):
            raise ValueError("important form requires readable contextual morphology explanation")
        definition += "<br>" + render_plain_content(f"Lemma: {card.parent_lemma}")
        definition += "<br>" + render_plain_content(card.context_cue)
    # Manual/highlight models intentionally lack these separate fields. Preserve
    # their content within the existing definition, without adding schema fields.
    if "Translation" not in names and "Sentence Translation" not in names and content:
        definition += "<br>" + render_plain_content(content.translation)
    if "word_audio" not in names and sounds["word"]:
        definition += "<br>" + sounds["word"]
    presentation = card.content.presentation if card.content else None
    readings = {
        key: render_plain_content(value) if value else None
        for key, value in (
            presentation.model_dump(exclude={"source_id", "source_sha256"}) if presentation else {}
        ).items()
    }
    row = ExportCardRow(
        identity=ExportCardIdentity(
            language=card.language,
            source_type=source,
            job_id=card.deck_edition_id,
            item_key=card.card_id,
            lemma_key=card.parent_lexical_identity_id,
            sort_index=card.rank or 0,
        ),
        note_guid=card.note_guid,
        word=render_plain_content(card.display_text),
        front_of_card=render_plain_content(card.display_text),
        definitions=definition,
        example_sentence=render_plain_content(
            content.example_sentence
            if content
            else card.context_cue
            if card.role == "important_form"
            else "Prototype only; example not provided."
        ),
        translation=render_plain_content(content.translation if content else ""),
        word_audio=sounds["word"],
        sentence_audio=sounds["sentence"],
        **readings,
    )
    qfmt = template.front
    definition_field = "Definitions" if "Definitions" in names else "Definition"
    if card.role == "reverse":
        if "word_audio" not in names:
            raise ValueError("reverse role requires a source contract with word_audio")
        qfmt = "{{" + definition_field + "}}"
    elif card.role == "listening":
        if not sounds["word"]:
            raise ValueError("listening card requires exact audio")
        if "word_audio" not in names:
            raise ValueError("listening role requires a source contract with word_audio")
        qfmt = "{{word_audio}}"
    elif card.role == "cloze":
        if not card.content:
            raise ValueError("cloze requires content with a verified target span")
        span = validate_target_span(
            card.content.target_evidence, content.example_sentence, card.display_text
        )
        if span is None:
            raise ValueError("cloze requires a verified target span")
        start, end = span
        marked_sentence = (
            render_plain_content(content.example_sentence[:start])
            + '<span class="semantic-cloze-target">'
            + render_plain_content(content.example_sentence[start:end])
            + "</span>"
            + render_plain_content(content.example_sentence[end:])
        )
        row = row.model_copy(update={"example_sentence": marked_sentence})
        sentence_field = "Example Sentence" if "Example Sentence" in names else "Sentence"
        qfmt = (
            '<div class="semantic-cloze-prompt">{{' + sentence_field + "}}</div>"
            "<style>.semantic-cloze-prompt .semantic-cloze-target{font-size:0}"
            '.semantic-cloze-prompt .semantic-cloze-target::after{content:"[…]";font-size:22px}</style>'
        )
    role = card.role if card.role in {"reverse", "listening", "cloze"} else "recognition"
    afmt = (
        template.back
        if role == "recognition"
        else template.back.replace("{{FrontSide}}", template.front)
    )
    model = genanki.Model(
        native_anki_model_id(language=card.language.value, source_type=source, role=role),
        f"Multilang::Semantic::{card.language.value}::{source}::{role}",
        fields=[{"name": name} for name in names],
        templates=[{"name": "Card 1", "qfmt": qfmt, "afmt": afmt}],
        css=template.css,
    )
    return model, [str(value) for value in row.ordered_field_mapping().values()], media
