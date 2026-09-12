import json
from datetime import UTC, datetime, timedelta

import pytest

from multilang.services.native_evidence import EvidenceStore, SignedEvidence


def test_signed_evidence_is_bound_to_payload_signer_and_expiry(tmp_path):
    secret = b"test-only-local-owner-key-32-bytes!"
    payload = {"profile": "en", "version": "1"}
    receipt = SignedEvidence.sign(
        payload,
        key=secret,
        signer="fixture-reviewer",
        purpose="language-profile",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    (tmp_path / f"{receipt.receipt_id}.json").write_text(receipt.model_dump_json())
    store = EvidenceStore(tmp_path, key=secret)
    assert store.verify(receipt.receipt_id, payload, purpose="language-profile")
    assert not store.verify(receipt.receipt_id, {"profile": "ko"}, purpose="language-profile")
    assert not store.verify(receipt.receipt_id, payload, purpose="topology")
    assert not EvidenceStore(tmp_path, key=b"wrong" * 8).verify(
        receipt.receipt_id, payload, purpose="language-profile"
    )
    with pytest.raises(ValueError):
        store.load("../secrets")


def test_mutating_receipt_and_expiration_cannot_authorize(tmp_path):
    key = b"x" * 32
    payload = {"policy": "fixture"}
    receipt = SignedEvidence.sign(
        payload,
        key=key,
        signer="reviewer",
        purpose="test",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    file = tmp_path / f"{receipt.receipt_id}.json"
    file.write_text(receipt.model_dump_json())
    assert not EvidenceStore(tmp_path, key=key).verify(receipt.receipt_id, payload, purpose="test")
    modified = json.loads(file.read_text())
    modified["signer"] = "different"
    file.write_text(json.dumps(modified))
    assert not EvidenceStore(tmp_path, key=key).verify(receipt.receipt_id, payload, purpose="test")
