"""Local, nonexportable previews of resolved machine lexical proposals.

The caller supplies mappings from a replayed draft/campaign and its language.
Mappings alone contain neither the language binding nor both review runs, so
this module cannot independently establish agreement or production authority.
"""

from __future__ import annotations

import base64
import hashlib
import html
from collections.abc import Sequence
from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.exporting import export_field_names_for_language_and_source
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256, normalize_identity_text
from multilang.services.qualification_machine_draft import MachineLexicalMapping


def _field_names(language: SupportedLanguage) -> tuple[str, ...]:
    return export_field_names_for_language_and_source(language=language, source_type="frequency")


def _content_fields(language: SupportedLanguage) -> tuple[str, str]:
    names = _field_names(language)
    return (
        next(name for name in ("word", "Target Word", "Word") if name in names),
        next(name for name in ("Definitions", "Definition") if name in names),
    )


def _verified_mapping(mapping: MachineLexicalMapping) -> MachineLexicalMapping:
    if not isinstance(mapping, MachineLexicalMapping):
        raise ValueError("preview requires complete machine lexical mappings")
    checked = MachineLexicalMapping.model_validate(mapping.model_dump(mode="json"))
    decision = checked.decision
    if decision.decision not in {"accepted", "corrected"} or decision.uncertainties:
        raise ValueError("preview requires resolved machine lexical mappings")
    if checked.item_id != decision.item_id:
        raise ValueError("preview mapping item identity mismatch")
    correction = (checked.original_lemma, checked.original_pos) != (
        decision.proposed_lemma,
        decision.proposed_pos,
    )
    if checked.source_correction_proposed != correction:
        raise ValueError("preview mapping source correction mismatch")
    normalize_identity_text(checked.original_lemma)
    normalize_identity_text(decision.proposed_lemma)
    return checked


def _identity(mapping: MachineLexicalMapping) -> tuple[str, str, str]:
    decision = mapping.decision
    return (
        normalize_identity_text(decision.proposed_lemma),
        decision.proposed_pos,
        decision.proposed_sense_id,
    )


def _group_mappings(mappings: Sequence[MachineLexicalMapping]):
    by_item, by_candidate, by_identity = {}, {}, {}
    for source in mappings:
        mapping = _verified_mapping(source)
        for key, lookup in ((mapping.item_id, by_item), (mapping.candidate_id, by_candidate)):
            if key in lookup and lookup[key] != mapping:
                raise ValueError("conflicting duplicate preview mapping")
        if mapping.item_id in by_item:
            continue
        by_item[mapping.item_id] = by_candidate[mapping.candidate_id] = mapping
        group = by_identity.setdefault(_identity(mapping), [])
        if group and (
            group[0].decision.proposed_lemma != mapping.decision.proposed_lemma
            or group[0].decision.proposed_gloss != mapping.decision.proposed_gloss
        ):
            raise ValueError("conflicting gloss or lemma for preview identity")
        group.append(mapping)
    return (
        tuple(
            tuple(sorted(by_identity[key], key=lambda item: item.item_id))
            for key in sorted(by_identity)
        ),
        len(by_item),
    )


