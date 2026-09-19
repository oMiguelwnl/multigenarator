"""Persisted Korean learning operations without eager provider construction."""

from __future__ import annotations

import re
from collections.abc import Callable
from copy import copy
from hashlib import sha256
from pathlib import Path

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from multilang.db.models import (
    LexicalCandidate,
    PrivateContextCapabilityModel,
    ReviewCurrentPointerModel,
    ReviewDecisionModel,
    ReviewFieldRevisionModel,
    TextQualityRecordModel,
)
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    GenerationRequest,
    ItemTerminalStatus,
    JobStage,
    SupportedLanguage,
)
from multilang.domain.korean import canonical_json_sha256, canonicalize_korean
from multilang.domain.korean_grammar import KoreanGrammarBundle
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.korean_personal_source_repository import KoreanPersonalSourceRepository
from multilang.repositories.review_repository import ReviewRepository
from multilang.repositories.text_repository import TextRepository
from multilang.repositories.transactions import lock_job_for_update, repository_transaction
from multilang.services.item_outcomes import ItemHandlerResult
from multilang.services.phase33_jobs import Phase33JobCoordinator, Phase33JobItem
from multilang.settings import Settings

_SOURCES = {"custom": "word-list", "highlight": "kindle-highlights", "grammar": "korean-grammar"}
_FIELDS = ("definition", "sentence", "translation", "word_audio", "sentence_audio")
_COUNTS = ("attempted", "processed", "accepted", "review_required", "failed", "skipped_current", "not_attempted")
_POLICY_HASH = canonical_json_sha256({"policy": "korean-learning-field-review-v1"})
_REVIEW_MUTATIONS = "korean_field_mutations"


class KoreanLearningRuntimeError(ValueError):
    """Controlled, content-free refusal from an operator operation."""


def _fail(code: str):
    raise KoreanLearningRuntimeError(code)


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _review_command(kind, *, actor_id, request_id, expected_pointer_version, **payload):
    if any(not isinstance(value, str) or not value.strip() or len(value) > 160 for value in (actor_id, request_id)):
        _fail("invalid_review_actor_or_request")
    if type(expected_pointer_version) is not int or expected_pointer_version < 1:
        _fail("stale_revision")
    key = canonical_json_sha256({"actor": actor_id, "request": request_id})
    digest = canonical_json_sha256({"kind": kind, "actor": actor_id, "request": request_id,
        "expected_pointer_version": expected_pointer_version, **payload})
    return key, digest


def _review_replay(job, key, digest):
    prior = job.resume_state.get(_REVIEW_MUTATIONS, {}).get(key)
    if prior is None:
        return None
    if prior["command_sha256"] != digest:
        _fail("review_request_conflict")
    return {**prior["result"], "replayed": True}


def _save_review_result(job, key, digest, output):
    job.resume_state = {**job.resume_state, _REVIEW_MUTATIONS: {
        **job.resume_state.get(_REVIEW_MUTATIONS, {}), key: {"command_sha256": digest, "result": output}}}


def public_korean_item_id(item_id: str) -> str:
    """Keep established opaque IDs and hide legacy word-derived item keys."""
    if re.fullmatch(r"(?:custom:[0-9a-f]{64}|highlight-ko-[0-9a-f-]+|row-[0-9]+|item:[0-9a-f]{64})", item_id):
        return item_id
    return "item:" + _hash(item_id)


class _Inventory:
    def __init__(self, items):
        self.items = items

    def list_items(self, job_id):
        return self.items


class _SingleItemTextRepository(TextRepository):
    """Keep the established generation pipeline bounded to the selected item."""

    def __init__(self, session, item_id):
        super().__init__(session)
        self.item_id = item_id

    def list_generation_candidates(self, job_id, *, missing_only=False):
        return [row for row in super().list_generation_candidates(job_id, missing_only=missing_only)
                if row.item_key == self.item_id]


