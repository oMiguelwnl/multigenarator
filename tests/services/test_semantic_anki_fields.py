"""Inspect field compatibility in actual semantic APKG collections."""

import json
import sqlite3
import zipfile
from hashlib import sha256

import pytest

from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.content import (
    ContentRequest,
    ContentVersion,
    GeneratedContent,
    TargetMatchEvidence,
)
from multilang.domain.exporting import export_field_names_for_language_and_source
from multilang.services.card_template_loader import load_card_template
from multilang.services.semantic_anki import export_semantic_anki


def family(language="en", *, inventory="core", presentation=None):
    words = {
        "en": ("be", "was", "were"),
        "pt": ("ser", "fui", "era"),
        "ja": ("行く", "行った", "行きます"),
        "zh": ("看", "看了", "看过"),
        "ko": ("가다", "갔다", "가요"),
    }[language]
    cards = []
    for index, word in enumerate(words):
        card = SemanticCard(
            parent_lexical_identity_id=f"lex:{language}",
            language=language,
            parent_lemma=words[0],
            sense_id="source-sense-123",
            role="important_form" if index else "headword",
            display_text=word,
            context_cue=f"Context {word}.",
            inventory=inventory,
            rank=1,
            namespace="user:fixture" if inventory in {"custom", "highlight"} else "core",
            deck_edition_id="fixture-1",
            **(
                {
                    "surface_form_id": f"surface:{index}",
                    "morphological_analysis_id": f"analysis:{index}",
                    "prerequisite_card_id": cards[0].card_id,
                }
                if index
                else {}
            ),
        )
        request = ContentRequest(
            lexical_identity_id=card.parent_lexical_identity_id,
            card_id=card.card_id,
            language=language,
            language_profile_version="1",
            lemma=words[0],
            display_text=word,
            sense_id=card.sense_id,
            morphological_analysis_id=card.morphological_analysis_id,
            context_cue=card.context_cue,
            namespace=card.namespace,
            deck_edition_id=card.deck_edition_id,
            grounding_sha256="a" * 64,
            target_concept_id="meaning",
        )
        payload = dict(
            request=request,
            content=GeneratedContent(
                definition="Contextual meaning & use.",
                example_sentence=f"Context {word}.",
                translation="Translated context.",
                explanation="Past tense in this context." if index else "Base form.",
            ),
            target_evidence=TargetMatchEvidence(
                lexical_identity_id=card.parent_lexical_identity_id,
                sense_id=card.sense_id,
                morphological_analysis_id=card.morphological_analysis_id,
                target_concept_id="meaning",
                matched=True,
                observed_concept_ids=("meaning",),
                analyzer_version="fixture",
                evidence_sha256="b" * 64,
            ),
            provider="fixture",
            model_version="1",
        )
        if presentation is not None:
            payload["presentation"] = presentation
        cards.append(
            SemanticCard.model_validate(card.model_dump() | {"content": ContentVersion(**payload)})
        )
    return tuple(cards)


def inspect_package(path, tmp_path):
    with zipfile.ZipFile(path) as archive:
        db = tmp_path / (path.stem + ".sqlite")
        db.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(db) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        notes = {
            guid: (models[str(mid)], fields.split("\x1f"))
            for guid, mid, fields in connection.execute("select guid,mid,flds from notes")
        }
    return notes


@pytest.mark.parametrize("language", ["en", "pt", "ko"])
def test_real_package_preserves_exact_fields_meaning_and_template(tmp_path, language):
    cards = family(language)
    path = tmp_path / f"{language}.apkg"
    result = export_semantic_anki(cards=cards, output_path=path, model="B", prototype=True)
    notes = inspect_package(path, tmp_path)
    expected = export_field_names_for_language_and_source(
        language=language, source_type="frequency"
    )
    for card in cards:
        model, values = notes[card.note_guid]
        assert tuple(field["name"] for field in model["flds"]) == expected
        mapping = dict(zip(expected, values, strict=True))
        assert mapping["word"] == card.display_text
        assert mapping["Definitions"].startswith("Contextual meaning &amp; use.")
        assert card.content.content.explanation in mapping["Definitions"]
        assert mapping["Image"] == ""
        assert all(
            secret not in " ".join(values) for secret in (card.card_id, card.sense_id, "analysis:")
        )
        template = load_card_template(source_type="frequency", language=card.language)
        assert model["tmpls"][0]["qfmt"] == template.front
        assert model["tmpls"][0]["afmt"] == template.back
    assert not result.client_acceptance_proven