class MachinePreviewMetadata(NativeContract):
    language: SupportedLanguage
    mappings: tuple[MachineLexicalMapping, ...] = Field(min_length=1, max_length=10000)
    origin: Literal["machine"] = "machine"
    production_eligible: Literal[False] = False
    exportable: Literal[False] = False
    content_status: Literal["preliminary_machine_lexical_proposal"] = (
        "preliminary_machine_lexical_proposal"
    )

    @model_validator(mode="after")
    def coherent_provenance(self):
        groups, count = _group_mappings(self.mappings)
        if len(groups) != 1 or count != len(self.mappings):
            raise ValueError("preview metadata requires one identity without duplicate mappings")
        object.__setattr__(self, "mappings", groups[0])
        return self

    @computed_field
    @property
    def sense_id(self) -> str:
        return self.mappings[0].decision.proposed_sense_id

    @computed_field
    @property
    def part_of_speech(self) -> str:
        return self.mappings[0].decision.proposed_pos

    @computed_field
    @property
    def preview_identity(self) -> str:
        # A local display identity, never a native LexicalIdentity or Anki GUID.
        return "machine-preview:" + canonical_sha256(
            [self.language.value, *_identity(self.mappings[0])]
        )

    @computed_field
    @property
    def field_status(self) -> dict[str, str]:
        word_field, definition_field = _content_fields(self.language)
        statuses = {name: "pending" for name in _field_names(self.language)}
        statuses[word_field] = "preliminary_machine_lemma"
        statuses[definition_field] = "preliminary_lexical_gloss"
        statuses["Image"] = "intentionally_empty"
        return statuses

    @computed_field
    @property
    def pending_requirements(self) -> tuple[str, ...]:
        return (
            "validated_definition",
            "grounded_pronunciation",
            "grounded_example_sentence",
            "validated_translation",
            "verified_word_audio",
            "verified_sentence_audio",
            "frequency_rank",
            "native_identity_and_profile_binding",
            "production_qualification",
        )


def _expected_fields(metadata: MachinePreviewMetadata) -> dict[str, str]:
    fields = {name: "" for name in _field_names(metadata.language)}
    word_field, definition_field = _content_fields(metadata.language)
    fields[word_field] = metadata.mappings[0].decision.proposed_lemma
    fields[definition_field] = metadata.mappings[0].decision.proposed_gloss
    return fields


class MachinePreviewCard(NativeContract):
    fields: dict[str, str] = Field(min_length=1, max_length=32)
    metadata: MachinePreviewMetadata

    @model_validator(mode="after")
    def only_preliminary_content(self):
        expected = _expected_fields(self.metadata)
        if self.fields != expected:
            raise ValueError("preview fields must contain only the exact proposed lemma and gloss")
        # JSON object ordering is not authoritative; restore the existing field order.
        object.__setattr__(self, "fields", expected)
        return self


