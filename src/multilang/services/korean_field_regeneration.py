"""One-field Korean regeneration with durable reservations and private local audit."""

import math
from hashlib import sha256
from time import perf_counter

from sqlalchemy import update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, SessionTransactionOrigin

from multilang.db.models import ReviewCurrentPointerModel
from multilang.domain.korean import canonical_json_sha256, canonicalize_korean
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.repositories.provider_call_log_repository import (
    ProviderCallLogCreate,
    ProviderCallLogRepository,
)
from multilang.repositories.transactions import lock_job_for_update, repository_transaction
from multilang.services.generation_leases import GenerationLeaseError, GenerationLeaseManager
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
)

_TASKS = {"definition": KoreanProviderTask.DEFINITION, "sentence": KoreanProviderTask.SENTENCE_GENERATION,
          "translation": KoreanProviderTask.TRANSLATION}
_RESULTS = {"definition": (DefinitionGenerationResult, "definitions_html", "generate_definition"),
            "sentence": (SentenceGenerationResult, "sentence", "generate_sentence"),
            "translation": (SentenceTranslationResult, "translation", "translate_sentence")}
_STATE = "korean_field_regenerations"


def _fail(code):
    from multilang.services.korean_learning_runtime import KoreanLearningRuntimeError
    raise KoreanLearningRuntimeError(code)


def _hash(value):
    return sha256(value.encode("utf-8")).hexdigest()


def _input_hash(candidate, values, request):
    return canonical_json_sha256({"values": values, "request": request.model_dump(mode="json"),
        "identity": candidate.korean_identity, "lemma": candidate.lemma, "lemma_key": candidate.lemma_key,
        "display_form": candidate.display_form, "source_type": candidate.source_type})


def _current_input_hash(runtime, job_id, item_id, field):
    candidate, record, values = runtime._values(job_id, item_id)
    return _input_hash(candidate, values, _request(candidate, record, field))


def _request(candidate, record, field):
    # Only lexical identity and generated teaching text enter the request. No
    # private highlight record, source filename, provenance notes or job history.
    if field == "translation":
        return SentenceTranslationRequest(sentence=record.example_sentence or "", translation_target_language="pt")
    from multilang.services.generate_text_items import GenerateTextItemsService
    lexical = GenerateTextItemsService._to_candidate(None, candidate)
    if lexical.korean_identity is None:
        _fail("korean_identity_required")
    if field == "definition":
        return DefinitionGenerationRequest(display_form=lexical.display_form, lemma=lexical.lemma,
            source_language="ko", target_language="pt", part_of_speech=lexical.korean_identity.part_of_speech,
            korean_identity=lexical.korean_identity)
    return SentenceGenerationRequest(display_form=lexical.display_form, lemma=lexical.lemma,
        definitions_html=lexical.definitions_html, target_language="ko", translation_target_language="pt",
        source_type=candidate.source_type, highlight_context=None, korean_identity=lexical.korean_identity)


def _replay(job, key, command_hash):
    prior = job.resume_state.get(_STATE, {}).get(key)
    if prior is None:
        return None
    if prior["command_sha256"] != command_hash:
        _fail("review_request_conflict")
    if prior["state"] != "completed":
        _fail("regeneration_recovery_required")
    return {**prior["result"], "replayed": True}


