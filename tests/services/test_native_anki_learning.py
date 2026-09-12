import json
import sqlite3
import zipfile
from hashlib import sha256

import pytest


def test_unknown_topology_version_cannot_authorize_the_current_exporter():
    from multilang.domain.anki_semantics import TopologyDecision

    with pytest.raises(ValueError, match="topology_version"):
        TopologyDecision(
            selected_model="B",
            topology_version="future-unimplemented",
            evidence=(),
            signer="fixture",
            decision_receipt_sha256="a" * 64,
            nonconcurrent_mechanism="explicit prerequisite queue",
        )


def cards_fixture():
    from multilang.domain.anki_semantics import SemanticCard

    base = {
        "parent_lexical_identity_id": "lex:be",
        "language": "en",
        "parent_lemma": "be",
        "sense_id": "exist",
        "inventory": "core",
        "rank": 1,
        "deck_edition_id": "en-1",
        "namespace": "core",
    }
    head = SemanticCard(
        **base,
        role="headword",
        display_text="be",
        context_cue="Exist or have a quality",
    )
    indicative = SemanticCard(
        **base,
        role="important_form",
        display_text="were",
        context_cue="They were ready.",
        surface_form_id="surface:were",
        morphological_analysis_id="analysis:indicative",
        prerequisite_card_id=head.card_id,
    )
    irrealis = SemanticCard(
        **base,
        role="important_form",
        display_text="were",
        context_cue="If I were ready.",
        surface_form_id="surface:were",
        morphological_analysis_id="analysis:irrealis",
        prerequisite_card_id=head.card_id,
    )
    return (head, indicative, irrealis)


def test_semantic_identity_ignores_rank_edition_and_preserves_form_analysis():
    head, first, second = cards_fixture()
    assert first.card_id != second.card_id
    assert first.destination == second.destination == head.destination == "en::Frequency::Level 1"
    assert head.model_copy(update={"rank": 1010, "deck_edition_id": "en-2"}).card_id == head.card_id
    with pytest.raises(ValueError, match="form"):
        type(first).model_validate(first.model_dump() | {"morphological_analysis_id": None})


def test_projection_does_not_truncate_mandatory_forms_and_reports_inventory():
    from multilang.services.semantic_anki import (
        summarize_cards,
        validate_semantic_cards,
    )

    cards = cards_fixture()
    validate_semantic_cards(cards, require_full_core=False)
    report = summarize_cards(cards)
    assert report["core"]["identities"] == 1
    assert report["core"]["important_forms"] == 2
    assert report["core"]["total"] == 3
    with pytest.raises(ValueError, match="3000"):
        validate_semantic_cards(cards, require_full_core=True)
    with pytest.raises(ValueError, match="parent|destination"):
        validate_semantic_cards(
            (cards[0], cards[1].model_copy(update={"rank": 1200})),
            require_full_core=False,
        )
    for changed in (
        {"rank": 2},
        {"sense_id": "false-sense"},
        {"parent_lemma": "false-lemma"},
    ):
        with pytest.raises(ValueError, match="parent"):
            validate_semantic_cards(
                (cards[0], cards[1].model_copy(update=changed)), require_full_core=False
            )


def test_topology_remains_unselected_and_fabricated_receipts_do_not_authorize_export(
    tmp_path,
):
    from multilang.services.semantic_anki import export_semantic_anki

    with pytest.raises(ValueError, match="ANKI-01"):
        export_semantic_anki(
            cards=cards_fixture(),
            output_path=tmp_path / "blocked.apkg",
            model="A",
            prototype=False,
        )
    assert not (tmp_path / "blocked.apkg").exists()


