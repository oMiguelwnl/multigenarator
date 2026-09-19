"""Real persistence with an offline Azure double; acoustic approval is never inferred."""

from __future__ import annotations

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.audio import (
    AudioAssetKind,
    AudioProvider,
    AudioReviewStatus,
    AudioSynthesisStatus,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import KoreanFrequencyJobAuthority, canonical_json_sha256
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.provider_call_log_repository import ProviderCallLogRepository
from multilang.repositories.text_repository import TextRepository
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.generation_leases import GenerationLeaseManager
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    KoreanVoiceProfile,
    synthesize_korean_frequency_audio,
)
from multilang.settings import Settings


def _hash(text):
    return sha256(text.encode()).hexdigest()


# Three MPEG-2 Layer III frames, 24 kHz / 48 kbps / mono, 24 ms each.
# This validates container structure only, not pronunciation or acoustic quality.
MP3 = (bytes.fromhex("fff364c0") + bytes(140)) * 3
VOICE = "ko-KR-SunHiNeural"


class FileAzure:
    provider = AudioProvider.AZURE
    provider_sdk_version = "offline-fixture"

    def __init__(self, payload=MP3, *, failure=False):
        self.payload = payload
        self.failure = failure
        self.calls = []

    def synthesize(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise ValueError("provider diagnostic with private content")
        path = kwargs["output_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.payload)
        return AudioSynthesisResponse(
            storage_path=path, byte_size=len(self.payload), duration_ms=72
        )


@pytest.fixture
def audio_run(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'audio.db'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session = Session(engine)
    jobs = JobRepository(session)
    job = jobs.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="frequency", level=1),
        run_key="korean-audio-runtime",
        source_fingerprint="fixture",
        total_items=1,
    )
    budget = KoreanProviderBudget(
        max_attempts=2,
        max_input_tokens=4096,
        max_output_tokens=0,
        max_total_tokens=4096,
        max_estimated_cost_usd=1,
        max_latency_ms=60000,
        timeout_seconds=60,
        max_batch_items=10,
        max_concurrency=1,
    )
    policy = KoreanProviderPolicy(
        routes=tuple(
            KoreanProviderRoute(
                task=task,
                provider="azure-speech",
                model=VOICE,
                budget=budget,
                cache_namespace=f"test-{task.value}",
                response_schema_sha256=_hash(task.value),
            )
            for task in KoreanProviderTask
        )
    )
    voices = [{"voice_id": VOICE, "locale": "ko-KR", "region": "koreacentral"}]
    content_hash = canonical_json_sha256({"catalog_locale": "ko-KR", "voices": voices})
    catalog = {
        "schema_version": "korean-azure-catalog-pilot-result-v1",
        "job_id": job.id,
        "binding_receipt_sha256": _hash("source_review_aggregate_sha256"),
        "provider_policy_sha256": policy.policy_sha256,
        "pilot_authority_sha256": _hash("pilot_authority_sha256"),
        "catalog_locator_sha256": _hash("catalog_locator_sha256"),
        "catalog_content_sha256": content_hash,
        "catalog_locale": "ko-KR",
        "voice_count": 1,
        "catalog_query_count": 1,
        "synthesis_attempt_count": 0,
        "production_database_used": False,
        "voices": voices,
    }
    catalog_file = tmp_path / "catalog.json"
    catalog_file.write_text(json.dumps(catalog))
    profile_payload = {
        "schema_version": "korean-voice-profile-v1",
        "voice_id": VOICE,
        "locale": "ko-KR",
        "region": "koreacentral",
        "provider": "azure-speech",
        "output_format": "audio-24khz-48kbitrate-mono-mp3",
        "profile_policy_version": "korean-neutral-ssml-v1",
        "ssml_policy": "neutral",
        "usage_scope": ["ordinary-frequency-word-audio", "ordinary-frequency-sentence-audio"],
        "fallback_policy": "none",
        "provider_sdk_version": "not-captured",
        "catalog_receipt_sha256": content_hash,
        "catalog_result_file_sha256": sha256(catalog_file.read_bytes()).hexdigest(),
        "catalog_locator_sha256": catalog["catalog_locator_sha256"],
        "catalog_content_sha256": content_hash,
        "provider_policy_sha256": policy.policy_sha256,
        "pilot_authority_sha256": catalog["pilot_authority_sha256"],
        "profile_authority_sha256": _hash("profile_sample_authority_sha256"),
    }
    profile = KoreanVoiceProfile(
        **profile_payload, profile_sha256=canonical_json_sha256(profile_payload)
    )
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(profile.model_dump_json())
    policy_file = tmp_path / "policy.json"
    policy_file.write_text(policy.model_dump_json())
    fields = {
        name: _hash(name) for name in KoreanFrequencyJobAuthority.model_fields if name != "stage"
    }
    fields.update(provider_policy_sha256=policy.policy_sha256, catalog_content_sha256=content_hash)
    authority = KoreanFrequencyJobAuthority(stage="full", **fields)
    jobs.bind_audio_authority(job.id, authority)
    audio_authority = KoreanAudioAuthority(
        job_id=job.id,
        binding_receipt_sha256=authority.source_review_aggregate_sha256,
        **{
            name: getattr(authority, name)
            for name in KoreanAudioAuthority.model_fields
            if name not in {"job_id", "binding_receipt_sha256", "region"}
        },
    )
    lexical = LexicalRepository(session)
    lexical.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="item-1",
        source_type="frequency",
        normalized_source="학교",
        candidate=LexicalCardCandidate(
            submitted_form="학교",
            display_form="학교",
            lemma="학교",
            lemma_key="ko:school",
            frequency_rank=1,
            frequency_level=1,
            definitions_html="escola",
            definition_language="pt",
            translation_target_language="pt",
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(source="fixture"),
        ),
    )
    candidate = lexical.get_candidate_for_item(job.id, "item-1")
    TextRepository(session).upsert_text_record(
        TextQualityRecord(
            job_id=job.id,
            item_key="item-1",
            lexical_candidate_id=candidate.id,
            example_sentence="학교에 가요.",
            translation_text="Vou para a escola.",
            generation_status=TextGenerationStatus.GENERATED,
            validation_status=ValidationStatus.PASSED,
            review_status=ReviewStatus.ACCEPTED,
            confidence_score=0.99,
            confidence_label=ConfidenceLabel.HIGH,
            sentence_provenance=TextProvenance(source="fixture"),
            translation_provenance=TextProvenance(source="fixture"),
            text_review_receipt_sha256=_hash("text-review"),
        )
    )
    entry = SimpleNamespace(
        final_rank=1,
        level=1,
        lexical_identity=SimpleNamespace(lexical_key="ko:school", canonical_nfc="학교"),
    )
    kwargs = dict(
        database_url=database_url,
        authority=audio_authority,
        job_authority=authority,
        catalog_result_file=catalog_file,
        voice_profile_file=profile_file,
        provider_policy_file=policy_file,
        frequency_bundle_root=tmp_path / "bundle",
        max_items=1,
        settings=Settings(
            _env_file=None,
            database_url=database_url,
            azure_speech_region="koreacentral",
            audio_provider="azure",
            audio_fallback_providers=[],
            audio_storage_dir=tmp_path / "audio",
            korean_azure_tts_usd_per_million_characters=1.0,
            korean_azure_tts_pricing_voice_id=VOICE,
        ),
        phase31_verifier=lambda **_: SimpleNamespace(
            receipt_sha256=authority.phase31_validation_receipt_sha256,
            snapshot_manifest_sha256=authority.phase31_snapshot_manifest_sha256,
            snapshot_root_sha256=authority.phase31_snapshot_root_sha256,
        ),
        entry_loader=lambda **_: (entry,),
    )
    yield SimpleNamespace(kwargs=kwargs, session=session, jobs=jobs, job_id=job.id, profile=profile)
    session.close()
    engine.dispose()


