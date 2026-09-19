"""Conservative definition admission; source reproduction is not semantic inference."""

import unicodedata
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from multilang.domain.korean import KoreanTextError, canonicalize_korean
from multilang.domain.lexicon import DefinitionRecord
from multilang.services.content.definition_policy import validate_definition
from multilang.services.part_of_speech import canonical_part_of_speech_label
from multilang.services.text_field_remediation import _is_learner_safe_definition
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
)


class DefinitionReviewVerdict(BaseModel):
    """Independent authority bound to exact evidence and draft, never model confidence.

    Reviewers are trusted application dependencies, not provider response fields.
    An approval requires a retrievable source/human review reference. AI judgments
    may only return advisory/review_required. No reviewer is installed by default.
    """

    decision: Literal["source_approved", "human_approved", "advisory", "review_required"]
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reference: str = Field(min_length=1, max_length=256)


class IndependentDefinitionReviewer(Protocol):
    def review(
        self, request: DefinitionGenerationRequest, draft: str
    ) -> DefinitionReviewVerdict: ...


@dataclass(frozen=True)
class DefinitionDecision:
    definitions_html: str | None
    actual_language: str | None
    review_required: bool
    record: DefinitionRecord


def evidence_digest(request: DefinitionGenerationRequest) -> str:
    return sha256(request.model_dump_json().encode()).hexdigest()


def _usable_definition(value: str, request: DefinitionGenerationRequest) -> bool:
    if request.source_language in {"ko", "la"}:
        return _is_learner_safe_definition(value)
    try:
        validate_definition(value, lemma=request.lemma, display_form=request.display_form,
                            part_of_speech=request.part_of_speech)
    except ValueError:
        return False
    return True


def _decide_definition(
    request: DefinitionGenerationRequest,
    result: DefinitionGenerationResult | None,
    *,
    failure_reason: str | None = None,
    reviewer: IndependentDefinitionReviewer | None = None,
) -> DefinitionDecision:
    """Preserve the source verbatim or require independent evidence for a rewrite.

    Formatting heuristics only reject unusable text. They never establish meaning.
    Multiple meanings without a selected sense cannot be collapsed to the first.
    """
    draft = result.definitions_html if result is not None else None
    meanings = tuple(dict.fromkeys(value.strip() for value in request.source_definitions))
    meaning = meanings[0] if len(meanings) == 1 else None
    language = request.source_definition_language
    label = canonical_part_of_speech_label(request.part_of_speech) or "term"
    rendered = f"{label}: {meaning}" if meaning else None
    if rendered and not _usable_definition(rendered, request):
        rendered = None
    has_evidence = bool(
        rendered and request.evidence_source and request.evidence_source != "wordfreq"
    )
    same_language = language is not None and language == request.target_language
    exact = bool(has_evidence and same_language and draft == rendered)
    source_only = result is None and failure_reason is None
    verdict = None
    if has_evidence and draft and not exact and reviewer is not None:
        proposed = reviewer.review(request, draft)
        if (
            proposed.decision in {"source_approved", "human_approved"}
            and proposed.evidence_sha256 == evidence_digest(request)
            and proposed.draft_sha256 == sha256(draft.encode()).hexdigest()
            and _usable_definition(draft, request)
        ):
            verdict = proposed
    if verdict is not None:
        text = draft
        return DefinitionDecision(
            text,
            request.target_language,
            False,
            DefinitionRecord(
                source=str(result.provenance.get("source", "definition-generator")),
                value=text,
                actual_language=request.target_language,
                quality_decision="independently_reviewed",
                evidence_source=request.evidence_source,
                review_reference=verdict.reference,
            ),
        )
    review_required = not (has_evidence and same_language)
    reason = failure_reason
    if not has_evidence:
        reason = "ambiguous_source_meanings" if len(meanings) > 1 else "missing_source_meaning"
    elif language is None:
        reason = "source_language_unknown"
    elif not same_language:
        reason = "target_language_evidence_unavailable"
    elif draft and not exact and reason is None:
        reason = "generated_meaning_unverified"
    text = rendered if has_evidence else None
    record = DefinitionRecord(
        source=(
            str(result.provenance.get("source", "definition-generator"))
            if exact
            else request.evidence_source or "unresolved"
        ),
        value=text,
        fallback_used=has_evidence and not exact and not source_only,
        actual_language=language,
        quality_decision="review_required"
        if review_required
        else "source_verified"
        if exact or source_only
        else "source_fallback",
        fallback_reason=None if exact else reason,
        evidence_source=request.evidence_source,
        generated_draft=draft if draft and not exact else None,
    )
    return DefinitionDecision(text, language, review_required, record)


def decide_definition(
    request: DefinitionGenerationRequest,
    result: DefinitionGenerationResult | None,
    *,
    failure_reason: str | None = None,
    reviewer: IndependentDefinitionReviewer | None = None,
) -> DefinitionDecision:
    """Admit evidence first, then canonicalize Korean learner output.

    Review digests bind the exact original request/draft; canonical equivalence
    is applied only to the admitted rendering, without rewriting source records.
    """
    decision = _decide_definition(request, result, failure_reason=failure_reason, reviewer=reviewer)
    if request.source_language != "ko" or decision.definitions_html is None:
        return decision
    try:
        if any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in decision.definitions_html
        ):
            raise KoreanTextError("definition contains invalid control characters")
        canonical = canonicalize_korean(decision.definitions_html)
    except KoreanTextError:
        return replace(
            decision,
            definitions_html=None,
            review_required=True,
            record=decision.record.model_copy(
                update={
                    "value": None,
                    "quality_decision": "review_required",
                    "fallback_used": False,
                    "fallback_reason": "invalid_definition_text",
                }
            ),
        )
    return replace(
        decision,
        definitions_html=canonical,
        record=decision.record.model_copy(update={"value": canonical}),
    )
