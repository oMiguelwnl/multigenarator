"""Explicitly scoped Korean personal audio generation and evidence-bound promotion.

Publication is pending until acoustic evidence is imported. Approved media can
only be replaced after an explicit atomic rejection of its current revision.
"""

from __future__ import annotations

import json
import math
import os
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, SessionTransactionOrigin

from multilang.db.models import (
    AudioPublicationReservationModel,
    ReviewCurrentPointerModel,
    ReviewDecisionModel,
    ReviewFieldRevisionModel,
)
from multilang.domain.audio import AudioAssetKind, AudioReviewStatus, AudioSynthesisStatus
from multilang.domain.korean import canonical_json_sha256
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.domain.review import AudioReviewEvidence, ReviewField, derive_audio_final_path
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.repositories.transactions import lock_job_for_update, repository_transaction
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.generation_leases import GenerationLeaseManager
from multilang.services.korean_audio import (
    KoreanVoiceProfile,
    _catalog_voice_mappings,
    _selected_catalog_voice,
)
from multilang.services.korean_audio_runtime import KoreanProfileAudioSynthesisService

Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9_.:-]+$")]
PersonalSource = Literal["word-list", "kindle-highlights"]
AudioField = Literal["word_audio", "sentence_audio"]
_STATE = "korean_personal_audio"
_REVIEWS = "korean_personal_audio_reviews"


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class PersonalVoiceAuthority(_Contract):
    schema_version: Literal["korean-personal-voice-authority-v1"] = "korean-personal-voice-authority-v1"
    power: Literal["bind-personal-voice-profile"] = "bind-personal-voice-profile"
    source_types: tuple[PersonalSource, ...] = Field(min_length=1, max_length=2)
    voice_id: str = Field(min_length=1, max_length=160)
    region: Identifier
    catalog_result_file_sha256: Hash
    catalog_content_sha256: Hash
    provider_policy_sha256: Hash


class PersonalVoiceBinding(_Contract):
    schema_version: Literal["korean-personal-voice-binding-v1"] = "korean-personal-voice-binding-v1"
    authority: PersonalVoiceAuthority
    profile: KoreanVoiceProfile

    @property
    def binding_sha256(self):
        return canonical_json_sha256(self.model_dump(mode="json"))


class PersonalAudioAuthority(_Contract):
    schema_version: Literal["korean-personal-audio-authority-v1"] = "korean-personal-audio-authority-v1"
    power: Literal["regenerate-one-personal-audio"] = "regenerate-one-personal-audio"
    job_id: Identifier
    item_id: Identifier
    source_type: PersonalSource
    field: AudioField
    actor_id: Identifier
    request_id: Identifier
    expected_pointer_version: int = Field(ge=0)
    voice_binding_sha256: Hash
    provider_policy_sha256: Hash
    spoken_text_sha256: Hash
    text_review_receipt_sha256: Hash
    synthesis_request_sha256: Hash
    audio_root_sha256: Hash
    pricing_usd_per_million_characters: float = Field(gt=0, allow_inf_nan=False)
    max_estimated_cost_usd: float = Field(ge=0, le=1000, allow_inf_nan=False)

    @property
    def authority_sha256(self):
        return canonical_json_sha256(self.model_dump(mode="json"))


class PersonalAudioReviewAuthority(_Contract):
    schema_version: Literal["korean-personal-audio-review-authority-v1"] = "korean-personal-audio-review-authority-v1"
    power: Literal["promote-reviewed-personal-audio"] = "promote-reviewed-personal-audio"
    job_id: Identifier
    item_id: Identifier
    field: AudioField
    revision_id: Identifier
    expected_pointer_version: int = Field(ge=1)
    actor_id: Identifier
    request_id: Identifier
    generation_authority_sha256: Hash
    review_evidence_sha256: Hash


class PersonalAudioRecoveryAuthority(_Contract):
    schema_version: Literal["korean-personal-audio-recovery-authority-v1"] = "korean-personal-audio-recovery-authority-v1"
    power: Literal["abandon-uncertain-personal-audio"] = "abandon-uncertain-personal-audio"
    job_id: Identifier
    item_id: Identifier
    field: AudioField
    revision_id: Identifier
    expected_pointer_version: int = Field(ge=1)
    generation_authority_sha256: Hash
    synthesis_request_sha256: Hash
    actor_id: Identifier
    request_id: Identifier
    acknowledge_unknown_outcome: Literal[True]


