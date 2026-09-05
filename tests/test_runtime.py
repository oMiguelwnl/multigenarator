"""Tests for local runtime helpers that support shipped smoke flows."""

from __future__ import annotations

import pytest

from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanFrequencyJobAuthority,
    KoreanFrequencyEntry,
    KoreanLexicalIdentity,
    KoreanMorphologyStatus,
    KoreanSignatureItem,
    raw_bytes_sha256,
)
from multilang.runtime import (
    KoreanFrequencyTextRuntimeAuthority,
    _default_deck_name,
    build_korean_frequency_text_runtime_service,
    build_runtime_service,
)
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.fallback_audio_adapter import FallbackAudioAdapter
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.library_pronunciation_adapters import (
    FallbackPronunciationAdapter,
    LibraryPronunciationAdapter,
)
from multilang.services.local_text_adapter import LocalSentenceAdapter, LocalTranslationAdapter
from multilang.services.provider_pronunciation_adapters import LiteLLMPronunciationAdapter
from multilang.services.text_generation import SentenceGenerationRequest, SentenceTranslationRequest
from multilang.settings import Settings


class FakeElevenLabsSpeechAdapter:
    instances = []

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings
        type(self).instances.append(self)

    def available_voice_ids(self) -> set[str] | None:
        return None

    def synthesize(self, **kwargs: object) -> AudioSynthesisResponse:
        raise AssertionError("not called")


class FakeAzureSpeechAdapter(FakeElevenLabsSpeechAdapter):
    instances = []


class FakeGoogleTranslateSpeechAdapter(FakeElevenLabsSpeechAdapter):
    instances = []


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def _korean_runtime_authority() -> KoreanFrequencyJobAuthority:
    return KoreanFrequencyJobAuthority(
        stage="full",
        phase31_pointer_locator_sha256=_hash("phase31-pointer-locator"),
        phase31_pointer_content_sha256=_hash("phase31-pointer-content"),
        phase31_validation_receipt_sha256=_hash("phase31-receipt"),
        phase31_snapshot_manifest_sha256=_hash("phase31-snapshot-manifest"),
        phase31_snapshot_root_sha256=_hash("phase31-snapshot-root"),
        frequency_bundle_locator_sha256=_hash("frequency-bundle-locator"),
        frequency_bundle_content_sha256=_hash("frequency-bundle-content"),
        source_retrieval_sha256=_hash("source-retrieval"),
        source_build_result_sha256=_hash("source-build-result"),
        source_review_aggregate_sha256=_hash("source-review-aggregate"),
        provider_policy_sha256=_hash("provider-policy"),
        pilot_authority_sha256=_hash("pilot-authority"),
        catalog_locator_sha256=_hash("catalog-locator"),
        catalog_content_sha256=_hash("catalog-content"),
        profile_sample_authority_sha256=_hash("profile-sample"),
        provider_review_authority_sha256=_hash("provider-review"),
        heard_review_authority_sha256=_hash("heard-review"),
    )


def _korean_fingerprint() -> KoreanAnalyzerFingerprint:
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


