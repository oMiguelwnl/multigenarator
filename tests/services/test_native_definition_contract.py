"""New native generation binds source meaning; historical content stays readable."""

import json
from types import SimpleNamespace

import pytest
from test_native_content_audio import content_request


def evidence(**changes):
    from multilang.domain.definitions import DefinitionEvidence

    return DefinitionEvidence(
        **(
            dict(
                lemma="run",
                source_language="en",
                part_of_speech="verb",
                sense_id="move",
                meaning="to move quickly on foot",
                language="en",
                source="fixture",
                lexical_record_sha256="b" * 64,
                source_version="1",
                source_sha256="c" * 64,
            )
            | changes
        )
    )


def test_new_evidence_is_bound_to_request_but_absent_fields_preserve_history():
    before = content_request().model_dump(mode="json")
    assert "definition_evidence" not in before
    with pytest.raises(ValueError, match="definition evidence"):
        content_request(definition_evidence=evidence(sense_id="operate"))
    request = content_request(definition_evidence=evidence())
    from multilang.services.native_content import provider_content_projection

    projection = provider_content_projection(request).model_dump()
    assert projection["definition_evidence"]["meaning"] == "to move quickly on foot"
    assert projection["definition_evidence"]["part_of_speech"] == "verb"


def test_resolver_selects_exact_identity_and_rejects_ambiguity():
    from multilang.services.content.definition_policy import resolve_definition_evidence
    from multilang.services.lexical_lookup import LexicalRecord

    identity = SimpleNamespace(
        language=SimpleNamespace(value="en"),
        normalized_lemma="run",
        part_of_speech="VERB",
        sense_id="move",
        source_id="fixture",
        source_version="1",
        source_sha256="c" * 64,
    )
    good = LexicalRecord(
        term="run",
        display_form="run",
        lemma="run",
        part_of_speech="verb",
        sense_id="move",
        source="fixture",
        definitions=["to move quickly on foot"],
        definition_language="en",
        source_version="1",
        source_sha256="c" * 64,
    )
    other = good.model_copy(update={"sense_id": "operate", "definitions": ["to manage a business"]})
    rows = [other, good]
    lookup = SimpleNamespace(lookup_candidates=lambda **_: rows)
    selected = resolve_definition_evidence(identity, lookup)
    assert selected.meaning == "to move quickly on foot"
    rows.append(good.model_copy(update={"definitions": ["to run a machine"]}))
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_definition_evidence(identity, lookup)
    rows[:] = [other]
    with pytest.raises(ValueError, match="missing"):
        resolve_definition_evidence(identity, lookup)


@pytest.mark.parametrize(
    "changes",
    [
        {"source_version": "2"},
        {"source_sha256": "d" * 64},
        {"source_version": None, "source_sha256": None},
    ],
)
def test_source_snapshot_must_match_persisted_identity(changes):
    from multilang.services.content.definition_policy import resolve_definition_evidence
    from multilang.services.lexical_lookup import LexicalRecord

    identity = SimpleNamespace(
        language=SimpleNamespace(value="en"),
        normalized_lemma="run",
        part_of_speech="verb",
        sense_id="move",
        source_id="fixture",
        source_version="1",
        source_sha256="c" * 64,
    )
    record = LexicalRecord.model_validate(
        dict(
            term="run",
            display_form="run",
            lemma="run",
            part_of_speech="verb",
            sense_id="move",
            source="fixture",
            definition_language="en",
            definitions=["to move on foot"],
            source_version="1",
            source_sha256="c" * 64,
        )
        | changes
    )
    with pytest.raises(ValueError, match="definition evidence"):
        resolve_definition_evidence(
            identity, SimpleNamespace(lookup_candidates=lambda **_: (record,))
        )


def test_native_generation_requires_meaning_before_spending_provider_budget():
    from multilang.services.native_content import NativeProviderContentAdapter
    from multilang.settings import Settings

    calls = []
    adapter = NativeProviderContentAdapter(
        settings=Settings(_env_file=None), completion=lambda **kwargs: calls.append(kwargs)
    )
    with pytest.raises(ValueError, match="definition evidence"):
        adapter(content_request())
    assert not calls


