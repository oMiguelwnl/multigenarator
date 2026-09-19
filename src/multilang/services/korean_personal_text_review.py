"""Import independent AI text-review evidence without executing any provider.

Personal reading content stays in its local records. Public review projections
contain hashes and bounded identifiers; imported evidence cannot override local
validation, changed content, rejected revisions or the job's exact judge route.
"""

from hashlib import sha256
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select

from multilang.db.models import (
    GenerationJob,
    LexicalCandidate,
    ReviewCurrentPointerModel,
    ReviewDecisionModel,
    ReviewFieldRevisionModel,
    TextQualityRecordModel,
)
from multilang.domain.korean import (
    KoreanLexicalIdentity,
    canonical_json_sha256,
    canonicalize_korean,
)
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.domain.text_quality import (
    KoreanProviderReviewEvidence,
    ReviewStatus,
    ValidationStatus,
)
from multilang.repositories.transactions import lock_job_for_update, repository_transaction
from multilang.services.ai_linguistic_review import (
    AIReviewDecision,
    AIValidatorRun,
    ai_review_content_hash,
)

Sha = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")]
TextField = Literal["definition", "sentence", "translation"]
FIELDS = ("definition", "sentence", "translation")
CLAIM_IDS = ("target-identity", "source-sense", "morphology-target", "korean-naturalness",
             "pt-br-definition", "pt-br-translation", "cross-field-consistency", "privacy-and-markup")
VALIDATOR_IDS = ("schema-unicode-fields", "morphology-and-language", "current-revision-binding")
_CLAIM_REFERENCES = {
    "target-identity": ("identity-binding",),
    "source-sense": ("source-binding", "identity-binding"),
    "morphology-target": ("identity-binding", "text-field-bindings", "deterministic-binding"),
    "korean-naturalness": ("text-field-bindings",),
    "pt-br-definition": ("identity-binding", "text-field-bindings"),
    "pt-br-translation": ("text-field-bindings",),
    "cross-field-consistency": ("identity-binding", "text-field-bindings"),
    "privacy-and-markup": ("text-field-bindings", "deterministic-binding"),
}
REVIEW_POLICY_SHA256 = canonical_json_sha256({
    "policy_id": "multilang-ai-linguistic-review-v1", "policy_version": "1",
    "scope": "korean-personal-text-v1", "critical_pass_count": 3, "minimum_confidence": 0.8,
    "claims": CLAIM_IDS, "claim_references": _CLAIM_REFERENCES,
    "validators": VALIDATOR_IDS, "consensus": "all-pass-no-uncertainty",
})
_STATE = "korean_personal_text_reviews"


class PersonalTextReviewError(ValueError):
    """Controlled error containing no card content, provider detail or local path."""


def _fail(code):
    raise PersonalTextReviewError(code)


def _text_hash(value):
    return sha256(value.encode("utf-8")).hexdigest()


def _seal(payload):
    return {**payload, "content_hash": ai_review_content_hash(payload)}


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class FieldRevisionBinding(_Closed):
    field: TextField
    revision_id: Identifier
    pointer_version: int = Field(ge=1)
    value_sha256: Sha
    review_status: Literal["needs_review", "approved"]


class PersonalTextReviewSnapshot(_Closed):
    schema_version: Literal[1]
    job_id: Identifier
    item_id: Identifier
    subject_id: Identifier
    source_type: Literal["word-list", "kindle-highlights"]
    source_sha256: Sha
    candidate_sha256: Sha
    identity_sha256: Sha
    analyzer_sha256: Sha
    deterministic_sha256: Sha
    field_revisions: tuple[FieldRevisionBinding, ...] = Field(min_length=3, max_length=3)
    generator_actor_hashes: tuple[Sha, ...] = Field(min_length=1, max_length=3)
    provider_policy_sha256: Sha
    review_policy_id: Literal["multilang-ai-linguistic-review-v1"]
    review_policy_version: Literal["1"]
    review_policy_sha256: Sha
    judge_route_sha256: Sha
    judge_schema_sha256: Sha
    judge_provider: Identifier
    judge_model: Identifier
    evidence_reference_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=8)
    content_hash: Sha

    @model_validator(mode="after")
    def canonical(self):
        if tuple(item.field for item in self.field_revisions) != FIELDS:
            _fail("text_review_field_coverage_invalid")
        if self.content_hash != ai_review_content_hash(self):
            _fail("text_review_snapshot_hash_invalid")
        return self