def _korean_frequency_entry(rank: int) -> KoreanFrequencyEntry:
    lemma = f"어휘{rank}"
    fingerprint = _korean_fingerprint()
    identity = KoreanLexicalIdentity(
        submitted_form=lemma,
        canonical_nfc=lemma,
        lemma=lemma,
        part_of_speech="NNG",
        sense_id=f"nikl:{rank}",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form=lemma, pos="NNG"),),
        analyzer_fingerprint=fingerprint,
        status="resolved",
    )
    return KoreanFrequencyEntry(
        language="ko",
        version="fixture-v1",
        level=((rank - 1) // 1000) + 1,
        final_rank=rank,
        source_rank=rank,
        source_provenance="nikl-korean-learners-vocabulary",
        source_version="2003-06-04.revised-2019-05-30",
        license_decision="approved-local-use",
        storage_disposition="synthetic-test-only",
        curation_decision="accepted",
        curation_flags=("source_rank_preserved",),
        grounding_confidence="source-backed",
        bundle_sha256=_hash("bundle"),
        retrieval_sha256=_hash("retrieval"),
        analyzer_fingerprint=fingerprint,
        lexical_identity=identity,
    )


def test_local_runtime_uses_curated_smoke_sentence_and_translation_for_lantern() -> None:
    sentence_adapter = LocalSentenceAdapter()
    translation_adapter = LocalTranslationAdapter()

    sentence = sentence_adapter.generate_sentence(
        SentenceGenerationRequest(
            display_form="lantern",
            lemma="lantern",
            definitions_html="a portable light protected by a transparent case",
            target_language="en",
            translation_target_language="pt",
        )
    )
    translation = translation_adapter.translate_sentence(
        SentenceTranslationRequest.from_sentence(
            sentence_result=sentence,
            translation_target_language="pt",
        )
    )

    assert sentence.sentence == "She hung the lantern beside the cabin door."
    assert translation.translation == "Ela pendurou a lanterna ao lado da porta da cabana."
    assert sentence.provenance["template_kind"] == "curated:lantern"


def test_korean_frequency_text_runtime_verifies_phase31_before_loading_and_building(tmp_path) -> None:
    authority = _korean_runtime_authority()
    order: list[str] = []

    def verifier(*, expected_receipt_sha256: str) -> object:
        order.append("verify_active")
        assert expected_receipt_sha256 == authority.phase31_validation_receipt_sha256
        return type(
            "Report",
            (),
            {
                "receipt_sha256": authority.phase31_validation_receipt_sha256,
                "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
            },
        )()

    def entry_loader(**kwargs: object) -> tuple[KoreanFrequencyEntry, ...]:
        order.append("load_entries")
        assert kwargs["job_id"] == "job-ko"
        assert kwargs["authority"] == authority
        assert kwargs["binding_receipt_sha256"] == authority.source_review_aggregate_sha256
        return ()

    def runtime_builder(**kwargs: object) -> object:
        order.append("build_runtime")
        assert order == ["verify_active", "load_entries", "build_runtime"]
        assert kwargs["korean_final_frequency_entries"] == ()
        assert kwargs["korean_source_review_aggregate_sha256"] == authority.source_review_aggregate_sha256
        return object()

    result = build_korean_frequency_text_runtime_service(
        settings=Settings(_env_file=None, database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}"),
        runtime_authority=KoreanFrequencyTextRuntimeAuthority(
            job_id="job-ko",
            bundle_root=tmp_path / "bundle",
            binding_receipt_sha256=authority.source_review_aggregate_sha256 or "",
            authority=authority,
        ),
        phase31_provenance_verifier=verifier,
        entry_loader=entry_loader,
        runtime_builder=runtime_builder,
    )

    assert result is not None
    assert order == ["verify_active", "load_entries", "build_runtime"]


def test_korean_frequency_text_runtime_blocks_phase31_drift_before_loading_entries(tmp_path) -> None:
    authority = _korean_runtime_authority()
    order: list[str] = []

    def verifier(*, expected_receipt_sha256: str) -> object:
        order.append("verify_active")
        return type(
            "Report",
            (),
            {
                "receipt_sha256": authority.phase31_validation_receipt_sha256,
                "snapshot_manifest_sha256": "0" * 64,
                "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
            },
        )()

    def entry_loader(**kwargs: object) -> tuple[KoreanFrequencyEntry, ...]:
        order.append("load_entries")
        return ()

    def runtime_builder(**kwargs: object) -> object:
        order.append("build_runtime")
        return object()

    with pytest.raises(ValueError, match="Phase 31 active authority drift"):
        build_korean_frequency_text_runtime_service(
            settings=Settings(_env_file=None, database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}"),
            runtime_authority=KoreanFrequencyTextRuntimeAuthority(
                job_id="job-ko",
                bundle_root=tmp_path / "bundle",
                binding_receipt_sha256=authority.source_review_aggregate_sha256 or "",
                authority=authority,
            ),
            phase31_provenance_verifier=verifier,
            entry_loader=entry_loader,
            runtime_builder=runtime_builder,
        )

    assert order == ["verify_active"]


def test_runtime_fails_loudly_when_litellm_is_configured_without_credentials(tmp_path) -> None:
    with pytest.raises(ValueError, match="LiteLLM sentence generation requires"):
        build_runtime_service(
            Settings(
                _env_file=None,
                database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
                text_generation_provider="litellm",
                translation_provider="local",
            )
        )


def test_runtime_fails_loudly_when_deepl_is_configured_without_credentials(tmp_path) -> None:
    with pytest.raises(ValueError, match="DeepL translation requires"):
        build_runtime_service(
            Settings(
                _env_file=None,
                database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
                text_generation_provider="local",
                translation_provider="deepl",
            )
        )


def test_runtime_allows_local_text_services_only_when_explicitly_configured(tmp_path) -> None:
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        )
    )

    assert service is not None
    assert isinstance(service.grounding_service._pronunciation_generator, LibraryPronunciationAdapter)


