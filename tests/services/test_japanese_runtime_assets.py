"""Synthetic review receipts exercise the adapter, never production approval."""

from hashlib import sha256

import pytest


def reviewed_fixture(tmp_path):
    from test_japanese_sources import write_source
    from test_vocabulary_review import sign, store

    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.services.vocabulary_preparation import prepare_vocabulary
    from multilang.services.vocabulary_review import (
        compile_reviewed_vocabulary,
        create_pending_review,
        decision_payload,
    )
    path, digest = write_source(tmp_path)
    prep = tmp_path / "prepared"
    prepare_vocabulary(language="ja", dictionary=path, dictionary_sha256=digest,
        dictionary_format="jmdict", output=prep)
    profile = LanguageProfileRegistry().get("ja").model_copy(update={"source_ids": ("fixture",),
        "analyzer_id": "fugashi-unidic", "analyzer_version": "synthetic-1"})
    verifier = store(tmp_path)
    review = create_pending_review(prep, source_id="fixture", source_version="synthetic-1")
    decisions = tuple(item.model_copy(update={"decision": "accepted", "reviewer": "synthetic-reviewer",
        "stable_sense_id": f"synthetic-{index}"}) for index, item in enumerate(review.senses))
    review = review.model_copy(update={"senses": decisions})
    review = review.model_copy(update={"senses": tuple(item.model_copy(update={
        "receipt_id": sign(verifier, decision_payload(review, item, profile), "vocabulary-sense")
    }) for item in review.senses)})
    source = tmp_path / "review.json"
    source.write_text(review.model_dump_json())
    bundle = compile_reviewed_vocabulary(preparation_dir=prep, decisions_path=source,
        decisions_sha256=sha256(source.read_bytes()).hexdigest(), profile=profile, verifier=verifier)
    assert bundle.identities
    return bundle, profile, verifier


def test_reviewed_jmdict_bridge_is_consumed_by_normal_lexical_lookup(tmp_path):
    from multilang.services.japanese_runtime_assets import export_japanese_lexical_cache
    from multilang.services.lexical_lookup import LexicalLookup
    bundle, profile, verifier = reviewed_fixture(tmp_path)
    output = tmp_path / "runtime"
    report = export_japanese_lexical_cache(bundle=bundle, profile=profile, verifier=verifier, output=output)
    lookup = LexicalLookup(output / "lexicon")
    records = lookup.lookup_candidates(language_code="ja", term="今日")
    assert len(records) == 1 and records[0].japanese_reading == "きょう"
    assert records[0].source_sha256 == bundle.preparation_manifest["dictionary_sha256"]
    assert report["identity_count"] == len(bundle.identities)
    assert not report["production_deck_approved"]
    assert (output / "ATTRIBUTION.md").exists()
    from multilang.domain.jobs import SupportedLanguage
    from multilang.domain.lexicon import LexicalCardCandidate
    from multilang.services.lexical_grounding import LexicalGroundingService
    identity = next(item for item in bundle.identities if item.normalized_lemma == "今日")
    candidate = LexicalCardCandidate(submitted_form="今日", display_form="今日", lemma="今日",
        lemma_key=identity.lexical_identity_id, definition_language="en", translation_target_language="en",
        frequency_rank=1, frequency_level=1, grounding_status="pending", provenance={"source": "synthetic-frequency"})
    grounded = LexicalGroundingService(lookup).ground_frequency_candidate(language=SupportedLanguage.JA, candidate=candidate)
    assert grounded.lemma_key == identity.lexical_identity_id
    assert grounded.spoken_form == "きょう"


def test_jmdict_cache_bridge_rejects_tampered_review(tmp_path):
    from multilang.services.japanese_runtime_assets import export_japanese_lexical_cache
    bundle, profile, verifier = reviewed_fixture(tmp_path)
    tampered = bundle.model_copy(update={"identities": ()})
    with pytest.raises(ValueError):
        export_japanese_lexical_cache(bundle=tampered, profile=profile, verifier=verifier, output=tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_frequency_release_cannot_publish_a_short_or_unsigned_inventory(tmp_path):
    from multilang.services.japanese_runtime_assets import freeze_japanese_frequency
    bundle, profile, verifier = reviewed_fixture(tmp_path)
    with pytest.raises(ValueError, match="3000"):
        freeze_japanese_frequency(bundle=bundle, profile=profile, verifier=verifier,
            selection=[], frequency=tmp_path / "absent.tsv", frequency_sha256="0" * 64,
            source_receipt_id=None, output=tmp_path / "bad")


def test_freeze_connects_all_three_levels_to_existing_frequency_loader(tmp_path, monkeypatch):
    from test_vocabulary_review import sign

    from multilang.domain.jobs import SupportedLanguage
    from multilang.services import japanese_runtime_assets as api
    from multilang.services.frequency_decks import load_curated_frequency_entries
    from multilang.services.lexical_lookup import LexicalLookup
    bundle, profile, verifier = reviewed_fixture(tmp_path)
    first = next(iter(api._reviewed_records(bundle, profile, verifier).values()))
    # Source-review verification is covered above; isolate the 3,000-row join,
    # ordering, signed source selection, file contracts and runtime lookup here.
    records, selection, lines = {}, [], ["word\tcount\tvideos\tchannels"]
    for i in range(3000):
        word, key = chr(0x4e00 + i), f"synthetic-candidate-{i}"
        identity = first[0].model_copy(update={"normalized_lemma": word})
        candidate = first[1].model_copy(update={"candidate_id": key, "lemma": word})
        lexical = first[2].model_copy(update={"term": word, "lemma": word, "display_form": word})
        records[key] = identity, candidate, lexical
        selection.append({"candidate_id": key, "frequency_word": word})
        lines.append(f"{word}\t{3000-i}\t1\t1")
    lines.append(f"[TOTAL]\t{sum(range(1,3001))}\t1\t1")
    source = tmp_path / "counts.tsv"
    source.write_text("\n".join(lines) + "\n")
    digest = sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(api, "_reviewed_records", lambda *args: records)
    payload = api.japanese_frequency_release_payload(bundle=bundle, frequency_sha256=digest, selection=selection)
    receipt = sign(verifier, payload, "japanese-frequency-source")
    kwargs = dict(bundle=bundle, profile=profile, verifier=verifier, selection=selection,
        frequency=source, frequency_sha256=digest, output=tmp_path / "runtime")
    with pytest.raises(ValueError, match="redistribution"):
        api.freeze_japanese_frequency(**kwargs, source_receipt_id=None)
    result = api.freeze_japanese_frequency(**kwargs, source_receipt_id=receipt)
    rows = load_curated_frequency_entries(SupportedLanguage.JA, version="tubelex-jmdict-v1",
        assets_dir=tmp_path / "runtime" / "frequency")
    assert len(rows) == 3000
    assert [sum(row.level == level for row in rows) for level in (1,2,3)] == [1000,1000,1000]
    record = LexicalLookup(tmp_path / "runtime" / "lexicon").lookup(language_code="ja", term=rows[0].lemma_key)
    assert record and record.japanese_reading == first[2].japanese_reading
    assert not result["production_deck_approved"]
