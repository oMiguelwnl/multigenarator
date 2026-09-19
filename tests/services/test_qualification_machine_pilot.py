"""Machine pilots retain provenance and never counterfeit production approvals."""

import importlib
import json
from hashlib import sha256

import pytest


def api():
    name = "multilang.services.qualification_machine_pilot"
    assert importlib.util.find_spec(name), "machine pilot service is missing"
    return importlib.import_module(name)


def pilot_fixture(tmp_path, *, inflection=False):
    from test_qualification_machine_campaign import machine_result

    from multilang.domain.lexical_identity import canonical_sha256
    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.services.qualification_machine_campaign import build_machine_campaign
    from multilang.services.qualification_review import (
        LexicalReviewItem,
        ReviewPacket,
        ReviewSource,
    )
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text(
        json.dumps(
            {
                "word": "go",
                "lang_code": "en",
                "pos": "verb",
                "senses": [
                    {
                        "glosses": ["move from one place to another"],
                        **({"form_of": [{"word": "move"}]} if inflection else {}),
                    }
                ],
                "sounds": [{"ipa": "/ɡoʊ/", "tags": ["US"]}, {"ipa": "/ɡəʊ/", "tags": ["UK"]}],
            }
        )
        + "\n"
    )
    prep = tmp_path / "prepared"
    prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=sha256(dictionary.read_bytes()).hexdigest(),
        output=prep,
    )
    candidate = json.loads((prep / "candidates.jsonl").read_text().splitlines()[0])
    profile = (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(
            update={
                "source_ids": ("fixture",),
                "analyzer_id": "contextual-morphology",
                "analyzer_version": "fixture-1",
            }
        )
    )
    item = LexicalReviewItem(
        item_id="lexical-go",
        candidate_id=candidate["candidate_id"],
        candidate_sha256=canonical_sha256(candidate),
        lemma="go",
        pos="VERB",
        sources=(
            ReviewSource(
                source_id="fixture",
                source_sha256=candidate["source_record_sha256"],
                record_id=candidate["candidate_id"],
                excerpt="move from one place to another",
            ),
        ),
    )
    packet = ReviewPacket(
        packet_id="fixture",
        language="en",
        split="pilot",
        profile_sha256=canonical_sha256(profile.model_dump(mode="json")),
        rubric_sha256="a" * 64,
        items=(item,),
    )
    campaign = build_machine_campaign(machine_result(packet, tag="fixture"), campaign_id="fixture")
    return campaign, dict(
        preparation_dir=prep,
        profile=profile,
        source_id="fixture",
        source_version="1",
        item_ids=(item.item_id,),
        variant="US",
    )


def content_fixture(tmp_path, *, definition="Move from one place to another."):
    from test_qualification_machine_runner import metadata_fixture

    from multilang.services.contextual_morphology import (
        ContextualAnalysis,
        ContextualToken,
        sentence_hash,
    )
    from multilang.services.qualification_machine import MachineActor

    module = api()
    campaign, kwargs = pilot_fixture(tmp_path)
    plan = module.build_machine_pilot(campaign, **kwargs)
    request = module.build_pilot_content_request(
        plan,
        actor=MachineActor(
            actor_id="fixture-proposer", context_id="fixture-proposer", execution_surface="mock"
        ),
    )
    entry = plan.entries[0]
    excerpt = entry.source.excerpt
    raw = {
        "items": [
            {
                "item_id": entry.item_id,
                "item_sha256": entry.item_sha256,
                "content": {
                    "definition": definition,
                    "example_sentence": "I go.",
                    "translation": "Eu vou.",
                },
                "target_span": [2, 4],
                "reason": "Synthetic fixture content review.",
                "citations": [
                    {
                        "source_index": 0,
                        "source_sha256": entry.source.source_sha256,
                        "start": 0,
                        "end": len(excerpt),
                        "quote": excerpt,
                    }
                ],
            }
        ]
    }
    proposal = module.accept_pilot_content(request, raw, metadata=metadata_fixture())
    judge_request = module.build_pilot_content_request(
        plan,
        actor=MachineActor(
            actor_id="fixture-judge", context_id="fixture-judge", execution_surface="mock"
        ),
        proposal=proposal,
    )
    judge = module.accept_pilot_content(judge_request, raw, metadata=metadata_fixture())
    sentence = "I go."
    digest = sentence_hash(sentence)
    analysis = ContextualAnalysis(
        language="en",
        status="complete",
        sentence_sha256=digest,
        model_fingerprint="b" * 64,
        reason="Synthetic analyzer fixture.",
        tokens=tuple(
            ContextualToken(
                text=text,
                lemma=lemma,
                pos=pos,
                start=start,
                end=end,
                sentence_sha256=digest,
                model_fingerprint="b" * 64,
            )
            for text, lemma, pos, start, end in [
                ("I", "I", "PRON", 0, 1),
                ("go", "go", "VERB", 2, 4),
                (".", ".", "PUNCT", 4, 5),
            ]
        ),
    )
    complete = module.complete_pilot_content(plan, proposal, judge, analyses=(analysis,))
    return plan, request, raw, proposal, judge, analysis, complete