class PersonalTextReviewPass(_Closed):
    schema_version: Literal[1]
    actor_type: Literal["ai_model"]
    is_human: Literal[False]
    actor_id: Identifier
    pass_id: Identifier
    fresh_context_id: Identifier
    independence_scope: Literal["fresh_context_same_model"]
    provider: Identifier
    model: Identifier
    model_version: Identifier
    provider_api_version: Identifier
    provider_policy_sha256: Sha
    review_policy_sha256: Sha
    route_policy_sha256: Sha
    response_schema_sha256: Sha
    prompt_id: Identifier
    prompt_version: Identifier
    prompt_template_sha256: Sha
    started_at: str
    completed_at: str
    decision: AIReviewDecision
    content_hash: Sha

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamp(cls, value):
        from datetime import datetime
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
            _fail("text_review_timestamp_invalid")
        return value

    @model_validator(mode="after")
    def canonical(self):
        if self.completed_at < self.started_at or self.content_hash != ai_review_content_hash(self):
            _fail("text_review_pass_invalid")
        return self


class PersonalTextReviewEvidence(_Closed):
    schema_version: Literal[1]
    snapshot: PersonalTextReviewSnapshot
    validators: tuple[AIValidatorRun, ...] = Field(min_length=3, max_length=3)
    passes: tuple[PersonalTextReviewPass, ...] = Field(min_length=3, max_length=3)
    content_hash: Sha

    @model_validator(mode="after")
    def canonical(self):
        if self.content_hash != ai_review_content_hash(self):
            _fail("text_review_evidence_hash_invalid")
        return self


def _snapshot(runtime, job_id, item_id):
    job = runtime.session.scalar(select(GenerationJob).where(GenerationJob.id == job_id)
        .execution_options(populate_existing=True))
    if job is None or job.language != "ko" or job.source_type not in {"word-list", "kindle-highlights"}:
        _fail("personal_korean_job_required")
    item_id = runtime._resolve_review_item_id(job_id, item_id)
    candidate, record, values = runtime._values(job_id, item_id)
    if candidate.source_type != job.source_type:
        _fail("personal_korean_source_mismatch")
    if record.validation_status is not ValidationStatus.PASSED or record.validation_flags:
        _fail("deterministic_validation_required")
    identity = KoreanLexicalIdentity.model_validate(candidate.korean_identity)
    if (candidate.lemma != identity.lemma or candidate.lemma_key != identity.lexical_key
            or candidate.display_form != identity.canonical_nfc
            or candidate.definition_language != "pt" or candidate.translation_target_language != "pt"):
        _fail("text_review_identity_mismatch")
    for value in values.values():
        if (not isinstance(value, str) or not value.strip() or len(value) > 8000
                or canonicalize_korean(value) != value or any(char in value for char in ("<", ">", "\x00"))):
            _fail("text_review_field_invalid")
    policy = KoreanProviderPolicy.model_validate(job.korean_provider_policy)
    if policy.policy_sha256 != job.korean_provider_policy_sha256:
        _fail("text_review_policy_mismatch")
    route = policy.route_for(KoreanProviderTask.JUDGE)
    if not route.enabled:
        _fail("text_review_judge_required")
    bindings, generators = [], set()
    for field in FIELDS:
        pointer = runtime._pointer(job_id, item_id, field)
        if pointer is None or pointer.review_status == "rejected":
            _fail("text_review_current_revision_required")
        revision = runtime.session.get(ReviewFieldRevisionModel, pointer.current_revision_id)
        if (revision is None or revision.job_id != job_id or revision.item_id != item_id
                or revision.field_name != field or revision.value_sha256 != _text_hash(values[field])):
            _fail("text_review_stale_revision")
        rejected = runtime.session.scalar(select(ReviewDecisionModel.id).where(
            ReviewDecisionModel.revision_id == revision.id, ReviewDecisionModel.review_status == "rejected").limit(1))
        if rejected is not None:
            _fail("text_review_rejected_revision_requires_replacement")
        bindings.append(dict(field=field, revision_id=revision.id, pointer_version=pointer.pointer_version,
            value_sha256=revision.value_sha256, review_status=pointer.review_status))
        generators.add(_text_hash(revision.generator_id))
    subject_id = "ko-personal-" + canonical_json_sha256({"job": job_id, "item": item_id})
    from multilang.services.korean_learning_runtime import public_korean_item_id
    payload = dict(schema_version=1, job_id=job_id, item_id=public_korean_item_id(item_id), subject_id=subject_id,
        source_type=job.source_type,
        source_sha256=canonical_json_sha256({"source": job.source_fingerprint, "candidate": candidate.id,
            "source_type": candidate.source_type, "normalized_source": candidate.normalized_source,
            "provenance": candidate.provenance, "lexical_evidence": candidate.lexical_evidence,
            "grounding_status": candidate.grounding_status,
            "source_review_receipt_sha256": candidate.source_review_receipt_sha256,
            "source_review_aggregate_sha256": candidate.source_review_aggregate_sha256}),
        candidate_sha256=canonical_json_sha256({"identity": identity.model_dump(mode="json"), "values": values,
            "lemma": candidate.lemma, "display_form": candidate.display_form,
            "submitted_form": candidate.submitted_form, "definition_language": candidate.definition_language,
            "translation_language": candidate.translation_target_language}),
        identity_sha256=canonical_json_sha256(identity.model_dump(mode="json")),
        analyzer_sha256=canonical_json_sha256(identity.analyzer_fingerprint.model_dump(mode="json")),
        deterministic_sha256=canonical_json_sha256({"status": record.validation_status.value,
            "flags": [flag.model_dump(mode="json") for flag in record.validation_flags],
            "confidence": record.confidence_score, "label": record.confidence_label.value}),
        field_revisions=bindings, generator_actor_hashes=sorted(generators),
        provider_policy_sha256=policy.policy_sha256, review_policy_id="multilang-ai-linguistic-review-v1",
        review_policy_version="1", review_policy_sha256=REVIEW_POLICY_SHA256,
        judge_route_sha256=route.route_policy_sha256, judge_schema_sha256=route.response_schema_sha256,
        judge_provider=route.provider, judge_model=route.model,
        evidence_reference_ids=("source-binding", "identity-binding", "text-field-bindings", "deterministic-binding"))
    return PersonalTextReviewSnapshot.model_validate(_seal(payload)), record