def test_runtime_wires_litellm_pronunciation_adapter_when_configured(tmp_path) -> None:
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="litellm",
            translation_provider="local",
            openai_api_key="test-key",
        )
    )

    adapter = service.grounding_service._pronunciation_generator

    assert isinstance(adapter, FallbackPronunciationAdapter)
    assert isinstance(adapter.adapters[0], LibraryPronunciationAdapter)
    assert isinstance(adapter.adapters[1], LiteLLMPronunciationAdapter)


def test_runtime_wires_elevenlabs_audio_provider(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeElevenLabsSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "ElevenLabsSpeechAdapter", FakeElevenLabsSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="elevenlabs",
            elevenlabs_api_key="test-key",
            elevenlabs_voice_id="voice-123",
        )
    )

    assert service is not None
    assert len(FakeElevenLabsSpeechAdapter.instances) == 1
    assert FakeElevenLabsSpeechAdapter.instances[0].settings.audio_provider == "elevenlabs"


def test_runtime_wires_google_translate_audio_provider(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeGoogleTranslateSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "GoogleTranslateSpeechAdapter", FakeGoogleTranslateSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="google_translate",
        )
    )

    assert service is not None
    assert len(FakeGoogleTranslateSpeechAdapter.instances) == 1
    assert FakeGoogleTranslateSpeechAdapter.instances[0].settings.audio_provider == "google_translate"


def test_runtime_wires_configured_audio_fallback_chain(tmp_path, monkeypatch) -> None:
    import multilang.runtime as runtime_module

    FakeAzureSpeechAdapter.instances.clear()
    FakeElevenLabsSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    monkeypatch.setattr(runtime_module, "ElevenLabsSpeechAdapter", FakeElevenLabsSpeechAdapter)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            audio_provider="azure",
            audio_fallback_providers=["elevenlabs"],
            elevenlabs_api_key="test-key",
        )
    )

    adapter = service.generate_audio_items_service.audio_synthesis_service.adapter
    assert isinstance(adapter, FallbackAudioAdapter)
    assert len(FakeAzureSpeechAdapter.instances) == 1
    assert len(FakeElevenLabsSpeechAdapter.instances) == 1


def test_runtime_injects_one_korean_morphology_object_into_all_consumers(tmp_path) -> None:
    morphology = KiwiKoreanMorphologyService(
        analyzer_factory=lambda: (_ for _ in ()).throw(RuntimeError("not requested"))
    )

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        ),
        korean_morphology_service=morphology,
    )

    generation_validator = service.generate_text_items_service.text_validation_service
    regeneration_validator = service.regenerate_text_item_service.text_validation_service

    assert service.grounding_service._korean_morphology is morphology
    assert generation_validator is regeneration_validator
    assert generation_validator.korean_matcher is morphology
    assert regeneration_validator.korean_matcher is morphology
    assert generation_validator.korean_matcher.fingerprint is morphology.fingerprint