def test_authorized_audio_persists_exact_bytes_pending_review_and_reuses(audio_run):
    adapter = FileAzure()
    result = synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert (result.processed_items, result.failed_items, result.fallback_items) == (2, 0, 0)
    assets = AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)
    assert len(assets) == 2
    assert {asset.normalized_input.tts_text for asset in assets} == {"학교", "학교에 가요."}
    for asset in assets:
        assert asset.provenance.artifact_sha256 == sha256(b"artifact:" + MP3).hexdigest()
        assert asset.provenance.byte_size == len(MP3)
        assert asset.provenance.provider_sdk_version == "offline-fixture"
        assert asset.provenance.audio_review_status is AudioReviewStatus.SYNTHESIZED_PENDING
        assert not asset.ready_for_korean_final_export
    logs = ProviderCallLogRepository(audio_run.session).list_for_job(audio_run.job_id)
    assert all(0 < log.estimated_cost < 1 for log in logs)
    assert all(log.input_tokens is None and log.total_tokens is None for log in logs)
    assert {log.operation for log in logs} == {"word_audio", "sentence_audio"}
    assert all(
        log.route_policy_sha256 and log.budget_snapshot_sha256 and log.response_hash for log in logs
    )
    replay = synthesize_korean_frequency_audio(
        **audio_run.kwargs, adapter=adapter, missing_only=True
    )
    assert replay.reused_items == 2
    assert len(adapter.calls) == 2