def prepare_personal_text_evidence(runtime, *, job_id, item_id):
    """Read the current hash-only review subject; never call or approve a provider."""
    if runtime.session.new or runtime.session.dirty or runtime.session.deleted:
        _fail("text_review_clean_session_required")
    with runtime.session.no_autoflush:
        snapshot, _record = _snapshot(runtime, job_id, item_id)
    return snapshot.model_dump(mode="json")


def _validate_consensus(evidence):
    snapshot = evidence.snapshot
    if snapshot.review_policy_sha256 != REVIEW_POLICY_SHA256:
        _fail("text_review_policy_mismatch")
    if tuple(run.validator_id for run in evidence.validators) != VALIDATOR_IDS:
        _fail("text_review_validator_coverage_invalid")
    for run in evidence.validators:
        if (run.subject_id != snapshot.subject_id or run.subject_content_sha256 != snapshot.content_hash
                or run.validator_version != "1" or run.result != "passed"):
            _fail("text_review_validator_failed")
    if (len({item.pass_id for item in evidence.passes}) != 3
            or len({item.fresh_context_id for item in evidence.passes}) != 3):
        _fail("text_review_independent_passes_required")
    for attempt in evidence.passes:
        if (attempt.provider_policy_sha256 != snapshot.provider_policy_sha256
                or attempt.review_policy_sha256 != REVIEW_POLICY_SHA256
                or attempt.route_policy_sha256 != snapshot.judge_route_sha256
                or attempt.response_schema_sha256 != snapshot.judge_schema_sha256
                or attempt.provider != snapshot.judge_provider or attempt.model != snapshot.judge_model
                or _text_hash(attempt.actor_id) in snapshot.generator_actor_hashes):
            _fail("text_review_judge_binding_invalid")
        decision = attempt.decision
        if (decision.subject_id != snapshot.subject_id or decision.subject_content_sha256 != snapshot.content_hash
                or decision.status != "ai_review_passed"
                or tuple(claim.claim_id for claim in decision.atomic_claims) != CLAIM_IDS):
            _fail("text_review_consensus_required")
        for claim in decision.atomic_claims:
            if (claim.verdict != "passed" or claim.confidence < 0.8 or claim.uncertainty_codes
                    or not set(claim.evidence_reference_ids) <= set(snapshot.evidence_reference_ids)
                    or not set(_CLAIM_REFERENCES[claim.claim_id]) <= set(claim.evidence_reference_ids)):
                _fail("text_review_atomic_claim_failed")


def _same_reviewed_content(current, prior):
    """A later manual approval may advance the pointer but cannot change its value."""
    def content(snapshot):
        payload = snapshot.model_dump(mode="json", exclude={"content_hash"})
        for binding in payload["field_revisions"]:
            binding.pop("pointer_version")
            binding.pop("review_status")
        return payload
    return content(current) == content(prior) and all(
        current_binding.pointer_version >= prior_binding.pointer_version
        for current_binding, prior_binding in zip(current.field_revisions, prior.field_revisions, strict=True))


