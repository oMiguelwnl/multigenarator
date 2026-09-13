"""Qualification labels require separate existing vocabulary evidence receipts."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_review import (
    FormDecision,
    FormReviewItem,
    HumanReviewSubmission,
    LexicalDecision,
    LexicalReviewItem,
    ReviewPacket,
    ReviewSource,
    review_signing_payload,
)


def bridge():
    from multilang.services.qualification_bridge import build_vocabulary_review_input

    return build_vocabulary_review_input


def fixture(
    tmp_path, *, corrected=False, include_form=False, source_pos="verb", dictionary_forms=False
):
    from multilang.services.language_profiles import LanguageProfileRegistry
    from multilang.services.native_evidence import EvidenceStore, SignedEvidence
    from multilang.services.vocabulary_preparation import prepare_vocabulary

    dictionary = tmp_path / "source.jsonl"
    dictionary.write_text(
        json.dumps(
            {
                "lang_code": "en",
                "word": "go",
                "pos": source_pos,
                "forms": [{"form": "went", "tags": ["past"]}] if dictionary_forms else [],
                "senses": [{"glosses": ["To move."], "senseid": ["motion"]}],
            }
        )
        + "\n"
    )
    prepared = tmp_path / "prepared"
    prepare_vocabulary(
        language="en",
        dictionary=dictionary,
        dictionary_sha256=hashlib.sha256(dictionary.read_bytes()).hexdigest(),
        output=prepared,
    )
    candidate = json.loads((prepared / "candidates.jsonl").read_text().splitlines()[0])
    profile = (
        LanguageProfileRegistry()
        .get("en")
        .model_copy(
            update={
                "source_ids": ("synthetic",),
                "analyzer_id": "contextual-morphology",
                "analyzer_version": "1",
            }
        )
    )
    source = ReviewSource(
        source_id="synthetic",
        source_sha256=candidate["source_record_sha256"],
        record_id=candidate["candidate_id"],
        excerpt="To move.",
    )
    item = LexicalReviewItem(
        item_id="lexical-1",
        candidate_id=candidate["candidate_id"],
        candidate_sha256=canonical_sha256(candidate),
        lemma="go",
        pos=candidate["pos"],
        sources=(source,),
    )
    choice = LexicalDecision(
        item_id=item.item_id,
        item_sha256=item.item_sha256,
        decision="corrected" if corrected else "accepted",
        reason="Synthetic review only",
        canonical_sense_id="motion",
        corrected_lemma="move" if corrected else None,
        corrected_pos="VERB" if corrected else None,
    )
    items, choices = [item], [choice]
    if include_form:
        form = FormReviewItem(
            item_id="form-1",
            candidate_id=candidate["candidate_id"],
            candidate_sha256=canonical_sha256(candidate),
            lemma="go",
            pos="VERB",
            text="went",
            sources=(source,),
        )
        items.append(form)
        choices.append(
            FormDecision(
                item_id=form.item_id,
                item_sha256=form.item_sha256,
                decision="accepted",
                reason="Synthetic form label",
                include=True,
            )
        )
    packet = ReviewPacket(
        packet_id="synthetic",
        language="en",
        split="pilot",
        profile_sha256=canonical_sha256(profile.model_dump(mode="json")),
        rubric_sha256="a" * 64,
        items=tuple(items),
    )
    submission = HumanReviewSubmission(
        packet_sha256=packet.packet_sha256,
        reviewer_id="synthetic",
        expertise_declaration="Synthetic only",
        reviewed_at=datetime.now(UTC),
        decisions=tuple(choices),
    )
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    store = EvidenceStore(evidence_root, key=b"synthetic-test-key-only" * 3)
    receipt = SignedEvidence.sign(
        review_signing_payload(packet, submission),
        key=store.key,
        signer="synthetic",
        purpose="qualification-review",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    (evidence_root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    submission = submission.model_copy(update={"receipt_id": receipt.receipt_id})
    return dict(
        preparation_dir=prepared,
        packet=packet,
        submission=submission,
        expected_reviewer="synthetic",
        verifier=store,
        profile=profile,
        source_id="synthetic",
        source_version="1",
    )


def test_authenticated_lexical_decision_produces_unsigned_existing_signing_input(tmp_path):
    result = bridge()(**fixture(tmp_path))
    assert result.review.senses[0].decision == "accepted"
    assert result.review.senses[0].stable_sense_id == "motion"
    assert result.review.senses[0].receipt_id is None
    assert result.unsigned_payloads[0].purpose == "vocabulary-sense"
    assert not result.production_eligible


def test_corrected_source_facts_remain_actionable_without_rewriting_source(tmp_path):
    kwargs = fixture(tmp_path, corrected=True)
    before = (kwargs["preparation_dir"] / "candidates.jsonl").read_bytes()
    result = bridge()(**kwargs)
    assert result.review.senses[0].decision == "pending"
    assert not result.unsigned_payloads
    assert result.source_corrections[0].corrected_lemma == "move"
    assert result.source_corrections[0].qualification_receipt_id == kwargs["submission"].receipt_id
    assert result.blockers[0].reason == "source_correction_requires_new_preparation"
    assert (kwargs["preparation_dir"] / "candidates.jsonl").read_bytes() == before


def test_forms_without_exact_native_evidence_are_retained_pending(tmp_path):
    result = bridge()(**fixture(tmp_path, include_form=True))
    assert len(result.review.forms) == 1
    assert result.review.forms[0].decision == "pending"
    assert result.review.forms[0].receipt_id is None
    assert any(b.reason == "exact_native_form_evidence_required" for b in result.blockers)


@pytest.mark.parametrize("failure", ["unsigned", "profile", "source", "candidate"])
def test_bridge_rechecks_authority_and_source_projection(tmp_path, failure):
    kwargs = fixture(tmp_path)
    if failure == "unsigned":
        kwargs["submission"] = kwargs["submission"].model_copy(update={"receipt_id": None})
    elif failure == "profile":
        kwargs["profile"] = kwargs["profile"].model_copy(update={"version": "other"})
    elif failure == "source":
        kwargs["source_id"] = "unauthorized"
    else:
        path = kwargs["preparation_dir"] / "candidates.jsonl"
        path.write_text(path.read_text().replace('"go"', '"move"'))
    with pytest.raises(ValueError):
        bridge()(**kwargs)


def test_corrected_source_is_a_new_pending_preparation_with_complete_provenance(tmp_path):
    from multilang.services.qualification_bridge import apply_reviewed_lexical_corrections
    from multilang.services.vocabulary_review import _load_preparation, create_pending_review

    kwargs = fixture(tmp_path, corrected=True)
    original = (kwargs["preparation_dir"] / "candidates.jsonl").read_bytes()
    output = tmp_path / "derived"
    result = apply_reviewed_lexical_corrections(**kwargs, output=output)
    manifest, candidates, _corpus, _artifacts = _load_preparation(output)
    old = json.loads(original)
    assert candidates[0].lemma == "move"
    assert candidates[0].candidate_id != old["candidate_id"]
    assert candidates[0].source_record_sha256 == old["source_record_sha256"]
    assert (
        manifest["correction_provenance"]["original_preparation_sha256"]
        == result.original_preparation_sha256
    )
    assert (
        manifest["correction_provenance"]["signed_qualification_payload"]["submission"][
            "reviewer_id"
        ]
        == "synthetic"
    )
    assert (output / "source-corrections.json").exists()
    assert (
        create_pending_review(output, source_id="synthetic", source_version="corrected-1")
        .senses[0]
        .decision
        == "pending"
    )
    assert (kwargs["preparation_dir"] / "candidates.jsonl").read_bytes() == original
    with pytest.raises(ValueError, match="exists"):
        apply_reviewed_lexical_corrections(**kwargs, output=output)


def test_derived_candidates_use_existing_separate_signing_and_compile_flow(tmp_path):
    from multilang.services.native_evidence import SignedEvidence
    from multilang.services.qualification_bridge import apply_reviewed_lexical_corrections
    from multilang.services.vocabulary_review import (
        compile_reviewed_vocabulary,
        create_pending_review,
        decision_payload,
        verify_compiled_vocabulary,
    )

    kwargs = fixture(tmp_path, corrected=True)
    output = tmp_path / "derived"
    apply_reviewed_lexical_corrections(**kwargs, output=output)
    review = create_pending_review(output, source_id="synthetic", source_version="corrected-1")
    choice = review.senses[0].model_copy(
        update={"decision": "accepted", "stable_sense_id": "motion", "reviewer": "synthetic"}
    )
    review = review.model_copy(update={"senses": (choice,)})
    store = kwargs["verifier"]
    receipt = SignedEvidence.sign(
        decision_payload(review, choice, kwargs["profile"]),
        key=store.key,
        signer="synthetic",
        purpose="vocabulary-sense",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    review = review.model_copy(
        update={"senses": (choice.model_copy(update={"receipt_id": receipt.receipt_id}),)}
    )
    path = tmp_path / "review.json"
    path.write_text(review.model_dump_json())
    bundle = compile_reviewed_vocabulary(
        preparation_dir=output,
        decisions_path=path,
        decisions_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        profile=kwargs["profile"],
        verifier=store,
    )
    assert bundle.identities[0].lemma == "move"
    assert (
        bundle.preparation_manifest["correction_provenance"]["corrections"][0][
            "original_candidate"
        ]["lemma"]
        == "go"
    )
    assert verify_compiled_vocabulary(bundle, profile=kwargs["profile"], verifier=store) == bundle


def actual_pilot_request(tmp_path, *, unresolved=False, form=False):
    from multilang.services.native_evidence import SignedEvidence
    from multilang.services.qualification_pilot import (
        PreparedVocabularyInput,
        prepare_qualification_pilot,
    )

    kwargs = fixture(tmp_path, source_pos="conj" if unresolved else "verb", dictionary_forms=form)
    output = tmp_path / "pilot"
    manifest = prepare_qualification_pilot(
        language="en",
        prepared_inputs=(
            PreparedVocabularyInput(
                directory=kwargs["preparation_dir"],
                manifest_sha256=hashlib.sha256(
                    (kwargs["preparation_dir"] / "manifest.json").read_bytes()
                ).hexdigest(),
            ),
        ),
        seed_words=("go",),
        headword_count=1,
        profile_sha256=canonical_sha256(kwargs["profile"].model_dump(mode="json")),
        rubric_sha256="a" * 64,
        output=output,
    )
    kind = "unresolved" if unresolved else "dictionary-forms" if form else "lexical"
    record = next(record for record in manifest["packets"] if record["kind"] == kind)
    packet = ReviewPacket.model_validate_json(
        (output / record["path"] / "packet.json").read_bytes()
    )
    item = packet.items[0]
    decision_args = dict(
        item_id=item.item_id, item_sha256=item.item_sha256, reason="Synthetic pilot review only"
    )
    decision = (
        FormDecision(**decision_args, decision="accepted", include=True)
        if form
        else LexicalDecision(
            **decision_args,
            decision="corrected" if unresolved else "accepted",
            canonical_sense_id="motion",
            corrected_lemma=item.lemma if unresolved else None,
            corrected_pos="SCONJ" if unresolved else None,
        )
    )
    submission = HumanReviewSubmission(
        packet_sha256=packet.packet_sha256,
        reviewer_id="synthetic",
        expertise_declaration="Synthetic only",
        reviewed_at=datetime.now(UTC),
        decisions=(decision,),
    )
    store = kwargs["verifier"]
    receipt = SignedEvidence.sign(
        review_signing_payload(packet, submission),
        key=store.key,
        signer="synthetic",
        purpose="qualification-review",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    kwargs.update(
        packet=packet, submission=submission.model_copy(update={"receipt_id": receipt.receipt_id})
    )
    return kwargs


def test_actual_pilot_transport_label_binds_verified_dictionary_and_record(tmp_path):
    kwargs = actual_pilot_request(tmp_path)
    assert kwargs["packet"].items[0].sources[0].source_id == "prepared-dictionary"
    result = bridge()(**kwargs)
    assert result.review.senses[0].decision == "accepted"
    assert result.review.source_id == "synthetic"
    assert result.unsigned_payloads[0].purpose == "vocabulary-sense"


def test_actual_unresolved_pilot_can_apply_explicit_source_pos_correction(tmp_path):
    from multilang.services.qualification_bridge import apply_reviewed_lexical_corrections
    from multilang.services.vocabulary_review import _load_preparation

    kwargs = actual_pilot_request(tmp_path, unresolved=True)
    assert kwargs["packet"].items[0].pos == "X"
    result = bridge()(**kwargs)
    assert result.source_corrections[0].original_pos == "CCONJ"
    assert result.source_corrections[0].corrected_pos == "SCONJ"
    output = tmp_path / "derived"
    apply_reviewed_lexical_corrections(**kwargs, output=output)
    assert _load_preparation(output)[1][0].pos == "SCONJ"


def test_actual_dictionary_form_pilot_remains_pending_without_native_parent_guess(tmp_path):
    kwargs = actual_pilot_request(tmp_path, form=True)
    result = bridge()(**kwargs)
    assert not result.unsigned_payloads
    assert result.review.forms[0].decision == "pending"
    assert result.review.forms[0].receipt_id is None
    assert result.blockers[0].reason == "unresolved_native_candidate_parent"


def test_transport_label_does_not_allow_unrelated_record_even_with_review_receipt(tmp_path):
    from multilang.services.native_evidence import SignedEvidence

    kwargs = actual_pilot_request(tmp_path)
    item = kwargs["packet"].items[0]
    item = item.model_copy(
        update={"sources": (item.sources[0].model_copy(update={"record_id": "wrong-record"}),)}
    )
    packet = kwargs["packet"].model_copy(update={"items": (item,)})
    submission = kwargs["submission"].model_copy(
        update={
            "packet_sha256": packet.packet_sha256,
            "decisions": (
                kwargs["submission"]
                .decisions[0]
                .model_copy(update={"item_sha256": item.item_sha256}),
            ),
            "receipt_id": None,
        }
    )
    store = kwargs["verifier"]
    receipt = SignedEvidence.sign(
        review_signing_payload(packet, submission),
        key=store.key,
        signer="synthetic",
        purpose="qualification-review",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    kwargs.update(
        packet=packet, submission=submission.model_copy(update={"receipt_id": receipt.receipt_id})
    )
    with pytest.raises(ValueError, match="source reference"):
        bridge()(**kwargs)