class KoreanLearningRuntime:
    def __init__(self, session: Session, *, settings: Settings | None = None,
                 text_processor: Callable[[str, str], None] | None = None):
        self.session = session
        self.settings = settings
        self.jobs = JobRepository(session)
        self.texts = TextRepository(session)
        self.reviews = ReviewRepository(session)
        self._text_processor = text_processor

    def _job(self, job_id):
        job = self.jobs.get_job(job_id)
        if job is None:
            _fail("unknown_job")
        if job.language != "ko":
            _fail("korean_job_required")
        return job

    def _candidates(self, job_id, source):
        return tuple(self.session.scalars(select(LexicalCandidate).where(
            LexicalCandidate.job_id == job_id, LexicalCandidate.source_type == _SOURCES[source]
        ).order_by(LexicalCandidate.created_at, LexicalCandidate.item_key)))

    def _inventory(self, job_id, source):
        self._job(job_id)
        if source not in _SOURCES:
            _fail("invalid_source")
        if source == "grammar":
            payload = self._job(job_id).resume_state.get("korean_grammar_bundle")
            if payload is None:
                return ()
            bundle = KoreanGrammarBundle.model_validate(payload)
            return tuple(Phase33JobItem(source_family=source, item_id=entry.entry_id)
                         for entry in (*bundle.lexical_bootstrap, *bundle.orientation_entries, *bundle.grammar_entries))
        if source == "custom":
            inventory = KoreanPersonalSourceRepository(self.session).list_inventory(job_id, "word-list")
            if inventory.rows:
                return tuple(Phase33JobItem(source_family=source,
                    item_id=row.item_key if row.duplicate_of_position is None else f"duplicate:{row.row_id}",
                    duplicate_of=row.item_key if row.duplicate_of_position is not None else None,
                    deferred_reason_code=ControlledReasonCode.DEFERRED if row.latest_decision
                        and row.latest_decision.decision_state == "defer" else None,
                    retryable=True) for row in inventory.rows)
        private_states = {}
        if source == "highlight":
            private_states = {row.item_id: row.state for row in self.session.scalars(select(PrivateContextCapabilityModel).where(
                PrivateContextCapabilityModel.job_id == job_id,
                PrivateContextCapabilityModel.state.in_(("disclosing", "disclosed", "failed_unknown"))))}
        return tuple(Phase33JobItem(source_family=source, item_id=row.item_key, retryable=True,
                                   private_state=private_states.get(row.item_key))
                     for row in self._candidates(job_id, source))

    def status(self, job_id):
        self._job(job_id)
        by_source = {source: self._inventory(job_id, source) for source in _SOURCES}
        ids = tuple(item.item_id for items in by_source.values() for item in items)
        facts = self.jobs.list_phase33_processing_facts(job_id, stage=JobStage.GENERATE_TEXT.value)
        statuses = {row.item_id: row for row in self.jobs.list_phase33_item_statuses(
            job_id, stage=JobStage.GENERATE_TEXT.value)}
        attempted = {row.item_id for row in facts if row.attempt_count > 0}
        processed = {row.item_id for row in facts if row.attempt_count > 0 and row.processed_at is not None}
        skipped = {row.item_id for row in facts if row.attempt_count == 0} - attempted
        groups = {"attempted": attempted, "processed": processed, "skipped_current": skipped,
                  "not_attempted": set(ids) - attempted - skipped}
        for name in ("accepted", "review_required", "failed"):
            groups[name] = {key for key, row in statuses.items() if row.terminal_status == name}
        personal_items = (*by_source["custom"], *by_source["highlight"])
        personal_ids = {item.item_id for item in personal_items}
        excluded_personal = {item.item_id for item in personal_items
            if item.duplicate_of is not None or item.deferred_reason_code is not None}
        current_personal = {item.item_id for item in personal_items
            if item.item_id in processed | skipped and item.item_id not in excluded_personal | groups["failed"]
            and self._personal_obligations(job_id, item).all_required_current}
        groups["accepted"] = (groups["accepted"] - personal_ids) | current_personal
        groups["review_required"] = (groups["review_required"] - personal_ids) | (
            (processed | skipped) & personal_ids - current_personal - excluded_personal - groups["failed"])
        grammar_ids = {item.item_id for item in by_source["grammar"]}
        ready_grammar_ids = self._ready_grammar_items(job_id) if grammar_ids else set()
        groups["accepted"] = (groups["accepted"] - grammar_ids) | ready_grammar_ids
        groups["review_required"] = (groups["review_required"] - ready_grammar_ids) | (
            grammar_ids & processed - ready_grammar_ids)
        groups["failed"] -= ready_grammar_ids
        denominators = {name: {"count": len([key for key in ids if key in groups[name]]),
                               "ids": [public_korean_item_id(key) for key in ids if key in groups[name]]} for name in _COUNTS}
        return {"job_id": job_id, "status": "complete" if ids and groups["accepted"] == set(ids) else "incomplete",
                "denominators": denominators, "safe_sources": {
                    source: {"eligible_count": len(items), "ready_count": sum(
                        item.item_id in groups["accepted"] for item in items)}
                    for source, items in by_source.items()}}

    def process(self, *, job_id, source, mode, max_items=None):
        items = self._inventory(job_id, source)
        if not items:
            _fail("empty_source")
        coordinator = Phase33JobCoordinator(job_repository=self.jobs,
            sources={source: _Inventory(items)},
            handlers={source: lambda item, attempt: self._process_item(job_id, item)}, max_attempts=1)
        result = coordinator.execute(job_id=job_id, mode=mode, max_items=max_items)
        counts = dict(result.report.counts)
        if source == "grammar":
            current = self.status(job_id)["denominators"]
            for name in ("accepted", "review_required", "failed"):
                counts[name] = current[name]["count"]
        else:
            current = self.status(job_id)["denominators"]
            source_ids = {public_korean_item_id(item.item_id) for item in items}
            for name in ("accepted", "review_required", "failed"):
                counts[name] = len(source_ids.intersection(current[name]["ids"]))
        return {"job_id": job_id, "source": source, "mode": mode, "max_items": max_items,
                **{name: counts[name] for name in _COUNTS},
                "no_server": True, "no_fallback": True, "complete": counts["accepted"] == len(items)}

    def _ready_grammar_items(self, job_id):
        from multilang.services.korean_grammar_delivery import current_grammar_delivery_items
        return current_grammar_delivery_items(self._job(job_id), self.load_grammar_bundle(job_id))

    def _process_item(self, job_id, item):
        if item.source_family == "custom":
            inventory = KoreanPersonalSourceRepository(self.session).list_inventory(job_id, "word-list")
            stored = next((row for row in inventory.rows if row.item_key == item.item_id), None)
            if stored is not None and (stored.latest_decision is None or stored.latest_decision.decision_state not in {"accepted", "bridge"}):
                return ItemHandlerResult(status=ItemTerminalStatus.REVIEW_REQUIRED,
                    reason_code=ControlledReasonCode.REVIEW_OUTSTANDING,
                    obligations=FieldObligationSummary(ai_review_current=False, integrity_current=False,
                        word_audio_required=True, word_audio_current=False,
                        sentence_audio_required=True, sentence_audio_current=False))
        if item.source_family == "grammar":
            current = item.item_id in self._ready_grammar_items(job_id)
            obligations = FieldObligationSummary(ai_review_current=current, integrity_current=current,
                word_audio_required=True, word_audio_current=current,
                sentence_audio_required=True, sentence_audio_current=current)
        else:
            record = self.texts.get_text_record(job_id, item.item_id)
            if record is None:
                if self._text_processor is not None:
                    self._text_processor(job_id, item.item_id)
                else:
                    self._generate_one(job_id, item.item_id)
                self.session.expire_all()
                record = self.texts.get_text_record(job_id, item.item_id)
            if record is None:
                _fail("text_generation_produced_no_record")
            self._snapshot_fields(job_id, item.item_id)
            obligations = self._personal_obligations(job_id, item)
        return ItemHandlerResult(
            status=ItemTerminalStatus.ACCEPTED if obligations.all_required_current else ItemTerminalStatus.REVIEW_REQUIRED,
            obligations=obligations,
            reason_code=None if obligations.all_required_current else ControlledReasonCode.REVIEW_OUTSTANDING)

    def _personal_obligations(self, job_id, item):
        """Read current local evidence without generating content or changing review state."""
        from multilang.services.korean_personal_text_review import personal_text_review_current

        missing = FieldObligationSummary(ai_review_current=False, integrity_current=False,
            word_audio_required=True, word_audio_current=False,
            sentence_audio_required=True, sentence_audio_current=False)
        if item.source_family == "custom":
            inventory = KoreanPersonalSourceRepository(self.session).list_inventory(job_id, "word-list")
            source_row = next((row for row in inventory.rows
                if row.item_key == item.item_id and row.duplicate_of_position is None), None)
            if source_row is not None and (source_row.latest_decision is None
                    or source_row.latest_decision.decision_state not in {"accepted", "bridge"}):
                return missing
        record = self.texts.get_text_record(job_id, item.item_id)
        candidate = self.session.scalar(select(LexicalCandidate).where(
            LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == item.item_id)
            .execution_options(populate_existing=True))
        if record is None or candidate is None:
            return missing
        assets = {asset.asset_kind.value: asset for asset in AudioRepository(self.session).list_assets_for_job(job_id)
            if asset.item_key == item.item_id}

        def audio_current(kind, expected_text):
            pointer = self._pointer(job_id, item.item_id, kind + "_audio")
            if pointer is not None and pointer.review_status == "rejected":
                return False
            asset = assets.get(kind)
            if asset is None or not asset.ready_for_korean_final_export:
                return False
            normalized, provenance = asset.normalized_input, asset.provenance
            return bool(expected_text and asset.display_text == normalized.display_text == expected_text
                and provenance.text_hash == normalized.text_hash == _hash(normalized.tts_text)
                and provenance.ssml_hash == normalized.ssml_hash == _hash(normalized.ssml_text or normalized.tts_text)
                and provenance.synthesis_request_sha256 == normalized.synthesis_request_sha256)

        matching_profiles = len({asset.provenance.voice_profile_sha256 for asset in assets.values()}) == 1
        values = {"definition": candidate.definitions_html, "sentence": record.example_sentence,
                  "translation": record.translation_text}
        current_revisions = True
        for field, value in values.items():
            pointer = self._pointer(job_id, item.item_id, field)
            if pointer is not None:
                revision = self.session.get(ReviewFieldRevisionModel, pointer.current_revision_id)
                if pointer.review_status == "rejected" or revision is None or revision.value_sha256 != _hash(value or ""):
                    current_revisions = False
        return FieldObligationSummary(
            ai_review_current=bool(current_revisions and record.text_review_receipt_sha256 and record.provider_review_evidence
                and record.provider_review_evidence.decision == "accepted"
                and record.provider_review_evidence.policy_sha256 == self._job(job_id).korean_provider_policy_sha256
                and record.review_status is ReviewStatus.ACCEPTED
                and personal_text_review_current(self.session, job_id, item.item_id)),
            integrity_current=current_revisions and record.validation_status is ValidationStatus.PASSED,
            word_audio_required=True, word_audio_current=matching_profiles and audio_current("word", candidate.lemma),
            sentence_audio_required=True, sentence_audio_current=matching_profiles and audio_current("sentence", record.example_sentence),
        )

    def _generate_one(self, job_id, item_id):
        job = self._job(job_id)
        if not job.korean_provider_policy:
            _fail("provider_policy_required")
        from multilang.domain.korean_provider import KoreanProviderPolicy
        from multilang.runtime import build_runtime_service
        policy = KoreanProviderPolicy.model_validate(job.korean_provider_policy)
        self.session.rollback()  # no transaction across provider calls
        runtime = build_runtime_service(settings=self.settings, korean_provider_policy=policy)
        try:
            service = copy(runtime.generate_text_items_service)
            service.text_repository = _SingleItemTextRepository(runtime.text_repository.session, item_id)
            # Context-free highlights are supported without a disclosure capability.
            service.highlight_import_repository = None
            service.execute(job_id=job_id, deck_language=SupportedLanguage.KO, missing_only=True, max_items=1)
        finally:
            runtime.text_repository.session.close()

    def _pointer(self, job_id, item_id, field):
        return self.session.scalar(select(ReviewCurrentPointerModel).where(
            ReviewCurrentPointerModel.job_id == job_id, ReviewCurrentPointerModel.item_id == item_id,
            ReviewCurrentPointerModel.field_name == field).execution_options(populate_existing=True))

    def _resolve_review_item_id(self, job_id, item_id):
        keys = tuple(self.session.scalars(select(LexicalCandidate.item_key).where(LexicalCandidate.job_id == job_id)))
        matches = [key for key in keys if key == item_id or public_korean_item_id(key) == item_id]
        if len(matches) != 1:
            _fail("unknown_review_item")
        return matches[0]

    def _values(self, job_id, item_id):
        candidate = self.session.scalar(select(LexicalCandidate).where(
            LexicalCandidate.job_id == job_id, LexicalCandidate.item_key == item_id)
            .execution_options(populate_existing=True))
        self.session.scalar(select(TextQualityRecordModel).where(
            TextQualityRecordModel.job_id == job_id, TextQualityRecordModel.item_key == item_id)
            .execution_options(populate_existing=True))
        record = self.texts.get_text_record(job_id, item_id)
        if candidate is None or record is None:
            _fail("unknown_review_item")
        return candidate, record, {"definition": candidate.definitions_html,
            "sentence": record.example_sentence, "translation": record.translation_text}

    def _snapshot_fields(self, job_id, item_id):
        _candidate, _record, values = self._values(job_id, item_id)
        with repository_transaction(self.session):
            for field, value in values.items():
                if value and self._pointer(job_id, item_id, field) is None:
                    self.reviews.create_candidate_revision(actor_id="korean-runtime",
                        request_id=f"import:{item_id}:{field}:{_hash(value)}", job_id=job_id, item_id=item_id,
                        field_name=field, value_sha256=_hash(value), generator_id="persisted-text",
                        generator_version="1", route_id=None, expected_pointer_version=0)

    def review_list(self, *, job_id, actor_id, request_id, status, field, source):
        job = self._job(job_id)
        if field not in (*_FIELDS, "all") or status not in ("needs_review", "approved", "rejected", "all"):
            _fail("invalid_review_filter")
        if source not in (*_SOURCES, "all"):
            _fail("invalid_source")
        source_types = tuple(_SOURCES.values()) if source == "all" else (_SOURCES[source],)
        result = self.reviews.list_fields_with_audit(actor_id=actor_id, request_id=request_id, job_id=job_id,
            fields=_FIELDS if field == "all" else (field,),
            statuses=("needs_review", "approved", "rejected") if status == "all" else (status,),
            source_types=source_types, policy_sha256=_POLICY_HASH,
            snapshot_sha256=canonical_json_sha256({"job": job.id, "source": job.source_fingerprint}))
        return {"access_event_id": result.event.event_id, "rows": [
            {**row, "item_id": public_korean_item_id(str(row["item_id"]))} for row in result.rows]}

    def review_edit(self, *, job_id, item_id, field, value, actor_id, request_id, expected_pointer_version,
                    _generator_id="operator-edit", _generator_version="1", _route_id=None):
        self._job(job_id)
        item_id = self._resolve_review_item_id(job_id, item_id)
        if field not in ("definition", "sentence", "translation"):
            _fail("text_field_required")
        if not isinstance(value, str) or not value.strip() or len(value) > 8000 or "<" in value or ">" in value:
            _fail("invalid_field_value")
        value = canonicalize_korean(value.strip())
        key, digest = _review_command("edit", actor_id=actor_id, request_id=request_id,
            expected_pointer_version=expected_pointer_version, job_id=job_id, item_id=item_id,
            field=field, value_sha256=_hash(value), generator_id=_generator_id,
            generator_version=_generator_version, route_id=_route_id)
        with repository_transaction(self.session):
            job = lock_job_for_update(self.session, job_id)
            replay = _review_replay(job, key, digest)
            if replay is not None:
                return replay
            candidate, record, values = self._values(job_id, item_id)
            pointer = self._pointer(job_id, item_id, field)
            if pointer is None or pointer.pointer_version != expected_pointer_version:
                _fail("stale_revision")
            if pointer.review_status == "approved":
                _fail("approved_field_preserved")
            prior = self.session.get(ReviewFieldRevisionModel, pointer.current_revision_id)
            mutation = self.reviews.create_candidate_revision(actor_id=actor_id, request_id=request_id,
                job_id=job_id, item_id=item_id, field_name=field, value_sha256=_hash(value),
                generator_id=_generator_id, generator_version=_generator_version, route_id=_route_id,
                expected_pointer_version=expected_pointer_version, previous_revision_sha256=prior.value_sha256)
            revision = self.session.get(ReviewFieldRevisionModel, mutation.revision.revision_id)
            history = list(job.resume_state.get("korean_field_history", []))
            history.append({"field": field, "before": values[field], "after": value,
                            "item_id": item_id, "revision_id": revision.id, "request_sha256": _hash(request_id)})
            # Job-local audit state is never sent as provider or export provenance.
            job.resume_state = {**job.resume_state, "korean_field_history": history}
            update = {"review_status": ReviewStatus.REVIEW_REQUIRED, "validation_status": ValidationStatus.PENDING,
                      "text_review_receipt_sha256": None, "provider_review_evidence": None}
            if field == "definition":
                candidate.definitions_html = value
            else:
                update["example_sentence" if field == "sentence" else "translation_text"] = value
            self.texts.upsert_text_record(record.model_copy(update=update))
            dependent_fields = {"definition": (), "sentence": ("translation", "sentence_audio"), "translation": ()}[field]
            for dependent in dependent_fields:
                sibling = self._pointer(job_id, item_id, dependent)
                if sibling is not None:
                    sibling.review_status = "needs_review"
                    sibling.pointer_version += 1
            output = mutation.model_dump(mode="json")
            output["revision"]["item_id"] = public_korean_item_id(item_id)
            _save_review_result(job, key, digest, output)
        return output

    def review_regenerate(self, *, job_id, item_id, field, actor_id, request_id,
                          expected_pointer_version, provider_factory=None):
        """Regenerate one text field, reserving paid work before contacting its provider."""
        from multilang.services.korean_field_regeneration import regenerate_review_field
        return regenerate_review_field(self, job_id=job_id, item_id=item_id, field=field,
            actor_id=actor_id, request_id=request_id, expected_pointer_version=expected_pointer_version,
            provider_factory=provider_factory)

    def review_regenerate_audio(self, **kwargs):
        from multilang.services.korean_personal_audio import regenerate_from_files
        return regenerate_from_files(self, **kwargs)

    def review_apply_audio_evidence(self, **kwargs):
        from multilang.services.korean_personal_audio import review_from_files
        return review_from_files(self, **kwargs)

    def review_recover_audio(self, **kwargs):
        from multilang.services.korean_personal_audio import recover_from_file
        return recover_from_file(self, **kwargs)

    def review_decide(self, *, job_id, item_id, field, revision_id, expected_pointer_version,
                      actor_id, request_id, decision):
        if field in {"word_audio", "sentence_audio"}:
            if decision != "rejected":
                _fail("audio_review_evidence_required")
            from multilang.services.korean_personal_audio import reject_personal_audio
            return reject_personal_audio(self, job_id=job_id, item_id=item_id, field=field,
                revision_id=revision_id, expected_pointer_version=expected_pointer_version,
                actor_id=actor_id, request_id=request_id)
        self._job(job_id)
        item_id = self._resolve_review_item_id(job_id, item_id)
        if field not in _FIELDS or decision not in ("approved", "rejected"):
            _fail("invalid_review_decision")
        key, digest = _review_command("decide", actor_id=actor_id, request_id=request_id,
            expected_pointer_version=expected_pointer_version, job_id=job_id, item_id=item_id,
            field=field, revision_id=revision_id, decision=decision)
        with repository_transaction(self.session):
            job = lock_job_for_update(self.session, job_id)
            replay = _review_replay(job, key, digest)
            if replay is not None:
                return replay
            pointer = self._pointer(job_id, item_id, field)
            if pointer is None or pointer.pointer_version != expected_pointer_version or pointer.current_revision_id != revision_id:
                _fail("stale_revision")
            if decision == "approved":
                _candidate, record, values = self._values(job_id, item_id)
                if field not in values or record.validation_status is not ValidationStatus.PASSED:
                    _fail("deterministic_validation_required")
                if _hash(values[field] or "") != self.session.get(ReviewFieldRevisionModel, revision_id).value_sha256:
                    _fail("stale_field_value")
            changed = self.session.execute(update(ReviewCurrentPointerModel).where(
                ReviewCurrentPointerModel.id == pointer.id,
                ReviewCurrentPointerModel.pointer_version == expected_pointer_version,
                ReviewCurrentPointerModel.current_revision_id == revision_id,
            ).values(review_status=decision, pointer_version=expected_pointer_version + 1)
              .returning(ReviewCurrentPointerModel.id).execution_options(synchronize_session=False)).scalar_one_or_none()
            if changed is None:
                _fail("stale_revision")
            existing = self.session.scalars(select(ReviewDecisionModel).where(ReviewDecisionModel.revision_id == revision_id)).all()
            self.session.add(ReviewDecisionModel(id=digest[:36], job_id=job_id, item_id=item_id, field_name=field,
                revision_id=revision_id, decision_revision=len(existing) + 1, review_status=decision,
                reviewer_id_sha256=_hash(actor_id), decision_sha256=digest, reason_code="operator_review"))
            if decision == "rejected":
                _candidate, record, _values = self._values(job_id, item_id)
                self.texts.upsert_text_record(record.model_copy(update={"review_status": ReviewStatus.REVIEW_REQUIRED}))
            self.session.expire(pointer)
            output = {"revision_id": revision_id, "pointer_version": expected_pointer_version + 1, "pointer_status": decision}
            _save_review_result(job, key, digest, output)
        return output

    def import_grammar_bundle(self, *, bundle: KoreanGrammarBundle, job_id: str | None = None):
        from multilang.services.korean_foundation_snapshot import (
            resolve_active_korean_foundation_snapshot,
        )
        from multilang.services.korean_grammar import KoreanGrammarBundleBuilder
        validated = KoreanGrammarBundleBuilder(active_snapshot_resolver=resolve_active_korean_foundation_snapshot).build_bundle(
            lexical_bootstrap=bundle.lexical_bootstrap, orientation_entries=bundle.orientation_entries,
            grammar_entries=bundle.grammar_entries)
        if validated != bundle or not (bundle.orientation_entries or bundle.grammar_entries):
            _fail("grammar_bundle_mismatch")
        if job_id is None:
            key = f"ko-grammar:{bundle.bundle_sha256}"
            job = self.jobs.get_job(run_key=key)
            if job is None:
                job = self.jobs.create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="korean-grammar"),
                    run_key=key, source_fingerprint=bundle.bundle_sha256,
                    total_items=len(bundle.lexical_bootstrap) + len(bundle.orientation_entries) + len(bundle.grammar_entries))
        else:
            job = self._job(job_id)
        existing = job.resume_state.get("korean_grammar_bundle")
        payload = bundle.model_dump(mode="json", by_alias=True)
        if existing is not None and existing != payload:
            _fail("grammar_import_conflict")
        with repository_transaction(self.session):
            job.resume_state = {**job.resume_state, "korean_grammar_bundle": payload}
        return {"job_id": job.id, "imported": len(bundle.lexical_bootstrap) + len(bundle.orientation_entries) + len(bundle.grammar_entries), "bundle_sha256": bundle.bundle_sha256,
                "reused": existing is not None}

    def load_grammar_bundle(self, job_id):
        payload = self._job(job_id).resume_state.get("korean_grammar_bundle")
        if payload is None:
            _fail("grammar_bundle_missing")
        return KoreanGrammarBundle.model_validate(payload)

    def bind_provider_policy(self, *, job_id, provider_policy):
        from multilang.domain.korean_provider import KoreanProviderPolicy
        from multilang.repositories.transactions import lock_job_for_update

        self._job(job_id)
        payload = provider_policy.model_dump(mode="json") if isinstance(provider_policy, KoreanProviderPolicy) else provider_policy
        policy = KoreanProviderPolicy.model_validate(payload)
        with repository_transaction(self.session):
            job = lock_job_for_update(self.session, job_id)
            existing = job.korean_provider_policy or {}
            recorded = {value for value in (job.korean_provider_policy_sha256,
                existing.get("provider_policy_sha256")) if value is not None}
            if existing and "routes" in existing:
                recorded.add(KoreanProviderPolicy.model_validate(existing).policy_sha256)
            if recorded and recorded != {policy.policy_sha256}:
                _fail("provider_policy_conflict")
            job.korean_provider_policy_sha256 = policy.policy_sha256
            job.korean_provider_policy = policy.model_dump(mode="json")
        return {"job_id": job_id, "provider_policy_sha256": policy.policy_sha256}

    def import_highlights(self, *, input_file: Path, grounding_service=None):
        """Import local Korean excerpts and lexical identities without provider calls."""
        from multilang.repositories.highlight_import_repository import HighlightImportRepository
        from multilang.repositories.lexical_repository import LexicalRepository
        from multilang.services.generate_job import GenerateJobService
        from multilang.services.ingest_lexical_items import IngestLexicalItemsService

        try:
            valid_input = (not input_file.is_symlink() and input_file.is_file()
                and 0 < input_file.stat().st_size <= 1_000_000)
        except OSError:
            valid_input = False
        if not valid_input:
            _fail("invalid_highlight_input")
        settings = self.settings or Settings(_env_file=None)
        if grounding_service is None:
            _resolver, grounding_service = _local_personal_resolver(settings)
        importer = IngestLexicalItemsService(job_service=GenerateJobService(self.jobs),
            lexical_repo=LexicalRepository(self.session), settings=settings, grounding_service=grounding_service,
            highlight_import_repo=HighlightImportRepository(self.session))
        result = importer.execute(GenerationRequest(language=SupportedLanguage.KO,
            source_type="kindle-highlights", input_file=input_file))
        if result.report.orchestration.diagnostic is not None:
            _fail("highlight_import_conflict")
        job_id = result.report.job_id
        return {"job_id": job_id,
            **{name: getattr(result, name) for name in ("imported_highlights", "extracted_candidates",
                "duplicate_candidates", "rejected_highlights", "blocked_candidates", "planned_cards", "reused_existing_items")},
            "item_ids": [public_korean_item_id(row.item_key) for row in self._candidates(job_id, "highlight")]}

    def import_custom(self, *, input_file: Path, resolver=None, prerequisite_evidence=None):
        from multilang.repositories.lexical_repository import LexicalRepository
        from multilang.services.korean_personal_sources import KoreanPersonalSourceService
        from multilang.services.word_list_parser import (
            ParsedWordListItem,
            parse_korean_ordered_word_list,
        )
        if input_file.is_symlink() or input_file.stat().st_size > 1_000_000:
            _fail("invalid_custom_input")
        parsed = parse_korean_ordered_word_list(input_file)
        if not parsed.rows or len(parsed.rows) > 10_000:
            _fail("invalid_custom_input")
        rows = tuple(row.model_copy(update={"normalized_duplicate_key": "custom:" + _hash(row.normalized_duplicate_key)})
                     for row in parsed.rows)
        digest = canonical_json_sha256([row.model_dump(mode="json") for row in rows])
        job = self.jobs.get_job(run_key=f"ko-custom:{digest}")
        if job is None:
            job = self.jobs.create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
                run_key=f"ko-custom:{digest}", source_fingerprint=digest, total_items=len(rows))
        repository = KoreanPersonalSourceRepository(self.session)
        inventory = repository.store_rows(job_id=job.id, source_type="word-list", parser_version="korean-ordered-v1", rows=rows)
        if all(row.latest_decision is not None for row in inventory.rows):
            return {"job_id": job.id, "imported": len(rows), "needs_review": sum(
                row.latest_decision.decision_state == "needs_review" for row in inventory.rows), "reused": True}
        grounding = None
        if resolver is None:
            resolver, grounding = _local_personal_resolver(self.settings or Settings())
        service = KoreanPersonalSourceService(resolver=resolver)
        outcomes = service.resolve_rows(rows)
        proposals = {}
        for outcome, stored in zip(outcomes, inventory.rows, strict=True):
            if stored.latest_decision is not None:
                continue
            evidence = (prerequisite_evidence or {}).get(str(outcome.row.input_position))
            state = "duplicate" if outcome.resolution_status == "duplicate" else "needs_review"
            reason = outcome.review_reason_code or "prerequisite_analysis_required"
            if evidence is not None and outcome.resolution_status == "resolved":
                proposal = service.assess_prerequisites(outcome,
                    observed_concept_ids=evidence["observed_concept_ids"],
                    prerequisite_concept_ids=evidence["prerequisite_concept_ids"],
                    known_concept_ids=evidence["known_concept_ids"])
                proposals[stored.row_id] = proposal.model_dump(mode="json")
                state = "accepted" if proposal.status == "ready" else "needs_review"
                reason = proposal.evidence.reason_codes[0]
            identity = outcome.lexical_identity
            repository.append_decision(row_id=stored.row_id, expected_latest_revision=0,
                decision_state=state, decision_reason_code=reason,
                korean_identity_sha256=canonical_json_sha256(identity.model_dump(mode="json")) if identity else None,
                resolved_lemma=identity.lemma if identity else None, resolved_pos=identity.part_of_speech if identity else None,
                resolved_sense_id=identity.sense_id if identity else None)
            if identity is not None and grounding is not None:
                candidate = grounding.ground_word_list_item(language=SupportedLanguage.KO, item=ParsedWordListItem(
                    line_number=outcome.row.line_number, submitted_form=outcome.row.submitted_form,
                    display_form=outcome.row.display_form, item_key=stored.item_key))
                LexicalRepository(self.session).upsert_candidate(job_id=job.id, run_key=job.run_key,
                    item_key=stored.item_key, source_type="word-list", normalized_source=stored.item_key, candidate=candidate)
        with repository_transaction(self.session):
            job.resume_state = {**job.resume_state, "korean_prerequisite_proposals": proposals}
        inventory = repository.list_inventory(job.id, "word-list")
        return {"job_id": job.id, "imported": len(rows), "needs_review": sum(
            row.latest_decision.decision_state == "needs_review" for row in inventory.rows), "reused": False,
            "proposals": proposals}

    def decide_prerequisites(self, *, job_id, row_id, command):
        from multilang.domain.personal_sources import (
            PersonalSourceDecisionCommand,
            PersonalSourcePrerequisiteProposal,
        )
        from multilang.services.korean_personal_sources import KoreanPersonalSourceService
        job = self._job(job_id)
        payload = job.resume_state.get("korean_prerequisite_proposals", {}).get(row_id)
        if payload is None:
            _fail("prerequisite_proposal_missing")
        proposal = PersonalSourcePrerequisiteProposal.model_validate(payload)
        decision = KoreanPersonalSourceService(resolver=None).record_prerequisite_decision(
            proposal, PersonalSourceDecisionCommand.model_validate(command))
        if decision.decision not in ("bridge", "defer"):
            _fail("invalid_prerequisite_decision")
        repository = KoreanPersonalSourceRepository(self.session)
        row = next((row for row in repository.list_inventory(job_id, "word-list").rows if row.row_id == row_id), None)
        if row is None or row.latest_decision is None:
            _fail("unknown_personal_row")
        latest = row.latest_decision
        result = repository.append_decision(row_id=row_id, expected_latest_revision=latest.decision_revision,
            decision_state=decision.decision, decision_reason_code=decision.reason_code,
            prerequisite_ids=decision.reviewed_prerequisite_ids,
            korean_identity_sha256=latest.korean_identity_sha256,
            resolved_lemma=latest.resolved_lemma, resolved_pos=latest.resolved_pos, resolved_sense_id=latest.resolved_sense_id)
        return {"row_id": row_id, "decision": result.decision_state, "revision": result.decision_revision}

    def review_validate(self, *, job_id, item_id, validator=None):
        self._job(job_id)
        item_id = self._resolve_review_item_id(job_id, item_id)
        from multilang.services.generate_text_items import GenerateTextItemsService
        from multilang.services.korean_morphology import KiwiKoreanMorphologyService
        from multilang.services.text_validation import TextValidationService
        candidate, record, values = self._values(job_id, item_id)
        input_hash = canonical_json_sha256({"values": values, "identity": candidate.korean_identity})
        lexical = GenerateTextItemsService._to_candidate(self, candidate)
        if lexical.korean_identity is None:
            _fail("korean_identity_required")
        validator = validator or TextValidationService(korean_matcher=KiwiKoreanMorphologyService())
        from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
        result = validator.validate(
            sentence=GeneratedSentence(text=record.example_sentence or "", target_language="ko", intended_sense=lexical.korean_identity.sense_id,
                uncertainty_notes=[], provenance=record.sentence_provenance),
            translation=GeneratedTranslation(text=record.translation_text or "", target_language="pt", provenance=record.translation_provenance),
            display_form=lexical.display_form, lemma=lexical.lemma, definitions_html=lexical.definitions_html,
            require_translation=True, korean_identity=lexical.korean_identity)
        with repository_transaction(self.session):
            lock_job_for_update(self.session, job_id)
            candidate, record, values = self._values(job_id, item_id)
            if canonical_json_sha256({"values": values, "identity": candidate.korean_identity}) != input_hash:
                _fail("stale_revision")
            saved = self.texts.upsert_text_record(record.model_copy(update={"validation_status": result.validation_status,
                "validation_flags": result.validation_flags, "confidence_score": result.confidence_score,
                "confidence_label": result.confidence_label, "review_status": ReviewStatus.REVIEW_REQUIRED}))
        return {"job_id": job_id, "item_id": public_korean_item_id(item_id), "validation_status": saved.validation_status.value,
                "flags": [flag.code.value for flag in saved.validation_flags]}

    def export_grammar(self, *, job_id, media_dir: Path, output_dir: Path, export_format: str,
                       bootstrap_cards_file: Path | None = None):
        import json
        import shutil

        from multilang.domain.exporting import ExportArtifactFormat
        from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
        from multilang.domain.source_profiles import get_source_profile
        from multilang.services.export_anki_package import export_anki_package
        from multilang.services.exporting.tabular import write_export_tabular_bundle
        from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows
        if export_format not in {"apkg", "csv", "tsv"} or media_dir.is_symlink() or not media_dir.is_dir():
            _fail("invalid_export_input")
        files = list(media_dir.iterdir())
        if len(files) > 10_000:
            _fail("media_limit_exceeded")
        media = {}
        total = 0
        for path in files:
            if path.is_symlink() or not path.is_file():
                _fail("invalid_media_file")
            size = path.stat().st_size
            total += size
            if size > 20_000_000 or total > 500_000_000:
                _fail("media_limit_exceeded")
            media[sha256(path.read_bytes()).hexdigest()] = path
        bootstrap_cards = ()
        if bootstrap_cards_file is not None:
            if (bootstrap_cards_file.is_symlink() or not bootstrap_cards_file.is_file()
                    or bootstrap_cards_file.stat().st_size > 8_000_000):
                _fail("invalid_bootstrap_cards")
            payload = json.loads(bootstrap_cards_file.read_text(encoding="utf-8"))
            if not isinstance(payload, list) or len(payload) > 256:
                _fail("invalid_bootstrap_cards")
            bootstrap_cards = tuple(KoreanGrammarBootstrapCard.model_validate(card) for card in payload)
        prepared = assemble_korean_grammar_export_rows(bundle=self.load_grammar_bundle(job_id), job_id=job_id,
            media_paths=media, bootstrap_cards=bootstrap_cards)
        if output_dir.exists() and any(output_dir.iterdir()):
            _fail("export_directory_not_empty")
        output_dir.mkdir(parents=True, exist_ok=True)
        if export_format == "apkg":
            result = export_anki_package(rows=prepared.rows, media_index=prepared.media_index,
                output_path=output_dir / "korean-grammar.apkg", deck_name="Korean::Particles & Endings")
        else:
            result = write_export_tabular_bundle(rows=prepared.rows, export_format=ExportArtifactFormat(export_format),
                output_dir=output_dir, deck_name="Korean::Particles & Endings",
                note_type_name=get_source_profile("korean-grammar").note_type_name)
            media_output = output_dir / "collection.media"
            media_output.mkdir()
            for filename, path in prepared.media_index.items():
                basename = filename.removeprefix("[sound:").removesuffix("]")
                if Path(basename).name != basename:
                    _fail("invalid_media_name")
                shutil.copyfile(path, media_output / basename)
        from multilang.services.korean_grammar_delivery import record_grammar_delivery
        record_grammar_delivery(self.session, self._job(job_id), prepared, result.output_path, bootstrap_cards=bootstrap_cards)
        return {"job_id": job_id, "output_path": str(result.output_path), "card_count": result.card_count,
                "bundle_sha256": prepared.bundle_sha256}


