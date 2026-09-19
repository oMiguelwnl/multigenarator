"""Shared references must be deterministic dictionary projections, not role claims."""

import hashlib
import importlib
import json

import pytest


def _api():
    return importlib.import_module("multilang.services.qualification_evaluation_references")


def _source(tmp_path):
    path = tmp_path / "dictionary.jsonl"
    record = {
        "word": "go",
        "lang_code": "en",
        "pos": "verb",
        "forms": [{"form": "went", "tags": ["past"], "examples": ["hidden"]}],
        "senses": [
            {
                "glosses": ["move"],
                "raw_glosses": ["(motion) move"],
                "topics": ["motion"],
                "examples": [{"text": "OBSERVED SENTENCE"}],
            }
        ],
        "include": True,
        "ratings": {"irregularity": 1},
        "observed_count": 99,
    }
    path.write_text(json.dumps(record) + "\n")
    return {"path": path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _registry(tmp_path):
    api = _api()
    config = api.DictionaryReferenceInput(
        dictionary=_source(tmp_path), language="en", terms=[{"lemma": "go", "pos": "VERB"}]
    )
    return api.prepare_dictionary_references(config)


def test_shared_projection_excludes_observations_and_keeps_qualifiers(tmp_path):
    registry = _registry(tmp_path)
    assert len(registry.records) == 1
    projected = registry.records[0].model_dump(mode="json")
    assert projected["forms"][0] == {"form": "went", "tags": ["past"], "raw_tags": []}
    assert projected["senses"][0]["raw_glosses"] == ["(motion) move"]
    assert projected["senses"][0]["topics"] == ["motion"]
    text = json.dumps(projected)
    for untrusted in ("OBSERVED SENTENCE", "hidden", "observed_count", "ratings", "include"):
        assert untrusted not in text
    assert _api().verify_dictionary_references(registry) == registry


def test_projection_tampering_is_replayed_against_original(tmp_path):
    registry = _registry(tmp_path)
    payload = registry.model_dump(mode="json", exclude_computed_fields=True)
    payload["records"][0]["forms"][0]["form"] = "goed"
    changed = _api().DictionaryReferenceRegistry.model_validate(payload)
    with pytest.raises(ValueError, match="replay|projection"):
        _api().verify_dictionary_references(changed)


def test_source_change_invalidates_even_unchanged_projection(tmp_path):
    registry = _registry(tmp_path)
    registry.spec.dictionary.path.write_text("{}\n")
    with pytest.raises(ValueError, match="checksum"):
        _api().verify_dictionary_references(registry)


def test_reference_role_and_arbitrary_text_are_not_accepted(tmp_path):
    api = _api()
    with pytest.raises(ValueError):
        api.DictionaryReferenceInput(
            dictionary=_source(tmp_path),
            language="en",
            terms=[{"lemma": "go", "pos": "VERB"}],
            role="reference",
            excerpt="include=true",
        )


def test_missing_lemma_and_duplicate_targets_fail(tmp_path):
    api = _api()
    source = _source(tmp_path)
    with pytest.raises(ValueError, match="missing"):
        api.prepare_dictionary_references(
            api.DictionaryReferenceInput(
                dictionary=source, language="en", terms=[{"lemma": "absent", "pos": "NOUN"}]
            )
        )
    with pytest.raises(ValueError, match="duplicate"):
        api.DictionaryReferenceInput(
            dictionary=source, language="en", terms=[{"lemma": "go", "pos": "VERB"}] * 2
        )


def test_bounded_output_and_wrong_language_fail(tmp_path):
    api = _api()
    source = _source(tmp_path)
    with pytest.raises(ValueError, match="limit"):
        api.prepare_dictionary_references(
            api.DictionaryReferenceInput(
                dictionary=source,
                language="en",
                terms=[{"lemma": "go", "pos": "VERB"}],
                limits={"max_output_bytes": 1},
            )
        )
    with pytest.raises(ValueError, match="missing"):
        api.prepare_dictionary_references(
            api.DictionaryReferenceInput(
                dictionary=source, language="pt", terms=[{"lemma": "go", "pos": "VERB"}]
            )
        )