@pytest.mark.parametrize("model,notes", [("A", 1), ("B", 3)])
def test_both_prototypes_write_real_decks_cards_and_manifest(tmp_path, model, notes):
    from multilang.services.semantic_anki import export_semantic_anki

    path = tmp_path / f"{model}.apkg"
    result = export_semantic_anki(
        cards=cards_fixture(), output_path=path, model=model, prototype=True
    )
    assert result.prototype
    assert len(result.manifest) == 3
    with zipfile.ZipFile(path) as archive:
        db = tmp_path / "collection.db"
        db.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(db) as connection:
        assert connection.execute("select count(*) from notes").fetchone()[0] == notes
        assert connection.execute("select count(*) from cards").fetchone()[0] == 3
        decks = json.loads(connection.execute("select decks from col").fetchone()[0])
        actual_ids = {row[0] for row in connection.execute("select did from cards")}
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        for exported_model in models.values():
            assert exported_model["flds"][-1]["name"] == "Image"
            assert all("{{Image}}" in template["afmt"] + template["qfmt"] for template in exported_model["tmpls"])
        assert {decks[str(deck_id)]["name"] for deck_id in actual_ids} == {"en::Frequency::Level 1"}
    assert result.native_sibling_structure is (model == "A")
    assert not result.client_acceptance_proven