def _lock_current_rows(runtime, job_id, item_id):
    """Hold content/pointer rows against writers that do not lock the parent job.

    Lock order is job (caller), lexical candidate, text record, then ordered text
    pointers. PostgreSQL retains these locks through acceptance; SQLite already
    has its write lock from the parent's no-op UPDATE. Re-read only after locking.
    """
    item_id = runtime._resolve_review_item_id(job_id, item_id)
    for model in (LexicalCandidate, TextQualityRecordModel):
        runtime.session.scalars(select(model).where(model.job_id == job_id, model.item_key == item_id)
            .order_by(model.id).with_for_update().execution_options(populate_existing=True)).all()
    runtime.session.scalars(select(ReviewCurrentPointerModel).where(
        ReviewCurrentPointerModel.job_id == job_id, ReviewCurrentPointerModel.item_id == item_id,
        ReviewCurrentPointerModel.field_name.in_(FIELDS)).order_by(ReviewCurrentPointerModel.id)
        .with_for_update().execution_options(populate_existing=True)).all()
    return item_id


def apply_personal_text_evidence(runtime, *, job_id, item_id, evidence, actor_id, request_id):
    """Atomically accept only exact current content supported by three AI passes."""
    if runtime.session.new or runtime.session.dirty or runtime.session.deleted:
        _fail("text_review_clean_session_required")
    if any(not isinstance(value, str) or not value.strip() or len(value) > 160 for value in (actor_id, request_id)):
        _fail("text_review_actor_or_request_invalid")
    evidence = PersonalTextReviewEvidence.model_validate(
        evidence.model_dump(mode="json") if isinstance(evidence, PersonalTextReviewEvidence) else evidence)
    _validate_consensus(evidence)
    key = canonical_json_sha256({"actor": actor_id, "request": request_id})
    command = canonical_json_sha256({"job": job_id, "item": evidence.snapshot.subject_id,
        "actor": actor_id, "request": request_id, "evidence": evidence.content_hash})
    with repository_transaction(runtime.session):
        job = lock_job_for_update(runtime.session, job_id)
        item_id = _lock_current_rows(runtime, job_id, item_id)
        current, record = _snapshot(runtime, job_id, item_id)
        state = job.resume_state.get(_STATE, {})
        prior = state.get("requests", {}).get(key)
        if prior is not None:
            if prior["command_sha256"] != command:
                _fail("text_review_request_conflict")
            if not _same_reviewed_content(current, evidence.snapshot):
                _fail("text_review_snapshot_stale")
            if (record.review_status is not ReviewStatus.ACCEPTED
                    or record.text_review_receipt_sha256 != evidence.content_hash
                    or record.provider_review_evidence is None
                    or record.provider_review_evidence.review_receipt_sha256 != evidence.content_hash
                    or record.provider_review_evidence.policy_sha256 != current.provider_policy_sha256
                    or record.provider_review_evidence.decision != "accepted"):
                _fail("text_review_receipt_not_current")
            return {**prior["result"], "replayed": True}
        if current != evidence.snapshot:
            _fail("text_review_snapshot_stale")
        receipt_hash = evidence.content_hash
        saved = record.model_copy(update={"review_status": ReviewStatus.ACCEPTED,
            "text_review_receipt_sha256": receipt_hash, "provider_review_evidence": KoreanProviderReviewEvidence(
                reviewer_class="ai_policy_linguistic_review", policy_sha256=current.provider_policy_sha256,
                review_receipt_sha256=receipt_hash, decision="accepted")})
        runtime.texts.upsert_text_record(saved)
        result = {"status": "ai_review_passed", "job_id": job_id, "item_id": current.item_id,
            "receipt_sha256": receipt_hash, "snapshot_sha256": current.content_hash, "replayed": False}
        job.resume_state = {**job.resume_state, _STATE: {
            "requests": {**state.get("requests", {}), key: {"command_sha256": command, "result": result}},
            "receipts": {**state.get("receipts", {}), receipt_hash: evidence.model_dump(mode="json")}}}
    return result


def personal_text_review_current(session, job_id, item_id) -> bool:
    """Check full stored evidence against live content without mutating or calling providers."""
    if session.new or session.dirty or session.deleted:
        return False
    from multilang.services.korean_learning_runtime import KoreanLearningRuntime
    runtime = KoreanLearningRuntime(session)
    try:
        with session.no_autoflush:
            current, record = _snapshot(runtime, job_id, item_id)
            if record.review_status is not ReviewStatus.ACCEPTED or record.provider_review_evidence is None:
                return False
            job = runtime._job(job_id)
            payload = job.resume_state.get(_STATE, {}).get("receipts", {}).get(record.text_review_receipt_sha256)
            evidence = PersonalTextReviewEvidence.model_validate(payload)
            _validate_consensus(evidence)
            return bool(_same_reviewed_content(current, evidence.snapshot)
                and record.text_review_receipt_sha256 == evidence.content_hash
                and record.provider_review_evidence.review_receipt_sha256 == evidence.content_hash
                and record.provider_review_evidence.policy_sha256 == current.provider_policy_sha256
                and record.provider_review_evidence.decision == "accepted")
    except (ValueError, TypeError, KeyError, AttributeError):
        return False
