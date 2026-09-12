"""Append independently approved generated versions without rewriting Core facts."""

from typing import Literal

from pydantic import Field
from sqlalchemy.orm import Session

from multilang.db.native_models import AudioVersionRecord, ContentVersionRecord
from multilang.domain.audio_version import AudioVersion
from multilang.domain.content import ContentVersion
from multilang.domain.datasets import DatasetManifest
from multilang.domain.language_profiles import NativeContract
from multilang.repositories.native_repository import NativeRepository, model_payload
from multilang.services.native_evidence import EvidenceStore


class ReviewApproval(NativeContract):
    kind: Literal["content", "audio", "dataset"]
    version_id: str = Field(min_length=1, max_length=128)
    receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    license_receipt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    new_version: str | None = Field(default=None, min_length=1, max_length=64)
    attribution: str = Field(default="", max_length=4000)


class NativeReviewService:
    def __init__(self, session: Session, evidence_store: EvidenceStore):
        self.session, self.evidence_store = session, evidence_store
        self.repository = NativeRepository(session)

    def approve(self, payload: dict, *, actor: str) -> dict:
        approval = ReviewApproval.model_validate(payload)
        signed_payload = approval.model_dump(mode="json", exclude={"receipt_sha256"}) | {
            "reviewer": actor
        }
        if not self.evidence_store.verify(
            approval.receipt_sha256, signed_payload, purpose=f"{approval.kind}-review"
        ):
            raise ValueError("independent signed evidence is required before review")
        if approval.kind == "content":
            row = self.session.get(ContentVersionRecord, approval.version_id)
            if row is None or row.owner_id:
                raise ValueError("unknown shared content version")
            version = ContentVersion.model_validate(row.payload)
            from multilang.services.native_validation import ContentValidator

            ContentValidator().validate(version).require_valid()
            approved = ContentVersion.model_validate(
                model_payload(version)
                | {
                    "review_status": "approved",
                    "review_receipt_sha256": approval.receipt_sha256,
                    "independent_reviewer": actor,
                }
            )
            self.repository.save_content(
                version_id=approved.version_id,
                identity_id=row.identity_id,
                namespace=row.namespace,
                owner_id="",
                edition_id=row.edition_id,
                payload=model_payload(approved),
                search_text=row.search_text,
                actor=actor,
            )
            return {"version_id": approved.version_id, "status": "approved"}
        if approval.kind == "audio":
            row = self.session.get(AudioVersionRecord, approval.version_id)
            if row is None or row.owner_id or approval.license_receipt_sha256 is None:
                raise ValueError("unknown shared audio or missing license evidence")
            version = AudioVersion.model_validate(row.payload)
            approved = AudioVersion.model_validate(
                model_payload(version)
                | {
                    "review_status": "approved",
                    "review_receipt_sha256": approval.receipt_sha256,
                    "license_receipt_sha256": approval.license_receipt_sha256,
                }
            )
            self.repository.save_audio(
                version_id=approved.version_id,
                signature_sha256=approved.signature.signature_sha256,
                namespace="core",
                owner_id="",
                payload=model_payload(approved),
                actor=actor,
            )
            return {"version_id": approved.version_id, "status": "approved"}
        data = self.repository.get_dataset(approval.version_id)
        if (
            data is None
            or not approval.new_version
            or not approval.attribution
            or not approval.license_receipt_sha256
        ):
            raise ValueError("dataset review needs source rights, attribution and a new version")
        manifest = DatasetManifest.model_validate(data)
        reviewed = manifest.model_copy(
            update={
                "version": approval.new_version,
                "redistribution_approved": True,
                "approval_sha256": approval.receipt_sha256,
                "attribution": approval.attribution,
                "metadata": dict(manifest.metadata)
                | {"license_receipt_sha256": approval.license_receipt_sha256},
            }
        )
        reviewed.require_production()
        self.repository.clone_dataset_version(
            manifest.dataset_id, reviewed, actor=actor, reason="independent_review"
        )
        return {"dataset_id": reviewed.dataset_id, "status": "approved"}