def test_runtime_default_korean_adapter_is_single_and_vendor_construction_is_lazy(
    tmp_path,
    monkeypatch,
) -> None:
    import multilang.runtime as runtime_module

    wrapper_instances: list[KiwiKoreanMorphologyService] = []
    analyzer_factory_calls = 0

    def unavailable_analyzer_factory() -> object:
        nonlocal analyzer_factory_calls
        analyzer_factory_calls += 1
        raise RuntimeError("private vendor detail")

    def morphology_factory() -> KiwiKoreanMorphologyService:
        wrapper = KiwiKoreanMorphologyService(
            analyzer_factory=unavailable_analyzer_factory
        )
        wrapper_instances.append(wrapper)
        return wrapper

    monkeypatch.setattr(
        runtime_module,
        "KiwiKoreanMorphologyService",
        morphology_factory,
        raising=False,
    )

    service = runtime_module.build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        )
    )

    assert len(wrapper_instances) == 1
    assert analyzer_factory_calls == 0
    shared_morphology = wrapper_instances[0]
    assert service.grounding_service._korean_morphology is shared_morphology
    assert (
        service.generate_text_items_service.text_validation_service.korean_matcher
        is shared_morphology
    )
    assert (
        service.regenerate_text_item_service.text_validation_service.korean_matcher
        is shared_morphology
    )

    first = shared_morphology.analyze("학교")
    second = shared_morphology.analyze("학교")

    assert analyzer_factory_calls == 1
    assert first.status is KoreanMorphologyStatus.UNAVAILABLE
    assert second.status is KoreanMorphologyStatus.UNAVAILABLE
    assert "private vendor detail" not in first.model_dump_json()
    assert "private vendor detail" not in second.model_dump_json()


def test_unavailable_korean_factory_does_not_block_non_korean_runtime_startup(
    tmp_path,
) -> None:
    analyzer_factory_calls = 0

    def unavailable_analyzer_factory() -> object:
        nonlocal analyzer_factory_calls
        analyzer_factory_calls += 1
        raise RuntimeError("private vendor detail")

    morphology = KiwiKoreanMorphologyService(
        analyzer_factory=unavailable_analyzer_factory
    )
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
        ),
        korean_morphology_service=morphology,
    )

    assert service is not None
    assert analyzer_factory_calls == 0
    assert _default_deck_name(SupportedLanguage.EN) == "Multilang English"

    korean_result = service.grounding_service.resolve_korean_source_identity(
        surface_form="학교"
    )

    assert korean_result.status == "unavailable"
    assert analyzer_factory_calls == 1
    assert _default_deck_name(SupportedLanguage.EN) == "Multilang English"


def test_korean_frequency_runtime_uses_explicit_final_entries_without_wordfreq_or_settings(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import multilang.services.frequency_decks as frequency_decks

    def forbidden_iter_wordlist(language: str):
        raise AssertionError("Korean final runtime must not discover authority from wordfreq")

    monkeypatch.setattr(frequency_decks, "iter_wordlist", forbidden_iter_wordlist)

    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
            text_generation_provider="local",
            translation_provider="local",
            frequency_assets_dir=tmp_path / "mutable-settings-assets",
        ),
        korean_final_frequency_entries=(_korean_frequency_entry(1),),
        korean_source_review_receipt_sha256=_hash("source-review-receipt"),
        korean_source_review_aggregate_sha256=_hash("source-review-aggregate"),
    )

    result = service.execute(
        GenerationRequest(
            language=SupportedLanguage.KO,
            source_type="frequency",
            level=1,
            cards_per_level=1,
        )
    )

    [candidate] = service.lexical_repo.list_candidates(result.report.job_id)
    assert result.grounded_candidates == 1
    assert result.level_counts == {1: 1, 2: 0, 3: 0}
    assert candidate.korean_identity is not None
    assert candidate.korean_identity.lexical_key.startswith("ko:")
    assert candidate.provenance.source == "korean-frequency-bundle"


def test_runtime_has_korean_display_name() -> None:
    assert _default_deck_name(SupportedLanguage.KO) == "Multilang Korean"