def _local_personal_resolver(settings):
    from multilang.domain.personal_sources import (
        KoreanPersonalSourceIdentitySelection,
        KoreanPersonalSourceResolutionFailure,
    )
    from multilang.services.korean_morphology import KiwiKoreanMorphologyService
    from multilang.services.lexical_grounding import LexicalGroundingService
    from multilang.services.lexical_lookup import LexicalLookup
    lookup = LexicalLookup(data_dir=settings.lexicon_data_dir)
    grounding = LexicalGroundingService(lookup=lookup, korean_morphology=KiwiKoreanMorphologyService())

    class Resolver:
        def resolve(self, submitted_form):
            result = grounding.resolve_korean_source_identity(surface_form=submitted_form, submitted_form=submitted_form)
            if result.identity is None:
                return KoreanPersonalSourceResolutionFailure(status="unavailable", reason_code="resolver_error")
            identity = result.identity
            records = tuple(lookup.iter_candidates(language_code="ko"))
            matches = [record for record in records if record.lemma == identity.lemma
                       and record.sense_id == identity.sense_id and (record.register or "standard") == identity.register]
            if len(matches) != 1:
                return KoreanPersonalSourceResolutionFailure(status="ambiguous", reason_code="non_consensus")
            digest = canonical_json_sha256(matches[0].model_dump(mode="json"))
            return KoreanPersonalSourceIdentitySelection(language="ko", lexical_identity=identity,
                analyzer_fingerprint=identity.analyzer_fingerprint, top_two_consensus=True, source_consensus=True,
                source_id="local-lexical-cache", source_version=digest[:32], source_entry_hash=digest,
                source_selector_hash=canonical_json_sha256({"selector": "kiwi-source-consensus-v1",
                    "inventory": [record.model_dump(mode="json") for record in records]}))
    return Resolver(), grounding


def build_korean_learning_runtime(settings: Settings | None = None):
    settings = settings or Settings()
    engine = create_engine(settings.database_url)
    ensure_database_schema(engine, settings.database_url)
    runtime = KoreanLearningRuntime(Session(engine), settings=settings)
    runtime.owned_session = True
    return runtime