def test_verified_selection_and_variant_ipa(tmp_path):
    campaign, kwargs = pilot_fixture(tmp_path)
    plan = api().build_machine_pilot(campaign, **kwargs)
    assert plan.entries[0].presentation.ipa == "/ɡoʊ/"
    assert plan.origin == "machine" and not plan.production_eligible
    assert plan.entries[0].card.inventory == "expansion"
    assert plan.entries[0].card.rank is None
    assert api().MachinePilotPlan.model_validate_json(plan.model_dump_json()) == plan
    for change in [
        {"item_ids": ("missing",)},
        {"item_ids": ("lexical-go", "lexical-go")},
        {"variant": "missing"},
    ]:
        with pytest.raises(ValueError):
            api().build_machine_pilot(campaign, **(kwargs | change))


def test_content_judgment_is_bound_and_pending(tmp_path):
    plan, request, raw, proposal, judge, analysis, content = content_fixture(tmp_path)
    assert content.cards[0].content.review_status == "pending"
    assert content.cards[0].content.review_receipt_sha256 is None
    assert content.cards[0].content.target_evidence.target_span == (2, 4)
    assert content.cards[0].content.presentation.ipa == "/ɡoʊ/"
    with pytest.raises(ValueError, match="context"):
        api().build_pilot_content_request(plan, actor=request.actor, proposal=proposal)
    raw["items"][0]["citations"][0]["quote"] = "x" * len(raw["items"][0]["citations"][0]["quote"])
    with pytest.raises(ValueError, match="citation"):
        api().accept_pilot_content(request, raw, metadata=proposal.metadata)
    with pytest.raises(ValueError, match="analysis|contextual"):
        api().complete_pilot_content(
            plan,
            proposal,
            judge,
            analyses=(analysis.model_copy(update={"sentence_sha256": "f" * 64}),),
        )


def audio_fixture(tmp_path, content):
    from support.audio import SILENT_MP3

    from multilang.domain.audio_version import AudioVersion

    plan = api().prepare_pilot_audio(
        content, locale="en-US", voice_id="en-US-AriaNeural", provider_model_version="fixture"
    )
    versions = []
    for index, item in enumerate(plan.items):
        path = tmp_path / f"fixture-{index}.mp3"
        path.write_bytes(SILENT_MP3)
        versions.append(
            AudioVersion(
                signature=item.signature,
                storage_path=str(path),
                artifact_sha256=sha256(path.read_bytes()).hexdigest(),
                byte_size=path.stat().st_size,
            )
        )
    return plan, tuple(versions)


def test_apkg_requires_exact_complete_audio_and_preserves_fields(tmp_path):
    import sqlite3
    import zipfile

    content = content_fixture(tmp_path)[-1]
    plan, versions = audio_fixture(tmp_path, content)
    with pytest.raises(ValueError, match="coverage"):
        api().export_machine_pilot(
            content, plan, audio_versions=versions[:1], output=tmp_path / "missing"
        )
    output = tmp_path / "export"
    manifest = api().export_machine_pilot(content, plan, audio_versions=versions, output=output)
    assert not manifest["production_eligible"]
    assert (
        api().export_machine_pilot(content, plan, audio_versions=versions, output=output)
        == manifest
    )
    with zipfile.ZipFile(output / "pilot.apkg") as archive:
        database = tmp_path / "collection.anki2"
        database.write_bytes(archive.read("collection.anki2"))
        assert len(json.loads(archive.read("media"))) == 2
    with sqlite3.connect(database) as connection:
        models = json.loads(connection.execute("select models from col").fetchone()[0])
        names = [field["name"] for field in next(iter(models.values()))["flds"]]
        fields, tags = connection.execute("select flds,tags from notes").fetchone()
        fields = dict(zip(names, fields.split("\x1f"), strict=True))
        assert len(names) == 9 and fields["Image"] == ""
        assert fields["word"] == "go" and fields["IPA"] == "/ɡoʊ/"
        assert fields["Definitions"] == "verb: Move from one place to another."
        assert "native_prototype_B" in tags
        assert "Prototype only" not in fields.values()
    saved = json.loads((output / "cards.json").read_text())[0]
    assert saved["content"]["content"]["definition"] == fields["Definitions"]
    assert type(content.cards[0]).model_validate(saved).card_id == content.cards[0].card_id
    assert saved["word_audio"]["signature"] == versions[0].signature.model_dump(mode="json")
    assert content.cards[0].content.content.definition == "Move from one place to another."
    assert api().MachinePilotContent.model_validate_json(content.model_dump_json()) == content
    assert json.loads((output / "report.json").read_text())["definition_presentation_policy"]
    (tmp_path / "fixture-0.mp3").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="audio|integrity"):
        api().export_machine_pilot(content, plan, audio_versions=versions, output=output)