def _hash(value):
    return sha256(value.encode("utf-8")).hexdigest()


def _fail(code):
    from multilang.services.korean_learning_runtime import KoreanLearningRuntimeError
    raise KoreanLearningRuntimeError("personal_audio_" + code)


def _validated(model, value):
    return model.model_validate(value.model_dump(mode="json") if isinstance(value, BaseModel) else value)


def bind_personal_voice_profile(*, authority, catalog, catalog_file_sha256, provider_policy):
    """Create a new personal binding; legacy frequency scope is never extended."""
    authority = _validated(PersonalVoiceAuthority, authority)
    policy = _validated(KoreanProviderPolicy, provider_policy)
    if (catalog_file_sha256 != authority.catalog_result_file_sha256
            or authority.provider_policy_sha256 != policy.policy_sha256
            or catalog.get("catalog_locale") != "ko-KR"
            or catalog.get("catalog_query_count") != 1 or catalog.get("synthesis_attempt_count") != 0
            or len(set(authority.source_types)) != len(authority.source_types)):
        _fail("voice_authority_drift")
    content_hash = canonical_json_sha256({"catalog_locale": "ko-KR", "voices": catalog.get("voices")})
    if content_hash != authority.catalog_content_sha256:
        _fail("catalog_drift")
    _selected_catalog_voice(_catalog_voice_mappings(catalog), selected_voice_id=authority.voice_id, region=authority.region)
    payload = dict(schema_version="korean-voice-profile-v1", voice_id=authority.voice_id,
        locale="ko-KR", region=authority.region, provider="azure-speech",
        output_format="audio-24khz-48kbitrate-mono-mp3", profile_policy_version="korean-neutral-ssml-v1",
        ssml_policy="neutral", fallback_policy="none", provider_sdk_version="not-captured",
        usage_scope=tuple(f"ordinary-{source}-{role}-audio" for source in authority.source_types for role in ("word", "sentence")),
        catalog_receipt_sha256=content_hash, catalog_result_file_sha256=catalog_file_sha256,
        catalog_locator_sha256=None, catalog_content_sha256=content_hash, pilot_authority_sha256=None,
        provider_policy_sha256=policy.policy_sha256,
        profile_authority_sha256=canonical_json_sha256(authority.model_dump(mode="json")))
    profile = KoreanVoiceProfile(**payload, profile_sha256=canonical_json_sha256(payload))
    return PersonalVoiceBinding(authority=authority, profile=profile)


def _session_engine(runtime):
    session = runtime.session
    transaction = session.get_transaction()
    if (session.new or session.dirty or session.deleted or session.in_nested_transaction()
            or (transaction is not None and transaction.origin is not SessionTransactionOrigin.AUTOBEGIN)):
        _fail("standalone_session_required")
    engine = session.get_bind()
    if not isinstance(engine, Engine) or runtime.settings is None:
        _fail("explicit_settings_required")
    return engine


def _key(actor, request):
    return canonical_json_sha256({"actor": actor, "request": request})


def _state(job, key):
    return (job.resume_state or {}).get(_STATE, {}).get(key)


def _save(job, key, payload):
    job.resume_state = {**job.resume_state, _STATE: {**job.resume_state.get(_STATE, {}), key: payload}}


def _replay(job, key, digest):
    previous = _state(job, key)
    if previous is None:
        return None
    if previous["authority_sha256"] != digest:
        _fail("request_conflict")
    if previous["state"] == "abandoned":
        _fail("request_abandoned")
    if previous["state"] != "synthesized":
        _fail("recovery_required")
    return {**previous["result"], "replayed": True}