def regenerate_review_field(runtime, *, job_id, item_id, field, actor_id, request_id,
                            expected_pointer_version, provider_factory=None):
    session = runtime.session
    transaction = session.get_transaction()
    if session.new or session.dirty or session.deleted or session.in_nested_transaction() or (
        transaction is not None and transaction.origin is not SessionTransactionOrigin.AUTOBEGIN
    ):
        _fail("regeneration_requires_standalone_session")
    if field not in _TASKS:
        _fail("text_field_required")
    if any(not isinstance(value, str) or not value.strip() or len(value) > 160 for value in (actor_id, request_id)):
        _fail("invalid_review_actor_or_request")
    if type(expected_pointer_version) is not int or expected_pointer_version < 1:
        _fail("stale_revision")
    session.expire_all()
    job = runtime._job(job_id)
    item_id = runtime._resolve_review_item_id(job_id, item_id)
    command_hash = canonical_json_sha256({"job": job_id, "item": item_id, "field": field,
        "version": expected_pointer_version, "actor": actor_id, "request": request_id})
    request_key = canonical_json_sha256({"actor": actor_id, "request": request_id})
    replay = _replay(job, request_key, command_hash)
    if replay is not None:
        return replay
    if request_key in job.resume_state.get("korean_field_mutations", {}):
        _fail("review_request_conflict")
    policy = KoreanProviderPolicy.model_validate(job.korean_provider_policy) if job.korean_provider_policy else None
    if policy is None or policy.policy_sha256 != job.korean_provider_policy_sha256:
        _fail("provider_policy_required")
    route = policy.route_for(_TASKS[field])
    if not route.enabled or route.budget.max_output_tokens < 1 or route.budget.max_latency_ms < 1:
        _fail("provider_route_unavailable")
    candidate, record, values = runtime._values(job_id, item_id)
    if candidate.source_type not in {"word-list", "kindle-highlights"}:
        _fail("personal_source_required")
    request = _request(candidate, record, field)
    # UTF-8 bytes are a conservative token upper bound; leave room for the fixed
    # transport prompt. Actual provider usage remains separate telemetry.
    if len(request.model_dump_json().encode()) + 1024 > route.budget.max_input_tokens:
        _fail("regeneration_input_budget_exceeded")
    input_hash = _input_hash(candidate, values, request)
    pointer = runtime._pointer(job_id, item_id, field)
    if pointer is None or pointer.pointer_version != expected_pointer_version:
        _fail("stale_revision")
    if pointer.review_status == "approved":
        _fail("approved_field_preserved")
    pointer_id, revision_id = pointer.id, pointer.current_revision_id
    engine = session.get_bind()
    if not isinstance(engine, Engine):
        _fail("regeneration_requires_engine_session")
    provider = (provider_factory or (lambda field, route: _build_provider(runtime.settings, field, route)))(field, route)
    if getattr(provider, "provider", None) != route.provider or getattr(provider, "model", None) != route.model:
        _fail("provider_route_mismatch")
    session.rollback()
    manager = GenerationLeaseManager(engine)
    try:
        with manager.hold(job_id) as lease:
            # Re-read after ownership: a concurrent completed command replays
            # without a second call, and stale UI versions fail before billing.
            with repository_transaction(session):
                lease.fence(session)
                job = lock_job_for_update(session, job_id)
                replay = _replay(job, request_key, command_hash)
                if replay is not None:
                    return replay
                if request_key in job.resume_state.get("korean_field_mutations", {}):
                    _fail("review_request_conflict")
                if job.korean_provider_policy_sha256 != policy.policy_sha256:
                    _fail("provider_policy_required")
                changed = session.execute(update(ReviewCurrentPointerModel).where(
                    ReviewCurrentPointerModel.id == pointer_id,
                    ReviewCurrentPointerModel.pointer_version == expected_pointer_version,
                    ReviewCurrentPointerModel.current_revision_id == revision_id,
                    ReviewCurrentPointerModel.review_status != "approved",
                ).values(pointer_version=expected_pointer_version).returning(ReviewCurrentPointerModel.id)
                  .execution_options(synchronize_session=False)).scalar_one_or_none()
                if changed is None or _current_input_hash(runtime, job_id, item_id, field) != input_hash:
                    _fail("stale_revision")
            lease.begin_item("field:" + command_hash)
            with repository_transaction(session):
                lease.fence(session)
                job = lock_job_for_update(session, job_id)
                job.resume_state = {**job.resume_state, _STATE: {**job.resume_state.get(_STATE, {}), request_key: {
                    "command_sha256": command_hash, "state": "pending", "route_sha256": route.route_policy_sha256}}}
            # No content transaction remains open during the provider request.
            started = perf_counter()
            result, error = None, None
            try:
                result_type, attribute, method = _RESULTS[field]
                result = getattr(provider, method)(request)
                result = result_type.model_validate(result.model_dump(mode="json"))
                value = canonicalize_korean(getattr(result, attribute).strip())
                if not value or len(value) > 8000 or "<" in value or ">" in value:
                    raise ValueError("invalid field output")
                if len(value.encode()) > route.budget.max_output_tokens * 4:
                    raise ValueError("output budget exceeded")
                if (perf_counter() - started) * 1000 > route.budget.max_latency_ms:
                    raise TimeoutError("provider deadline exceeded")
                if result.provenance.get("fallback_from") or result.provenance.get("fallback_used"):
                    raise ValueError("fallback forbidden")
            except Exception as exc:
                error = exc
            prompt_hash = canonical_json_sha256(request.model_dump(mode="json"))
            usage = {}
            if result is not None:
                for name in ("input_tokens", "output_tokens", "total_tokens"):
                    count = result.provenance.get(name)
                    if type(count) is int and count >= 0:
                        usage[name] = count
                cost = result.provenance.get("estimated_cost")
                if type(cost) in (int, float) and math.isfinite(cost) and cost >= 0:
                    usage["estimated_cost"] = cost
            with Session(engine) as telemetry_session:
                ProviderCallLogRepository(telemetry_session).insert(ProviderCallLogCreate(
                    operation=route.task.value, provider=route.provider, model=route.model,
                    job_id=job_id, item_key="item:" + _hash(item_id), status="failure" if error else "success",
                    latency_ms=max(0, int((perf_counter() - started) * 1000)),
                    error_code="regeneration_failed" if error else None,
                    error_summary="regeneration_failed" if error else None, prompt_hash=prompt_hash,
                    response_hash=canonical_json_sha256(result.model_dump(mode="json")) if result else None,
                    route_policy_sha256=route.route_policy_sha256, budget_snapshot_sha256=route.budget_snapshot_sha256,
                    cache_key_sha256=route.cache_key_sha256(item_sha256=_hash(item_id), input_sha256=prompt_hash),
                    response_schema_sha256=route.response_schema_sha256, **usage))
            if error is not None:
                _fail("regeneration_failed")
            with repository_transaction(session):
                lease.fence(session)
                job = lock_job_for_update(session, job_id)
                if job.korean_provider_policy_sha256 != policy.policy_sha256:
                    _fail("provider_policy_required")
                if _current_input_hash(runtime, job_id, item_id, field) != input_hash:
                    _fail("stale_revision")
                output = runtime.review_edit(job_id=job_id, item_id=item_id, field=field, value=value,
                    actor_id=actor_id, request_id=request_id, expected_pointer_version=expected_pointer_version,
                    _generator_id=route.provider, _generator_version=route.model, _route_id=route.route_policy_sha256)
                output["revision"].update(generator_id=route.provider, generator_version=route.model,
                                            route_id=route.route_policy_sha256)
                job = runtime._job(job_id)
                job.resume_state = {**job.resume_state, _STATE: {**job.resume_state.get(_STATE, {}), request_key: {
                    "command_sha256": command_hash, "state": "completed", "route_sha256": route.route_policy_sha256,
                    "result": output}}}
                lease.finish_item(session)
            lease.current_item_sha256 = None
            return output
    except GenerationLeaseError:
        session.rollback()
        _fail("regeneration_recovery_required" if manager.status(job_id)["state"] == "recovery_required"
              else "regeneration_in_progress")


def _build_provider(settings, field, route):
    from multilang.services.korean_field_provider import KoreanFieldProvider
    return KoreanFieldProvider(settings, field, route)
