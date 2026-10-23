"""Offline negative tests for future use of persisted, unqualified Korean ranks."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import KoreanAnalyzerFingerprint
from multilang.domain.lexicon import (
    KoreanFrequencyLexicalEvidence,
    LexicalCardCandidate,
    LexicalProvenance,
)
from multilang.services.generate_audio_items import GenerateAudioItemsService
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.korean_frequency_ordering import KoreanFrequencyOrderingError
from multilang.services.regenerate_text_item import RegenerateTextItemService


def candidate(*, evidence=False):
    fingerprint = KoreanAnalyzerFingerprint(
        analyzer_name="kiwi", analyzer_package_version="0.23.2", model_package_version="0.23.0",
        model_type="cong", enabled_dialects="standard", num_workers=1, integrate_allomorph=True,
        top_n=2, split_complex=False, compatible_jamo=False, normalize_coda=False,
        z_coda=False, typos=None, oov_handling="chr", policy_version="kiwi-top2-consensus-v1",
    )
    rank_evidence = KoreanFrequencyLexicalEvidence(
        source_id="nikl-korean-learners-vocabulary", source_version="v1", source_rank=1, final_rank=1, level=1,
        part_of_speech="NNG", sense_id="fixture:1", grounding_confidence="reviewed-source-backed",
        license_decision="approved-local-use", curation_decision="accepted",
        bundle_sha256="a" * 64, source_sha256="b" * 64,
        source_review_receipt_sha256="c" * 64, source_review_aggregate_sha256="d" * 64,
        analyzer_fingerprint=fingerprint,
    ) if evidence else None
    return LexicalCardCandidate(
        submitted_form="학교", display_form="학교", lemma="학교", lemma_key="fixture:school",
        frequency_rank=1, frequency_level=1, translation_target_language="pt",
        grounding_status="grounded", provenance=LexicalProvenance(source="fixture"),
        korean_frequency_evidence=rank_evidence,
    )


def text_service(texts):
    return GenerateTextItemsService(
        job_repository=Mock(), lexical_repository=Mock(), text_repository=texts,
        text_generation_service=Mock(), text_validation_service=Mock(), tatoeba_sentence_source=Mock(),
        review_repository=Mock(),
    )


@pytest.mark.parametrize("repair_only", [False, True])
def test_batch_blocks_persisted_frequency_before_selector_or_item_attempt(monkeypatch, repair_only):
    row = SimpleNamespace(id="row", item_key="item", candidate=candidate(), source_type="frequency")
    texts = SimpleNamespace(
        list_example_sentences_for_job=lambda *_: [],
        list_generation_candidates=lambda *_, **__: [row],
        list_repair_candidates=lambda *_, **__: [row],
        begin_generation_item=Mock(),
    )
    selector = Mock(side_effect=AssertionError("selector must not be constructed"))
    monkeypatch.setattr("multilang.services.generate_text_items.KoreanTextGenerationSelector", selector)
    with pytest.raises(KoreanFrequencyOrderingError):
        text_service(texts).execute(job_id="job", deck_language=SupportedLanguage.KO, repair_only=repair_only)
    selector.assert_not_called()
    texts.begin_generation_item.assert_not_called()


def test_item_regeneration_blocks_before_replaceable_selector(monkeypatch):
    row = SimpleNamespace(candidate=candidate(), source_type="frequency")
    selector = Mock(side_effect=AssertionError("selector must not be constructed"))
    monkeypatch.setattr("multilang.services.regenerate_text_item.KoreanTextGenerationSelector", selector)
    service = RegenerateTextItemService(
        job_repository=Mock(), lexical_repository=SimpleNamespace(get_candidate_for_item=lambda *_: row),
        text_repository=SimpleNamespace(get_text_record=lambda *_: object(), list_example_sentences_for_job=lambda *_, **__: []),
        text_generation_service=Mock(), text_validation_service=Mock(),
    )
    with pytest.raises(KoreanFrequencyOrderingError):
        service.execute(job_id="job", item_key="item", deck_language=SupportedLanguage.KO)
    selector.assert_not_called()


@pytest.mark.parametrize("field", ["definition", "sentence", "microexample", "translation", "word_audio", "sentence_audio"])
def test_field_regeneration_blocks_bound_evidence_without_source_type(field, monkeypatch):
    service = text_service(Mock())
    route = "sentence" if field == "microexample" else "audio" if field.endswith("audio") else field
    boundary = Mock(side_effect=AssertionError("field provider route reached"))
    monkeypatch.setattr(service, f"_regenerate_{route}_field", boundary)
    with pytest.raises(KoreanFrequencyOrderingError):
        service.regenerate_field(
            job_id="job", item_id="item", field_name=field, candidate=candidate(evidence=True),
            deck_language=SupportedLanguage.KO, request_id="request", expected_pointer_version=0,
        )
    boundary.assert_not_called()


@pytest.mark.parametrize("evidence", [False, True])
def test_audio_blocks_before_asset_preparation(evidence):
    model = candidate(evidence=evidence)
    row = model if evidence else SimpleNamespace(**model.model_dump(), source_type="frequency")
    provider = Mock()
    provider.prepare_item_assets.side_effect = AssertionError("audio adapter reached")
    service = GenerateAudioItemsService(
        job_repository=Mock(), lexical_repository=SimpleNamespace(get_candidate_for_item=lambda *_: row),
        text_repository=SimpleNamespace(list_accepted_records=lambda *_: [SimpleNamespace(item_key="item")]),
        audio_repository=Mock(), audio_synthesis_service=provider,
    )
    with pytest.raises(KoreanFrequencyOrderingError):
        service.execute(job_id="job", deck_language=SupportedLanguage.KO)
    provider.prepare_item_assets.assert_not_called()


@pytest.mark.parametrize("language,source_type", [
    (SupportedLanguage.KO, "word-list"), (SupportedLanguage.KO, "kindle-highlights"),
    (SupportedLanguage.KO, "korean-grammar"), (SupportedLanguage.KO, "korean-foundations"),
    (SupportedLanguage.KO, None), (SupportedLanguage.EN, "frequency"),
])
def test_generic_rank_alone_does_not_block_other_field_generation(language, source_type, monkeypatch):
    service = text_service(Mock())
    result = object()
    boundary = Mock(return_value=result)
    monkeypatch.setattr(service, "_regenerate_definition_field", boundary)
    assert service.regenerate_field(
        job_id="job", item_id="item", field_name="definition", candidate=candidate(),
        deck_language=language, source_type=source_type, request_id="request", expected_pointer_version=0,
    ) is result
    boundary.assert_called_once()


def test_empty_generic_korean_text_and_audio_are_noops():
    texts = SimpleNamespace(
        list_example_sentences_for_job=lambda *_: [], list_generation_candidates=lambda *_, **__: [],
    )
    assert text_service(texts).execute(job_id="job", deck_language=SupportedLanguage.KO).processed_items == 0
    service = GenerateAudioItemsService(
        job_repository=Mock(), lexical_repository=Mock(),
        text_repository=SimpleNamespace(list_accepted_records=lambda *_: []),
        audio_repository=Mock(), audio_synthesis_service=Mock(),
    )
    assert service.execute(job_id="job", deck_language=SupportedLanguage.KO).processed_items == 0
    service.audio_synthesis_service.prepare_item_assets.assert_not_called()