def test_runtime_injects_canonical_meaning_and_rejects_client_spoof(tmp_path):
    from multilang.native_runtime import NativeFacade
    from multilang.settings import Settings

    path = tmp_path / "en" / "lexical-index.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "run": dict(
                    term="run",
                    display_form="run",
                    lemma="run",
                    part_of_speech="verb",
                    sense_id="move",
                    source="fixture",
                    definition_language="en",
                    definitions=["to move quickly on foot"],
                    source_version="1",
                    source_sha256="c" * 64,
                )
            }
        )
    )
    facade = NativeFacade(
        session=None, settings=Settings(_env_file=None, lexicon_data_dir=tmp_path)
    )
    identity = SimpleNamespace(
        language=SimpleNamespace(value="en"),
        normalized_lemma="run",
        part_of_speech="VERB",
        sense_id="move",
        source_id="fixture",
        source_version="1",
        source_sha256="c" * 64,
    )
    facade._identity = lambda _: (identity, "a" * 64)
    bound = facade._definition_context(content_request())
    assert bound.definition_evidence.meaning == "to move quickly on foot"
    spoof = bound.model_copy(
        update={
            "definition_evidence": bound.definition_evidence.model_copy(
                update={"meaning": "to operate a business"}
            )
        }
    )
    with pytest.raises(ValueError, match="canonical local source"):
        facade._definition_context(spoof)


def test_runtime_resolves_evidence_before_content_service(tmp_path):
    from multilang.native_runtime import NativeFacade
    from multilang.settings import Settings

    facade = NativeFacade(
        session=None, settings=Settings(_env_file=None, lexicon_data_dir=tmp_path)
    )
    facade._content_context = lambda *_: (content_request(), object())
    facade._identity = lambda _: (
        SimpleNamespace(
            language=SimpleNamespace(value="en"),
            normalized_lemma="run",
            part_of_speech="verb",
            sense_id="move",
            source_id="fixture",
            source_version="1",
            source_sha256="c" * 64,
        ),
        "a" * 64,
    )
    facade._content_service = lambda _: pytest.fail(
        "missing lexical evidence must stop before provider"
    )
    with pytest.raises(ValueError, match="definition evidence"):
        facade.generate_content({}, "fixture")


def test_native_generation_uses_common_template_and_checks_exact_definition_example():
    from multilang.domain.definitions import DefinitionConsistencyVerdict
    from multilang.services.native_content import NativeProviderContentAdapter
    from multilang.settings import Settings

    calls, reviews = [], []
    payload = {
        "definition": "verb: to move quickly on foot",
        "example_sentence": "I ran home yesterday.",
        "translation": "Eu corri para casa ontem.",
    }

    def complete(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": json.dumps(payload)}}]}

    def check(request):
        reviews.append(request)
        return DefinitionConsistencyVerdict(decision="consistent")

    adapter = NativeProviderContentAdapter(
        settings=Settings(_env_file=None), completion=complete, definition_checker=check
    )
    result = adapter(content_request(definition_evidence=evidence()))
    assert result.definition == payload["definition"]
    assert "definition-single-sense-v2" in calls[0]["messages"][0]["content"]
    assert reviews[0].definition == payload["definition"]
    assert reviews[0].sentence == payload["example_sentence"]
    payload["definition"] = "noun: a quick movement"
    with pytest.raises(ValueError, match="part of speech"):
        adapter(content_request(definition_evidence=evidence()))
    assert len(reviews) == 1


@pytest.mark.parametrize("decision", ["mismatch", "uncertain"])
def test_native_mismatched_or_uncertain_pair_is_not_accepted(decision):
    from multilang.domain.definitions import DefinitionConsistencyVerdict
    from multilang.services.native_content import NativeProviderContentAdapter
    from multilang.settings import Settings

    payload = {
        "definition": "verb: to move quickly on foot",
        "example_sentence": "I ran a business.",
        "translation": "Eu administrei uma empresa.",
    }
    adapter = NativeProviderContentAdapter(
        settings=Settings(_env_file=None),
        completion=lambda **_: {"choices": [{"message": {"content": json.dumps(payload)}}]},
        definition_checker=lambda _: DefinitionConsistencyVerdict(decision=decision),
    )
    with pytest.raises(ValueError, match="definition.*consistency"):
        adapter(content_request(definition_evidence=evidence()))
