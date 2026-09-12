"""Semantic projection and explicitly unapproved A/B Anki prototypes."""

from __future__ import annotations

import csv
import sqlite3
import zipfile
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from tempfile import TemporaryDirectory

import genanki

from multilang.domain.anki_semantics import (
    SemanticCard,
    SemanticExportResult,
    SemanticManifestEntry,
    TopologyDecision,
)
from multilang.domain.content import canonical_content_hash
from multilang.services.anki_id_registry import (
    ANKI_ID_REGISTRY,
    AnkiIdKind,
    native_anki_deck_id,
    registry_id,
    validate_anki_id_registry,
)
from multilang.services.native_audio import audio_artifact_hash, reusable_audio_version
from multilang.services.native_content import render_plain_content, validate_target_span


def project_cards(
    *,
    identities: Iterable[object],
    approved_forms: Iterable[object] = (),
    ranks: Mapping[str, int],
    deck_edition_id: str,
    inventory: str = "core",
    namespace: str = "core",
    optional_roles: tuple[str, ...] = (),
) -> tuple[SemanticCard, ...]:
    if set(optional_roles) - {"reverse", "listening", "cloze"} or len(set(optional_roles)) != len(
        optional_roles
    ):
        raise ValueError("unsupported or duplicate optional card role")
    parents: dict[str, SemanticCard] = {}
    cards: list[SemanticCard] = []
    for identity in identities:
        identity_id = identity.lexical_identity_id
        if identity_id in parents:
            raise ValueError("duplicate lexical identity")
        card = SemanticCard(
            parent_lexical_identity_id=identity_id,
            language=identity.language,
            parent_lemma=identity.normalized_lemma,
            sense_id=identity.sense_id,
            role="headword",
            display_text=identity.normalized_lemma,
            context_cue=f"{identity.normalized_lemma}: {identity.sense_id}",
            inventory=inventory,
            rank=ranks.get(identity_id),
            deck_edition_id=deck_edition_id,
            namespace=namespace,
        )
        parents[identity_id] = card
        cards.append(card)
    for selection in approved_forms:
        form = selection.form
        parent = parents.get(form.lexical_identity_id)
        if parent is None:
            raise ValueError("approved form references missing parent identity")
        if not form.context:
            raise ValueError("important form requires unambiguous context cue")
        cards.append(
            SemanticCard(
                parent_lexical_identity_id=parent.parent_lexical_identity_id,
                language=parent.language,
                parent_lemma=parent.parent_lemma,
                sense_id=parent.sense_id,
                role="important_form",
                display_text=form.text,
                context_cue=form.context,
                surface_form_id=form.surface_form_id,
                morphological_analysis_id=form.analysis.morphological_analysis_id,
                inventory=parent.inventory,
                rank=parent.rank,
                deck_edition_id=parent.deck_edition_id,
                namespace=parent.namespace,
                prerequisite_card_id=parent.card_id,
            )
        )
    for parent in parents.values():
        for role in optional_roles:
            cards.append(
                SemanticCard.model_validate(
                    parent.model_dump(mode="json")
                    | {"role": role, "prerequisite_card_id": parent.card_id}
                )
            )
    cards.sort(
        key=lambda card: (
            card.language.value,
            card.rank or 1000000,
            card.parent_lexical_identity_id,
            card.role != "headword",
            card.card_id,
        )
    )
    validate_semantic_cards(cards, require_full_core=False)
    return tuple(cards)


def validate_semantic_cards(
    cards: Iterable[SemanticCard], *, require_full_core: bool = True
) -> None:
    cards = tuple(cards)
    ids: set[str] = set()
    parents = {
        (card.parent_lexical_identity_id, card.namespace): card
        for card in cards
        if card.role == "headword"
    }
    core: dict[str, list[SemanticCard]] = defaultdict(list)
    for unvalidated in cards:
        card = SemanticCard.model_validate(unvalidated.model_dump(mode="json"))
        if card.card_id in ids:
            raise ValueError("duplicate semantic card identity")
        ids.add(card.card_id)
        if card.role != "headword":
            parent = parents.get((card.parent_lexical_identity_id, card.namespace))
            if (
                parent is None
                or card.destination != parent.destination
                or card.inventory != parent.inventory
                or card.rank != parent.rank
                or card.sense_id != parent.sense_id
                or card.parent_lemma != parent.parent_lemma
                or card.language != parent.language
            ):
                raise ValueError("card form/optional destination must match parent")
            if (
                card.prerequisite_card_id != parent.card_id
                or card.deck_edition_id != parent.deck_edition_id
            ):
                raise ValueError("card prerequisite/edition must match parent")
        if card.inventory == "core" and card.role == "headword":
            core[card.language.value].append(card)
    if require_full_core:
        for headwords in core.values():
            if len(headwords) != 3000 or {card.rank for card in headwords} != set(range(1, 3001)):
                raise ValueError(
                    "Core requires exactly 3000 identities and 1000 in each real level"
                )