@pytest.mark.parametrize(
    "language,presentation,checks",
    [
        ("en", {"ipa": "biː"}, {"IPA": "biː"}),
        (
            "ja",
            {
                "word_reading": "行[い]く",
                "word_romaji": "iku",
                "sentence_furigana": "行[い]く。",
                "sentence_romaji": "Iku.",
            },
            {
                "Word Reading": "行[い]く",
                "Word Romaji": "iku",
                "Sentence Furigana": "行[い]く。",
                "Sentence Romaji": "Iku.",
            },
        ),
        (
            "zh",
            {
                "mandarin_word_pinyin": "kàn",
                "mandarin_word_traditional": "看",
                "mandarin_sentence_pinyin": "Kàn.",
                "mandarin_sentence_traditional": "看。",
            },
            {
                "Pinyin": "kàn",
                "Traditional": "看",
                "Sentence Pinyin": "Kàn.",
                "Traditional Sentence": "看。",
            },
        ),
    ],
)
def test_source_backed_readings_survive_in_existing_fields(
    tmp_path, language, presentation, checks
):
    cards = family(
        language,
        presentation=presentation | {"source_id": "fixture-lexicon", "source_sha256": "c" * 64},
    )[:1]
    path = tmp_path / f"{language}.apkg"
    export_semantic_anki(cards=cards, output_path=path, model="B", prototype=True)
    model, values = inspect_package(path, tmp_path)[cards[0].note_guid]
    names = tuple(field["name"] for field in model["flds"])
    assert names == export_field_names_for_language_and_source(
        language=language, source_type="frequency"
    )
    mapping = dict(zip(names, values, strict=True))
    assert all(mapping[key] == value for key, value in checks.items())
    assert mapping["Target Word" if language == "ja" else "word"] == cards[0].display_text


def test_presentation_is_hash_bound_without_changing_old_content_hashes():
    from multilang.domain.content import canonical_content_hash

    old = family()[0].content
    assert "presentation" not in old.model_dump(mode="json")
    assert old.version_id == "content:1:" + canonical_content_hash(old.model_dump(mode="json"))
    new = family(presentation={"ipa": "biː", "source_id": "dictionary", "source_sha256": "a" * 64})[
        0
    ].content
    assert old.version_id != new.version_id
    with pytest.raises(ValueError):
        ContentVersion.model_validate(old.model_dump() | {"presentation": {"ipa": "invented"}})


@pytest.mark.parametrize("language", ["ja", "zh"])
def test_missing_required_language_readings_fail_closed(tmp_path, language):
    with pytest.raises(ValueError, match="require"):
        export_semantic_anki(
            cards=family(language), output_path=tmp_path / "missing.apkg", model="B", prototype=True
        )
    assert not (tmp_path / "missing.apkg").exists()


def add_audio(card, tmp_path):
    from multilang.domain.audio_version import AudioVersion, PronunciationSignature

    assets = {}
    for kind, text in (
        ("word", card.display_text),
        ("sentence", card.content.content.example_sentence),
    ):
        path = tmp_path / f"{card.note_guid}-{kind}.mp3"
        path.write_bytes(f"synthetic-fixture:{kind}:{text}".encode())
        assets[f"{kind}_audio"] = AudioVersion(
            signature=PronunciationSignature(
                language=card.language.value,
                language_profile_version="1",
                display_text=text,
                normalized_text=text,
                contextual_reading=text,
                context=card.context_cue,
                sense_id=card.sense_id,
                morphological_analysis_id=card.morphological_analysis_id,
                locale="ko-KR" if card.language.value == "ko" else "en-US",
                voice_id="fixture",
                ssml="<speak>fixture</speak>",
                pronunciation_policy_version="1",
                provider="azure",
                provider_model_version="synthetic-fixture",
                audio_format="audio-24khz-48kbitrate-mono-mp3",
                asset_kind=kind,
            ),
            namespace=card.namespace,
            storage_path=str(path),
            artifact_sha256=sha256(path.read_bytes()).hexdigest(),
            byte_size=path.stat().st_size,
        )
    return SemanticCard.model_validate(card.model_dump() | assets)


def test_exact_audio_for_headword_and_two_forms_is_packaged(tmp_path):
    cards = tuple(add_audio(card, tmp_path) for card in family())
    path = tmp_path / "audio.apkg"
    export_semantic_anki(cards=cards, output_path=path, model="B", prototype=True)
    notes = inspect_package(path, tmp_path)
    with zipfile.ZipFile(path) as archive:
        media = json.loads(archive.read("media"))
        by_name = {name: archive.read(key) for key, name in media.items()}
    assert len(by_name) == 6
    for card in cards:
        model, values = notes[card.note_guid]
        fields = dict(zip((field["name"] for field in model["flds"]), values, strict=True))
        for kind in ("word", "sentence"):
            asset = getattr(card, f"{kind}_audio")
            from pathlib import Path

            asset_path = Path(asset.storage_path)
            assert fields[f"{kind}_audio"] == f"[sound:{asset_path.name}]"
            assert by_name[asset_path.name] == asset_path.read_bytes()


