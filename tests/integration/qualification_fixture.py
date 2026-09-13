"""Synthetic review authority used only by the complete local export regression."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

from test_native_application import qualified_profile

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.native_evidence import EvidenceStore, SignedEvidence
from multilang.services.qualification_bridge import build_vocabulary_review_input
from multilang.services.qualification_review import (
    HumanReviewSubmission,
    LexicalDecision,
    LexicalReviewItem,
    ReviewPacket,
    ReviewSource,
    export_review,
    import_review,
    review_signing_payload,
)
from multilang.services.vocabulary_preparation import prepare_vocabulary
from multilang.services.vocabulary_review import compile_reviewed_vocabulary, decision_payload


def import_qualification_fixture(facade, tmp_path, settings):
    profile = qualified_profile().model_copy(update={"provider_locales": {"azure": "en-US"}})
    source = tmp_path / "qualification-dictionary.jsonl"
    source.write_text(
        "".join(
            json.dumps(
                {
                    "word": word,
                    "lang_code": "en",
                    "pos": "verb",
                    "senses": [{"glosses": ["Move on foot."], "senseid": ["move"]}],
                }
            )
            + "\n"
            for word in ("run", "walk")
        )
    )
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    prepared = tmp_path / "qualification-prepared"
    prepare_vocabulary(
        language="en", dictionary=source, dictionary_sha256=source_sha, output=prepared
    )
    candidates = [
        json.loads(line) for line in (prepared / "candidates.jsonl").read_text().splitlines()
    ]
    items = tuple(
        LexicalReviewItem(
            item_id=c["candidate_id"],
            candidate_id=c["candidate_id"],
            candidate_sha256=canonical_sha256(c),
            lemma=c["lemma"],
            pos=c["pos"],
            glosses=c["glosses"],
            sources=(
                ReviewSource(
                    source_id="fixture",
                    source_sha256=source_sha,
                    record_id=c["candidate_id"],
                    excerpt="Synthetic source only",
                ),
            ),
        )
        for c in candidates
    )
    packet = ReviewPacket(
        packet_id="synthetic-export-fixture",
        language="en",
        split="calibration",
        profile_sha256=canonical_sha256(profile.model_dump(mode="json")),
        rubric_sha256="e" * 64,
        items=items,
    )
    exported = export_review(packet, tmp_path / "qualification-review")
    decisions = tuple(
        LexicalDecision(
            item_id=i.item_id,
            item_sha256=i.item_sha256,
            decision="accepted",
            reason="Synthetic independent review fixture",
            canonical_sense_id="move",
        )
        for i in items
    )
    submission = HumanReviewSubmission(
        packet_sha256=packet.packet_sha256,
        reviewer_id="synthetic-linguist",
        expertise_declaration="Automated fixture, not real expert qualification",
        reviewed_at=datetime.now(UTC),
        decisions=decisions,
    )
    store = EvidenceStore(
        settings.native_evidence_dir,
        key=settings.native_evidence_signing_key.get_secret_value().encode(),
    )

    def sign(payload, purpose):
        receipt = SignedEvidence.sign(
            payload,
            key=store.key,
            signer="synthetic-linguist",
            purpose=purpose,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        (store.root / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
        return receipt.receipt_id

    submission = submission.model_copy(
        update={
            "receipt_id": sign(review_signing_payload(packet, submission), "qualification-review")
        }
    )
    submission_path = tmp_path / "qualification-decisions.json"
    submission_path.write_text(submission.model_dump_json())
    validated = import_review(
        packet_path=tmp_path / "qualification-review/packet.json",
        packet_sha256=exported.packet_file_sha256,
        submission_path=submission_path,
        submission_sha256=hashlib.sha256(submission_path.read_bytes()).hexdigest(),
        expected_reviewer="synthetic-linguist",
        verifier=store,
    )
    bridge = build_vocabulary_review_input(
        preparation_dir=prepared,
        packet=validated.packet,
        submission=validated.submission,
        expected_reviewer="synthetic-linguist",
        verifier=store,
        profile=profile,
        source_id="fixture",
        source_version="synthetic-qualification-1",
    )
    assert not bridge.blockers
    review = bridge.review.model_copy(
        update={
            "senses": tuple(
                d.model_copy(
                    update={
                        "receipt_id": sign(
                            decision_payload(bridge.review, d, profile), "vocabulary-sense"
                        )
                    }
                )
                for d in bridge.review.senses
            )
        }
    )
    native_decisions = tmp_path / "native-qualification-decisions.json"
    native_decisions.write_text(review.model_dump_json())
    bundle = compile_reviewed_vocabulary(
        preparation_dir=prepared,
        decisions_path=native_decisions,
        decisions_sha256=hashlib.sha256(native_decisions.read_bytes()).hexdigest(),
        profile=profile,
        verifier=store,
        output=tmp_path / "qualification-compiled",
    )
    assert len(bundle.identities) == 2
    assert not bundle.quarantine
    return facade.import_reviewed_vocabulary(
        {
            "format": "reviewed-vocabulary",
            "bundle": bundle.model_dump(mode="json"),
            "namespace": "core",
            "version": "synthetic-qualification-1",
            "profile_version": profile.version,
        },
        "synthetic-linguist",
    )