def summarize_cards(cards: Iterable[SemanticCard]) -> dict[str, dict[str, int]]:
    report: dict[str, dict[str, int]] = {}
    for card in cards:
        keys = [card.inventory, f"{card.language.value}:{card.inventory}"]
        if card.inventory == "core":
            keys.append(f"core:level:{card.level}")
            keys.append(f"{card.language.value}:core:level:{card.level}")
        for key in keys:
            group = report.setdefault(
                key,
                {
                    "identities": 0,
                    "headwords": 0,
                    "important_forms": 0,
                    "reverse": 0,
                    "listening": 0,
                    "cloze": 0,
                    "total": 0,
                },
            )
            group["total"] += 1
            if card.role == "headword":
                group["identities"] += 1
                group["headwords"] += 1
            elif card.role == "important_form":
                group["important_forms"] += 1
            else:
                group[card.role] += 1
    return report


def _render_card(card: SemanticCard, *, prototype: bool) -> tuple[str, str, list[Path]]:
    media: list[Path] = []
    if card.content is None:
        if card.role == "cloze":
            raise ValueError("cloze requires content with a verified target span")
        if not prototype:
            raise ValueError("production card requires approved content")
        front = render_plain_content(
            card.display_text if card.role == "headword" else card.context_cue
        )
        back = render_plain_content(
            f"Prototype only: {card.parent_lemma} / {card.display_text} / {card.sense_id}"
        )
        return front, back, media
    content = card.content.content
    if not prototype and card.content.review_status != "approved":
        raise ValueError("production card requires independently approved content")
    word_sound = ""
    sentence_sound = ""
    for asset in (card.word_audio, card.sentence_audio):
        if asset is None:
            if not prototype:
                raise ValueError("production card requires exact word and sentence audio")
            continue
        if not reusable_audio_version(asset.signature, asset, namespace=card.namespace):
            raise ValueError("audio artifact integrity failed")
        if not prototype and asset.review_status != "approved":
            raise ValueError("production audio requires approved review/license evidence")
        path = Path(asset.storage_path)
        media.append(path)
        if asset is card.word_audio:
            word_sound = f"[sound:{path.name}]"
        else:
            sentence_sound = f"[sound:{path.name}]"
    front = render_plain_content(card.display_text if card.role == "headword" else card.context_cue)
    back = "<br>".join(
        render_plain_content(value)
        for value in (
            card.display_text,
            content.definition,
            content.example_sentence,
            content.translation,
            f"Lemma: {card.parent_lemma}",
            f"Role: {card.role}",
            f"Analysis: {card.morphological_analysis_id or 'headword'}",
            f"Sense: {card.sense_id}",
        )
    )
    back += "<br>" + word_sound + "<br>" + sentence_sound
    if card.role == "reverse":
        front = render_plain_content(content.definition)
    elif card.role == "listening":
        if not word_sound:
            raise ValueError("listening card requires exact audio")
        front = word_sound
    elif card.role == "cloze":
        span = validate_target_span(
            card.content.target_evidence, content.example_sentence, card.display_text
        )
        if span is None:
            raise ValueError("cloze requires a verified target span")
        start, end = span
        front = render_plain_content(
            content.example_sentence[:start] + "[…]" + content.example_sentence[end:]
        )
    return front, back, media


