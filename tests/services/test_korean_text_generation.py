"""Tests for bounded Korean final text generation selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
from multilang.domain.lexicon import DefinitionRecord, GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    TextGenerationStatus,
    TextProvenance,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.provider_text_adapters import LiteLLMSentenceAdapter
from multilang.services.korean_text_generation import KoreanTextGenerationSelector
from multilang.services.text_generation import (
    GeneratedSentence,
    GeneratedTextBundle,
    GeneratedTranslation,
    KoreanSelectorAttemptContext,
    SentenceGenerationRequest,
)
from multilang.services.text_validation import TextValidationResult
from multilang.settings import Settings


def _hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _fingerprint() -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version="0.23.2",
        model_package_version="0.23.0",
        model_type="cong",
        enabled_dialects="standard",
        num_workers=1,
        integrate_allomorph=True,
        top_n=2,
        split_complex=False,
        compatible_jamo=False,
        normalize_coda=False,
        z_coda=False,
        typos=None,
        oov_handling="chr",
        policy_version="kiwi-top2-consensus-v1",
    )


def _candidate() -> LexicalCardCandidate:
    identity = KoreanLexicalIdentity(
        submitted_form="먹다",
        canonical_nfc="먹다",
        lemma="먹다",
        part_of_speech="VV",
        sense_id="fixture:eat:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="먹", pos="VV"),),
        analyzer_fingerprint=_fingerprint(),
        status="resolved",
    )
    return LexicalCardCandidate(
        submitted_form="먹다",
        display_form="먹다",
        lemma="먹다",
        lemma_key=identity.lexical_key,
        frequency_rank=1,
        frequency_level=1,
        definitions_html="verbo: comer",
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(
            source="source-backed-test",
            definition=DefinitionRecord(source="source-backed-test", value="verbo: comer"),
        ),
        korean_identity=identity,
    )


def _bundle(sentence: str, translation: str) -> GeneratedTextBundle:
    return GeneratedTextBundle(
        sentence=GeneratedSentence(
            text=sentence,
            target_language="ko",
            intended_sense="fixture:eat:1",
            uncertainty_notes=[],
            provenance=TextProvenance(source="provider-text-generator", provider="fake-provider"),
        ),
        translation=GeneratedTranslation(
            text=translation,
            target_language="pt",
            provenance=TextProvenance(source="provider-translator", provider="fake-translator"),
        ),
    )


def _validation(
    status: ValidationStatus,
    *,
    score: float,
    code: ValidationFlagCode | None = None,
) -> TextValidationResult:
    return TextValidationResult(
        validation_status=status,
        confidence_label=ConfidenceLabel.HIGH if status is ValidationStatus.PASSED else ConfidenceLabel.LOW,
        confidence_score=score,
        validation_flags=(
            [ValidationFlag(code=code, detail=f"controlled {code.value}")]
            if code is not None
            else []
        ),
    )


@dataclass
class FakeGenerationService:
    bundles: list[GeneratedTextBundle]
    calls: list[dict[str, object]] = field(default_factory=list)
    fallback_calls: int = 0

    def generate_bundle(self, **kwargs: object) -> GeneratedTextBundle:
        self.calls.append(kwargs)
        return self.bundles.pop(0)

    def generate_bundle_from_fallback(self, **kwargs: object) -> GeneratedTextBundle:
        self.fallback_calls += 1
        raise AssertionError("Korean selector must not use fallback generation")


@dataclass
class FakeValidationService:
    results: list[TextValidationResult]
    calls: list[dict[str, object]] = field(default_factory=list)

    def validate_bundle(self, **kwargs: object) -> TextValidationResult:
        self.calls.append(kwargs)
        return self.results.pop(0)


def test_two_plus_one_selector_repairs_only_after_both_initial_candidates_fail() -> None:
    generation = FakeGenerationService(
        bundles=[
            _bundle("먹다 예문입니다.", "comer"),
            _bundle("오늘 밥을 먹습니다.", "Hoje eu eat school."),
            _bundle("오늘 집에서 밥을 먹어요.", "Hoje eu como arroz em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            _validation(
                ValidationStatus.FAILED,
                score=0.2,
                code=ValidationFlagCode.BANNED_PATTERN,
            ),
            _validation(
                ValidationStatus.FAILED,
                score=0.3,
                code=ValidationFlagCode.TRANSLATION_MISMATCH,
            ),
            _validation(ValidationStatus.PASSED, score=0.93),
        ]
    )
    selector = KoreanTextGenerationSelector(
        text_generation_service=generation,
        validate_bundle=validation.validate_bundle,
    )

    result = selector.select(
        candidate=_candidate(),
        deck_language=SupportedLanguage.KO,
        source_type="frequency",
        highlight_context=None,
        seen_sentences=set(),
        job_id="job-ko",
        item_key="level-1-rank-0001",
    )

    assert result.bundle.sentence.text == "오늘 집에서 밥을 먹어요."
    assert result.validation.validation_status is ValidationStatus.PASSED
    assert result.generation_status is TextGenerationStatus.REPAIRED
    assert result.repair_attempt_count == 1
    assert [call["korean_selector_attempt"].stage for call in generation.calls] == [
        "initial",
        "initial",
        "repair",
    ]
    assert [call["korean_selector_attempt"].ordinal for call in generation.calls] == [1, 2, 3]
    repair_context = generation.calls[2]["korean_selector_attempt"]
    assert repair_context.rejected_candidate_sha256s == tuple(
        entry.candidate_sha256 for entry in result.history.attempts[:2]
    )
    assert repair_context.rejection_codes == ("banned_pattern", "translation_mismatch")
    assert len({call["korean_selector_attempt"].cache_identity for call in generation.calls}) == 3
    assert generation.fallback_calls == 0


def test_selector_stops_after_second_initial_pass_and_never_opens_repair_path() -> None:
    generation = FakeGenerationService(
        bundles=[
            _bundle("먹다 예문입니다.", "comer"),
            _bundle("오늘 집에서 밥을 먹어요.", "Hoje eu como arroz em casa."),
        ]
    )
    validation = FakeValidationService(
        results=[
            _validation(
                ValidationStatus.FAILED,
                score=0.2,
                code=ValidationFlagCode.BANNED_PATTERN,
            ),
            _validation(ValidationStatus.PASSED, score=0.91),
        ]
    )
    selector = KoreanTextGenerationSelector(
        text_generation_service=generation,
        validate_bundle=validation.validate_bundle,
    )

    result = selector.select(
        candidate=_candidate(),
        deck_language=SupportedLanguage.KO,
        source_type="frequency",
        highlight_context=None,
        seen_sentences=set(),
        job_id="job-ko",
        item_key="level-1-rank-0001",
    )

    assert result.bundle.sentence.text == "오늘 집에서 밥을 먹어요."
    assert result.generation_status is TextGenerationStatus.GENERATED
    assert result.repair_attempt_count == 0
    assert [call["korean_selector_attempt"].stage for call in generation.calls] == [
        "initial",
        "initial",
    ]
    assert result.history.repair_attempt_count == 0
    assert generation.fallback_calls == 0


def test_selector_fails_closed_without_korean_identity_or_with_non_korean_language() -> None:
    selector = KoreanTextGenerationSelector(
        text_generation_service=FakeGenerationService(bundles=[]),
        validate_bundle=FakeValidationService(results=[]).validate_bundle,
    )
    candidate = _candidate().model_copy(update={"korean_identity": None})

    with pytest.raises(ValueError, match="persisted Korean identity"):
        selector.select(
            candidate=candidate,
            deck_language=SupportedLanguage.KO,
            source_type="frequency",
            highlight_context=None,
            seen_sentences=set(),
            job_id="job-ko",
            item_key="level-1-rank-0001",
        )

    with pytest.raises(ValueError, match="Korean selector only handles Korean"):
        selector.select(
            candidate=_candidate(),
            deck_language=SupportedLanguage.EN,
            source_type="frequency",
            highlight_context=None,
            seen_sentences=set(),
            job_id="job-ko",
            item_key="level-1-rank-0001",
        )


def test_selector_attempt_context_is_visible_to_provider_prompt_as_hash_only_contract() -> None:
    calls: list[dict[str, object]] = []

    def fake_completion(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "sentence": "오늘 집에서 밥을 먹어요.",
                                "intended_sense": "fixture:eat:1",
                                "uncertainty_notes": [],
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }

    cache_identity = _hash("repair-cache")
    rejected = (_hash("bad-candidate-1"), _hash("bad-candidate-2"))
    adapter = LiteLLMSentenceAdapter(
        Settings(
            _env_file=None,
            text_generation_model="openai/gpt-4o-mini",
            openrouter_api_key="router-key",
        ),
        completion_func=fake_completion,
    )

    adapter.generate_sentence(
        SentenceGenerationRequest(
            display_form="먹다",
            lemma="먹다",
            definitions_html="verbo: comer",
            target_language="ko",
            translation_target_language="pt",
            korean_identity=_candidate().korean_identity,
            korean_selector_attempt=KoreanSelectorAttemptContext(
                stage="repair",
                ordinal=3,
                cache_identity=cache_identity,
                rejected_candidate_sha256s=rejected,
                rejection_codes=("banned_pattern", "translation_mismatch"),
            ),
        )
    )

    prompt = calls[0]["messages"][1]["content"]
    assert "Korean generation attempt" in prompt
    assert "trusted orchestration metadata" in prompt
    assert cache_identity in prompt
    assert rejected[0] in prompt
    assert rejected[1] in prompt
    assert "banned_pattern" in prompt
    assert "translation_mismatch" in prompt
    assert "먹다 예문입니다" not in prompt