@pytest.mark.parametrize(
    "payload,failure",
    [
        (b"ID3-not-real-media", False),
        ((bytes.fromhex("fff364c0") + bytes([255]) * 140) * 3, False),
        ((bytes.fromhex("fff364c0") + bytes([170]) * 140) * 3, False),
        (MP3, True),
    ],
    ids=["invalid-media", "undecodable-frames", "partially-decoded-frames", "provider-failure"],
)
def test_invalid_or_failed_audio_never_advances_item(audio_run, payload, failure):
    before = audio_run.jobs.get_job(audio_run.job_id).completed_items
    result = synthesize_korean_frequency_audio(
        **audio_run.kwargs, adapter=FileAzure(payload, failure=failure)
    )
    assert result.failed_items == 2
    audio_run.session.expire_all()
    assert audio_run.jobs.get_job(audio_run.job_id).completed_items == before
    assert all(
        asset.provenance.status is AudioSynthesisStatus.FAILED
        for asset in AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)
    )
    logs = ProviderCallLogRepository(audio_run.session).list_for_job(audio_run.job_id)
    assert all("private content" not in (log.error_summary or "") for log in logs)


def test_profile_tampering_blocks_before_provider_or_database_writes(audio_run):
    path = audio_run.kwargs["voice_profile_file"]
    payload = json.loads(path.read_text())
    payload["voice_id"] = "ko-KR-OtherNeural"
    path.write_text(json.dumps(payload))
    adapter = FileAzure()
    with pytest.raises(ValueError, match="profile.*drift"):
        synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert not adapter.calls
    assert not AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)


def test_missing_only_rechecks_actual_media_bytes(audio_run):
    from pathlib import Path

    adapter = FileAzure()
    synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    asset = AudioRepository(audio_run.session).get_asset(
        audio_run.job_id, "item-1", AudioAssetKind.WORD
    )
    Path(asset.provenance.storage_path).write_bytes(b"corrupt")
    result = synthesize_korean_frequency_audio(
        **audio_run.kwargs, adapter=adapter, missing_only=True
    )
    assert (result.processed_items, result.reused_items) == (2, 1)
    assert len(adapter.calls) == 3


@pytest.mark.parametrize("payload_byte", [255, 170])
def test_reuse_rejects_matching_hashes_when_full_frames_cannot_decode(audio_run, payload_byte):
    from pathlib import Path

    adapter = FileAzure()
    synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    repository = AudioRepository(audio_run.session)
    asset = repository.get_asset(audio_run.job_id, "item-1", AudioAssetKind.WORD)
    corrupt = (bytes.fromhex("fff364c0") + bytes([payload_byte]) * 140) * 3
    Path(asset.provenance.storage_path).write_bytes(corrupt)
    repository.upsert_audio_asset(asset.model_copy(update={
        "provenance": asset.provenance.model_copy(update={
            "artifact_sha256": sha256(b"artifact:" + corrupt).hexdigest(),
        }),
    }))

    result = synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter, missing_only=True)

    assert result.reused_items == 1
    assert result.processed_items == 2
    assert result.failed_items == 0
    assert len(adapter.calls) == 3


