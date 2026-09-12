"""Only synthetic signed reviews are used by these deterministic bridge tests."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from multilang.domain.lexical_identity import canonical_sha256


def api():
    from multilang.services import vocabulary_review

    return vocabulary_review


def profile():
    from multilang.services.language_profiles import LanguageProfileRegistry

    return (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(
            update={
                "analyzer_id": "contextual-morphology",
                "analyzer_version": "1",
                "tagset": "UPOS",
                "tagset_version": "1",
                "source_ids": ("fixture",),
            }
        )
    )


def prepared(tmp_path, *, reverse=False, split="test", with_corpus=False, repeat_corpus=False):
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    records = [
        {
            "word": "go",
            "lang_code": "en",
            "pos": "verb",
            "senses": [
                {
                    "senseid": [sense],
                    "glosses": [gloss],
                    "examples": [{"text": "I went."}, {"text": "He went."}],
                }
            ],
            "forms": [{"form": "went", "tags": ["past"]}],
        }
        for sense, gloss in [("motion", "To move."), ("function", "To function.")]
    ]
    dictionary = tmp_path / "dictionary.jsonl"
    dictionary.write_text(
        "".join(json.dumps(r) + "\n" for r in (records[::-1] if reverse else records))
    )
    output = tmp_path / "prepared"
    corpus_args = {}
    if with_corpus:
        corpus = tmp_path / "corpus.conllu"
        corpus.write_text(
            "# newdoc id = doc\n# sent_id = sent\n# text = I went.\n"
            "1\tI\tI\tPRON\t_\t_\t2\tnsubj\t_\t_\n"
            "2\twent\tgo\tVERB\t_\tTense=Past\t0\troot\t_\tSpaceAfter=No\n"
            "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n\n"
        )
        if repeat_corpus:
            first = corpus.read_text()
            corpus.write_text(
                first
                + first.replace("# newdoc id = doc", "# newdoc id = doc2").replace(
                    "# sent_id = sent", "# sent_id = sent2"
                )
            )
        corpus_args = {
            "corpus": corpus,
            "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
        }
    manifest = prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=hashlib.sha256(dictionary.read_bytes()).hexdigest(),
        output=output,
        corpus_split=split,
        **corpus_args,
    )
    candidates = [
        json.loads(line) for line in (output / "candidates.jsonl").read_text().splitlines()
    ]
    return output, manifest, candidates


def store(tmp_path):
    from multilang.services.native_evidence import EvidenceStore

    root = tmp_path / "receipts"
    root.mkdir(exist_ok=True)
    return EvidenceStore(root, key=b"test-fixture-key-only-no-real-review" * 2)


def sign(store, payload, purpose):
    from multilang.services.native_evidence import SignedEvidence

    receipt = SignedEvidence.sign(
        payload,
        key=store.key,
        signer="synthetic-test-reviewer",
        purpose=purpose,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    return receipt.receipt_id


def review_for(manifest, candidates):
    module = api()
    senses = tuple(
        module.SenseDecision(
            candidate_id=c["candidate_id"],
            candidate_sha256=canonical_sha256(c),
            source_record_sha256=c["source_record_sha256"],
            lemma=c["lemma"],
            pos=c["pos"],
            decision="accepted",
            stable_sense_id=c["source_sense_ids"][0],
            reviewer="synthetic-test-reviewer",
        )
        for c in candidates
    )
    return module.VocabularyReview(
        preparation_sha256=manifest["preparation_sha256"],
        language="en",
        source_id="fixture",
        source_version="fixture-1",
        senses=senses,
    )


def sign_review(review, verifier):
    module = api()
    senses = tuple(
        d.model_copy(
            update={
                "receipt_id": sign(
                    verifier, module.decision_payload(review, d, profile()), "vocabulary-sense"
                )
            }
        )
        if d.decision == "accepted"
        else d
        for d in review.senses
    )
    forms = tuple(
        d.model_copy(
            update={
                "receipt_id": sign(
                    verifier, module.decision_payload(review, d, profile()), "vocabulary-form"
                )
            }
        )
        if d.decision == "accepted"
        else d
        for d in review.forms
    )
    aggregations = tuple(
        d.model_copy(
            update={
                "receipt_id": sign(
                    verifier,
                    module.decision_payload(review, d, profile()),
                    "vocabulary-form-aggregation",
                )
            }
        )
        if d.decision == "accepted"
        else d
        for d in review.aggregations
    )
    return review.model_copy(
        update={"senses": senses, "forms": forms, "aggregations": aggregations}
    )


def compile_review(tmp_path, prep, review, verifier, *, output=None):
    path = tmp_path / "decisions.json"
    path.write_text(review.model_dump_json())
    return api().compile_reviewed_vocabulary(
        preparation_dir=prep,
        decisions_path=path,
        decisions_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        profile=profile(),
        verifier=verifier,
        output=output,
    )


def test_reviewed_distinct_senses_have_stable_identity_ids_across_source_order(tmp_path):
    results = []
    for reverse in (False, True):
        root = tmp_path / str(reverse)
        root.mkdir()
        prep, manifest, candidates = prepared(root, reverse=reverse)
        verifier = store(root)
        review = sign_review(review_for(manifest, candidates), verifier)
        results.append(compile_review(root, prep, review, verifier))
    assert len(results[0].identities) == 2
    assert {i.sense_id for i in results[0].identities} == {"motion", "function"}
    assert [i.lexical_identity_id for i in results[0].identities] == [
        i.lexical_identity_id for i in results[1].identities
    ]
    assert all(i.lemma == "go" and i.part_of_speech == "VERB" for i in results[0].identities)
    assert not results[0].production_eligible
    assert not results[0].forms  # Dictionary form labels alone do not attest context.


def test_pending_rejected_ambiguous_and_forged_reviews_never_create_identity(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    for decision in ("pending", "rejected", "ambiguous", "accepted"):
        changed = review.model_copy(
            update={
                "senses": tuple(
                    d.model_copy(update={"decision": decision, "receipt_id": "f" * 64})
                    for d in review.senses
                )
            }
        )
        bundle = compile_review(tmp_path, prep, changed, verifier)
        assert not bundle.identities
        assert len(bundle.quarantine) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"candidate_sha256": "a" * 64},
        {"source_record_sha256": "b" * 64},
        {"lemma": "GO"},
        {"pos": "NOUN"},
        {"candidate_id": "missing"},
    ],
)
def test_even_signed_wrong_candidate_evidence_is_rejected(tmp_path, changes):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    review = review.model_copy(update={"senses": (review.senses[0].model_copy(update=changes),)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert not bundle.identities
    assert bundle.quarantine


def test_conflicting_decisions_are_quarantined_instead_of_first_sense(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    first = review.senses[0]
    review = review.model_copy(
        update={"senses": (first, first.model_copy(update={"stable_sense_id": "other"}))}
    )
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert not bundle.identities
    assert any(q.reason == "ambiguous_review" for q in bundle.quarantine)


def form_decision(review, candidate, manifest):
    from multilang.domain.lexical_identity import LexicalIdentity, MorphologicalAnalysis
    from multilang.services.contextual_morphology import (
        ContextualToken,
        ReviewedSenseBinding,
        sentence_hash,
    )

    identity = LexicalIdentity(
        language="en",
        normalized_lemma="go",
        part_of_speech="VERB",
        sense_id="motion",
        profile_version=profile().version,
        normalizer_version=profile().normalization_version,
        analyzer_version=profile().analyzer_version,
        source_id="fixture",
        source_version="fixture-1",
        source_sha256=candidate["source_record_sha256"],
    )
    token = ContextualToken(
        text="went",
        lemma="go",
        pos="VERB",
        features=(("Tense", "Past"),),
        start=2,
        end=6,
        sentence_sha256=sentence_hash("I went."),
        model_fingerprint="e" * 64,
    )
    analysis = MorphologicalAnalysis(
        lexical_identity_id=identity.lexical_identity_id,
        analyzer_id=profile().analyzer_id,
        analyzer_version=profile().analyzer_version,
        features={"tense": "Past"},
        confidence="1",
        evidence_sha256=token.analysis_id,
        sense_context="motion",
    )
    binding = ReviewedSenseBinding(
        language="en",
        sentence_sha256=token.sentence_sha256,
        start=2,
        end=6,
        token_analysis_id=token.analysis_id,
        lexical_identity_id=identity.lexical_identity_id,
        sense_id="motion",
        morphological_analysis_id=analysis.morphological_analysis_id,
        concept_id="motion",
        source_sha256=manifest["dictionary_sha256"],
        reviewer="synthetic-test-reviewer",
        review_receipt_sha256="0" * 64,
    )
    return api().ObservedFormDecision(
        decision_id="observation:went",
        candidate_id=candidate["candidate_id"],
        decision="accepted",
        reviewer="synthetic-test-reviewer",
        context="I went.",
        context_source="dictionary_example",
        context_source_sha256=manifest["dictionary_sha256"],
        token=token,
        binding=binding,
        analysis=analysis,
    )


def reviewed_form(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    candidate = next(c for c in candidates if c["source_sense_ids"] == ["motion"])
    form = form_decision(review, candidate, manifest)
    # The original binding receipt is independently verified for its own purpose.
    receipt = sign(
        verifier,
        form.binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    form = form.model_copy(
        update={"binding": form.binding.model_copy(update={"review_receipt_sha256": receipt})}
    )
    return prep, verifier, review.model_copy(update={"forms": (form,)})


def test_observed_form_is_retained_without_automatic_important_approval(tmp_path):
    prep, verifier, review = reviewed_form(tmp_path)
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.text for f in bundle.forms] == ["went"]
    assert bundle.forms[0].analysis.features == {"tense": "Past"}
    assert not bundle.important_forms
    assert bundle.workload["observed_forms"] == 1
    with pytest.raises(TypeError):
        bundle.forms[0].analysis.features["tense"] = "Pres"


def test_existing_binding_review_can_be_reused_by_a_different_form_reviewer(tmp_path):
    prep, verifier, review = reviewed_form(tmp_path)
    form = review.forms[0].model_copy(update={"reviewer": "second-synthetic-reviewer"})
    review = review.model_copy(update={"forms": (form,)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.text for f in bundle.forms] == ["went"]
    assert bundle.review.forms[0].binding.reviewer == "synthetic-test-reviewer"


@pytest.mark.parametrize("change", ["context", "span", "hash", "analysis", "binding", "unobserved"])
def test_wrong_form_context_span_hash_analysis_or_binding_rejected(tmp_path, change):
    prep, verifier, review = reviewed_form(tmp_path)
    form = review.forms[0]
    if change == "context":
        form = form.model_copy(update={"context": "I want."})
    elif change == "span":
        form = form.model_copy(
            update={"token": form.token.model_copy(update={"start": 1, "end": 5})}
        )
    elif change == "hash":
        form = form.model_copy(update={"context_source_sha256": "a" * 64})
    elif change == "analysis":
        form = form.model_copy(
            update={"analysis": form.analysis.model_copy(update={"features": {"tense": "Pres"}})}
        )
    elif change == "binding":
        form = form.model_copy(
            update={"binding": form.binding.model_copy(update={"review_receipt_sha256": "a" * 64})}
        )
    else:
        form = form.model_copy(update={"context": "We went."})
    review = review.model_copy(update={"forms": (form,)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert not bundle.forms
    assert any(q.kind == "form" for q in bundle.quarantine)


def test_preparation_and_decision_bytes_are_hash_verified(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = sign_review(review_for(manifest, candidates), verifier)
    (prep / "candidates.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="checksum"):
        compile_review(tmp_path, prep, review, verifier)


def test_output_and_signed_bundle_round_trip_are_immutable(tmp_path):
    prep, verifier, review = reviewed_form(tmp_path)
    bundle = compile_review(
        tmp_path, prep, sign_review(review, verifier), verifier, output=tmp_path / "compiled"
    )
    path = tmp_path / "compiled" / "bundle.json"
    restored = api().load_compiled_vocabulary(
        path,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        profile=profile(),
        verifier=verifier,
    )
    assert restored == bundle
    assert restored.forms
    with pytest.raises(ValueError, match="new|exist|replace"):
        compile_review(tmp_path, prep, review, verifier, output=tmp_path / "compiled")
    assert json.loads(path.read_text())["production_eligible"] is False


def test_test_corpus_cannot_be_requested_as_ranking_input(tmp_path):
    prep, manifest, candidates = prepared(tmp_path, split="test", with_corpus=True)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates).model_copy(update={"use_corpus_for_ranking": True})
    with pytest.raises(ValueError, match="ranking|held.out|test"):
        compile_review(tmp_path, prep, sign_review(review, verifier), verifier)


def test_sparse_oversized_bundle_is_rejected_before_reading(tmp_path):
    path = tmp_path / "oversized.json"
    with path.open("wb") as stream:
        stream.truncate(128 * 1024**2 + 1)
    with pytest.raises(ValueError, match="bounded|limit"):
        api().load_compiled_vocabulary(
            path, expected_sha256="a" * 64, profile=profile(), verifier=store(tmp_path)
        )


def test_decisions_checksum_is_verified(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    path = tmp_path / "decisions.json"
    path.write_text(review_for(manifest, candidates).model_dump_json())
    with pytest.raises(ValueError, match="checksum"):
        api().compile_reviewed_vocabulary(
            preparation_dir=prep,
            decisions_path=path,
            decisions_sha256="a" * 64,
            profile=profile(),
            verifier=store(tmp_path),
        )


def test_corpus_form_uses_exact_source_sentence_and_can_only_stage_train_rank_input(tmp_path):
    prep, manifest, candidates = prepared(tmp_path, split="train", with_corpus=True)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    candidate = next(c for c in candidates if c["source_sense_ids"] == ["motion"])
    form = form_decision(review, candidate, manifest)
    binding = form.binding.model_copy(update={"source_sha256": manifest["corpus"]["sha256"]})
    receipt = sign(
        verifier,
        binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    form = form.model_copy(
        update={
            "context_source": "corpus",
            "document_id": "doc",
            "sentence_id": "sent",
            "context_source_sha256": manifest["corpus"]["sha256"],
            "binding": binding.model_copy(update={"review_receipt_sha256": receipt}),
        }
    )
    review = review.model_copy(update={"forms": (form,), "use_corpus_for_ranking": True})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.text for f in bundle.forms] == ["went"]
    assert bundle.ranking_inputs["split"] == "train"
    assert not bundle.ranking_inputs["canonical_ranking_input"]
    assert not bundle.production_eligible


def test_bundle_reverification_rejects_rewritten_source_snapshots(tmp_path):
    prep, manifest, candidates = prepared(tmp_path)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    review = review.model_copy(
        update={
            "senses": tuple(d.model_copy(update={"decision": "pending"}) for d in review.senses)
        }
    )
    bundle = compile_review(tmp_path, prep, review, verifier)
    candidate = bundle.candidates[0].model_copy(update={"examples": ("Invented context.",)})
    quarantine = tuple(
        q.model_copy(
            update={"candidate_sha256": canonical_sha256(candidate.model_dump(mode="json"))}
        )
        if q.record_id == candidate.candidate_id
        else q
        for q in bundle.quarantine
    )
    changed = bundle.model_copy(
        update={"candidates": (candidate, *bundle.candidates[1:]), "quarantine": quarantine}
    )
    with pytest.raises(ValueError, match="source|checksum|artifact"):
        api().verify_compiled_vocabulary(changed, profile=profile(), verifier=verifier)


def test_unapproved_importance_does_not_discard_an_observed_form(tmp_path):
    prep, verifier, review = reviewed_form(tmp_path)
    review = review.model_copy(
        update={"forms": (review.forms[0].model_copy(update={"important": True}),)}
    )
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.text for f in bundle.forms] == ["went"]
    assert not bundle.important_forms
    assert any(q.reason == "unverified_important_form_policy" for q in bundle.quarantine)


def test_important_form_requires_explicit_decision_and_signed_policy(tmp_path):
    from multilang.domain.lexical_identity import ImportantFormPolicy

    prep, verifier, review = reviewed_form(tmp_path)
    policy = ImportantFormPolicy(
        policy_id="fixture-only",
        version="1",
        weights={"irregularity": "1"},
        minimum_score="0.5",
        attestation_threshold=1,
        analysis_confidence_threshold="1",
        approval_sha256="0" * 64,
    )
    review = review.model_copy(
        update={
            "important_form_policy": policy,
            "policy_reviewer": "synthetic-test-reviewer",
            "forms": (
                review.forms[0].model_copy(
                    update={"important": True, "evidence_values": {"irregularity": "1"}}
                ),
            ),
        }
    )
    receipt = sign(verifier, api().policy_payload(review, profile()), "vocabulary-form-policy")
    review = review.model_copy(
        update={"important_form_policy": policy.model_copy(update={"approval_sha256": receipt})}
    )
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert len(bundle.forms) == len(bundle.important_forms) == 1
    assert bundle.important_forms[0].form.text == "went"


def aggregation_review(tmp_path):
    from multilang.services.contextual_morphology import sentence_hash

    prep, verifier, review = reviewed_form(tmp_path)
    first = review.forms[0]
    token = first.token.model_copy(
        update={"start": 3, "end": 7, "sentence_sha256": sentence_hash("He went.")}
    )
    analysis = first.analysis.model_copy(update={"evidence_sha256": token.analysis_id})
    binding = first.binding.model_copy(
        update={
            "start": 3,
            "end": 7,
            "sentence_sha256": token.sentence_sha256,
            "token_analysis_id": token.analysis_id,
        }
    )
    receipt = sign(
        verifier,
        binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    second = first.model_copy(
        update={
            "decision_id": "observation:went-2",
            "context": "He went.",
            "token": token,
            "analysis": analysis,
            "binding": binding.model_copy(update={"review_receipt_sha256": receipt}),
        }
    )
    aggregate = api().FormAggregationDecision(
        aggregation_id="aggregate:went",
        decision="accepted",
        reviewer="synthetic-aggregate-reviewer",
        observation_ids=(first.decision_id, second.decision_id),
        representative_observation_id=first.decision_id,
        representative_context=first.context,
        lexical_identity_id=first.analysis.lexical_identity_id,
        text="went",
        morphological_analysis_id=first.analysis.morphological_analysis_id,
        model_fingerprint=first.token.model_fingerprint,
        attestation=2,
    )
    return (
        prep,
        verifier,
        review.model_copy(update={"forms": (first, second), "aggregations": (aggregate,)}),
    )


def test_explicit_reviewed_aggregation_counts_observations_and_preserves_originals(tmp_path):
    prep, verifier, review = aggregation_review(tmp_path)
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert len(bundle.forms) == 1
    assert bundle.forms[0].attestation == 2
    assert bundle.forms[0].context == "I went."
    assert len(bundle.observations) == 2
    assert all(o.form.attestation == 1 for o in bundle.observations)
    assert not bundle.quarantine
    assert api().verify_compiled_vocabulary(bundle, profile=profile(), verifier=verifier) == bundle


@pytest.mark.parametrize(
    "change", ["duplicate", "missing", "count", "sense", "model", "context", "unsigned"]
)
def test_invalid_aggregation_never_inflates_attestation(tmp_path, change):
    prep, verifier, review = aggregation_review(tmp_path)
    aggregate = review.aggregations[0]
    updates = {
        "duplicate": {"observation_ids": (review.forms[0].decision_id,) * 2},
        "missing": {"observation_ids": (review.forms[0].decision_id, "unknown")},
        "count": {"attestation": 3},
        "sense": {"lexical_identity_id": "lex:wrong"},
        "model": {"model_fingerprint": "f" * 64},
        "context": {"representative_context": "Invented."},
    }
    if change in updates:
        review = review.model_copy(
            update={"aggregations": (aggregate.model_copy(update=updates[change]),)}
        )
    review = sign_review(review, verifier)
    if change == "unsigned":
        review = review.model_copy(
            update={
                "aggregations": (
                    review.aggregations[0].model_copy(update={"receipt_id": "f" * 64}),
                )
            }
        )
    bundle = compile_review(tmp_path, prep, review, verifier)
    assert not any(f.attestation > 1 for f in bundle.forms)
    assert len(bundle.observations) == 2
    assert any(q.kind == "aggregation" for q in bundle.quarantine)


def test_signed_aggregation_can_meet_important_policy_attestation_threshold(tmp_path):
    from multilang.domain.lexical_identity import ImportantFormPolicy

    prep, verifier, review = aggregation_review(tmp_path)
    policy = ImportantFormPolicy(
        policy_id="fixture-aggregate",
        version="1",
        weights={"frequency": "1"},
        minimum_score="0.5",
        attestation_threshold=2,
        analysis_confidence_threshold="1",
        approval_sha256="0" * 64,
    )
    aggregate = review.aggregations[0].model_copy(
        update={"important": True, "evidence_values": {"frequency": "1"}}
    )
    review = review.model_copy(
        update={
            "aggregations": (aggregate,),
            "important_form_policy": policy,
            "policy_reviewer": "synthetic-policy-reviewer",
        }
    )
    receipt = sign(verifier, api().policy_payload(review, profile()), "vocabulary-form-policy")
    review = review.model_copy(
        update={"important_form_policy": policy.model_copy(update={"approval_sha256": receipt})}
    )
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert len(bundle.important_forms) == 1
    assert bundle.important_forms[0].form.attestation == 2


def test_aggregation_receipt_binds_exact_observation_payloads_not_reusable_labels(tmp_path):
    prep, verifier, review = aggregation_review(tmp_path)
    review = sign_review(review, verifier)
    second = review.forms[1]
    second = second.model_copy(
        update={"analysis": second.analysis.model_copy(update={"confidence": "0.5"})}
    )
    second = second.model_copy(
        update={
            "receipt_id": sign(
                verifier, api().decision_payload(review, second, profile()), "vocabulary-form"
            )
        }
    )
    review = review.model_copy(update={"forms": (review.forms[0], second)})
    bundle = compile_review(tmp_path, prep, review, verifier)
    assert not any(f.attestation > 1 for f in bundle.forms)
    assert any(q.kind == "aggregation" for q in bundle.quarantine)


def test_explicit_aggregate_can_count_a_reviewed_subset_without_losing_other_observations(tmp_path):
    prep, verifier, review = aggregation_review(tmp_path)
    extra = review.forms[0].model_copy(update={"decision_id": "additional-observation-label"})
    review = review.model_copy(update={"forms": (*review.forms, extra)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.attestation for f in bundle.forms] == [2]
    assert len(bundle.observations) == 3


def test_reanalysis_of_one_source_occurrence_cannot_inflate_attestation(tmp_path):
    prep, verifier, review = aggregation_review(tmp_path)
    first, second = review.forms
    token = first.token.model_copy(update={"features": (*first.token.features, ("XPOS", "VBD"))})
    analysis = first.analysis.model_copy(update={"evidence_sha256": token.analysis_id})
    binding = first.binding.model_copy(update={"token_analysis_id": token.analysis_id})
    receipt = sign(
        verifier,
        binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    second = second.model_copy(
        update={
            "context": first.context,
            "token": token,
            "analysis": analysis,
            "binding": binding.model_copy(update={"review_receipt_sha256": receipt}),
        }
    )
    review = review.model_copy(update={"forms": (first, second)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert not any(f.attestation > 1 for f in bundle.forms)
    assert any(q.kind == "aggregation" for q in bundle.quarantine)


def test_identical_text_at_distinct_authenticated_corpus_locations_counts_separately(tmp_path):
    prep, manifest, candidates = prepared(tmp_path, with_corpus=True, repeat_corpus=True)
    verifier = store(tmp_path)
    review = review_for(manifest, candidates)
    candidate = next(c for c in candidates if c["source_sense_ids"] == ["motion"])
    first = form_decision(review, candidate, manifest)
    binding = first.binding.model_copy(update={"source_sha256": manifest["corpus"]["sha256"]})
    receipt = sign(
        verifier,
        binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    )
    first = first.model_copy(
        update={
            "context_source": "corpus",
            "context_source_sha256": manifest["corpus"]["sha256"],
            "document_id": "doc",
            "sentence_id": "sent",
            "binding": binding.model_copy(update={"review_receipt_sha256": receipt}),
        }
    )
    second = first.model_copy(
        update={
            "decision_id": "observation:second-location",
            "document_id": "doc2",
            "sentence_id": "sent2",
        }
    )
    aggregate = api().FormAggregationDecision(
        aggregation_id="aggregate:repeated-text",
        decision="accepted",
        reviewer="synthetic-aggregate-reviewer",
        observation_ids=(first.decision_id, second.decision_id),
        representative_observation_id=first.decision_id,
        representative_context=first.context,
        lexical_identity_id=first.analysis.lexical_identity_id,
        text="went",
        morphological_analysis_id=first.analysis.morphological_analysis_id,
        model_fingerprint=first.token.model_fingerprint,
        attestation=2,
    )
    review = review.model_copy(update={"forms": (first, second), "aggregations": (aggregate,)})
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    assert [f.attestation for f in bundle.forms] == [2]


def native_review_case(tmp_path, monkeypatch, *, flag=True, qualified=True):
    import sys

    from sqlalchemy import create_engine

    from multilang.db.base import Base
    from multilang.domain.language_profiles import POLICY_GROUPS, CapabilityEvidence
    from multilang.native_runtime import NativeFacade  # Registers native tables.
    from multilang.settings import Settings

    selected = profile()
    if qualified:
        approval = CapabilityEvidence(state="enabled", evidence_sha256="e" * 64)
        selected = selected.model_copy(
            update={
                "capabilities": {"core": approval},
                "policies": {group: approval for group in POLICY_GROUPS},
            }
        )
    monkeypatch.setattr(sys.modules[__name__], "profile", lambda: selected)
    prep, verifier, review = aggregation_review(tmp_path)
    bundle = compile_review(tmp_path, prep, sign_review(review, verifier), verifier)
    settings = Settings(
        _env_file=None,
        roadmap_4_enabled=flag,
        native_evidence_dir=verifier.root,
        native_evidence_signing_key=verifier.key.decode("ascii"),
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    payload = {
        "format": "reviewed-vocabulary",
        "profile_version": selected.version,
        "version": "fixture-import-1",
        "namespace": "core",
        "bundle": bundle.model_dump(mode="json"),
    }
    return engine, settings, payload, bundle, NativeFacade


def test_native_reviewed_import_preserves_aggregate_forms_search_ids_and_replay(
    tmp_path, monkeypatch
):
    from sqlalchemy.orm import Session

    engine, settings, payload, bundle, facade_class = native_review_case(tmp_path, monkeypatch)
    try:
        with Session(engine) as session:
            facade = facade_class(session, settings)
            facade.repository.put_profile(profile())
            # Earlier global evidence must not leak into this reviewed edition.
            for identity in bundle.identities:
                facade.repository.put_identity(identity, actor="fixture", reason="prior-source")
            other_form = bundle.forms[0].model_copy(update={"text": "gone"})
            facade.repository.put_form(
                other_form,
                identity_id=other_form.lexical_identity_id,
                analysis_id=other_form.analysis.morphological_analysis_id,
                text=other_form.text,
                actor="fixture",
            )
            result = facade.import_dataset(payload, actor="synthetic-import-reviewer")
            session.commit()
            assert result["identity_count"] == 2
            assert result["form_count"] == 1
            assert result["important_form_count"] == 0
            assert result["production_eligible"] is False
            stored = facade.repository.dataset_forms(result["dataset_id"])
            assert [(f.text, f.attestation) for f in stored] == [("went", 2)]
            from multilang.services.vocabulary_review import load_compiled_vocabulary

            metadata = facade.repository.get_dataset(result["dataset_id"])["metadata"]
            artifact = metadata["review_bundle_artifact_sha256"]
            restored = load_compiled_vocabulary(
                settings.native_evidence_dir / "artifacts" / artifact,
                expected_sha256=artifact,
                profile=profile(),
                verifier=store(tmp_path),
            )
            assert restored == bundle
            assert {
                i.lexical_identity_id
                for i in facade.repository.dataset_identities(result["dataset_id"])
            } == {i.lexical_identity_id for i in bundle.identities}
            assert len(facade.search("go", language="en")) == 2
            replay = facade.import_dataset(payload, actor="synthetic-import-reviewer")
            assert replay["dataset_id"] == result["dataset_id"]
            assert len(facade.repository.dataset_forms(result["dataset_id"])) == 1
    finally:
        engine.dispose()


def test_native_reviewed_import_rejects_modified_bundle_before_writing(tmp_path, monkeypatch):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from multilang.db.native_models import LexicalIdentityRecord, SurfaceFormRecord

    engine, settings, payload, bundle, facade_class = native_review_case(tmp_path, monkeypatch)
    changed = bundle.model_copy(
        update={"forms": (bundle.forms[0].model_copy(update={"attestation": 99}),)}
    )
    payload = {**payload, "bundle": changed.model_dump(mode="json")}
    try:
        with Session(engine) as session:
            facade = facade_class(session, settings)
            facade.repository.put_profile(profile())
            with pytest.raises(ValueError):
                facade.import_dataset(payload, actor="synthetic-import-reviewer")
            assert session.scalar(select(func.count()).select_from(LexicalIdentityRecord)) == 0
            assert session.scalar(select(func.count()).select_from(SurfaceFormRecord)) == 0
            assert not facade.list_datasets()
    finally:
        engine.dispose()


@pytest.mark.parametrize("blocked", ["flag", "profile"])
def test_native_reviewed_import_requires_enabled_flag_and_qualified_profile(
    tmp_path, monkeypatch, blocked
):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from multilang.db.native_models import LexicalIdentityRecord

    engine, settings, payload, _bundle, facade_class = native_review_case(
        tmp_path, monkeypatch, flag=blocked != "flag", qualified=blocked != "profile"
    )
    try:
        with Session(engine) as session:
            facade = facade_class(session, settings)
            facade.repository.put_profile(profile())
            with pytest.raises(
                ValueError, match="ROADMAP_4_ENABLED|capability|not enabled|qualification"
            ):
                facade.import_dataset(payload, actor="synthetic-import-reviewer")
            assert session.scalar(select(func.count()).select_from(LexicalIdentityRecord)) == 0
    finally:
        engine.dispose()