def test_pilot_word_prosody_is_slower_without_changing_sentence_signature(tmp_path):
    from xml.etree import ElementTree

    from multilang.services.native_audio import validate_pronunciation_ssml

    content = content_fixture(tmp_path)[-1]
    plan, _ = audio_fixture(tmp_path, content)
    word, sentence = (item.signature for item in plan.items)
    ns = {"ssml": "http://www.w3.org/2001/10/synthesis"}
    prosody = ElementTree.fromstring(word.ssml).find("ssml:voice/ssml:prosody", ns)
    assert prosody is not None, "isolated words need deliberate pronunciation"
    assert prosody.attrib == {"rate": "-15%", "volume": "+20%"}
    assert prosody.text == word.normalized_text == "go"
    assert word.pronunciation_policy_version == "machine-pilot-word-clear-2"
    assert (
        sentence.ssml
        == '<speak xmlns="http://www.w3.org/2001/10/synthesis" version="1.0" xml:lang="en-US"><voice name="en-US-AriaNeural">I go.</voice></speak>'
    )
    assert sentence.pronunciation_policy_version == "machine-pilot-source-ipa-1"
    for signature in (word, sentence):
        validate_pronunciation_ssml(signature)


@pytest.mark.parametrize(
    "definition",
    ["noun: a journey", "unknown: movement", "verb:", " noun: a journey", "proper_noun: a person"],
)
def test_pilot_export_rejects_incompatible_or_invalid_definition_label(tmp_path, definition):
    content = content_fixture(tmp_path, definition=definition)[-1]
    plan, versions = audio_fixture(tmp_path, content)
    with pytest.raises(ValueError, match="definition"):
        api().export_machine_pilot(content, plan, audio_versions=versions, output=tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_pilot_export_does_not_duplicate_existing_definition_label(tmp_path):
    definition = "verb: Move from one place to another."
    content = content_fixture(tmp_path, definition=definition)[-1]
    plan, versions = audio_fixture(tmp_path, content)
    output = tmp_path / "export"
    api().export_machine_pilot(content, plan, audio_versions=versions, output=output)
    saved = json.loads((output / "cards.json").read_text())[0]
    assert saved["content"]["content"]["definition"] == definition


@pytest.mark.parametrize("attack", ["undecodable", "ssml", "parent_symlink", "voice"])
def test_audio_payload_attacks_fail_before_export(tmp_path, attack):
    content = content_fixture(tmp_path)[-1]
    plan, versions = audio_fixture(tmp_path, content)
    version = versions[0]
    if attack == "undecodable":
        path = tmp_path / "fixture-0.mp3"
        path.write_bytes(b"not actual audio")
        version = version.model_copy(
            update={
                "byte_size": path.stat().st_size,
                "artifact_sha256": sha256(path.read_bytes()).hexdigest(),
            }
        )
    elif attack == "parent_symlink":
        link = tmp_path / "linked"
        link.symlink_to(tmp_path, target_is_directory=True)
        version = version.model_copy(update={"storage_path": str(link / "fixture-0.mp3")})
    else:
        updates = (
            {"ssml": '<speak xml:lang="en-US"><voice name="en-US-AriaNeural">wrong</voice></speak>'}
            if attack == "ssml"
            else {"voice_id": "fr-FR-Other"}
        )
        signature = version.signature.model_copy(update=updates)
        version = version.model_copy(update={"signature": signature})
        plan = plan.model_copy(
            update={
                "items": (
                    plan.items[0].model_copy(update={"signature": signature}),
                    *plan.items[1:],
                )
            }
        )
    with pytest.raises(ValueError, match="audio|SSML|symlink|voice"):
        api().export_machine_pilot(
            content, plan, audio_versions=(version, *versions[1:]), output=tmp_path / "attack"
        )


@pytest.mark.parametrize("attack", ["coverage", "hash", "active", "metadata", "span"])
def test_content_response_attacks_fail(tmp_path, attack):
    _, request, raw, proposal, *_ = content_fixture(tmp_path)
    if attack == "coverage":
        raw["items"].append(raw["items"][0])
    elif attack == "hash":
        raw["items"][0]["item_sha256"] = "f" * 64
    elif attack == "active":
        raw["items"][0]["content"]["definition"] = '<img src="x" onerror="alert(1)">'
    elif attack == "metadata":
        raw["metadata"] = {"executed_at": "2026-01-01"}
    else:
        raw["items"][0]["target_span"] = [0, 1]
    with pytest.raises(ValueError):
        api().accept_pilot_content(request, raw, metadata=proposal.metadata)


def test_source_presentation_cannot_change_without_candidate_change(tmp_path):
    campaign, kwargs = pilot_fixture(tmp_path)
    plan = api().build_machine_pilot(campaign, **kwargs)
    raw = plan.model_dump(mode="json", exclude_computed_fields=True)
    raw["entries"][0]["presentation"]["ipa"] = "/fake/"
    with pytest.raises(ValueError, match="projection"):
        api().MachinePilotPlan.model_validate(raw)


def test_dictionary_excerpt_does_not_attribute_machine_gloss_to_source(tmp_path):
    campaign, kwargs = pilot_fixture(tmp_path)
    plan = api().build_machine_pilot(campaign, **kwargs)
    source = json.loads(plan.entries[0].source.excerpt)
    assert "machine_sense_proposal" not in source
    assert source["candidate"]["glosses"] == ["move from one place to another"]


def test_audio_locale_must_agree_with_source_ipa_variant(tmp_path):
    content = content_fixture(tmp_path)[-1]
    with pytest.raises(ValueError, match="variant"):
        api().prepare_pilot_audio(
            content, locale="en-GB", voice_id="en-GB-SoniaNeural", provider_model_version="fixture"
        )


def test_inflection_candidate_cannot_become_pilot_headword(tmp_path):
    campaign, kwargs = pilot_fixture(tmp_path, inflection=True)
    with pytest.raises(ValueError, match="headword|lexeme|inflection"):
        api().build_machine_pilot(campaign, **kwargs)


@pytest.mark.parametrize("correction", [{"proposed_lemma": "move"}, {"proposed_pos": "NOUN"}])
def test_corrected_identity_cannot_inherit_original_pronunciation(tmp_path, correction):
    from test_qualification_machine_runner import metadata_fixture

    from multilang.services.qualification_machine import (
        MachineActor,
        accept_machine_response,
        build_machine_request,
        reconcile_machine_reviews,
    )
    from multilang.services.qualification_machine_campaign import build_machine_campaign

    original, kwargs = pilot_fixture(tmp_path)
    packet = original.base_result.packet
    response = original.base_result.proposal.response.model_dump(mode="json")
    response["decisions"][0].update(decision="corrected", **correction)
    request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="corrector", context_id="corrector", execution_surface="mock"),
        run_id="correction",
    )
    proposal = accept_machine_response(request, response, metadata=metadata_fixture())
    judgment_request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="reviewer", context_id="reviewer", execution_surface="mock"),
        run_id="correction-review",
        proposal=proposal,
    )
    judgment = accept_machine_response(judgment_request, response, metadata=metadata_fixture())
    campaign = build_machine_campaign(
        reconcile_machine_reviews(packet, proposal, judgment), campaign_id="corrected"
    )
    with pytest.raises(ValueError, match="pronunciation.*identity"):
        api().build_machine_pilot(campaign, **kwargs)


@pytest.mark.parametrize("attack", ["oversized", "parent_symlink"])
def test_invalid_audio_is_rejected_before_unbounded_file_read(tmp_path, monkeypatch, attack):
    from pathlib import Path

    content = content_fixture(tmp_path)[-1]
    plan, versions = audio_fixture(tmp_path, content)
    version = versions[0]
    path = Path(version.storage_path)
    if attack == "oversized":
        with path.open("wb") as handle:
            handle.truncate(17 * 1024**2)
        version = version.model_copy(update={"byte_size": path.stat().st_size})
    else:
        link = tmp_path / "linked-media"
        link.symlink_to(tmp_path, target_is_directory=True)
        path = link / path.name
        version = version.model_copy(update={"storage_path": str(path)})
    original_open = Path.open

    def reject_unbounded_open(target, *args, **kwargs):
        if target == path:
            pytest.fail("invalid audio reached an unbounded file read before path/size validation")
        return original_open(target, *args, **kwargs)

    monkeypatch.setattr(Path, "open", reject_unbounded_open)
    with pytest.raises(ValueError, match="bounded|symlink"):
        api().export_machine_pilot(
            content, plan, audio_versions=(version, *versions[1:]), output=tmp_path / "invalid"
        )