def _spoken(runtime, job_id, item_id, field):
    from multilang.services.korean_personal_text_review import personal_text_review_current
    if not personal_text_review_current(runtime.session, job_id, item_id):
        _fail("accepted_text_required")
    candidate, record, _ = runtime._values(job_id, item_id)
    if (record.review_status is not ReviewStatus.ACCEPTED
            or record.validation_status is not ValidationStatus.PASSED or not record.text_review_receipt_sha256):
        _fail("accepted_text_required")
    text = candidate.lemma if field == "word_audio" else record.example_sentence
    if not text:
        _fail("spoken_text_required")
    return candidate, record, text


def _assert_replaceable(runtime, job_id, item_id, field, expected):
    pointer = runtime._pointer(job_id, item_id, field)
    if (pointer.pointer_version if pointer else 0) != expected:
        _fail("stale_revision")
    asset = AudioRepository(runtime.session).get_asset(job_id, item_id, AudioAssetKind(field.removesuffix("_audio")))
    if ((pointer is not None and pointer.review_status == "approved")
            or (asset and asset.provenance.audio_review_status is AudioReviewStatus.APPROVED)):
        _fail("approved_asset_preserved")
    return pointer


def _safe_path(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        _fail("media_path_invalid")
    return path


def _integrity(asset, relative):
    return canonical_json_sha256({"path": relative, "artifact": asset.provenance.artifact_sha256,
        "bytes": asset.provenance.byte_size, "duration_ms": asset.provenance.duration_ms,
        "spoken": asset.provenance.text_hash, "ssml": asset.provenance.ssml_hash,
        "request": asset.provenance.synthesis_request_sha256, "profile": asset.provenance.voice_profile_sha256})


def _audio_identity(runtime, job_id, item_id, field):
    pointer = runtime._pointer(job_id, item_id, field)
    revision = runtime.session.get(ReviewFieldRevisionModel, pointer.current_revision_id) if pointer else None
    asset = AudioRepository(runtime.session).get_asset(job_id, item_id, AudioAssetKind(field.removesuffix("_audio")))
    return dict(revision_sha256=_hash(revision.id) if revision else None,
        value_sha256=revision.value_sha256 if revision else None,
        artifact_sha256=asset.provenance.artifact_sha256 if asset else None,
        request_sha256=asset.provenance.synthesis_request_sha256 if asset else None,
        pointer_version=pointer.pointer_version if pointer else 0,
        review_status=pointer.review_status if pointer else None)


def regenerate_personal_audio(runtime, *, authority, binding, catalog, catalog_file_sha256, provider_policy, adapter=None):
    """Reserve exactly one field before billing, then publish immutable pending bytes."""
    authority = _validated(PersonalAudioAuthority, authority)
    binding = _validated(PersonalVoiceBinding, binding)
    policy = _validated(KoreanProviderPolicy, provider_policy)
    engine = _session_engine(runtime)
    session = runtime.session
    job = runtime._job(authority.job_id)
    key, digest = _key(authority.actor_id, authority.request_id), authority.authority_sha256
    replay = _replay(job, key, digest)
    if replay:
        return replay
    if bind_personal_voice_profile(authority=binding.authority, catalog=catalog,
            catalog_file_sha256=catalog_file_sha256, provider_policy=policy) != binding:
        _fail("voice_binding_drift")
    if (binding.binding_sha256 != authority.voice_binding_sha256
            or authority.source_type not in binding.authority.source_types
            or job.source_type != authority.source_type
            or policy.policy_sha256 != authority.provider_policy_sha256
            or job.korean_provider_policy_sha256 != policy.policy_sha256
            or canonical_json_sha256(job.korean_provider_policy) != canonical_json_sha256(policy.model_dump(mode="json"))):
        _fail("source_or_policy_drift")
    item_id = runtime._resolve_review_item_id(authority.job_id, authority.item_id)
    from multilang.services.korean_learning_runtime import public_korean_item_id
    if public_korean_item_id(item_id) != authority.item_id:
        _fail("public_item_identity_required")
    candidate, record, spoken = _spoken(runtime, authority.job_id, item_id, authority.field)
    if candidate.source_type != authority.source_type:
        _fail("source_drift")
    _assert_replaceable(runtime, authority.job_id, item_id, authority.field, authority.expected_pointer_version)
    root = runtime.settings.audio_storage_dir.resolve()
    if (authority.audio_root_sha256 != _hash(str(root))
            or authority.pricing_usd_per_million_characters != runtime.settings.korean_azure_tts_usd_per_million_characters
            or authority.spoken_text_sha256 != _hash(spoken)
            or authority.text_review_receipt_sha256 != record.text_review_receipt_sha256):
        _fail("input_authority_drift")
    audio_adapter = adapter or AzureSpeechAdapter(runtime.settings)
    service = KoreanProfileAudioSynthesisService(profile=binding.profile, provider_policy=policy,
        adapter=audio_adapter, settings=runtime.settings, provider_call_logger=None, source_type=authority.source_type)
    kind = AudioAssetKind(authority.field.removesuffix("_audio"))
    prepared = service._prepare(authority.job_id, authority.item_id, kind, spoken)
    if (prepared.provenance.synthesis_request_sha256 != authority.synthesis_request_sha256
            or prepared.normalized_input.text_hash != authority.spoken_text_sha256):
        _fail("request_drift")
    cost = service.estimated_cost(prepared)
    if not math.isfinite(cost) or cost > authority.max_estimated_cost_usd:
        _fail("cost_budget_exceeded")
    session.rollback()
    with GenerationLeaseManager(engine).hold(authority.job_id) as lease:
        with repository_transaction(session):
            lease.fence(session)
            job = lock_job_for_update(session, authority.job_id)
            replay = _replay(job, key, digest)
            if replay:
                return replay
            _assert_replaceable(runtime, authority.job_id, item_id, authority.field, authority.expected_pointer_version)
            if any(value["state"] not in {"synthesized", "abandoned"} and value["item_sha256"] == _hash(item_id)
                    and value["field"] == authority.field for value in job.resume_state.get(_STATE, {}).values()):
                _fail("recovery_required")
            _, current, current_spoken = _spoken(runtime, authority.job_id, item_id, authority.field)
            if (_hash(current_spoken) != authority.spoken_text_sha256
                    or current.text_review_receipt_sha256 != authority.text_review_receipt_sha256
                    or job.korean_provider_policy_sha256 != policy.policy_sha256):
                _fail("input_authority_drift")
            content_hash = canonical_json_sha256({"request": authority.synthesis_request_sha256,
                "spoken": authority.spoken_text_sha256, "profile": binding.profile.profile_sha256})
            before = _audio_identity(runtime, authority.job_id, item_id, authority.field)
            mutation = runtime.reviews.create_candidate_revision(actor_id=authority.actor_id, request_id=authority.request_id,
                job_id=authority.job_id, item_id=item_id, field_name=authority.field, value_sha256=content_hash,
                generator_id="azure-speech", generator_version=binding.profile.voice_id,
                route_id=policy.route_for(KoreanProviderTask(authority.field)).route_policy_sha256,
                previous_revision_sha256=before["value_sha256"],
                expected_pointer_version=authority.expected_pointer_version)
            revision_id = mutation.revision.revision_id
            relative = derive_audio_final_path(field=ReviewField(authority.field), item_id="item-" + _hash(item_id),
                revision_id=revision_id, request_sha256=authority.synthesis_request_sha256, profile_extension="mp3")
            reservation = runtime.reviews.reserve_audio_publication(job_id=authority.job_id, item_id=item_id,
                field_name=authority.field, field_revision_id=revision_id, request_sha256=authority.synthesis_request_sha256,
                final_path=relative, authority_sha256=digest, root_prestate_sha256=authority.audio_root_sha256,
                expected_pointer_version=mutation.pointer_version)
            state = dict(authority_sha256=digest, item_sha256=_hash(item_id), field=authority.field,
                source_type=authority.source_type,
                state="reserved", revision_id=revision_id, pointer_version=mutation.pointer_version,
                reservation_id=reservation.reservation_id, relative_path=relative,
                synthesis_request_sha256=authority.synthesis_request_sha256,
                spoken_text_sha256=authority.spoken_text_sha256, text_review_receipt_sha256=authority.text_review_receipt_sha256,
                policy_sha256=policy.policy_sha256, profile_sha256=binding.profile.profile_sha256,
                revision_content_sha256=content_hash, audio_root_sha256=authority.audio_root_sha256,
                before=before, before_sha256=canonical_json_sha256(before), after_sha256=None)
            _save(job, key, state)
        lease.begin_item("personal-audio:" + digest)
        try:
            root.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(prefix=".personal-audio-", dir=root) as temporary, Session(engine) as telemetry:
                staging_settings = runtime.settings.model_copy(update={"audio_storage_dir": Path(temporary)})
                staged_service = KoreanProfileAudioSynthesisService(profile=binding.profile, provider_policy=policy,
                    adapter=audio_adapter, settings=staging_settings, provider_call_logger=ProviderCallLogRepository(telemetry),
                    source_type=authority.source_type)
                staged = staged_service._prepare(authority.job_id, authority.item_id, kind, spoken)
                asset = staged_service.synthesize_prepared_asset(staged)
                info = inspect_local_mp3(asset.provenance.storage_path, artifact_hash_prefix=b"artifact:")
                if (asset.provenance.status is not AudioSynthesisStatus.SYNTHESIZED or info is None
                        or info.artifact_sha256 != asset.provenance.artifact_sha256
                        or abs(info.duration_ms - asset.provenance.duration_ms) > 100):
                    _fail("media_or_provider_failed")
                target = _safe_path(root, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target = _safe_path(root, relative)
                with target.open("xb") as output:
                    output.write(Path(asset.provenance.storage_path).read_bytes())
                    output.flush()
                    os.fsync(output.fileno())
                asset = asset.model_copy(update={"item_key": item_id, "provenance": asset.provenance.model_copy(
                    update={"storage_path": str(target), "duration_ms": info.duration_ms})})
            with repository_transaction(session):
                lease.fence(session)
                job = lock_job_for_update(session, authority.job_id)
                pointer = runtime._pointer(authority.job_id, item_id, authority.field)
                _, current, current_spoken = _spoken(runtime, authority.job_id, item_id, authority.field)
                if (pointer.current_revision_id != revision_id or pointer.pointer_version != mutation.pointer_version
                        or _hash(current_spoken) != authority.spoken_text_sha256
                        or current.text_review_receipt_sha256 != authority.text_review_receipt_sha256
                        or job.korean_provider_policy_sha256 != policy.policy_sha256):
                    _fail("stale_revision")
                changed = session.execute(update(ReviewCurrentPointerModel).where(
                    ReviewCurrentPointerModel.id == pointer.id,
                    ReviewCurrentPointerModel.current_revision_id == revision_id,
                    ReviewCurrentPointerModel.pointer_version == mutation.pointer_version,
                    ReviewCurrentPointerModel.review_status == "needs_review",
                ).values(pointer_version=mutation.pointer_version).returning(ReviewCurrentPointerModel.id)
                  .execution_options(synchronize_session=False)).scalar_one_or_none()
                if changed is None:
                    _fail("stale_revision")
                for index, (before, after) in enumerate((("reserved", "staged"), ("staged", "published"))):
                    runtime.reviews.append_audio_publication_transition(reservation_id=reservation.reservation_id,
                        from_state=before, to_state=after, expected_version=index,
                        transition_sha256=canonical_json_sha256({"authority": digest, "state": after}))
                AudioRepository(session).upsert_audio_asset(asset)
                result = dict(status="needs_review", revision_id=revision_id, pointer_version=mutation.pointer_version,
                    synthesis_request_sha256=authority.synthesis_request_sha256, artifact_sha256=asset.provenance.artifact_sha256,
                    relative_path=relative, integrity_sha256=_integrity(asset, relative), revision_content_sha256=content_hash,
                    replayed=False)
                after = dict(revision_sha256=_hash(revision_id), value_sha256=content_hash,
                    artifact_sha256=asset.provenance.artifact_sha256, request_sha256=authority.synthesis_request_sha256,
                    pointer_version=mutation.pointer_version, review_status="needs_review")
                _save(job, key, {**state, "state": "synthesized", "after": after,
                    "after_sha256": canonical_json_sha256(after), "result": result})
                lease.finish_item(session)
            lease.current_item_sha256 = None
            return result
        except Exception:
            session.rollback()
            with repository_transaction(session):
                lease.fence(session)
                job = lock_job_for_update(session, authority.job_id)
                _save(job, key, {**state, "state": "failed_unknown"})
            _fail("recovery_required")


def _generation_for_revision(job, revision_id):
    matches = [entry for entry in job.resume_state.get(_STATE, {}).values()
        if entry.get("revision_id") == revision_id and entry.get("state") == "synthesized"]
    if len(matches) != 1:
        _fail("unknown_revision")
    return matches[0]


def _decision(runtime, *, job, item_id, field, revision_id, version, actor, request, decision, digest, evidence=None):
    before = _audio_identity(runtime, job.id, item_id, field)
    changed = runtime.session.execute(update(ReviewCurrentPointerModel).where(
        ReviewCurrentPointerModel.job_id == job.id, ReviewCurrentPointerModel.item_id == item_id,
        ReviewCurrentPointerModel.field_name == field, ReviewCurrentPointerModel.current_revision_id == revision_id,
        ReviewCurrentPointerModel.pointer_version == version).values(review_status=decision, pointer_version=version + 1)
        .returning(ReviewCurrentPointerModel.id).execution_options(synchronize_session=False)).scalar_one_or_none()
    if changed is None:
        _fail("stale_revision")
    rows = runtime.session.scalars(select(ReviewDecisionModel).where(ReviewDecisionModel.revision_id == revision_id)).all()
    import uuid
    runtime.session.add(ReviewDecisionModel(id=str(uuid.uuid4()), job_id=job.id, item_id=item_id,
        field_name=field, revision_id=revision_id, decision_revision=max((row.decision_revision for row in rows), default=0) + 1,
        review_status=decision, reviewer_id_sha256=_hash(actor), decision_sha256=digest, reason_code="personal_audio_review"))
    result = dict(status=decision, revision_id=revision_id, pointer_version=version + 1, replayed=False)
    after = {**before, "pointer_version": version + 1, "review_status": decision}
    job.resume_state = {**job.resume_state, _REVIEWS: {**job.resume_state.get(_REVIEWS, {}), _key(actor, request): {
        "command_sha256": digest, "before": before, "after": after,
        "before_sha256": canonical_json_sha256(before), "after_sha256": canonical_json_sha256(after),
        "evidence": evidence, "result": result}}}
    runtime.session.flush()
    runtime.session.expire_all()
    return result


def review_personal_audio(runtime, *, authority, evidence):
    """Promote only exact externally reviewed bytes; this never calls a provider."""
    authority = _validated(PersonalAudioReviewAuthority, authority)
    evidence = _validated(AudioReviewEvidence, evidence)
    _session_engine(runtime)
    digest = canonical_json_sha256(authority.model_dump(mode="json"))
    if (canonical_json_sha256(evidence.model_dump(mode="json")) != authority.review_evidence_sha256
            or evidence.status != "ai_acoustic_review_passed" or evidence.source_kind != "production"
            or not evidence.acoustic_review_sha256):
        _fail("acoustic_evidence_required")
    session = runtime.session
    with repository_transaction(session):
        job = lock_job_for_update(session, authority.job_id)
        previous = job.resume_state.get(_REVIEWS, {}).get(_key(authority.actor_id, authority.request_id))
        if previous:
            if previous["command_sha256"] != digest:
                _fail("request_conflict")
            return {**previous["result"], "replayed": True}
        item_id = runtime._resolve_review_item_id(authority.job_id, authority.item_id)
        state = _generation_for_revision(job, authority.revision_id)
        if state["authority_sha256"] != authority.generation_authority_sha256 or state["item_sha256"] != _hash(item_id):
            _fail("review_authority_drift")
        candidate, record, spoken = _spoken(runtime, authority.job_id, item_id, authority.field)
        asset = AudioRepository(session).get_asset(authority.job_id, item_id, AudioAssetKind(authority.field.removesuffix("_audio")))
        revision = session.get(ReviewFieldRevisionModel, authority.revision_id)
        root = runtime.settings.audio_storage_dir.resolve()
        path = _safe_path(root, state["relative_path"])
        info = inspect_local_mp3(path, artifact_hash_prefix=b"artifact:")
        if (asset is None or info is None or state["field"] != authority.field
                or state["source_type"] != job.source_type or job.language != "ko"
                or candidate.source_type != state["source_type"]
                or state["audio_root_sha256"] != _hash(str(root))
                or state["spoken_text_sha256"] != _hash(spoken)
                or state["text_review_receipt_sha256"] != record.text_review_receipt_sha256
                or state["policy_sha256"] != job.korean_provider_policy_sha256
                or _validated(KoreanProviderPolicy, job.korean_provider_policy).policy_sha256 != state["policy_sha256"]
                or asset.normalized_input.text_hash != state["spoken_text_sha256"]
                or asset.provenance.text_hash != asset.normalized_input.text_hash
                or asset.display_text != asset.normalized_input.display_text or asset.display_text != spoken
                or asset.provenance.ssml_hash != asset.normalized_input.ssml_hash
                or asset.normalized_input.synthesis_request_sha256 != state["synthesis_request_sha256"]
                or asset.provenance.storage_path != str(path)
                or info.artifact_sha256 != asset.provenance.artifact_sha256
                or info.byte_size != asset.provenance.byte_size
                or info.duration_ms != asset.provenance.duration_ms
                or evidence.final_path != state["relative_path"]
                or evidence.artifact_sha256 != asset.provenance.artifact_sha256
                or evidence.artifact_sha256 != state["result"]["artifact_sha256"]
                or evidence.integrity_sha256 != _integrity(asset, state["relative_path"])
                or evidence.integrity_sha256 != state["result"]["integrity_sha256"]
                or evidence.request_sha256 != asset.provenance.synthesis_request_sha256
                or evidence.request_sha256 != state["synthesis_request_sha256"]
                or evidence.profile_sha256 != state["profile_sha256"]
                or evidence.profile_sha256 != asset.provenance.voice_profile_sha256
                or evidence.policy_sha256 != state["policy_sha256"]
                or evidence.revision_content_sha256 != state["revision_content_sha256"]
                or revision is None or revision.value_sha256 != state["revision_content_sha256"]):
            _fail("review_evidence_drift")
        result = _decision(runtime, job=job, item_id=item_id, field=authority.field,
            revision_id=authority.revision_id, version=authority.expected_pointer_version,
            actor=authority.actor_id, request=authority.request_id, decision="approved", digest=digest,
            evidence=evidence.model_dump(mode="json"))
        AudioRepository(session).upsert_audio_asset(asset.model_copy(update={"provenance": asset.provenance.model_copy(update={
            "audio_review_status": AudioReviewStatus.APPROVED, "audio_review_receipt_sha256": authority.review_evidence_sha256,
            "heard_review_receipt_sha256": evidence.acoustic_review_sha256})}))
        return result


def reject_personal_audio(runtime, *, job_id, item_id, field, revision_id, expected_pointer_version, actor_id, request_id):
    """Reject pointer and active projection atomically, preserving every byte and revision."""
    _session_engine(runtime)
    if field not in ("word_audio", "sentence_audio"):
        _fail("audio_field_required")
    digest = canonical_json_sha256(dict(job=job_id, item=item_id, field=field, revision=revision_id,
        version=expected_pointer_version, actor=actor_id, request=request_id, action="reject"))
    with repository_transaction(runtime.session):
        job = lock_job_for_update(runtime.session, job_id)
        if job.source_type not in ("word-list", "kindle-highlights") or job.language != "ko":
            _fail("personal_source_required")
        previous = job.resume_state.get(_REVIEWS, {}).get(_key(actor_id, request_id))
        if previous:
            if previous["command_sha256"] != digest:
                _fail("request_conflict")
            return {**previous["result"], "replayed": True}
        item_id = runtime._resolve_review_item_id(job_id, item_id)
        state = _generation_for_revision(job, revision_id)
        if state["item_sha256"] != _hash(item_id) or state["field"] != field:
            _fail("review_authority_drift")
        asset = AudioRepository(runtime.session).get_asset(job_id, item_id, AudioAssetKind(field.removesuffix("_audio")))
        if asset is None or asset.provenance.synthesis_request_sha256 != state["result"]["synthesis_request_sha256"]:
            _fail("review_evidence_drift")
        result = _decision(runtime, job=job, item_id=item_id, field=field, revision_id=revision_id,
            version=expected_pointer_version, actor=actor_id, request=request_id, decision="rejected", digest=digest)
        AudioRepository(runtime.session).upsert_audio_asset(asset.model_copy(update={"provenance": asset.provenance.model_copy(update={
            "audio_review_status": AudioReviewStatus.REJECTED, "rejection_reason_code": "operator_rejected"})}))
        return result


def recover_personal_audio(runtime, *, authority):
    """Abandon an uncertain command after explicit lease recovery; never replay it."""
    authority = _validated(PersonalAudioRecoveryAuthority, authority)
    engine = _session_engine(runtime)
    manager = GenerationLeaseManager(engine)
    lease_status = manager.status(authority.job_id)
    if lease_status["state"] not in {"idle", "expired"} or lease_status["inflight_item_sha256"]:
        _fail("lease_recovery_required")
    runtime.session.rollback()
    digest = canonical_json_sha256(authority.model_dump(mode="json"))
    with manager.hold(authority.job_id) as lease, repository_transaction(runtime.session):
        lease.fence(runtime.session)
        job = lock_job_for_update(runtime.session, authority.job_id)
        previous = job.resume_state.get(_REVIEWS, {}).get(_key(authority.actor_id, authority.request_id))
        if previous:
            if previous["command_sha256"] != digest:
                _fail("request_conflict")
            return {**previous["result"], "replayed": True}
        item_id = runtime._resolve_review_item_id(authority.job_id, authority.item_id)
        matches = [(key, value) for key, value in job.resume_state.get(_STATE, {}).items()
            if value["authority_sha256"] == authority.generation_authority_sha256]
        if len(matches) != 1:
            _fail("recovery_authority_drift")
        key, state = matches[0]
        if (state["state"] not in {"reserved", "failed_unknown"}
                or state["revision_id"] != authority.revision_id
                or state["synthesis_request_sha256"] != authority.synthesis_request_sha256
                or state["item_sha256"] != _hash(item_id) or state["field"] != authority.field):
            _fail("recovery_authority_drift")
        _assert_replaceable(runtime, authority.job_id, item_id, authority.field, authority.expected_pointer_version)
        reservation = runtime.session.get(AudioPublicationReservationModel, state["reservation_id"])
        if reservation.state in {"reserved", "staged", "published"}:
            runtime.reviews.append_audio_publication_transition(reservation_id=reservation.id,
                from_state=reservation.state, to_state="failed_unknown", expected_version=reservation.reservation_version,
                transition_sha256=canonical_json_sha256({"recovery": digest, "reservation": reservation.id}))
        result = _decision(runtime, job=job, item_id=item_id, field=authority.field,
            revision_id=authority.revision_id, version=authority.expected_pointer_version,
            actor=authority.actor_id, request=authority.request_id, decision="rejected", digest=digest)
        job = runtime._job(authority.job_id)
        _save(job, key, {**state, "state": "abandoned", "recovery_sha256": digest,
            "prior_state_sha256": canonical_json_sha256(state)})
        # Existing rejected media and any uncertain final bytes are retained.
        return result


def read_contract_file(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        _fail("invalid_contract_file")
    with path.open("rb") as source:
        raw = source.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        _fail("invalid_contract_file")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        _fail("invalid_contract_file")
    return payload, sha256(raw).hexdigest()


def regenerate_from_files(runtime, *, authority_file, profile_file, catalog_file, provider_policy_file):
    catalog, catalog_hash = read_contract_file(catalog_file)
    return regenerate_personal_audio(runtime, authority=read_contract_file(authority_file)[0],
        binding=read_contract_file(profile_file)[0], catalog=catalog, catalog_file_sha256=catalog_hash,
        provider_policy=read_contract_file(provider_policy_file)[0])


def review_from_files(runtime, *, authority_file, evidence_file):
    return review_personal_audio(runtime, authority=read_contract_file(authority_file)[0], evidence=read_contract_file(evidence_file)[0])


def recover_from_file(runtime, *, authority_file):
    return recover_personal_audio(runtime, authority=read_contract_file(authority_file)[0])