def test_bounded_missing_only_advances_past_already_synthesized_items(audio_run):
    adapter = FileAzure()
    synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    _add_second_audio_item(audio_run)
    synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter, missing_only=True)
    assert len(adapter.calls) == 4
    assert (
        AudioRepository(audio_run.session).get_asset(
            audio_run.job_id, "item-2", AudioAssetKind.SENTENCE
        )
        is not None
    )


def _add_second_audio_item(audio_run):
    lexical = LexicalRepository(audio_run.session)
    job = audio_run.jobs.get_job(audio_run.job_id)
    lexical.upsert_candidate(
        job_id=job.id,
        run_key=job.run_key,
        item_key="item-2",
        source_type="frequency",
        normalized_source="집",
        candidate=LexicalCardCandidate(
            submitted_form="집",
            display_form="집",
            lemma="집",
            lemma_key="ko:home",
            frequency_rank=2,
            frequency_level=1,
            definitions_html="casa",
            definition_language="pt",
            translation_target_language="pt",
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(source="fixture"),
        ),
    )
    candidate = lexical.get_candidate_for_item(job.id, "item-2")
    texts = TextRepository(audio_run.session)
    texts.upsert_text_record(
        texts.get_text_record(job.id, "item-1").model_copy(
            update={
                "item_key": "item-2",
                "lexical_candidate_id": candidate.id,
                "example_sentence": "집에 가요.",
                "translation_text": "Vou para casa.",
            }
        )
    )
    original_entry = audio_run.kwargs["entry_loader"]()[0]
    second = SimpleNamespace(
        final_rank=2,
        level=1,
        lexical_identity=SimpleNamespace(lexical_key="ko:home", canonical_nfc="집"),
    )
    audio_run.kwargs["entry_loader"] = lambda **_: (original_entry, second)


@pytest.mark.parametrize("field", ["provider_policy_sha256", "frequency_bundle_content_sha256"])
def test_bound_job_authority_drift_blocks_attempts(audio_run, field):
    adapter = FileAzure()
    audio_run.kwargs["job_authority"] = audio_run.kwargs["job_authority"].model_copy(
        update={field: _hash("drift")}
    )
    with pytest.raises(ValueError, match="authority drift"):
        synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert not adapter.calls


def test_audio_attempts_share_the_generation_lease(audio_run):
    engine = create_engine(audio_run.kwargs["database_url"])
    adapter = FileAzure()
    try:
        with GenerationLeaseManager(engine).hold(audio_run.job_id):
            with pytest.raises(ValueError, match="already running"):
                synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
        assert not adapter.calls
    finally:
        engine.dispose()


def test_ambiguous_audio_outcome_preserves_stage_specific_recovery_marker(audio_run):
    class InterruptedAzure(FileAzure):
        def synthesize(self, **kwargs):
            super().synthesize(**kwargs)
            raise TimeoutError("provider outcome unknown")

    adapter = InterruptedAzure()
    result = synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert result.failed_items == 1
    assert len(adapter.calls) == 1
    assets = AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)
    assert {asset.provenance.status for asset in assets} == {
        AudioSynthesisStatus.FAILED,
        AudioSynthesisStatus.PENDING,
    }
    engine = create_engine(audio_run.kwargs["database_url"])
    try:
        status = GenerationLeaseManager(engine).status(audio_run.job_id)
        assert status["state"] == "recovery_required"
        assert status["inflight_item_sha256"] == _hash("audio:item-1")
        with pytest.raises(ValueError, match="requires recovery"):
            synthesize_korean_frequency_audio(
                **audio_run.kwargs, adapter=adapter, missing_only=True
            )
        assert len(adapter.calls) == 1
    finally:
        engine.dispose()