def export_semantic_anki(
    *,
    cards: Iterable[SemanticCard],
    output_path: Path,
    model: str,
    prototype: bool = False,
    decision: TopologyDecision | None = None,
    evidence_verifier: Callable[[TopologyDecision], bool] | None = None,
) -> SemanticExportResult:
    if model not in {"A", "B"}:
        raise ValueError("unknown Anki topology")
    if not prototype:
        if decision is None:
            raise ValueError(
                "ANKI-01 topology remains unselected without signed real-client evidence"
            )
        decision.require_verified(evidence_verifier)
        if decision.selected_model != model:
            raise ValueError("ANKI-01 rejected model cannot be a production fallback")
    cards = tuple(cards)
    if not cards:
        raise ValueError("cannot export empty semantic edition")
    validate_semantic_cards(cards, require_full_core=not prototype)
    if len({card.namespace for card in cards}) != 1:
        raise ValueError("cannot mix private and shared namespaces in one package")
    validate_anki_id_registry(ANKI_ID_REGISTRY)
    decks = {
        card.destination: genanki.Deck(native_anki_deck_id(card.destination), card.destination)
        for card in cards
    }
    families: dict[str, list[SemanticCard]] = defaultdict(list)
    for card in cards:
        families[card.parent_lexical_identity_id].append(card)
    for family in families.values():
        family.sort(key=lambda card: (card.role != "headword", card.card_id))
    slots = max(len(family) for family in families.values()) if model == "A" else 1
    registered_model = (
        registry_id(family="native_prototype", role="family_model", kind=AnkiIdKind.MODEL)
        if model == "A"
        else registry_id(family="native_prototype", role="separate_model", kind=AnkiIdKind.MODEL)
    )
    fields = [
        {"name": name} for index in range(slots) for name in (f"Front{index}", f"Back{index}")
    ]
    fields.append({"name": "Image"})
    templates = [
        {
            "name": f"Semantic {index}",
            "qfmt": "{{#Front"
            + str(index)
            + "}}{{Front"
            + str(index)
            + "}}{{/Front"
            + str(index)
            + "}}",
            "afmt": "{{FrontSide}}<hr>{{Back" + str(index) + "}}{{#Image}}<br>{{Image}}{{/Image}}",
        }
        for index in range(slots)
    ]
    note_model = genanki.Model(
        registered_model,
        f"Multilang::Native Prototype {model}",
        fields=fields,
        templates=templates,
        css=".card { font-family: sans-serif; font-size: 22px; }",
    )
    media: dict[str, Path] = {}
    manifest: list[SemanticManifestEntry] = []
    groups = (
        list(families.values())
        if model == "A"
        else [[card] for family in families.values() for card in family]
    )
    for group in groups:
        parent = group[0]
        note_guid = (
            canonical_content_hash(
                {
                    "family": parent.parent_lexical_identity_id,
                    "namespace": parent.namespace,
                    "schema": "1",
                }
            )[:32]
            if model == "A"
            else parent.note_guid
        )
        values = [""] * (slots * 2 + 1)
        for ordinal, card in enumerate(group):
            front, back, card_media = _render_card(card, prototype=prototype)
            values[ordinal * 2 : ordinal * 2 + 2] = [front, back]
            for path in card_media:
                if path.name in media and audio_artifact_hash(
                    media[path.name]
                ) != audio_artifact_hash(path):
                    raise ValueError("conflicting media basenames")
                media[path.name] = path
            manifest.append(
                SemanticManifestEntry(
                    card_id=card.card_id,
                    note_guid=note_guid,
                    template_ordinal=ordinal,
                    model_id=registered_model,
                    deck_id=decks[card.destination].deck_id,
                    destination=card.destination,
                    parent_lexical_identity_id=card.parent_lexical_identity_id,
                    role=card.role,
                    surface_form_id=card.surface_form_id,
                    morphological_analysis_id=card.morphological_analysis_id,
                    sense_id=card.sense_id,
                    context_cue=card.context_cue,
                    prerequisite_card_id=card.prerequisite_card_id,
                    inventory=card.inventory,
                    deck_edition_id=card.deck_edition_id,
                )
            )
        note = genanki.Note(
            model=note_model,
            fields=values,
            guid=note_guid,
            tags=["multilang", f"native_prototype_{model}"],
        )
        decks[parent.destination].add_note(note)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="native-anki-", dir=output_path.parent) as temporary:
        staged = Path(temporary) / "staged.apkg"
        package = genanki.Package(list(decks.values()))
        package.media_files = [str(path) for path in media.values()]
        package.write_to_file(str(staged))
        with zipfile.ZipFile(staged) as archive:
            database = Path(temporary) / "collection.anki2"
            database.write_bytes(archive.read("collection.anki2"))
        with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True) as connection:
            actual = connection.execute(
                "SELECT n.guid,c.ord,c.did FROM cards c JOIN notes n ON n.id=c.nid"
            ).fetchall()
        expected = {(entry.note_guid, entry.template_ordinal, entry.deck_id) for entry in manifest}
        if set(actual) != expected or len(actual) != len(manifest):
            raise ValueError("semantic APKG generated note/card/ordinal/deck manifest mismatch")
        staged.replace(output_path)
    result = SemanticExportResult(
        output_path=str(output_path),
        model=model,
        prototype=prototype,
        native_sibling_structure=model == "A",
        client_acceptance_proven=not prototype,
        manifest=tuple(manifest),
        artifact_sha256=audio_artifact_hash(output_path),
        composition_sha256=canonical_content_hash([entry.model_dump() for entry in manifest]),
    )
    output_path.with_suffix(".manifest.json").write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )
    for suffix, delimiter in ((".csv", ","), (".tsv", "\t")):
        with output_path.with_suffix(suffix).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(SemanticManifestEntry.model_fields),
                delimiter=delimiter,
            )
            writer.writeheader()
            for entry in manifest:
                values = entry.model_dump()
                # Spreadsheet manifests must not execute formula-like private cues.
                writer.writerow(
                    {
                        key: "'" + value
                        if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                        else value
                        for key, value in values.items()
                    }
                )
    return result
