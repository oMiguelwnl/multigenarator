"""Bridge authenticated qualification reviews to unsigned native source decisions."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import Field

from multilang.domain.language_profiles import Identifier, LanguageProfile, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.native_evidence import EvidenceStore
from multilang.services.qualification_review import (
    FormDecision,
    FormReviewItem,
    HumanReviewSubmission,
    LexicalDecision,
    LexicalReviewItem,
    ReviewPacket,
    review_signing_payload,
    validate_review,
)
from multilang.services.vocabulary_review import (
    ObservedFormDecision,
    SenseDecision,
    VocabularyReview,
    _load_preparation,
    _plain_path,
    _read_bytes,
    decision_payload,
)


class BridgeBlocker(NativeContract):
    item_id: Identifier
    reason: Identifier
    requested_important: bool | None = None


class SourceCorrectionProposal(NativeContract):
    item_id: Identifier
    candidate_id: Identifier
    candidate_sha256: Sha256
    source_record_sha256: Sha256
    original_lemma: str = Field(min_length=1, max_length=512)
    original_pos: Identifier
    corrected_lemma: str = Field(min_length=1, max_length=512)
    corrected_pos: Identifier
    canonical_sense_id: Identifier
    reviewer_id: Identifier
    qualification_receipt_id: Sha256


class BridgeSigningInput(NativeContract):
    purpose: Literal["vocabulary-sense"] = "vocabulary-sense"
    payload: dict = Field(max_length=32)


class QualificationVocabularyBridge(NativeContract):
    review: VocabularyReview
    qualification_packet_sha256: Sha256
    qualification_submission_sha256: Sha256
    qualification_receipt_id: Sha256
    unsigned_payloads: tuple[BridgeSigningInput, ...]
    blockers: tuple[BridgeBlocker, ...]
    source_corrections: tuple[SourceCorrectionProposal, ...]
    production_eligible: Literal[False] = False


def build_vocabulary_review_input(
    *,
    preparation_dir: Path,
    packet: ReviewPacket,
    submission: HumanReviewSubmission,
    expected_reviewer: str,
    verifier: EvidenceStore,
    profile: LanguageProfile,
    source_id: str,
    source_version: str,
) -> QualificationVocabularyBridge:
    checked = validate_review(
        packet, submission, expected_reviewer=expected_reviewer, verifier=verifier
    )
    if not checked.authenticated:
        raise ValueError("vocabulary bridge requires authenticated qualification review")
    packet, submission = checked.packet, checked.submission
    profile = LanguageProfile.model_validate(profile.model_dump(mode="json"))
    if (
        packet.profile_sha256 != canonical_sha256(profile.model_dump(mode="json"))
        or packet.language != profile.language
    ):
        raise ValueError("qualification profile mismatch")
    if source_id not in profile.source_ids:
        raise ValueError("qualification source is not declared in the profile")
    manifest, candidates, _corpus, _artifacts = _load_preparation(preparation_dir)
    if manifest["language"] != packet.language.value:
        raise ValueError("qualification preparation language mismatch")
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("duplicate preparation candidate")
    pending = {
        candidate.candidate_id: SenseDecision(
            candidate_id=candidate.candidate_id,
            candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
            source_record_sha256=candidate.source_record_sha256,
            lemma=candidate.lemma,
            pos=candidate.pos,
        )
        for candidate in candidates
    }
    decisions = {decision.item_id: decision for decision in submission.decisions}
    blockers, corrections, forms = [], [], []
    lexical_seen = set()

    def pending_form(item, decision, reason):
        # A reviewed importance label does not establish a native parent or
        # contextual analysis. Preserve the request without inventing either.
        forms.append(
            ObservedFormDecision(
                decision_id=item.item_id,
                candidate_id=item.candidate_id,
                reviewer=submission.reviewer_id if decision else None,
                evidence_values=decision.ratings if isinstance(decision, FormDecision) else {},
            )
        )
        blockers.append(
            BridgeBlocker(
                item_id=item.item_id,
                reason=reason,
                requested_important=decision.include
                if isinstance(decision, FormDecision)
                else None,
            )
        )

    for item in packet.items:
        if not isinstance(item, (LexicalReviewItem, FormReviewItem)):
            continue
        candidate = by_id.get(item.candidate_id)
        decision = decisions.get(item.item_id)
        if candidate is None and isinstance(item, FormReviewItem):
            pending_form(item, decision, "unresolved_native_candidate_parent")
            continue
        if (
            candidate is None
            or canonical_sha256(candidate.model_dump(mode="json")) != item.candidate_sha256
        ):
            raise ValueError("qualification candidate does not match verified preparation")
        quarantined_pos = item.pos == "X" and (decision is None or decision.decision != "accepted")
        if item.lemma != candidate.lemma or (item.pos != candidate.pos and not quarantined_pos):
            raise ValueError("qualification proposal differs from original candidate")
        source_hashes = {candidate.source_record_sha256, manifest.get("dictionary_sha256")}
        if not any(
            (source.source_id == source_id and source.source_sha256 in source_hashes)
            or (
                source.source_id == "prepared-dictionary"
                and source.source_sha256 == manifest.get("dictionary_sha256")
                and source.record_id in {candidate.candidate_id, candidate.source_record_sha256}
            )
            for source in item.sources
        ):
            raise ValueError("qualification source reference does not match preparation")
        if isinstance(item, FormReviewItem):
            pending_form(item, decision, "exact_native_form_evidence_required")
            continue
        if item.candidate_id in lexical_seen:
            raise ValueError("multiple lexical review items address the same candidate")
        lexical_seen.add(item.candidate_id)
        if not isinstance(decision, LexicalDecision):
            blockers.append(BridgeBlocker(item_id=item.item_id, reason="human_decision_pending"))
            continue
        if decision.decision in {"rejected", "inconclusive"}:
            pending[item.candidate_id] = pending[item.candidate_id].model_copy(
                update={
                    "decision": "rejected" if decision.decision == "rejected" else "ambiguous",
                    "reviewer": submission.reviewer_id,
                }
            )
            continue
        corrected_lemma = decision.corrected_lemma or item.lemma
        corrected_pos = decision.corrected_pos or item.pos
        if (corrected_lemma, corrected_pos) != (candidate.lemma, candidate.pos):
            corrections.append(
                SourceCorrectionProposal(
                    item_id=item.item_id,
                    candidate_id=candidate.candidate_id,
                    candidate_sha256=item.candidate_sha256,
                    source_record_sha256=candidate.source_record_sha256,
                    original_lemma=candidate.lemma,
                    original_pos=candidate.pos,
                    corrected_lemma=corrected_lemma,
                    corrected_pos=corrected_pos,
                    canonical_sense_id=decision.canonical_sense_id,
                    reviewer_id=submission.reviewer_id,
                    qualification_receipt_id=submission.receipt_id,
                )
            )
            blockers.append(
                BridgeBlocker(
                    item_id=item.item_id, reason="source_correction_requires_new_preparation"
                )
            )
            continue
        if candidate.kind != "lexeme":
            blockers.append(
                BridgeBlocker(
                    item_id=item.item_id, reason="inflection_candidate_is_not_a_lexical_identity"
                )
            )
            continue
        pending[item.candidate_id] = pending[item.candidate_id].model_copy(
            update={
                "decision": "accepted",
                "stable_sense_id": decision.canonical_sense_id,
                "reviewer": submission.reviewer_id,
            }
        )
    review = VocabularyReview(
        preparation_sha256=manifest["preparation_sha256"],
        language=packet.language,
        source_id=source_id,
        source_version=source_version,
        senses=tuple(pending[key] for key in sorted(pending)),
        forms=tuple(forms),
    )
    return QualificationVocabularyBridge(
        review=review,
        qualification_packet_sha256=packet.packet_sha256,
        qualification_submission_sha256=canonical_sha256(submission.model_dump(mode="json")),
        qualification_receipt_id=submission.receipt_id,
        unsigned_payloads=tuple(
            BridgeSigningInput(payload=decision_payload(review, choice, profile))
            for choice in review.senses
            if choice.decision == "accepted"
        ),
        blockers=tuple(blockers),
        source_corrections=tuple(corrections),
    )


class DerivedPreparationResult(NativeContract):
    original_preparation_sha256: Sha256
    preparation_sha256: Sha256
    corrected_candidate_ids: tuple[Identifier, ...]
    qualification_receipt_id: Sha256
    production_eligible: Literal[False] = False


def apply_reviewed_lexical_corrections(
    *,
    preparation_dir: Path,
    packet: ReviewPacket,
    submission: HumanReviewSubmission,
    expected_reviewer: str,
    verifier: EvidenceStore,
    profile: LanguageProfile,
    source_id: str,
    source_version: str,
    output: Path,
) -> DerivedPreparationResult:
    """Publish a new pending source projection; preserve original dictionary facts.

    New candidate IDs bind the original candidate, exact human correction and
    receipt. The original record hash remains an ancestry reference, while the
    manifest explicitly identifies the human-derived facts. No canonical sense
    or vocabulary receipt is assigned to the new candidates.
    """
    result = build_vocabulary_review_input(
        preparation_dir=preparation_dir,
        packet=packet,
        submission=submission,
        expected_reviewer=expected_reviewer,
        verifier=verifier,
        profile=profile,
        source_id=source_id,
        source_version=source_version,
    )
    output = _plain_path(output)
    if output.exists():
        raise ValueError("derived preparation output already exists")
    if not result.source_corrections:
        raise ValueError("review contains no source corrections to apply")
    manifest, candidates, _corpus, _artifacts = _load_preparation(preparation_dir)
    original_manifest_sha = manifest["preparation_sha256"]
    original_manifest = manifest
    corrections = {correction.candidate_id: correction for correction in result.source_corrections}
    decisions = {decision.item_id: decision for decision in submission.decisions}
    derived, ids, records = [], [], []
    for candidate in candidates:
        correction = corrections.get(candidate.candidate_id)
        if correction is None:
            derived.append(candidate)
            continue
        identifier_payload = {
            "schema_version": 1,
            "original_candidate_sha256": correction.candidate_sha256,
            "review_decision": decisions[correction.item_id].model_dump(mode="json"),
            "qualification_receipt_id": result.qualification_receipt_id,
        }
        new_id = "derived:" + canonical_sha256(identifier_payload)
        replacement = candidate.model_copy(
            update={
                "candidate_id": new_id,
                "lemma": correction.corrected_lemma,
                "pos": correction.corrected_pos,
                "stable_sense_id": None,
            }
        )
        derived.append(replacement)
        ids.append(new_id)
        records.append(
            {
                "original_candidate": candidate.model_dump(mode="json"),
                "correction": correction.model_dump(mode="json"),
                "derived_candidate_id": new_id,
                "derived_candidate_sha256": canonical_sha256(replacement.model_dump(mode="json")),
                "identifier_payload": identifier_payload,
            }
        )
    provenance = {
        "schema_version": 1,
        "kind": "human-corrected-source-projection",
        "original_preparation_sha256": original_manifest_sha,
        "original_dictionary_sha256": manifest["dictionary_sha256"],
        "qualification_receipt_id": result.qualification_receipt_id,
        "signed_qualification_payload": review_signing_payload(packet, submission),
        "signed_receipt": verifier.load(result.qualification_receipt_id).model_dump(mode="json"),
        "corrections": records,
        "source_record_hash_semantics": "original-dictionary-ancestry-not-corrected-facts",
        "candidate_status": "pending-new-vocabulary-review",
        "previous_correction_provenance": manifest.get("correction_provenance"),
    }
    manifest = {
        key: value for key, value in manifest.items() if key not in {"files", "preparation_sha256"}
    }
    manifest["correction_provenance"] = provenance
    manifest["distinct_word_count"] = len({candidate.lemma for candidate in derived})
    manifest["unresolved_pos_count"] = sum(candidate.pos == "X" for candidate in derived)
    manifest["blockers"] = sorted(
        set(manifest["blockers"]) | {"derived_source_requires_new_vocabulary_review"}
    )
    if not manifest["unresolved_pos_count"]:
        manifest["blockers"] = [
            reason for reason in manifest["blockers"] if reason != "unresolved_part_of_speech"
        ]
    if len(json.dumps(manifest, ensure_ascii=False).encode()) > 1024**2 - 16384:
        raise ValueError("correction provenance exceeds manifest limit; split the review batch")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".corrected-source-", dir=output.parent) as directory:
        staging = Path(directory) / "prepared"
        staging.mkdir(mode=0o700)
        total = 0

        def write(name, blob):
            nonlocal total
            total += len(blob)
            if total > 128 * 1024**2:
                raise ValueError("derived preparation byte limit exceeded")
            path = staging / name
            path.write_bytes(blob)
            path.chmod(0o600)

        for name, digest in original_manifest["files"].items():
            if name not in {"candidates.jsonl", "review.jsonl", "source-corrections.json"}:
                write(name, _read_bytes(Path(preparation_dir) / name, digest))
        write(
            "candidates.jsonl",
            "".join(candidate.model_dump_json() + "\n" for candidate in derived).encode(),
        )
        write(
            "review.jsonl",
            "".join(
                json.dumps(
                    {
                        "candidate_id": candidate.candidate_id,
                        "lemma": candidate.lemma,
                        "pos": candidate.pos,
                        "glosses": candidate.glosses,
                        "kind": candidate.kind,
                        "stable_sense_id": None,
                        "decision": "pending",
                        "reviewer": None,
                        "evidence_sha256": None,
                    },
                    ensure_ascii=False,
                )
                + "\n"
                for candidate in derived
            ).encode(),
        )
        write(
            "source-corrections.json",
            (json.dumps(provenance, ensure_ascii=False, indent=2) + "\n").encode(),
        )
        manifest["files"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(staging.iterdir())
        }
        manifest["preparation_sha256"] = canonical_sha256(manifest)
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        if len(manifest_bytes) > 1024**2:
            raise ValueError("correction provenance exceeds manifest limit; split the review batch")
        write("manifest.json", manifest_bytes)
        if output.exists():
            raise ValueError("derived preparation output created concurrently")
        os.rename(staging, output)
    return DerivedPreparationResult(
        original_preparation_sha256=original_manifest_sha,
        preparation_sha256=manifest["preparation_sha256"],
        corrected_candidate_ids=tuple(ids),
        qualification_receipt_id=result.qualification_receipt_id,
    )