def test_telemetry_failure_after_synthesis_requires_explicit_recovery(audio_run, monkeypatch):
    def unavailable_telemetry(self, record):
        raise ValueError("private database diagnostic")

    monkeypatch.setattr(ProviderCallLogRepository, "insert", unavailable_telemetry)
    adapter = FileAzure()
    with pytest.raises(ValueError, match="telemetry persistence failed; recovery required"):
        synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert len(adapter.calls) == 1
    assets = AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)
    assert len(assets) == 2
    assert all(asset.provenance.status is AudioSynthesisStatus.PENDING for asset in assets)
    engine = create_engine(audio_run.kwargs["database_url"])
    try:
        status = GenerationLeaseManager(engine).status(audio_run.job_id)
        assert status["state"] == "recovery_required"
        assert status["inflight_item_sha256"] == _hash("audio:item-1")
        with pytest.raises(ValueError, match="requires recovery"):
            synthesize_korean_frequency_audio(
                **audio_run.kwargs, adapter=adapter, missing_only=True
            )
        assert len(adapter.calls) == 1
    finally:
        engine.dispose()


@pytest.mark.parametrize("price,pricing_voice", [
    (None, VOICE), (0.0, VOICE), (float("inf"), VOICE), (1.0, "ko-KR-OtherNeural"),
])
def test_audio_requires_explicit_finite_voice_bound_price_before_provider(
    audio_run, price, pricing_voice,
):
    audio_run.kwargs["settings"] = audio_run.kwargs["settings"].model_copy(update={
        "korean_azure_tts_usd_per_million_characters": price,
        "korean_azure_tts_pricing_voice_id": pricing_voice,
    })
    adapter = FileAzure()
    with pytest.raises(ValueError, match="Korean audio.*pric"):
        synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert not adapter.calls


def test_zero_dollar_audio_budget_blocks_before_synthesis(audio_run):
    from multilang.services.korean_audio_runtime import KoreanProfileAudioSynthesisService

    policy = KoreanProviderPolicy.model_validate_json(
        audio_run.kwargs["provider_policy_file"].read_text()
    )
    policy = policy.model_copy(update={"routes": tuple(
        route.model_copy(update={"budget": route.budget.model_copy(update={
            "max_estimated_cost_usd": 0.0,
        })}) for route in policy.routes
    )})
    adapter = FileAzure()
    service = KoreanProfileAudioSynthesisService(
        profile=audio_run.profile, provider_policy=policy, adapter=adapter,
        settings=audio_run.kwargs["settings"], provider_call_logger=SimpleNamespace(insert=lambda _: None),
    )
    with pytest.raises(ValueError, match="Korean audio cost budget exceeded"):
        prepared = service._prepare(audio_run.job_id, "item-1", AudioAssetKind.WORD, "학교")
        service.synthesize_prepared_asset(prepared)
    assert not adapter.calls


def test_audio_records_exact_ssml_bytes_submitted_to_azure(audio_run):
    from multilang.services.azure_speech_adapter import build_azure_ssml
    from multilang.services.korean_audio import build_korean_tts_input

    normalized = build_korean_tts_input(
        "학교의 '문'과 <창>", asset_kind=AudioAssetKind.WORD, profile=audio_run.profile,
    )
    submitted = build_azure_ssml(
        text=normalized.ssml_text, voice_id=audio_run.profile.voice_id, locale="ko-KR",
    )
    assert submitted.encode("utf-8") == normalized.ssml_text.encode("utf-8")


def test_total_audio_batch_cost_blocks_before_any_synthesis(audio_run):
    _add_second_audio_item(audio_run)
    audio_run.kwargs["max_items"] = 2
    audio_run.kwargs["settings"] = audio_run.kwargs["settings"].model_copy(update={
        "korean_azure_tts_usd_per_million_characters": 4000.0,
    })
    adapter = FileAzure()
    with pytest.raises(ValueError, match="Korean audio cost budget exceeded"):
        synthesize_korean_frequency_audio(**audio_run.kwargs, adapter=adapter)
    assert not adapter.calls
    assert not AudioRepository(audio_run.session).list_assets_for_job(audio_run.job_id)


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf")])
def test_settings_reject_invalid_korean_audio_price(price):
    with pytest.raises(ValueError):
        Settings(_env_file=None, korean_azure_tts_usd_per_million_characters=price)