def test_dynamic_forms_reexport_and_multilingual_models_preserve_identity(tmp_path):
    original = family()
    first = export_semantic_anki(
        cards=original[:2], output_path=tmp_path / "first.apkg", model="B", prototype=True
    )
    changed = []
    for card in original:
        payload = card.model_dump()
        payload.update(rank=1010, deck_edition_id="fixture-2")
        payload["content"]["request"]["deck_edition_id"] = "fixture-2"
        payload["content"]["content"]["definition"] = "Revised contextual meaning."
        changed.append(SemanticCard.model_validate(payload))
    second = export_semantic_anki(
        cards=(*changed, *family("pt")),
        output_path=tmp_path / "second.apkg",
        model="B",
        prototype=True,
    )
    stable = {
        entry.card_id: (entry.note_guid, entry.model_id, entry.template_ordinal)
        for entry in second.manifest
    }
    assert all(
        stable[entry.card_id] == (entry.note_guid, entry.model_id, entry.template_ordinal)
        for entry in first.manifest
    )
    assert len(second.manifest) == 6
    assert len({entry.model_id for entry in second.manifest}) == 2
    assert all(
        entry.destination.endswith("Level 2")
        for entry in second.manifest
        if entry.parent_lexical_identity_id == "lex:en"
    )


@pytest.mark.parametrize(
    "inventory,source", [("custom", "word-list"), ("highlight", "kindle-highlights")]
)
def test_personal_models_keep_exact_source_fields_and_all_content(tmp_path, inventory, source):
    card = add_audio(family(inventory=inventory)[0], tmp_path)
    path = tmp_path / "personal.apkg"
    export_semantic_anki(cards=(card,), output_path=path, model="B", prototype=True)
    model, values = inspect_package(path, tmp_path)[card.note_guid]
    names = tuple(field["name"] for field in model["flds"])
    assert names == export_field_names_for_language_and_source(language="en", source_type=source)
    fields = dict(zip(names, values, strict=True))
    assert fields["Word"] == "be"
    assert "Translated context." in fields["Definition"]
    assert f"[sound:{card.note_guid}-word.mp3]" in fields["Definition"]


@pytest.mark.parametrize(
    "text", ["<script>alert(1)</script>", "[sound:injected.mp3]", "unsafe\x1fextra"]
)
def test_unsafe_presentation_cannot_reach_package(tmp_path, text):
    cards = family(presentation={"ipa": text, "source_id": "fixture", "source_sha256": "a" * 64})
    with pytest.raises(ValueError):
        export_semantic_anki(
            cards=cards, output_path=tmp_path / "unsafe.apkg", model="B", prototype=True
        )
    assert not (tmp_path / "unsafe.apkg").exists()


@pytest.mark.parametrize("role", ["reverse", "listening"])
def test_optional_roles_answer_reuses_full_card_without_losing_target(tmp_path, role):
    head = family()[0]
    data = head.model_dump()
    data.update(role=role, prerequisite_card_id=head.card_id)
    data["content"] = None
    card = SemanticCard.model_validate(data)
    content = head.content.model_dump()
    content["request"]["card_id"] = card.card_id
    card = add_audio(
        SemanticCard.model_validate(card.model_dump() | {"content": content}), tmp_path
    )
    path = tmp_path / f"{role}.apkg"
    export_semantic_anki(cards=(head, card), output_path=path, model="B", prototype=True)
    model, _ = inspect_package(path, tmp_path)[card.note_guid]
    assert "{{word}}" in model["tmpls"][0]["afmt"]


def test_family_topology_remains_explicitly_field_incompatible(tmp_path):
    result = export_semantic_anki(
        cards=family(), output_path=tmp_path / "A.apkg", model="A", prototype=True
    )
    assert not result.field_contract_compatible
    assert not result.client_acceptance_proven


@pytest.mark.parametrize('inventory', ['custom', 'highlight'])
def test_reverse_rejects_source_fields_that_expose_answer_audio(tmp_path, inventory):
    head = family(inventory=inventory)[0]
    data = head.model_dump()
    data.update(role='reverse', prerequisite_card_id=head.card_id, content=None)
    card = SemanticCard.model_validate(data)
    content = head.content.model_dump()
    content['request']['card_id'] = card.card_id
    card = add_audio(SemanticCard.model_validate(card.model_dump() | {'content': content}), tmp_path)
    with pytest.raises(ValueError, match='reverse role requires a source contract with word_audio'):
        export_semantic_anki(cards=(head, card), output_path=tmp_path/'reverse.apkg',
                             model='B', prototype=True)
    assert not (tmp_path/'reverse.apkg').exists()