class MachineCardPreview(NativeContract):
    schema_version: Literal["machine-card-preview-1"] = "machine-card-preview-1"
    origin: Literal["machine"] = "machine"
    language: SupportedLanguage
    language_binding: Literal["caller_declared"] = "caller_declared"
    production_eligible: Literal[False] = False
    exportable: Literal[False] = False
    limit: int = Field(default=10, ge=1, le=100, strict=True)
    source_mapping_count: int = Field(ge=0, le=10000, strict=True)
    available_cards: int = Field(ge=0, le=10000, strict=True)
    cards: tuple[MachinePreviewCard, ...] = Field(max_length=100)

    @model_validator(mode="after")
    def coherent_preview(self):
        if len(self.cards) != min(self.limit, self.available_cards):
            raise ValueError("preview limit/card counts mismatch")
        if self.source_mapping_count < self.available_cards:
            raise ValueError("preview source mapping count mismatch")
        if any(card.metadata.language != self.language for card in self.cards):
            raise ValueError("preview language mismatch")
        if len({card.metadata.preview_identity for card in self.cards}) != len(self.cards):
            raise ValueError("duplicate preview identity")
        _, visible_mapping_count = _group_mappings(
            tuple(mapping for card in self.cards for mapping in card.metadata.mappings)
        )
        if self.source_mapping_count < visible_mapping_count + self.available_cards - len(
            self.cards
        ):
            raise ValueError("preview source mapping count does not cover displayed provenance")
        return self

    @computed_field
    @property
    def field_names(self) -> tuple[str, ...]:
        return _field_names(self.language)

    @computed_field
    @property
    def omitted_cards(self) -> int:
        return self.available_cards - len(self.cards)

    @computed_field
    @property
    def preview_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def build_machine_card_preview(
    mappings: Sequence[MachineLexicalMapping],
    *,
    language: SupportedLanguage | str,
    limit: int = 10,
) -> MachineCardPreview:
    """Display resolved proposals; never generate content, media or export receipts."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("preview limit must be an integer from 1 to 100")
    if not isinstance(mappings, Sequence) or len(mappings) > 10000:
        raise ValueError("preview requires a bounded sequence of at most 10000 mappings")
    language = SupportedLanguage(language)
    groups, count = _group_mappings(mappings)
    cards = []
    for group in groups[:limit]:
        metadata = MachinePreviewMetadata(language=language, mappings=group)
        cards.append(MachinePreviewCard(fields=_expected_fields(metadata), metadata=metadata))
    return MachineCardPreview(
        language=language,
        limit=limit,
        source_mapping_count=count,
        available_cards=len(groups),
        cards=tuple(cards),
    )


def render_machine_card_preview(
    preview: MachineCardPreview, *, conflicting_mapping_count: int = 0
) -> str:
    """Render escaped static HTML with no scripts, URLs, media or external resources."""
    preview = MachineCardPreview.model_validate(preview.model_dump(mode="json"))
    if type(conflicting_mapping_count) is not int or not 0 <= conflicting_mapping_count <= 10000:
        raise ValueError("preview conflict count must be a bounded integer")
    sections = []
    for index, card in enumerate(preview.cards, 1):
        rows = "".join(
            '<tr><th scope="row">'
            + html.escape(name)
            + "</th><td><pre>"
            + html.escape(value)
            + "</pre></td><td>"
            + html.escape(card.metadata.field_status[name])
            + "</td></tr>"
            for name, value in card.fields.items()
        )
        pending = "".join(
            "<li>" + html.escape(requirement) + "</li>"
            for requirement in card.metadata.pending_requirements
        )
        provenance = html.escape(card.metadata.model_dump_json(indent=2))
        sections.append(
            "<section><h2>Cartão preliminar " + str(index) + "</h2>"
            "<p>Sentido proposto: " + html.escape(card.metadata.sense_id) + "</p>"
            "<table><thead><tr><th>Campo</th><th>Conteúdo preliminar</th><th>Estado</th>"
            "</tr></thead><tbody>" + rows + "</tbody></table>"
            "<h3>Pendências</h3><ul>" + pending + "</ul>"
            "<details><summary>Proveniência e metadados</summary><pre>"
            + provenance
            + "</pre></details></section>"
        )
    style = (
        "body{font:17px/1.6 system-ui,sans-serif;max-width:68rem;margin:2rem auto;"
        "padding:0 1rem;color:#17232c;background:#fafbf9}"
        "section{border-top:1px solid #cbd5cf;padding:1rem 0}"
        "table{width:100%;border-collapse:collapse}th,td{border:1px solid #cbd5cf;"
        "padding:.5rem;text-align:left;vertical-align:top}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.85rem}"
        "summary{cursor:pointer}"
    )
    style_hash = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    return (
        '<!doctype html><html lang="pt"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "style-src 'sha256-" + style_hash + "'; base-uri 'none'; form-action 'none'\">"
        "<title>Prévia local de cartões</title><style>" + style + "</style></head><body>"
        "<h1>Rascunho de máquina — não exportável</h1>"
        "<p>Esta prévia local contém somente lema e gloss lexical preliminares. "
        "A gloss lexical não é uma definição didática validada. "
        "A prévia não representa revisão humana, aprovação de produção ou pacote Anki.</p>"
        "<p>Idioma declarado pelo chamador: "
        + html.escape(preview.language.value)
        + ". Os mapeamentos isolados não comprovam idioma nem acordo entre revisores.</p>"
        "<p>Cartões exibidos: "
        + str(len(preview.cards))
        + " de "
        + str(preview.available_cards)
        + "; omitidos pelo limite: "
        + str(preview.omitted_cards)
        + ".</p>"
        + (
            "<p>Mapeamentos em conflito, fora da prévia: "
            + str(conflicting_mapping_count)
            + ". As propostas completas e seus motivos estão preservados em draft.json.</p>"
            if conflicting_mapping_count
            else ""
        )
        + (
            "".join(sections)
            if sections
            else "<p>Nenhum cartão resolvido disponível para prévia.</p>"
        )
        + "</body></html>"
    )


__all__ = [
    "MachineCardPreview",
    "MachinePreviewCard",
    "MachinePreviewMetadata",
    "build_machine_card_preview",
    "render_machine_card_preview",
]