def build_history_package(tmp_path):
    database = tmp_path / "source.db"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE notes (id INTEGER, guid TEXT, mid INTEGER);
            CREATE TABLE cards (id INTEGER, nid INTEGER, ord INTEGER, did INTEGER, type INTEGER, queue INTEGER, due INTEGER, ivl INTEGER, factor INTEGER, reps INTEGER, lapses INTEGER);
            CREATE TABLE revlog (id INTEGER, cid INTEGER, ease INTEGER, ivl INTEGER, lastIvl INTEGER, factor INTEGER, time INTEGER, type INTEGER);
            INSERT INTO notes VALUES (1, 'known-guid', 123);
            INSERT INTO notes VALUES (2, 'ambiguous-guid', 123);
            INSERT INTO cards VALUES (11, 1, 0, 44, 2, 2, 20, 10, 2500, 5, 1);
            INSERT INTO cards VALUES (12, 2, 0, 44, 2, 2, 20, 10, 2500, 5, 1);
            INSERT INTO revlog VALUES (1000, 11, 3, 10, 5, 2500, 2000, 1);
        """)
    package = tmp_path / "history.apkg"
    with zipfile.ZipFile(package, "w") as archive:
        archive.write(database, "collection.anki2")
    return package


def test_history_is_readonly_minimized_and_uncertain_mapping_is_quarantined(tmp_path):
    from multilang.domain.learning import HistoryAlias
    from multilang.services.anki_history import read_anki_history

    package = build_history_package(tmp_path)
    before = sha256(package.read_bytes()).hexdigest()
    alias = HistoryAlias(
        note_guid="known-guid",
        template_ordinal=0,
        semantic_card_id=cards_fixture()[0].card_id,
        parent_lexical_identity_id="lex:be",
        model_id=123,
        evidence_sha256="a" * 64,
    )
    result = read_anki_history(package, aliases=(alias,), namespace="user:alice")
    assert result.input_sha256 == before == sha256(package.read_bytes()).hexdigest()
    assert len(result.states) == 1
    assert result.quarantined_count == 1
    assert result.states[0].review_count == 1
    assert "known-guid" not in result.model_dump_json()
    assert not list(tmp_path.glob("native-history-*"))


def test_history_rejects_duplicate_note_keys_before_joining_package(tmp_path):
    from multilang.services.anki_history import read_anki_history

    package = build_history_package(tmp_path)
    with sqlite3.connect(tmp_path / "source.db") as connection:
        connection.execute("INSERT INTO notes VALUES (1, 'duplicate-guid', 123)")
    with zipfile.ZipFile(package, "w") as archive:
        archive.write(tmp_path / "source.db", "collection.anki2")
    with pytest.raises(ValueError, match="duplicate|key"):
        read_anki_history(package, aliases=(), namespace="user:alice")


def test_history_limits_cannot_be_increased_past_hard_safety_ceilings():
    from multilang.domain.learning import HistoryLimits

    for field in (
        "max_archive_bytes",
        "max_member_bytes",
        "max_total_uncompressed_bytes",
        "max_members",
        "max_cards",
        "max_reviews",
        "max_sqlite_operations",
    ):
        with pytest.raises(ValueError):
            HistoryLimits(**{field: 10**15})


def test_history_rejects_traversal_archive_bomb_and_ambiguous_alias(tmp_path):
    from multilang.domain.learning import HistoryAlias, HistoryLimits
    from multilang.services.anki_history import read_anki_history

    package = tmp_path / "bad.apkg"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../escape", b"x")
        archive.writestr("collection.anki2", b"x" * 20000)
    with pytest.raises(ValueError):
        read_anki_history(package, aliases=(), namespace="user:a")
    package = build_history_package(tmp_path)
    with pytest.raises(ValueError, match="limit"):
        read_anki_history(
            package,
            aliases=(),
            namespace="user:a",
            limits=HistoryLimits(max_archive_bytes=1),
        )
    alias = HistoryAlias(
        note_guid="known-guid",
        template_ordinal=0,
        semantic_card_id="card:1",
        parent_lexical_identity_id="lex:be",
        model_id=123,
        evidence_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="ambiguous"):
        read_anki_history(
            package,
            aliases=(alias, alias.model_copy(update={"semantic_card_id": "card:2"})),
            namespace="user:a",
        )


def test_adaptation_is_deterministic_private_and_requires_parent():
    from multilang.domain.learning import AdaptivePolicy, LearnerState
    from multilang.services.adaptive_queue import build_adaptive_queue, reset_adaptation

    cards = cards_fixture()
    snapshot = tuple(card.model_dump_json() for card in cards)
    learner = LearnerState(namespace="user:alice")
    policy = AdaptivePolicy(mode="balanced", module_size=50)
    queue = build_adaptive_queue(cards=cards, learner_state=learner, policy=policy)
    assert queue == build_adaptive_queue(cards=cards, learner_state=learner, policy=policy)
    assert [entry.card_id for entry in queue.eligible] == [cards[0].card_id]
    assert len(queue.deferred) == 2
    learned = learner.model_copy(update={"known_card_ids": (cards[0].card_id,)})
    progressed = build_adaptive_queue(cards=cards, learner_state=learned, policy=policy)
    assert len(progressed.eligible) == 2
    assert tuple(card.model_dump_json() for card in cards) == snapshot
    assert reset_adaptation(learned).known_card_ids == ()
    assert reset_adaptation(learned).namespace == learned.namespace


def test_private_cards_cannot_collide_with_shared_guids_or_bypass_form_cues():
    head, form, _ = cards_fixture()
    private = type(head).model_validate(
        head.model_dump() | {"inventory": "custom", "namespace": "user:alice"}
    )
    assert private.note_guid != head.note_guid
    with pytest.raises(ValueError, match="cue"):
        type(form).model_validate(form.model_dump() | {"context_cue": "were"})


def test_history_revocation_and_reset_keep_core_and_other_imports_unchanged(tmp_path):
    from multilang.domain.learning import LearnerState
    from multilang.services.adaptive_queue import (
        override_priority,
        reset_adaptation,
        revoke_history,
    )
    from multilang.services.anki_history import read_anki_history

    imported = read_anki_history(build_history_package(tmp_path), aliases=(), namespace="user:a")
    state = LearnerState(namespace="user:a", history=(imported,))
    changed = override_priority(state, card_id="test", priority=50)
    assert changed.overrides == {"test": 50}
    assert reset_adaptation(changed).history == state.history
    assert revoke_history(changed, imported.import_id).history == ()
    assert state.history == (imported,)


def test_project_cards_integrates_approved_core_identity_and_form_contracts():
    from multilang.domain.lexical_identity import (
        ImportantFormSelection,
        LexicalIdentity,
        MorphologicalAnalysis,
        SurfaceForm,
    )
    from multilang.services.semantic_anki import project_cards

    identity = LexicalIdentity(
        language="en",
        normalized_lemma="be",
        part_of_speech="VERB",
        sense_id="exist",
        profile_version="1",
        normalizer_version="1",
        analyzer_version="1",
        source_id="fixture",
        source_version="1",
        source_sha256="a" * 64,
    )
    analysis = MorphologicalAnalysis(
        lexical_identity_id=identity.lexical_identity_id,
        analyzer_id="fixture",
        analyzer_version="1",
        features={"tense": "past"},
        confidence="1",
        evidence_sha256="b" * 64,
    )
    form = SurfaceForm(
        lexical_identity_id=identity.lexical_identity_id,
        text="were",
        analysis=analysis,
        source_id="fixture",
        source_sha256="a" * 64,
        attestation=10,
        context="They were ready.",
    )
    selected = ImportantFormSelection(form=form, score="1", policy_sha256="c" * 64)
    cards = project_cards(
        identities=(identity,),
        approved_forms=(selected,),
        ranks={identity.lexical_identity_id: 1},
        deck_edition_id="en-1",
    )
    assert [card.role for card in cards] == ["headword", "important_form"]
    assert cards[0].destination == cards[1].destination
    assert cards[1].prerequisite_card_id == cards[0].card_id


def test_content_backed_prototype_references_both_exact_audio_artifacts(tmp_path):
    from multilang.domain.audio_version import AudioVersion, PronunciationSignature
    from multilang.domain.content import (
        ContentRequest,
        ContentVersion,
        GeneratedContent,
        TargetMatchEvidence,
    )
    from multilang.services.semantic_anki import _render_card

    card = cards_fixture()[0]
    request = ContentRequest(
        lexical_identity_id=card.parent_lexical_identity_id,
        card_id=card.card_id,
        language="en",
        language_profile_version="1",
        lemma="be",
        display_text="be",
        sense_id="exist",
        context_cue=card.context_cue,
        namespace="core",
        deck_edition_id="en-1",
        grounding_sha256="a" * 64,
        target_concept_id="be",
    )
    content = ContentVersion(
        request=request,
        content=GeneratedContent(
            definition="Exist.",
            example_sentence="They will be ready.",
            translation="They will be ready.",
        ),
        target_evidence=TargetMatchEvidence(
            lexical_identity_id=card.parent_lexical_identity_id,
            sense_id="exist",
            target_concept_id="be",
            matched=True,
            observed_concept_ids=("be",),
            analyzer_version="1",
            evidence_sha256="b" * 64,
        ),
        provider="fixture",
        model_version="1",
    )
    assets = {}
    for kind, text in (("word", "be"), ("sentence", content.content.example_sentence)):
        path = tmp_path / f"{kind}.mp3"
        path.write_bytes(b"fixture-audio")
        assets[f"{kind}_audio"] = AudioVersion(
            signature=PronunciationSignature(
                language="en",
                language_profile_version="1",
                display_text=text,
                normalized_text=text,
                contextual_reading=text,
                context=card.context_cue,
                sense_id="exist",
                locale="en-US",
                voice_id="en-US-JennyNeural",
                ssml=f'<speak xml:lang="en-US"><voice name="en-US-JennyNeural">{text}</voice></speak>',
                pronunciation_policy_version="1",
                provider="azure",
                provider_model_version="1",
                audio_format="audio-24khz-48kbitrate-mono-mp3",
                asset_kind=kind,
            ),
            storage_path=str(path),
            artifact_sha256=sha256(path.read_bytes()).hexdigest(),
            byte_size=13,
        )
    card = type(card).model_validate(card.model_dump() | {"content": content} | assets)
    _, back, media = _render_card(card, prototype=True)
    assert "[sound:word.mp3]" in back
    assert "[sound:sentence.mp3]" in back
    assert len(media) == 2
    for changed in (
        {"language": "ko"},
        {"lemma": "false-lemma"},
        {"context_cue": "false-context"},
    ):
        forged_content = ContentVersion.model_validate(
            content.model_dump() | {"request": request.model_dump() | changed}
        )
        with pytest.raises(ValueError, match="content"):
            type(card).model_validate(card.model_dump() | {"content": forged_content})