def test_cloze_keeps_fields_and_marks_only_verified_span(tmp_path):
    head = family()[0]
    card = SemanticCard.model_validate(
        head.model_dump() | {"role": "cloze", "content": None, "prerequisite_card_id": head.card_id}
    )
    content = head.content.model_dump()
    content["request"]["card_id"] = card.card_id
    content["content"]["example_sentence"] = "They will be before us."
    content["target_evidence"]["target_span"] = (10, 12)
    card = SemanticCard.model_validate(card.model_dump() | {"content": content})
    path = tmp_path / "cloze.apkg"
    export_semantic_anki(cards=(head, card), output_path=path, model="B", prototype=True)
    model, values = inspect_package(path, tmp_path)[card.note_guid]
    fields = dict(zip((field["name"] for field in model["flds"]), values, strict=True))
    assert (
        fields["Example Sentence"]
        == 'They will <span class="semantic-cloze-target">be</span> before us.'
    )
    assert "{{Example Sentence}}" in model["tmpls"][0]["qfmt"]
    assert "{{word}}" in model["tmpls"][0]["afmt"]
    assert fields["word"] == "be"


def test_form_phonetics_are_not_replaced_by_parent_reading(tmp_path):
    cards = []
    for card, ipa in zip(family(), ("biː", "wɒz", "wɜː"), strict=True):
        payload = card.model_dump()
        payload["content"]["presentation"] = {
            "ipa": ipa,
            "source_id": "dictionary",
            "source_sha256": "a" * 64,
        }
        cards.append(SemanticCard.model_validate(payload))
    path = tmp_path / "phonetics.apkg"
    export_semantic_anki(cards=cards, output_path=path, model="B", prototype=True)
    notes = inspect_package(path, tmp_path)
    for card, ipa in zip(cards, ("biː", "wɒz", "wɜː"), strict=True):
        model, values = notes[card.note_guid]
        fields = dict(zip((field["name"] for field in model["flds"]), values, strict=True))
        assert fields["IPA"] == ipa


def test_cloze_unicode_sentence_and_audio_survive_trusted_span_markup(tmp_path):
    from html import unescape

    head = family("ko")[0]
    card = SemanticCard.model_validate(
        head.model_dump() | {"role": "cloze", "content": None, "prerequisite_card_id": head.card_id}
    )
    content = head.content.model_dump()
    content["request"]["card_id"] = card.card_id
    sentence = "“가다” & 가다."
    content["content"]["example_sentence"] = sentence
    content["target_evidence"]["target_span"] = (7, 9)
    card = add_audio(
        SemanticCard.model_validate(card.model_dump() | {"content": content}), tmp_path
    )
    path = tmp_path / "unicode-cloze.apkg"
    export_semantic_anki(cards=(head, card), output_path=path, model="B", prototype=True)
    model, values = inspect_package(path, tmp_path)[card.note_guid]
    fields = dict(zip((field["name"] for field in model["flds"]), values, strict=True))
    marked = fields["Example Sentence"]
    assert marked.count('<span class="semantic-cloze-target">') == 1
    assert "&amp;" in marked
    assert (
        unescape(marked.replace('<span class="semantic-cloze-target">', "").replace("</span>", ""))
        == sentence
    )
    assert fields["sentence_audio"] == f"[sound:{card.note_guid}-sentence.mp3]"


def test_prototype_a_does_not_put_technical_identifiers_on_cards(tmp_path):
    path = tmp_path / "A.apkg"
    cards = family()
    export_semantic_anki(cards=cards, output_path=path, model="A", prototype=True)
    notes = inspect_package(path, tmp_path)
    for _, values in notes.values():
        assert "source-sense-123" not in " ".join(values)
        assert "analysis:" not in " ".join(values)


def test_manifest_retains_immutable_content_and_audio_versions(tmp_path):
    card = add_audio(family()[0], tmp_path)
    result = export_semantic_anki(
        cards=(card,), output_path=tmp_path / "versioned.apkg", model="B", prototype=True
    )
    entry = result.manifest[0].model_dump()
    assert entry["content_version_id"] == card.content.version_id
    assert entry["word_audio_version_id"] == card.word_audio.version_id
    assert entry["sentence_audio_version_id"] == card.sentence_audio.version_id


def test_unenriched_prototype_does_not_display_internal_headword_cue(tmp_path):
    head = family()[0]
    card = SemanticCard.model_validate(head.model_dump() | {"content": None, "context_cue": "be: source-sense-123"})
    path = tmp_path / "placeholder.apkg"
    export_semantic_anki(cards=(card,), output_path=path, model="B", prototype=True)
    _, values = inspect_package(path, tmp_path)[card.note_guid]
    assert "source-sense-123" not in " ".join(values)
