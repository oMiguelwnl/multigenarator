"""Compile signed source reviews into immutable, non-production native staging.

This boundary assigns no senses, generates no forms and makes no ranking or
qualification claims. Receipt verification is supplied by the operator's store.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Literal, Protocol

from pydantic import Field, computed_field

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, LanguageProfile, NativeContract, Sha256
from multilang.domain.lexical_identity import (
    ImportantFormPolicy,
    ImportantFormSelection,
    LexicalIdentity,
    MorphologicalAnalysis,
    SurfaceForm,
    UnitDecimal,
    canonical_sha256,
    normalize_identity_text,
)
from multilang.services.contextual_morphology import (
    ContextualToken,
    ReviewedSenseBinding,
    sentence_hash,
)
from multilang.services.vocabulary_sources import CorpusSentence, LexicalSenseCandidate

_MAX_BYTES = 128 * 1024**2
_MAX_RECORDS = 100_000
_FEATURE_NAMES = frozenset(
    "tense mood person number case gender aspect register voice degree animacy definiteness polarity possessive".split()
)
Decision = Literal["accepted", "pending", "rejected", "ambiguous"]


class EvidenceVerifier(Protocol):
    def verify(self, receipt_id: str, payload: dict, *, purpose: str) -> bool: ...


class SenseDecision(NativeContract):
    candidate_id: Identifier
    candidate_sha256: Sha256
    source_record_sha256: Sha256
    lemma: str = Field(min_length=1, max_length=512)
    pos: Identifier
    decision: Decision = "pending"
    stable_sense_id: Identifier | None = None
    reviewer: Identifier | None = None
    receipt_id: Sha256 | None = None


class ObservedFormDecision(NativeContract):
    decision_id: Identifier
    candidate_id: Identifier
    decision: Decision = "pending"
    reviewer: Identifier | None = None
    receipt_id: Sha256 | None = None
    context_source: Literal["dictionary_example", "corpus"] = "dictionary_example"
    context_source_sha256: Sha256 | None = None
    context_source_id: Identifier | None = None
    context_candidate_id: Identifier | None = None
    document_id: Identifier | None = None
    sentence_id: Identifier | None = None
    context: str | None = Field(default=None, max_length=2000)
    token: ContextualToken | None = None
    binding: ReviewedSenseBinding | None = None
    analysis: MorphologicalAnalysis | None = None
    important: bool = False
    evidence_values: dict[str, UnitDecimal] = Field(default_factory=dict)
    prerequisite_depth: int = Field(default=1, ge=1, le=100)


class FormAggregationDecision(NativeContract):
    aggregation_id: Identifier
    decision: Decision = "pending"
    reviewer: Identifier | None = None
    receipt_id: Sha256 | None = None
    observation_ids: tuple[Identifier, ...] = Field(min_length=2, max_length=_MAX_RECORDS)
    representative_observation_id: Identifier
    representative_context: str = Field(min_length=1, max_length=2000)
    lexical_identity_id: Identifier
    text: str = Field(min_length=1, max_length=512)
    morphological_analysis_id: Identifier
    model_fingerprint: Sha256
    attestation: int = Field(ge=2, le=_MAX_RECORDS, strict=True)
    important: bool = False
    evidence_values: dict[str, UnitDecimal] = Field(default_factory=dict)


class CompiledFormObservation(NativeContract):
    observation_id: Identifier
    form: SurfaceForm


class VocabularyReview(NativeContract):
    schema_version: Literal[1] = 1
    preparation_sha256: Sha256
    language: SupportedLanguage
    source_id: Identifier
    source_version: Identifier
    senses: tuple[SenseDecision, ...] = Field(default=(), max_length=_MAX_RECORDS)
    forms: tuple[ObservedFormDecision, ...] = Field(default=(), max_length=_MAX_RECORDS)
    aggregations: tuple[FormAggregationDecision, ...] = Field(default=(), max_length=_MAX_RECORDS)
    important_form_policy: ImportantFormPolicy | None = None
    policy_reviewer: Identifier | None = None
    use_corpus_for_ranking: bool = False


class ReviewQuarantine(NativeContract):
    kind: Literal["candidate", "form", "aggregation"]
    record_id: Identifier
    reason: Identifier
    candidate_sha256: Sha256 | None = None


class ReviewSourceEvidence(NativeContract):
    kind: Literal["identity", "form", "aggregation"]
    object_id: Identifier
    record_id: Identifier
    source_id: Identifier
    source_sha256: Sha256
    candidate_sha256: Sha256
    reviewer: Identifier
    receipt_id: Sha256


class CompiledVocabularyBundle(NativeContract):
    schema_version: Literal[1] = 1
    language: SupportedLanguage
    profile_sha256: Sha256
    preparation_manifest: dict = Field(max_length=64)
    source_artifacts: dict[str, Annotated[str, Field(max_length=_MAX_BYTES)]] = Field(max_length=2)
    decisions_sha256: Sha256
    review: VocabularyReview
    candidates: tuple[LexicalSenseCandidate, ...] = Field(max_length=_MAX_RECORDS)
    corpus: tuple[CorpusSentence, ...] = Field(default=(), max_length=_MAX_RECORDS)
    identities: tuple[LexicalIdentity, ...] = Field(max_length=_MAX_RECORDS)
    forms: tuple[SurfaceForm, ...] = Field(max_length=_MAX_RECORDS)
    observations: tuple[CompiledFormObservation, ...] = Field(default=(), max_length=_MAX_RECORDS)
    important_forms: tuple[ImportantFormSelection, ...] = Field(default=(), max_length=_MAX_RECORDS)
    source_evidence: tuple[ReviewSourceEvidence, ...] = Field(max_length=3 * _MAX_RECORDS)
    quarantine: tuple[ReviewQuarantine, ...] = Field(max_length=4 * _MAX_RECORDS)
    ranking_inputs: dict = Field(default_factory=dict, max_length=16)
    workload: dict[str, int] = Field(max_length=16)
    production_eligible: Literal[False] = False

    @computed_field
    @property
    def bundle_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def _profile_hash(profile: LanguageProfile) -> str:
    return canonical_sha256(profile.model_dump(mode="json"))


def _review_context(review: VocabularyReview, profile: LanguageProfile) -> dict:
    return {
        "schema_version": 1,
        "preparation_sha256": review.preparation_sha256,
        "language": review.language.value,
        "source_id": review.source_id,
        "source_version": review.source_version,
        "profile_sha256": _profile_hash(profile),
        "use_corpus_for_ranking": review.use_corpus_for_ranking,
    }


def _decision_payload(
    review: VocabularyReview,
    decision: SenseDecision | ObservedFormDecision | FormAggregationDecision,
    profile: LanguageProfile,
    observation_index=None,
) -> dict:
    """Exact payload for operator signing; receipt IDs are never self-signed."""
    payload = {
        **_review_context(review, profile),
        "kind": (
            "sense"
            if isinstance(decision, SenseDecision)
            else "form-aggregation"
            if isinstance(decision, FormAggregationDecision)
            else "form"
        ),
        "important_form_policy_sha256": review.important_form_policy.policy_sha256
        if isinstance(decision, (ObservedFormDecision, FormAggregationDecision))
        and decision.important
        and review.important_form_policy
        else None,
        "decision": decision.model_dump(mode="json", exclude={"receipt_id"}),
    }
    if isinstance(decision, FormAggregationDecision):
        # User-facing observation IDs are labels, not immutable hashes. Bind
        # every referenced payload as well as separately verifying its receipt.
        wanted = set(decision.observation_ids)
        selected = (
            (item for key in wanted for item in observation_index.get(key, ()))
            if observation_index is not None
            else (item for item in review.forms if item.decision_id in wanted)
        )
        payload["observations"] = [
            item.model_dump(mode="json", exclude={"receipt_id"})
            for item in sorted(selected, key=lambda form: form.decision_id)
        ]
    return payload


def decision_payload(
    review: VocabularyReview,
    decision: SenseDecision | ObservedFormDecision | FormAggregationDecision,
    profile: LanguageProfile,
) -> dict:
    """Exact operator-signing payload, including aggregate member content."""
    return _decision_payload(review, decision, profile)


def policy_payload(review: VocabularyReview, profile: LanguageProfile) -> dict:
    if review.important_form_policy is None:
        raise ValueError("important-form policy is absent")
    return {
        **_review_context(review, profile),
        "reviewer": review.policy_reviewer,
        "policy": review.important_form_policy.model_dump(
            mode="json", exclude={"approval_sha256"}, exclude_computed_fields=True
        ),
    }


def _verified(verifier: EvidenceVerifier, receipt: str | None, payload: dict, purpose: str) -> bool:
    if not receipt:
        return False
    try:
        return verifier.verify(receipt, payload, purpose=purpose) is True
    except Exception:
        return False  # Missing evidence or store failure cannot authorize acceptance.


def _plain_path(path: Path) -> Path:
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("review artifacts cannot traverse symlinks")
    return path


def _read_bytes(path: Path, expected: str | None = None, *, limit: int = _MAX_BYTES) -> bytes:
    path = _plain_path(path)
    if expected is not None and not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("artifact checksum is malformed")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError("review artifact is not a bounded regular file")
        data = handle.read(limit + 1)
        after = os.fstat(handle.fileno())
    if len(data) > limit or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ValueError("review artifact changed or exceeded byte limit")
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("artifact checksum mismatch")
    return data


def _manifest_check(manifest: dict) -> None:
    if (
        manifest.get("schema_version") != 1
        or manifest.get("production_eligible") is not False
        or manifest.get("status") != "candidate_only"
    ):
        raise ValueError("unsupported preparation manifest")
    expected = manifest.get("preparation_sha256")
    if expected != canonical_sha256(
        {k: v for k, v in manifest.items() if k != "preparation_sha256"}
    ):
        raise ValueError("preparation manifest checksum mismatch")
    artifacts = manifest.get("files")
    if (
        not isinstance(artifacts, dict)
        or not 1 <= len(artifacts) <= 32
        or "candidates.jsonl" not in artifacts
    ):
        raise ValueError("preparation artifact manifest is incomplete")
    for name, digest in artifacts.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.jsonl?", name)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError("invalid preparation artifact path or checksum")


def _jsonl(data: bytes, cls):
    rows = data.splitlines()
    if len(rows) > _MAX_RECORDS or any(len(row) > 2 * 1024**2 for row in rows):
        raise ValueError("review compilation record limit exceeded")
    return tuple(cls.model_validate_json(row) for row in rows if row.strip())


def _load_preparation(path: Path):
    root = _plain_path(path)
    manifest = json.loads(_read_bytes(root / "manifest.json", limit=1024**2))
    if not isinstance(manifest, dict):
        raise ValueError("preparation manifest must be an object")
    _manifest_check(manifest)
    data, total = {}, 0
    for name, digest in manifest["files"].items():
        blob = _read_bytes(root / name, digest)
        total += len(blob)
        if total > _MAX_BYTES:
            raise ValueError("preparation aggregate byte limit exceeded")
        if name in {"candidates.jsonl", "reference-corpus.jsonl"}:
            data[name] = blob
    candidates = _jsonl(data["candidates.jsonl"], LexicalSenseCandidate)
    corpus = _jsonl(data.get("reference-corpus.jsonl", b""), CorpusSentence)
    return manifest, candidates, corpus, {name: blob.decode("utf-8") for name, blob in data.items()}


def _compile(
    manifest, candidates, corpus, review, profile, verifier, decisions_sha256, source_artifacts
):
    _manifest_check(manifest)
    required = {"candidates.jsonl"} | (
        {"reference-corpus.jsonl"} if "reference-corpus.jsonl" in manifest["files"] else set()
    )
    if set(source_artifacts) != required:
        raise ValueError("compiled source artifacts are incomplete")
    total = 0
    for name, text in source_artifacts.items():
        data = text.encode("utf-8")
        total += len(data)
        if total > _MAX_BYTES or hashlib.sha256(data).hexdigest() != manifest["files"][name]:
            raise ValueError("compiled source artifact checksum mismatch")
    source_candidates = _jsonl(
        source_artifacts["candidates.jsonl"].encode("utf-8"), LexicalSenseCandidate
    )
    source_corpus = _jsonl(
        source_artifacts.get("reference-corpus.jsonl", "").encode("utf-8"), CorpusSentence
    )
    if tuple(sorted(source_candidates, key=lambda c: c.candidate_id)) != tuple(
        sorted(candidates, key=lambda c: c.candidate_id)
    ) or tuple(sorted(source_corpus, key=lambda s: (s.document_id, s.sentence_id))) != tuple(
        sorted(corpus, key=lambda s: (s.document_id, s.sentence_id))
    ):
        raise ValueError("compiled source projection differs from verified source artifacts")
    if (
        profile.family != "modern"
        or profile.language != review.language
        or manifest["language"] != review.language.value
        or manifest["preparation_sha256"] != review.preparation_sha256
    ):
        raise ValueError("review preparation/profile/language mismatch")
    if (
        profile.normalization_version != "nfc-preserve-1"
        or not profile.analyzer_id
        or not profile.analyzer_version
        or review.source_id not in profile.source_ids
    ):
        raise ValueError("review needs explicit profile source and analyzer metadata")
    if review.use_corpus_for_ranking and (manifest["corpus"]["split"] != "train" or not corpus):
        raise ValueError("held-out/test/reference corpus cannot be used as ranking input")
    if len(candidates) > _MAX_RECORDS or len(corpus) > _MAX_RECORDS:
        raise ValueError("review compilation record limit exceeded")
    by_id = {c.candidate_id: c for c in candidates}
    if len(by_id) != len(candidates) or any(c.language != profile.language for c in candidates):
        raise ValueError("duplicate candidate or source language mismatch")
    if any(
        s.language != profile.language or s.source_sha256 != manifest["corpus"]["sha256"]
        for s in corpus
    ):
        raise ValueError("corpus provenance mismatch")
    if len({(s.document_id, s.sentence_id) for s in corpus}) != len(corpus):
        raise ValueError("ambiguous corpus sentence identifiers")
    decisions = defaultdict(list)
    for decision in review.senses:
        decisions[decision.candidate_id].append(decision)
    identities, accepted, evidence, quarantine = {}, {}, [], []

    def reject(kind, record_id, reason, candidate=None):
        quarantine.append(
            ReviewQuarantine(
                kind=kind,
                record_id=record_id,
                reason=reason,
                candidate_sha256=canonical_sha256(candidate.model_dump(mode="json"))
                if candidate
                else None,
            )
        )

    for key in sorted(by_id.keys() | decisions.keys()):
        candidate = by_id.get(key)
        choices = decisions.get(key, ())
        if candidate is None:
            reject("candidate", key, "unknown_candidate")
            continue
        if len(choices) != 1:
            reject("candidate", key, "ambiguous_review" if choices else "pending_review", candidate)
            continue
        decision = choices[0]
        if decision.decision != "accepted":
            reject("candidate", key, decision.decision + "_review", candidate)
            continue
        candidate_hash = canonical_sha256(candidate.model_dump(mode="json"))
        if (
            decision.candidate_sha256 != candidate_hash
            or decision.source_record_sha256 != candidate.source_record_sha256
            or decision.lemma != candidate.lemma
            or decision.pos != candidate.pos
            or candidate.kind != "lexeme"
            or not decision.stable_sense_id
            or not decision.reviewer
        ):
            reject("candidate", key, "invalid_source_decision", candidate)
            continue
        if not _verified(
            verifier,
            decision.receipt_id,
            decision_payload(review, decision, profile),
            "vocabulary-sense",
        ):
            reject("candidate", key, "unverified_review", candidate)
            continue
        try:
            if normalize_identity_text(candidate.lemma) != candidate.lemma:
                raise ValueError("review may not rewrite source lemma")
            identity = LexicalIdentity(
                language=profile.language,
                normalized_lemma=candidate.lemma,
                part_of_speech=candidate.pos,
                sense_id=decision.stable_sense_id,
                profile_version=profile.version,
                normalizer_version=profile.normalization_version,
                analyzer_version=profile.analyzer_version,
                source_id=review.source_id,
                source_version=review.source_version,
                source_sha256=candidate.source_record_sha256,
            )
        except ValueError:
            reject("candidate", key, "unresolved_identity", candidate)
            continue
        identities.setdefault(identity.lexical_identity_id, identity)
        accepted[key] = identity
        evidence.append(
            ReviewSourceEvidence(
                kind="identity",
                object_id=identity.lexical_identity_id,
                record_id=key,
                source_id=review.source_id,
                source_sha256=candidate.source_record_sha256,
                candidate_sha256=candidate_hash,
                reviewer=decision.reviewer,
                receipt_id=decision.receipt_id,
            )
        )

    policy = review.important_form_policy
    policy_verified = (
        policy is not None
        and review.policy_reviewer is not None
        and _verified(
            verifier,
            policy.approval_sha256,
            policy_payload(review, profile),
            "vocabulary-form-policy",
        )
    )
    forms, important, form_evidence = {}, {}, defaultdict(list)
    observations = {}
    form_decisions = defaultdict(list)
    for decision in review.forms:
        form_decisions[decision.decision_id].append(decision)
    conflicted_forms = set()
    for key in sorted(form_decisions):
        choices = form_decisions[key]
        if len(choices) != 1:
            reject("form", key, "ambiguous_review")
            continue
        decision = choices[0]
        if decision.decision != "accepted":
            reject("form", key, decision.decision + "_review")
            continue
        identity = accepted.get(decision.candidate_id)
        candidate = by_id.get(decision.candidate_id)
        try:
            if identity is None or candidate is None:
                raise ValueError("unaccepted_parent")
            form = _compile_form(
                decision, identity, candidate, by_id, manifest, corpus, review, profile, verifier
            )
            observations[key] = form
            selections = ()
            if decision.important:
                if not policy_verified:
                    reject("form", key, "unverified_important_form_policy", candidate)
                else:
                    selections = policy.select((form,))
                    if len(selections) != 1:
                        reject("form", key, "important_form_policy_not_satisfied", candidate)
            form_id = form.surface_form_id
            if form_id in forms and (
                forms[form_id] != form or (form_id in important) != bool(selections)
            ):
                conflicted_forms.add(form_id)
            forms.setdefault(form_id, form)
            if selections:
                important[form_id] = selections[0]
            form_evidence[form_id].append(
                ReviewSourceEvidence(
                    kind="form",
                    object_id=form_id,
                    record_id=key,
                    source_id=form.source_id,
                    source_sha256=form.source_sha256,
                    candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
                    reviewer=decision.reviewer,
                    receipt_id=decision.receipt_id,
                )
            )
        except (ValueError, TypeError, AttributeError):
            reject("form", key, "invalid_or_unverified_form", candidate)

    aggregation_decisions = defaultdict(list)
    for aggregation in review.aggregations:
        aggregation_decisions[aggregation.aggregation_id].append(aggregation)
    aggregate_groups = defaultdict(list)
    for key in sorted(aggregation_decisions):
        choices = aggregation_decisions[key]
        if len(choices) != 1:
            reject("aggregation", key, "ambiguous_review")
            continue
        aggregation = choices[0]
        if aggregation.decision != "accepted":
            reject("aggregation", key, aggregation.decision + "_review")
            continue
        try:
            form = _compile_aggregation(
                aggregation, observations, form_decisions, review, profile, verifier
            )
        except (ValueError, TypeError, AttributeError):
            reject("aggregation", key, "invalid_or_unverified_aggregation")
            continue
        aggregate_groups[form.surface_form_id].append((aggregation, form))
    accepted_aggregates = 0
    for form_id, groups in sorted(aggregate_groups.items()):
        if len(groups) != 1:
            for aggregation, _ in groups:
                reject("aggregation", aggregation.aggregation_id, "ambiguous_aggregation")
            continue
        aggregation, form = groups[0]
        accepted_aggregates += 1
        forms[form_id] = form
        conflicted_forms.discard(form_id)
        important.pop(form_id, None)
        if aggregation.important:
            if not policy_verified:
                reject(
                    "aggregation", aggregation.aggregation_id, "unverified_important_form_policy"
                )
            else:
                selections = policy.select((form,))
                if selections:
                    important[form_id] = selections[0]
                else:
                    reject(
                        "aggregation",
                        aggregation.aggregation_id,
                        "important_form_policy_not_satisfied",
                    )
        representative = form_decisions[aggregation.representative_observation_id][0]
        candidate = by_id[representative.candidate_id]
        evidence.append(
            ReviewSourceEvidence(
                kind="aggregation",
                object_id=form_id,
                record_id=aggregation.aggregation_id,
                source_id=form.source_id,
                source_sha256=form.source_sha256,
                candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
                reviewer=aggregation.reviewer,
                receipt_id=aggregation.receipt_id,
            )
        )
    for key in conflicted_forms:
        forms.pop(key, None)
        important.pop(key, None)
        for item in form_evidence.get(key, ()):
            reject("form", item.record_id, "conflicting_form_evidence")
    for items in form_evidence.values():
        evidence.extend(items)
    ranking_inputs = {}
    if review.use_corpus_for_ranking:
        ranking_inputs = {
            "source_sha256": manifest["corpus"]["sha256"],
            "split": "train",
            "source_annotation_only": True,
            "canonical_ranking_input": False,
            "requires_sense_bound_observations": True,
        }
    return CompiledVocabularyBundle(
        language=profile.language,
        profile_sha256=_profile_hash(profile),
        preparation_manifest=manifest,
        source_artifacts=source_artifacts,
        decisions_sha256=decisions_sha256,
        review=review,
        candidates=tuple(sorted(candidates, key=lambda c: c.candidate_id)),
        corpus=tuple(sorted(corpus, key=lambda s: (s.document_id, s.sentence_id))),
        identities=tuple(identities[key] for key in sorted(identities)),
        forms=tuple(forms[key] for key in sorted(forms)),
        observations=tuple(
            CompiledFormObservation(observation_id=key, form=observations[key])
            for key in sorted(observations)
        ),
        important_forms=tuple(important[key] for key in sorted(important)),
        source_evidence=tuple(sorted(evidence, key=lambda e: (e.kind, e.record_id, e.object_id))),
        quarantine=tuple(sorted(quarantine, key=lambda q: (q.kind, q.record_id, q.reason))),
        ranking_inputs=ranking_inputs,
        workload={
            "reviewed_identities": len(identities),
            "observed_forms": len(forms),
            "authenticated_observations": len(observations),
            "reviewed_aggregates": accepted_aggregates,
            "explicit_important_form_cards": len(important),
            "quarantined_records": len(quarantine),
            "headword_target": 3000,
            "provider_calls_executed": 0,
            "production_cards_approved": 0,
        },
    )


def _compile_aggregation(aggregation, observations, form_decisions, review, profile, verifier):
    ids = aggregation.observation_ids
    if (
        not aggregation.reviewer
        or len(set(ids)) != len(ids)
        or aggregation.representative_observation_id not in ids
        or any(key not in observations for key in ids)
    ):
        raise ValueError("invalid_aggregation_members")
    if not _verified(
        verifier,
        aggregation.receipt_id,
        _decision_payload(review, aggregation, profile, form_decisions),
        "vocabulary-form-aggregation",
    ):
        raise ValueError("unverified_aggregation")
    representative = observations[aggregation.representative_observation_id]
    if representative.context != aggregation.representative_context:
        raise ValueError("aggregation_representative_context_mismatch")
    distinct = set()
    for key in ids:
        form = observations[key]
        decision = form_decisions[key][0]
        if (
            form.lexical_identity_id != aggregation.lexical_identity_id
            or form.text != aggregation.text
            or form.analysis.morphological_analysis_id != aggregation.morphological_analysis_id
            or form.analysis.analyzer_id != representative.analysis.analyzer_id
            or form.analysis.analyzer_version != representative.analysis.analyzer_version
            or decision.token.model_fingerprint != aggregation.model_fingerprint
        ):
            raise ValueError("aggregation_identity_analysis_or_model_mismatch")
        distinct.add(
            (
                decision.context_source_sha256,
                (decision.document_id, decision.sentence_id)
                if decision.context_source == "corpus"
                else (decision.context_candidate_id or decision.candidate_id,),
                decision.token.sentence_sha256,
                decision.token.start,
                decision.token.end,
                form.analysis.morphological_analysis_id,
            )
        )
    if aggregation.attestation != len(distinct) or len(distinct) != len(ids):
        raise ValueError("aggregation_attestation_drift_or_duplicate_observation")
    return representative.model_copy(
        update={
            "attestation": aggregation.attestation,
            "evidence_values": aggregation.evidence_values,
        }
    )


def _compile_form(
    decision, identity, candidate, by_id, manifest, corpus, review, profile, verifier
):
    token, binding, analysis = decision.token, decision.binding, decision.analysis
    if not all((token, binding, analysis, decision.context, decision.reviewer)):
        raise ValueError("incomplete_form_evidence")
    if not _verified(
        verifier,
        decision.receipt_id,
        decision_payload(review, decision, profile),
        "vocabulary-form",
    ):
        raise ValueError("unverified_form_review")
    if not _verified(
        verifier,
        binding.review_receipt_sha256,
        binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
        "contextual-sense-binding",
    ):
        raise ValueError("unverified_sense_binding")
    if (
        token.lemma != identity.normalized_lemma
        or token.pos != identity.part_of_speech
        or token.sentence_sha256 != sentence_hash(decision.context)
        or decision.context[token.start : token.end] != token.text
        or not 0 <= token.start < token.end <= len(decision.context)
        or normalize_identity_text(token.text) != token.text
        or token.model_fingerprint == "0" * 64
    ):
        raise ValueError("form_token_mismatch")
    if (
        binding.language != profile.language.value
        or binding.sentence_sha256 != token.sentence_sha256
        or binding.start != token.start
        or binding.end != token.end
        or binding.token_analysis_id != token.analysis_id
        or binding.lexical_identity_id != identity.lexical_identity_id
        or binding.sense_id != identity.sense_id
        or binding.morphological_analysis_id != analysis.morphological_analysis_id
        or binding.source_sha256 != decision.context_source_sha256
    ):
        raise ValueError("form_binding_mismatch")
    if (
        analysis.lexical_identity_id != identity.lexical_identity_id
        or analysis.analyzer_id != profile.analyzer_id
        or analysis.analyzer_version != profile.analyzer_version
        or analysis.evidence_sha256 != token.analysis_id
    ):
        raise ValueError("form_analysis_mismatch")
    # Supported UD features must be retained exactly. Native tag projections may
    # add signed mapped features, but cannot contradict directly analyzed facts.
    expected = {k.lower(): v for k, v in token.features if k.lower() in _FEATURE_NAMES}
    if any(analysis.features.get(k) != v for k, v in expected.items()):
        raise ValueError("form_feature_mismatch")
    source_id = decision.context_source_id or review.source_id
    if source_id not in profile.source_ids:
        raise ValueError("unauthorized_form_source")
    if decision.context_source == "dictionary_example":
        context_candidate = by_id.get(decision.context_candidate_id or candidate.candidate_id)
        if (
            context_candidate is None
            or decision.context not in context_candidate.examples
            or decision.context_source_sha256 != manifest["dictionary_sha256"]
            or source_id != review.source_id
        ):
            raise ValueError("unattested_dictionary_context")
        if context_candidate.candidate_id != candidate.candidate_id and (
            context_candidate.kind != "inflection"
            or identity.normalized_lemma not in context_candidate.form_of
            or context_candidate.lemma != token.text
            or context_candidate.pos != identity.part_of_speech
        ):
            raise ValueError("unrelated_inflection_source")
    else:
        matches = [
            s
            for s in corpus
            if s.document_id == decision.document_id
            and s.sentence_id == decision.sentence_id
            and s.text == decision.context
            and s.source_sha256 == decision.context_source_sha256
        ]
        if len(matches) != 1:
            raise ValueError("unattested_corpus_context")
        source_tokens = [
            t
            for t in matches[0].tokens
            if (t.start, t.end, t.text) == (token.start, token.end, token.text)
        ]
        if len(source_tokens) != 1:
            raise ValueError("unaligned_corpus_form")
    return SurfaceForm(
        lexical_identity_id=identity.lexical_identity_id,
        text=token.text,
        analysis=analysis,
        source_id=source_id,
        source_sha256=decision.context_source_sha256,
        attestation=1,
        context=decision.context,
        evidence_values=decision.evidence_values,
        prerequisite_depth=decision.prerequisite_depth,
    )


def compile_reviewed_vocabulary(
    *,
    preparation_dir: Path,
    decisions_path: Path,
    decisions_sha256: str,
    profile: LanguageProfile,
    verifier: EvidenceVerifier,
    output: Path | None = None,
) -> CompiledVocabularyBundle:
    """Verify immutable source bytes and explicit reviews; optionally publish staging files."""
    profile = LanguageProfile.model_validate(profile.model_dump(mode="json"))
    if output is not None:
        output = _plain_path(output)
        if output.exists():
            raise ValueError("review output must be a new directory; refusing replacement")
    manifest, candidates, corpus, source_artifacts = _load_preparation(preparation_dir)
    review = VocabularyReview.model_validate_json(_read_bytes(decisions_path, decisions_sha256))
    bundle = _compile(
        manifest, candidates, corpus, review, profile, verifier, decisions_sha256, source_artifacts
    )
    if output is not None:
        data = (bundle.model_dump_json(indent=2) + "\n").encode("utf-8")
        if len(data) > _MAX_BYTES:
            raise ValueError("compiled bundle exceeds byte limit")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir()  # Atomic reservation; never overwrite an existing directory.
        with (output / "bundle.json").open("xb") as handle:
            handle.write(data)
        artifact_manifest = {
            "schema_version": 1,
            "bundle_sha256": bundle.bundle_sha256,
            "files": {"bundle.json": hashlib.sha256(data).hexdigest()},
            "production_eligible": False,
        }
        with (output / "manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(artifact_manifest, handle, sort_keys=True, indent=2)
            handle.write("\n")
    return bundle


def create_pending_review(
    preparation_dir: Path, *, source_id: str, source_version: str
) -> VocabularyReview:
    """Create an editable review document, retaining exact candidate hashes and no approvals."""
    manifest, candidates, _corpus, _artifacts = _load_preparation(preparation_dir)
    return VocabularyReview(
        preparation_sha256=manifest["preparation_sha256"],
        language=manifest["language"],
        source_id=source_id,
        source_version=source_version,
        senses=tuple(
            SenseDecision(
                candidate_id=candidate.candidate_id,
                candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
                source_record_sha256=candidate.source_record_sha256,
                lemma=candidate.lemma,
                pos=candidate.pos,
            )
            for candidate in candidates
        ),
    )


def verify_compiled_vocabulary(
    bundle: CompiledVocabularyBundle, *, profile: LanguageProfile, verifier: EvidenceVerifier
) -> CompiledVocabularyBundle:
    """Rebuild signed facts before native persistence; no form-dropping legacy conversion."""
    checked = CompiledVocabularyBundle.model_validate(bundle.model_dump(mode="json"))
    profile = LanguageProfile.model_validate(profile.model_dump(mode="json"))
    if checked.profile_sha256 != _profile_hash(profile):
        raise ValueError("compiled review profile checksum mismatch")
    rebuilt = _compile(
        checked.preparation_manifest,
        checked.candidates,
        checked.corpus,
        checked.review,
        profile,
        verifier,
        checked.decisions_sha256,
        checked.source_artifacts,
    )
    if rebuilt != checked:
        raise ValueError("compiled bundle differs from its verified review evidence")
    return checked


def load_compiled_vocabulary(
    path: Path, *, expected_sha256: str, profile: LanguageProfile, verifier: EvidenceVerifier
) -> CompiledVocabularyBundle:
    bundle = CompiledVocabularyBundle.model_validate_json(_read_bytes(path, expected_sha256))
    return verify_compiled_vocabulary(bundle, profile=profile, verifier=verifier)


def persist_compiled_vocabulary(bundle: CompiledVocabularyBundle, root: Path) -> str:
    """Retain the complete reviewed provenance beside other content-addressed evidence."""
    root = _plain_path(root)
    root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".review-", dir=root) as directory:
        temporary = Path(directory) / "bundle.json"
        digest, total = hashlib.sha256(), 0
        with temporary.open("xb") as handle:
            encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for chunk in encoder.iterencode(bundle.model_dump(mode="json")):
                data = chunk.encode("utf-8")
                total += len(data)
                if total > _MAX_BYTES:
                    raise ValueError("compiled bundle exceeds byte limit")
                digest.update(data)
                handle.write(data)
        key = digest.hexdigest()
        target = _plain_path(root / key)
        try:
            os.link(temporary, target)
        except FileExistsError:
            _read_bytes(target, key)
    return key
