"""Korean frozen-prefix and hard-gate text-quality evidence tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanConcept,
    KoreanFrequencyEntry,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
    raw_bytes_sha256,
)


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def _fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _entry(rank: int, *, lemma: str | None = None, sense_id: str | None = None) -> KoreanFrequencyEntry:
    resolved_lemma = lemma or f"어휘{rank}"
    fingerprint = _fingerprint()
    identity = KoreanLexicalIdentity(
        submitted_form=resolved_lemma,
        canonical_nfc=resolved_lemma,
        lemma=resolved_lemma,
        part_of_speech="NNG",
        sense_id=sense_id or f"nikl:{rank}",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form=resolved_lemma, pos="NNG"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )
    return KoreanFrequencyEntry(
        language="ko",
        version="fixture-v1",
        level=((rank - 1) // 1000) + 1,
        final_rank=rank,
        source_rank=rank,
        source_provenance="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        license_decision="approved-local-use",
        storage_disposition="synthetic-test-only",
        curation_decision="accepted",
        curation_flags=("source_rank_preserved",),
        grounding_confidence="source-backed",
        bundle_sha256=_hash("frequency-bundle"),
        retrieval_sha256=_hash("retrieval"),
        analyzer_fingerprint=fingerprint,
        lexical_identity=identity,
    )


def _snapshot(*, receipt_sha256: str = "") -> object:
    concepts = (
        KoreanConcept(id="orthography:hangul", domain="orthography", prerequisite_ids=(), sequence=1),
        KoreanConcept(
            id="phonology:batchim",
            domain="phonology",
            prerequisite_ids=("orthography:hangul",),
            sequence=2,
        ),
    )
    return SimpleNamespace(
        receipt_sha256=receipt_sha256 or _hash("phase31-receipt"),
        snapshot_manifest_sha256=_hash("phase31-manifest"),
        snapshot_root_sha256=_hash("phase31-root"),
        bundle_sha256=_hash("phase31-bundle"),
        concept_registry=SimpleNamespace(concepts=concepts),
    )


class RecordingVerifier:
    def __init__(self) -> None:
        self.expected_receipts: list[str] = []

    def __call__(self, *, expected_receipt_sha256: str) -> object:
        self.expected_receipts.append(expected_receipt_sha256)
        return SimpleNamespace(active=True)


class FakeKoreanMatcher:
    def __init__(self, status: KoreanMatchStatus) -> None:
        self.fingerprint = _fingerprint()
        self.status = status
        self.calls: list[tuple[str, KoreanLexicalIdentity]] = []

    def match_target(self, sentence_text: str, target: KoreanLexicalIdentity) -> KoreanMatchResult:
        self.calls.append((sentence_text, target))
        reason_codes = {
            KoreanMatchStatus.MATCHED: KoreanReasonCode.CONSENSUS_MATCH,
            KoreanMatchStatus.MISMATCH: KoreanReasonCode.NO_SIGNATURE_MATCH,
            KoreanMatchStatus.AMBIGUOUS: KoreanReasonCode.ANALYSIS_DISAGREEMENT,
        }
        return KoreanMatchResult(
            status=self.status,
            reason_code=reason_codes.get(self.status, KoreanReasonCode.ANALYSIS_DISAGREEMENT),
            analyzer_fingerprint=self.fingerprint,
            alternative_matches=(
                (True, True)
                if self.status is KoreanMatchStatus.MATCHED
                else (False, False)
                if self.status is KoreanMatchStatus.MISMATCH
                else (True, False)
            ),
        )


def _service(**overrides: object):
    from multilang.services.korean_text_quality import KoreanTextQualityService

    verifier = overrides.pop("active_provenance_verifier", RecordingVerifier())
    snapshot = overrides.pop("snapshot", _snapshot())
    service = KoreanTextQualityService(
        active_snapshot_resolver=lambda: snapshot,
        active_provenance_verifier=verifier,
        **overrides,
    )
    return service, verifier


def _known_prefix(service: object, *, target_rank: int, entries: tuple[KoreanFrequencyEntry, ...]):
    return service.known_prefix(
        target_rank=target_rank,
        frequency_entries=entries,
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
    )


def test_known_state_rank_one_uses_active_foundation_concepts_only() -> None:
    service, verifier = _service()

    prefix = _known_prefix(service, target_rank=1, entries=(_entry(1), _entry(2)))

    assert prefix.foundation_concept_ids == ("orthography:hangul", "phonology:batchim")
    assert prefix.lexical_concept_ids == ()
    assert prefix.known_concept_ids == ("orthography:hangul", "phonology:batchim")
    assert prefix.known_concept_count == 2
    assert prefix.phase31_validation_receipt_sha256 == _hash("phase31-receipt")
    assert verifier.expected_receipts == [_hash("phase31-receipt")]


def test_frozen_prefix_rank_boundary_is_deterministic_and_text_status_independent() -> None:
    service, _ = _service()
    entries = (_entry(3), _entry(1), _entry(2))

    first = _known_prefix(service, target_rank=3, entries=entries)
    second = _known_prefix(service, target_rank=3, entries=tuple(reversed(entries)))

    assert first.lexical_concept_ids == (
        f"lexicon:{_entry(1).lexical_identity.lexical_key}",
        f"lexicon:{_entry(2).lexical_identity.lexical_key}",
    )
    assert first.known_concept_ids == tuple(sorted(first.known_concept_ids))
    assert first.known_prefix_sha256 == second.known_prefix_sha256
    assert first.known_concept_count == second.known_concept_count == 4


def test_known_state_blocks_missing_reordered_duplicate_or_authority_drifted_prefixes() -> None:
    service, _ = _service(snapshot=_snapshot(receipt_sha256=_hash("wrong-receipt")))

    with pytest.raises(ValueError, match="Phase 31 active receipt drift"):
        _known_prefix(service, target_rank=2, entries=(_entry(1), _entry(2)))

    service, _ = _service()
    with pytest.raises(ValueError, match="missing lower Korean frequency rank"):
        _known_prefix(service, target_rank=3, entries=(_entry(1), _entry(3)))

    with pytest.raises(ValueError, match="duplicate Korean known concept"):
        _known_prefix(service, target_rank=3, entries=(_entry(1), _entry(2, lemma="어휘1", sense_id="nikl:1")))


def test_incidental_concepts_exclude_known_prefix_and_target_identity() -> None:
    service, _ = _service()
    target = _entry(2)
    prefix = _known_prefix(service, target_rank=2, entries=(_entry(1), target))

    adaptive = service.build_adaptive_evidence(
        prefix=prefix,
        target_entry=target,
        observed_concept_ids=(
            "orthography:hangul",
            f"lexicon:{_entry(1).lexical_identity.lexical_key}",
            f"lexicon:{target.lexical_identity.lexical_key}",
            "grammar:topic",
        ),
        candidate_sha256=_hash("candidate"),
        selected_ordinal=1,
    )

    assert adaptive.known_prefix_sha256 == prefix.known_prefix_sha256
    assert adaptive.target_concept_id == f"lexicon:{target.lexical_identity.lexical_key}"
    assert adaptive.incidental_concept_ids == ("grammar:topic",)
    assert adaptive.known_concept_count == prefix.known_concept_count


def test_hard_gate_selected_morphology_mismatch_blocks_before_adaptive_score() -> None:
    matcher = FakeKoreanMatcher(KoreanMatchStatus.MISMATCH)
    service, _ = _service(korean_matcher=matcher)
    target = _entry(1)

    result = service.evaluate_candidate(
        target_entry=target,
        target_rank=1,
        frequency_entries=(target,),
        sentence_text="저는 학교에 가요.",
        translation_text="Eu vou para a escola.",
        observed_concept_ids=(f"lexicon:{target.lexical_identity.lexical_key}",),
        candidate_sha256=_hash("candidate"),
        selected_ordinal=1,
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
    )

    assert result.selectable is False
    assert result.hard_gate_codes == ("selected_morphology_mismatch",)
    assert result.adaptive_evidence is None
    assert result.score_components == {}


def test_hard_gate_register_template_naturalness_and_sense_failures_are_non_selectable() -> None:
    matcher = FakeKoreanMatcher(KoreanMatchStatus.MATCHED)
    service, _ = _service(korean_matcher=matcher)
    target = _entry(1)

    result = service.evaluate_candidate(
        target_entry=target,
        target_rank=1,
        frequency_entries=(target,),
        sentence_text="이 문장은 학교를 사용합니다.",
        translation_text="Eu vou para a escola.",
        observed_concept_ids=(f"lexicon:{target.lexical_identity.lexical_key}",),
        candidate_sha256=_hash("candidate"),
        selected_ordinal=1,
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
        intended_sense_id="nikl:other",
    )

    assert result.selectable is False
    assert set(result.hard_gate_codes) >= {"register_policy", "template_naturalness", "source_sense_mismatch"}
    assert result.adaptive_evidence is None


def test_hard_gate_passed_candidate_receives_adaptive_review_required_evidence_only() -> None:
    matcher = FakeKoreanMatcher(KoreanMatchStatus.MATCHED)
    service, _ = _service(korean_matcher=matcher)
    target = _entry(2)

    result = service.evaluate_candidate(
        target_entry=target,
        target_rank=2,
        frequency_entries=(_entry(1), target),
        sentence_text="저는 오늘 학교에 가요.",
        translation_text="Hoje eu vou para a escola.",
        observed_concept_ids=(
            "orthography:hangul",
            f"lexicon:{_entry(1).lexical_identity.lexical_key}",
            f"lexicon:{target.lexical_identity.lexical_key}",
            "grammar:topic",
        ),
        candidate_sha256=_hash("candidate"),
        selected_ordinal=1,
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
        intended_sense_id=target.lexical_identity.sense_id,
    )

    assert result.selectable is True
    assert result.hard_gate_codes == ()
    assert result.adaptive_evidence is not None
    assert result.selection_evidence is not None
    assert result.selection_evidence.hard_gate_status == "passed"
    assert result.review_status == "review_required"


def _review_role_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "reviewer_kind": "human",
        "reviewer_role": "qualified_linguistic_reviewer",
        "reviewer_id_sha256": _hash("reviewer-id"),
        "qualification_policy_sha256": _hash("qualification-policy"),
        "qualification_receipt_sha256": _hash("qualification-receipt"),
    }
    payload.update(overrides)
    return payload


def _review_coverage_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_identity": True,
        "source_sense": True,
        "morphology_match": True,
        "natural_korean": True,
        "pt_br_translation": True,
        "adaptive_i_plus_one": True,
        "no_private_context": True,
        "no_unsafe_markup": True,
    }
    payload.update(overrides)
    return payload


def _review_decision_payload(**overrides: object) -> dict[str, object]:
    from multilang.domain.text_quality import KoreanTextReviewCoverage, KoreanTextReviewQualification

    identity_hash = _hash("candidate-identity")
    payload: dict[str, object] = {
        "production_run_sha256": _hash("production-run"),
        "job_sha256": _hash("job"),
        "run_sha256": _hash("run"),
        "item_sha256": _hash("item"),
        "candidate_sha256": _hash("candidate"),
        "candidate_identity_sha256": identity_hash,
        "reviewed_identity_sha256": identity_hash,
        "policy_sha256": _hash("review-policy"),
        "evidence_root_sha256": _hash("evidence-root"),
        "reviewer": KoreanTextReviewQualification(**_review_role_payload()),
        "coverage": KoreanTextReviewCoverage(**_review_coverage_payload()),
        "outcome": "accepted",
    }
    payload.update(overrides)
    return payload


def test_review_decision_immutable_and_binds_exact_role_coverage_hashes_without_authority() -> None:
    from multilang.domain.text_quality import KoreanTextReviewDecision

    decision = KoreanTextReviewDecision(**_review_decision_payload())

    assert decision.authority_scope == "review_record_only"
    assert decision.can_mutate_database is False
    assert decision.can_promote_or_export is False
    assert decision.rejection_codes == ()

    with pytest.raises(Exception):
        decision.outcome = "rejected"  # type: ignore[misc]
    with pytest.raises(ValueError):
        KoreanTextReviewDecision(**_review_decision_payload(private_source_path="/home/reader/book.txt"))


def test_review_rejection_role_and_coverage_fail_closed_for_machine_or_stale_contradictory_fields() -> None:
    from multilang.domain.text_quality import (
        KoreanTextReviewCoverage,
        KoreanTextReviewDecision,
        KoreanTextReviewQualification,
        KoreanTextReviewRejection,
    )

    with pytest.raises(ValueError):
        KoreanTextReviewQualification(**_review_role_payload(reviewer_kind="machine"))
    with pytest.raises(ValueError, match="stale Korean identity"):
        KoreanTextReviewDecision(**_review_decision_payload(reviewed_identity_sha256=_hash("stale-identity")))
    with pytest.raises(ValueError, match="accepted decision cannot carry rejection codes"):
        KoreanTextReviewDecision(**_review_decision_payload(rejection_codes=("wrong_sense",)))
    with pytest.raises(ValueError, match="accepted decision requires complete coverage"):
        KoreanTextReviewDecision(
            **_review_decision_payload(
                coverage=KoreanTextReviewCoverage(**_review_coverage_payload(pt_br_translation=False))
            )
        )
    with pytest.raises(ValueError, match="rejected decision requires rejection codes"):
        KoreanTextReviewDecision(**_review_decision_payload(outcome="rejected"))

    rejection = KoreanTextReviewRejection(
        **_review_decision_payload(
            outcome="rejected",
            rejection_codes=("wrong_sense", "unsafe_markup"),
        )
    )

    assert rejection.outcome == "rejected"
    assert rejection.authority_scope == "review_record_only"


def test_pt_br_translation_hard_gate_rejects_english_leakage_isolated_words_and_unsafe_markup() -> None:
    matcher = FakeKoreanMatcher(KoreanMatchStatus.MATCHED)
    service, _ = _service(korean_matcher=matcher)
    target = _entry(1)

    cases = (
        ("The student goes to school.", "english_leakage"),
        ("Escola.", "isolated_word_translation"),
        ("<p>Eu vou para a escola.</p>", "unsafe_markup"),
    )

    for translation_text, expected_code in cases:
        result = service.evaluate_candidate(
            target_entry=target,
            target_rank=1,
            frequency_entries=(target,),
            sentence_text="저는 오늘 학교에 가요.",
            translation_text=translation_text,
            observed_concept_ids=(f"lexicon:{target.lexical_identity.lexical_key}",),
            candidate_sha256=_hash(f"candidate-{expected_code}"),
            selected_ordinal=1,
            expected_phase31_receipt_sha256=_hash("phase31-receipt"),
            phase31_pointer_locator_sha256=_hash("pointer-locator"),
            phase31_pointer_content_sha256=_hash("pointer-content"),
            frequency_bundle_locator_sha256=_hash("frequency-locator"),
            frequency_bundle_content_sha256=_hash("frequency-bundle"),
            intended_sense_id=target.lexical_identity.sense_id,
        )

        assert result.selectable is False
        assert expected_code in result.hard_gate_codes
        assert result.adaptive_evidence is None


def test_score_tie_uses_candidate_hash_then_ordinal_after_hard_gate_passes() -> None:
    from multilang.services.korean_text_quality import KoreanTextCandidate

    matcher = FakeKoreanMatcher(KoreanMatchStatus.MATCHED)
    service, _ = _service(korean_matcher=matcher)
    target = _entry(2)
    target_concept = f"lexicon:{target.lexical_identity.lexical_key}"
    known_concept = f"lexicon:{_entry(1).lexical_identity.lexical_key}"
    lower_incidental_candidate = KoreanTextCandidate(
        sentence_text="저는 오늘 학교에 가요.",
        translation_text="Hoje eu vou para a escola.",
        observed_concept_ids=("orthography:hangul", known_concept, target_concept),
        candidate_sha256="b" * 64,
        ordinal=2,
        intended_sense_id=target.lexical_identity.sense_id,
    )
    higher_incidental_candidate = KoreanTextCandidate(
        sentence_text="저는 오늘 도서관과 학교에 가요.",
        translation_text="Hoje eu vou para a biblioteca e a escola.",
        observed_concept_ids=("orthography:hangul", known_concept, target_concept, "lexicon:library"),
        candidate_sha256="a" * 64,
        ordinal=1,
        intended_sense_id=target.lexical_identity.sense_id,
    )

    first = service.select_best_candidate(
        target_entry=target,
        target_rank=2,
        frequency_entries=(_entry(1), target),
        candidates=(higher_incidental_candidate, lower_incidental_candidate),
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
    )
    second = service.select_best_candidate(
        target_entry=target,
        target_rank=2,
        frequency_entries=(_entry(1), target),
        candidates=(lower_incidental_candidate, higher_incidental_candidate),
        expected_phase31_receipt_sha256=_hash("phase31-receipt"),
        phase31_pointer_locator_sha256=_hash("pointer-locator"),
        phase31_pointer_content_sha256=_hash("pointer-content"),
        frequency_bundle_locator_sha256=_hash("frequency-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle"),
    )

    assert first.selectable is True
    assert first.selection_evidence is not None
    assert second.selection_evidence is not None
    assert first.selection_evidence.selected_candidate_sha256 == "b" * 64
    assert first.selection_evidence.selected_candidate_sha256 == second.selection_evidence.selected_candidate_sha256
    assert first.selection_evidence.selected_ordinal == second.selection_evidence.selected_ordinal == 2
