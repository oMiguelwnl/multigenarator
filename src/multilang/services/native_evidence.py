"""Local operator-signed evidence receipts with payload, purpose and expiry binding.

This verifies provenance of a decision, not the linguistic/client claims inside
it. Operators sign only after independent review of the referenced artifacts.
"""

import hmac
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field

from multilang.domain.events import canonical_hash
from multilang.domain.language_profiles import NativeContract


class SignedEvidence(NativeContract):
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signer: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=64)
    expires_at: datetime
    signature: str = Field(pattern=r"^[0-9a-f]{64}$")

    @property
    def receipt_id(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))

    @classmethod
    def sign(cls, payload: dict, *, key: bytes, signer: str, purpose: str, expires_at: datetime):
        if len(key) < 32 or expires_at.tzinfo is None:
            raise ValueError("evidence needs a 32-byte signing key and timezone-aware expiry")
        values = dict(
            payload_sha256=canonical_hash(payload),
            signer=signer,
            purpose=purpose,
            expires_at=expires_at.isoformat(),
        )
        signature = hmac.new(key, canonical_hash(values).encode(), "sha256").hexdigest()
        return cls(**values, signature=signature)


class EvidenceStore:
    def __init__(self, root: Path, *, key: bytes | None):
        self.root = Path(root).resolve()
        self.key = key

    def load(self, receipt_id: str) -> SignedEvidence:
        if not re.fullmatch(r"[a-f0-9]{64}", receipt_id):
            raise ValueError("evidence identifier must be a SHA-256")
        path = self.root / f"{receipt_id}.json"
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16000:
            raise ValueError("signed evidence missing or outside bounds")
        receipt = SignedEvidence.model_validate_json(path.read_bytes())
        if receipt.receipt_id != receipt_id:
            raise ValueError("evidence receipt hash mismatch")
        return receipt

    def verify(self, receipt_id: str, payload: dict, *, purpose: str) -> bool:
        if self.key is None or len(self.key) < 32:
            return False
        try:
            receipt = self.load(receipt_id)
            if receipt.expires_at.tzinfo is None or receipt.expires_at <= datetime.now(UTC):
                return False
            expected = SignedEvidence.sign(
                payload,
                key=self.key,
                signer=receipt.signer,
                purpose=purpose,
                expires_at=receipt.expires_at,
            )
            return receipt.purpose == purpose and hmac.compare_digest(
                receipt.signature, expected.signature
            )
        except (ValueError, OSError):
            return False

    def verify_topology(self, decision) -> bool:
        payload = decision.model_dump(mode="json", exclude={"decision_receipt_sha256"})
        if not self.verify(decision.decision_receipt_sha256, payload, purpose="anki-topology"):
            return False
        from multilang.services.native_migration import file_sha256

        for evidence in decision.evidence:
            for digest in (evidence.artifact_sha256, evidence.fixture_sha256):
                path = self.root / "artifacts" / digest
                if path.is_symlink() or not path.is_file() or file_sha256(path) != digest:
                    return False
        return True
