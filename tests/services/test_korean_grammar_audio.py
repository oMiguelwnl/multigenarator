"""Grammar audio stays budget-bound and never converts integrity into acoustics."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from multilang.domain.audio import AudioProvider
from multilang.domain.korean import canonical_json_sha256
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.services import korean_grammar_audio as grammar_audio
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.korean_audio import KoreanVoiceProfile
from multilang.services.korean_audio_runtime import KoreanProfileAudioSynthesisService
from multilang.settings import Settings


class AzureDouble:
    provider = AudioProvider.AZURE
    provider_sdk_version = "fixture"

    def __init__(self):
        self.calls = 0
        self.interrupt = False
        self.frames = 3
        self.failures = 0

    def synthesize(self, **kwargs):
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise ValueError("provider failure")
        if self.interrupt:
            raise KeyboardInterrupt()
        payload = (bytes.fromhex("fff364c0") + bytes(140)) * self.frames
        kwargs["output_path"].write_bytes(payload)
        return AudioSynthesisResponse(
            storage_path=kwargs["output_path"], byte_size=len(payload), duration_ms=self.frames * 24
        )


@pytest.fixture
def setup_audio(tmp_path):
    voice = "ko-KR-SunHi:DragonHDLatestNeural"
    budget = KoreanProviderBudget(
        max_attempts=1,
        max_input_tokens=4096,
        max_output_tokens=0,
        max_total_tokens=4096,
        max_estimated_cost_usd=0.1,
        max_latency_ms=60000,
        timeout_seconds=60,
        max_batch_items=1,
        max_concurrency=1,
    )
    policy = KoreanProviderPolicy(
        routes=tuple(
            KoreanProviderRoute(
                task=task,
                provider="azure-speech"
                if task in {KoreanProviderTask.WORD_AUDIO, KoreanProviderTask.SENTENCE_AUDIO}
                else "disabled",
                model=voice
                if task in {KoreanProviderTask.WORD_AUDIO, KoreanProviderTask.SENTENCE_AUDIO}
                else None,
                budget=budget,
                cache_namespace=f"grammar-{task.value}",
                response_schema_sha256="a" * 64,
            )
            for task in KoreanProviderTask
        )
    )
    profile = KoreanVoiceProfile(
        voice_id=voice,
        locale="ko-KR",
        region="eastus",
        provider_sdk_version="fixture",
        catalog_receipt_sha256="a" * 64,
        profile_authority_sha256="b" * 64,
        profile_sha256="c" * 64,
        provider_policy_sha256=policy.policy_sha256,
        usage_scope=("ordinary-grammar-word-audio", "ordinary-grammar-sentence-audio"),
    )
    profile = profile.model_copy(
        update={
            "profile_sha256": canonical_json_sha256(
                profile.model_dump(mode="json", exclude={"profile_sha256"})
            )
        }
    )
    adapter = AzureDouble()
    service = KoreanProfileAudioSynthesisService(
        profile=profile,
        provider_policy=policy,
        adapter=adapter,
        source_type="grammar",
        provider_call_logger=SimpleNamespace(insert=lambda record: None),
        settings=Settings(
            _env_file=None,
            audio_provider="azure",
            audio_fallback_providers=(),
            azure_speech_region="eastus",
            audio_storage_dir=tmp_path / "media",
            korean_azure_tts_usd_per_million_characters=22,
            korean_azure_tts_pricing_voice_id=voice,
        ),
    )
    source = tmp_path / "source.json"
    source.write_text('{"reviewed":true}')
    return service, adapter, source


def _plan(setup_audio):
    service, _, source = setup_audio
    return grammar_audio.plan_grammar_audio(
        service=service,
        rows=[
            {"entry_id": "g0.copula", "role": role, "text": "학생이에요."}
            for role in ("word", "sentence")
        ],
        source_files=[source],
    )


def _authorization(plan):
    return {
        "authorized": True,
        "plan_sha256": plan["plan_sha256"],
        "max_estimated_cost_usd": plan["max_estimated_cost_usd"],
        "max_provider_calls": plan["unique_provider_requests"],
    }


def test_plan_deduplicates_transport_but_preserves_role_identity(setup_audio):
    plan = _plan(setup_audio)
    assert plan["role_count"] == 2
    assert plan["unique_provider_requests"] == 1
    assert plan["max_concurrency"] == 1
    assert (
        len({row["prepared"]["provenance"]["synthesis_request_sha256"] for row in plan["roles"]})
        == 2
    )
    assert plan["source_files"][0]["sha256"] == sha256(setup_audio[2].read_bytes()).hexdigest()
    assert plan["max_estimated_cost_usd"] > 6 * 22 / 1_000_000


def test_resume_reuses_media_and_retains_pending_acoustic_review(setup_audio, tmp_path):
    service, adapter, _ = setup_audio
    plan = _plan(setup_audio)
    kwargs = dict(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    first = grammar_audio.run_grammar_audio(**kwargs)
    second = grammar_audio.run_grammar_audio(**kwargs)
    assert adapter.calls == 1
    assert first == second
    assert first["status"] == "automated_integrity_passed"
    assert first["acoustic_review_status"] == "not_reviewed"
    assert len(first["roles"]) == 2
    assert len({row["media_sha256"] for row in first["roles"]}) == 1
    assert first["roles"][0]["audio_asset"]["asset_kind"] == "word"
    assert first["roles"][1]["audio_asset"]["asset_kind"] == "sentence"


@pytest.mark.parametrize("problem", ["disabled", "budget", "calls", "source", "plan"])
def test_invalid_authority_or_drift_makes_no_provider_calls(setup_audio, tmp_path, problem):
    service, adapter, source = setup_audio
    plan = _plan(setup_audio)
    authority = _authorization(plan)
    if problem == "disabled":
        authority["authorized"] = False
    if problem == "budget":
        authority["max_estimated_cost_usd"] = 0
    if problem == "calls":
        authority["max_provider_calls"] = 0
    if problem == "source":
        source.write_text("changed")
    if problem == "plan":
        plan["roles"][0]["text"] = "다르다"
    with pytest.raises(ValueError):
        grammar_audio.run_grammar_audio(
            plan=plan, service=service, state_dir=tmp_path / "state", authorization=authority
        )
    assert adapter.calls == 0


def test_interruption_reserves_call_and_blocks_automatic_replay(setup_audio, tmp_path):
    service, adapter, _ = setup_audio
    plan = _plan(setup_audio)
    kwargs = dict(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    adapter.interrupt = True
    with pytest.raises(KeyboardInterrupt):
        grammar_audio.run_grammar_audio(**kwargs)
    adapter.interrupt = False
    with pytest.raises(ValueError, match="recovery required"):
        grammar_audio.run_grammar_audio(**kwargs)
    assert adapter.calls == 1


def test_corrupt_cached_media_never_silently_spends_again(setup_audio, tmp_path):
    from pathlib import Path

    service, adapter, _ = setup_audio
    plan = _plan(setup_audio)
    kwargs = dict(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    result = grammar_audio.run_grammar_audio(**kwargs)
    Path(result["roles"][0]["audio_asset"]["provenance"]["storage_path"]).write_bytes(b"bad")
    with pytest.raises(ValueError, match="recovery required"):
        grammar_audio.run_grammar_audio(**kwargs)
    assert adapter.calls == 1


def test_telemetry_is_durable_for_repository_dataclass(tmp_path):
    from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate

    target = tmp_path / "calls.jsonl"
    logger = grammar_audio.GrammarAudioCallLogger(target)
    logger.insert(
        ProviderCallLogCreate(
            operation="word_audio", provider="azure-speech", status="success", estimated_cost=0.001
        )
    )
    assert json.loads(target.read_text())["estimated_cost"] == 0.001


@pytest.mark.parametrize("seconds_cap", [8, 15])
def test_asr_compares_exact_bytes_without_granting_pronunciation_approval(
    setup_audio, tmp_path, seconds_cap
):
    service, _, _ = setup_audio
    plan = _plan(setup_audio)
    manifest = grammar_audio.run_grammar_audio(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    calls = []

    def recognize(**kwargs):
        calls.append(kwargs)
        assert kwargs["wav_bytes"].startswith(b"RIFF")
        return {
            "RecognitionStatus": "Success",
            "NBest": [{"Lexical": "학생이에요", "Confidence": 0.98}],
        }

    authority = {
        "authorized": True,
        "manifest_sha256": canonical_json_sha256(manifest),
        "max_calls": 1,
        "max_estimated_cost_usd": seconds_cap / 3600,
        "max_audio_seconds": seconds_cap,
    }
    kwargs = dict(
        manifest=manifest,
        mode="asr",
        state_dir=tmp_path / "asr",
        authorization=authority,
        requester=recognize,
    )
    first = grammar_audio.analyze_grammar_audio(**kwargs)
    assert grammar_audio.analyze_grammar_audio(**kwargs) == first
    assert len(calls) == 1
    assert first["items"][0]["transcript_matches"] is True
    assert first["acoustic_review_status"] == "not_reviewed"
    assert first["items"][0]["signal"]["rms"] == 0
    assert first["items"][0]["signal"]["integrity_passed"] is False


def test_asr_failure_is_reserved_and_not_retried(setup_audio, tmp_path):
    service, _, _ = setup_audio
    plan = _plan(setup_audio)
    manifest = grammar_audio.run_grammar_audio(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    count = []

    def recognize(**kwargs):
        count.append(1)
        raise TimeoutError("private provider diagnostics")

    kwargs = dict(
        manifest=manifest,
        mode="asr",
        state_dir=tmp_path / "asr",
        authorization={
            "authorized": True,
            "manifest_sha256": canonical_json_sha256(manifest),
            "max_calls": 1,
            "max_estimated_cost_usd": 15 / 3600,
        },
        requester=recognize,
    )
    with pytest.raises(ValueError, match="recovery required"):
        grammar_audio.analyze_grammar_audio(**kwargs)
    with pytest.raises(ValueError, match="recovery required"):
        grammar_audio.analyze_grammar_audio(**kwargs)
    assert len(count) == 1
    state = json.loads((tmp_path / "asr/state.json").read_text())
    assert next(iter(state["requests"].values()))["error_code"] == "timeout"


def test_azure_free_asr_never_receives_reference_and_pa_disables_paid_prosody(monkeypatch):
    import base64
    import io

    requests = []

    def open_request(request, timeout):
        requests.append(request)
        assert timeout == 30
        assert request.full_url.startswith("https://eastus.stt.speech.microsoft.com/")
        return io.BytesIO(b'{"RecognitionStatus":"Success","NBest":[]}')

    monkeypatch.setattr(grammar_audio, "urlopen", open_request)
    client = grammar_audio.AzureGrammarAudioAnalysis(
        SimpleNamespace(azure_speech_region="eastus", azure_speech_key="offline-fixture")
    )
    client(wav_bytes=b"RIFF-fixture", mode="asr", reference_text="학생")
    assert requests[0].get_header("Pronunciation-assessment") is None
    assert "학생" not in requests[0].full_url
    client(wav_bytes=b"RIFF-fixture", mode="pronunciation", reference_text="학생")
    params = json.loads(base64.b64decode(requests[1].get_header("Pronunciation-assessment")))
    assert params["ReferenceText"] == "학생"
    assert params["EnableProsodyAssessment"] is False
    assert params["Granularity"] == "Phoneme"


def test_analysis_eight_second_cap_blocks_long_media_before_paid_request(setup_audio, tmp_path):
    service, adapter, _ = setup_audio
    adapter.frames = 375  # A fully decodable nine-second MP3.
    plan = _plan(setup_audio)
    manifest = grammar_audio.run_grammar_audio(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )
    calls = []
    with pytest.raises(ValueError, match="duration exceeds authorized budget"):
        grammar_audio.analyze_grammar_audio(
            manifest=manifest,
            mode="asr",
            state_dir=tmp_path / "asr",
            requester=lambda **kwargs: calls.append(kwargs),
            authorization={
                "authorized": True,
                "manifest_sha256": canonical_json_sha256(manifest),
                "max_calls": 1,
                "max_audio_seconds": 8,
                "max_estimated_cost_usd": 8 / 3600,
            },
        )
    assert calls == []


def test_batch_can_finish_independent_requests_without_replaying_failed_one(setup_audio, tmp_path):
    service, adapter, source = setup_audio
    plan = grammar_audio.plan_grammar_audio(
        service=service,
        source_files=[source],
        rows=[
            {"entry_id": "g0.first", "role": "word", "text": "학생"},
            {"entry_id": "g0.second", "role": "word", "text": "친구"},
        ],
    )
    adapter.failures = 1
    kwargs = dict(
        plan=plan,
        service=service,
        state_dir=tmp_path / "state",
        authorization=_authorization(plan),
        continue_after_failure=True,
    )
    result = grammar_audio.run_grammar_audio(**kwargs)
    assert result["status"] == "blocked_uncertainty"
    assert len(result["blocked_transports"]) == 1
    assert len(result["roles"]) == 1
    assert result["roles"][0]["entry_id"] == "g0.second"
    assert grammar_audio.run_grammar_audio(**kwargs) == result
    assert adapter.calls == 2


@pytest.fixture
def two_audio_manifest(setup_audio, tmp_path):
    service, _, source = setup_audio
    plan = grammar_audio.plan_grammar_audio(
        service=service,
        source_files=[source],
        rows=[
            {"entry_id": "g0.first", "role": "word", "text": "학생"},
            {"entry_id": "g0.second", "role": "word", "text": "친구"},
        ],
    )
    return grammar_audio.run_grammar_audio(
        plan=plan, service=service, state_dir=tmp_path / "state", authorization=_authorization(plan)
    )


@pytest.mark.parametrize("first_unknown", [False, True])
@pytest.mark.parametrize("limiting_field", ["calls", "cost"])
def test_analysis_disjoint_resume_counts_all_reservations(
    two_audio_manifest, tmp_path, first_unknown, limiting_field
):
    manifest = two_audio_manifest
    keys = [row["transport_sha256"] for row in manifest["roles"]]
    calls = []

    def recognize(**kwargs):
        calls.append(kwargs)
        if first_unknown:
            raise TimeoutError()
        return {"RecognitionStatus": "Success", "DisplayText": "학생"}

    kwargs = dict(
        manifest=manifest,
        mode="asr",
        state_dir=tmp_path / "asr",
        requester=recognize,
        authorization={
            "authorized": True,
            "manifest_sha256": canonical_json_sha256(manifest),
            "max_calls": 1 if limiting_field == "calls" else 2,
            "max_estimated_cost_usd": (30 if limiting_field == "calls" else 15) / 3600,
        },
    )
    if first_unknown:
        with pytest.raises(ValueError, match="recovery required"):
            grammar_audio.analyze_grammar_audio(**kwargs, selected_transports=keys[:1])
    else:
        grammar_audio.analyze_grammar_audio(**kwargs, selected_transports=keys[:1])
    with pytest.raises(ValueError, match="cumulative analysis budget"):
        grammar_audio.analyze_grammar_audio(**kwargs, selected_transports=keys[1:])
    assert len(calls) == 1


def test_analysis_authorization_cannot_change_in_existing_journal(two_audio_manifest, tmp_path):
    manifest = two_audio_manifest
    keys = [row["transport_sha256"] for row in manifest["roles"]]
    calls = []
    authority = {
        "authorized": True,
        "manifest_sha256": canonical_json_sha256(manifest),
        "max_calls": 1,
        "max_estimated_cost_usd": 15 / 3600,
    }

    def recognize(**kwargs):
        calls.append(kwargs)
        return {"RecognitionStatus": "Success", "DisplayText": "학생"}

    kwargs = dict(manifest=manifest, mode="asr", state_dir=tmp_path / "asr", requester=recognize)
    grammar_audio.analyze_grammar_audio(
        **kwargs, authorization=authority, selected_transports=keys[:1]
    )
    expanded = {**authority, "max_calls": 2, "max_estimated_cost_usd": 30 / 3600}
    with pytest.raises(ValueError, match="authorization drift"):
        grammar_audio.analyze_grammar_audio(
            **kwargs, authorization=expanded, selected_transports=keys[1:]
        )
    assert len(calls) == 1


def test_analysis_resume_report_accounts_for_complete_and_unknown_calls(
    two_audio_manifest, tmp_path
):
    manifest = two_audio_manifest
    keys = [row["transport_sha256"] for row in manifest["roles"]]
    attempts = []

    def recognize(**kwargs):
        attempts.append(kwargs)
        if len(attempts) == 1:
            raise TimeoutError()
        return {"RecognitionStatus": "Success", "DisplayText": "친구"}

    kwargs = dict(
        manifest=manifest,
        mode="asr",
        state_dir=tmp_path / "asr",
        requester=recognize,
        authorization={
            "authorized": True,
            "manifest_sha256": canonical_json_sha256(manifest),
            "max_calls": 2,
            "max_estimated_cost_usd": 30 / 3600,
        },
    )
    with pytest.raises(ValueError, match="recovery required"):
        grammar_audio.analyze_grammar_audio(**kwargs, selected_transports=keys[:1])
    report = grammar_audio.analyze_grammar_audio(**kwargs, selected_transports=keys[1:])
    assert report["provider_call_count"] == 2
    assert report["estimated_cost_usd"] == pytest.approx(16 / 3600)
    assert report["max_cost_usd"] == pytest.approx(30 / 3600)
    assert report["unresolved_requests"] == [keys[0]]
    assert len(attempts) == 2


def test_prosody_repair_has_explicit_profile_and_preserves_exact_text(setup_audio, tmp_path):
    from xml.etree import ElementTree

    from multilang.services.azure_speech_adapter import build_azure_ssml

    service, adapter, source = setup_audio
    payload = {
        **service.profile.model_dump(mode="json"),
        "profile_policy_version": "korean-grammar-prosody-repair-v1",
        "ssml_policy": "bounded-prosody-repair",
        "repair_text": "여기 학교예요.",
        "pause_after_text": "여기",
        "rate": "-20%",
        "pause_ms": 200,
    }
    payload["profile_sha256"] = canonical_json_sha256(
        {key: value for key, value in payload.items() if key != "profile_sha256"}
    )
    profile = grammar_audio.KoreanGrammarProsodyProfile.model_validate(payload)
    runtime = grammar_audio.KoreanGrammarProsodyRepairService(
        profile=profile,
        provider_policy=service.policy,
        settings=service.settings,
        adapter=adapter,
        provider_call_logger=service.logger,
        source_type="grammar",
    )
    rows = [
        {"entry_id": "g0.predicate-final", "role": role, "text": "여기 학교예요."}
        for role in ("word", "sentence")
    ]
    plan = grammar_audio.plan_grammar_audio(service=runtime, rows=rows, source_files=[source])
    prepared = plan["requests"][0]["prepared"]
    ssml = prepared["normalized_input"]["ssml_text"]
    assert build_azure_ssml(text=ssml, locale=profile.locale, voice_id=profile.voice_id) == ssml
    assert "".join(ElementTree.fromstring(ssml).itertext()) == "여기 학교예요."
    assert '<prosody rate="-20%">' in ssml and '<break time="200ms"' in ssml
    assert prepared["provenance"]["voice_profile_sha256"] != service.profile.profile_sha256
    assert prepared["normalized_input"]["tts_text"] == "여기 학교예요."
    assert plan["unique_provider_requests"] == 1
    assert adapter.calls == 0
    with pytest.raises(ValueError, match="repair text scope"):
        grammar_audio.plan_grammar_audio(
            service=runtime, rows=[{**rows[0], "text": "여기 집이에요."}], source_files=[source]
        )
    manifest = grammar_audio.run_grammar_audio(
        plan=plan,
        service=runtime,
        state_dir=tmp_path / "repair",
        authorization=_authorization(plan),
    )
    assert len(manifest["roles"]) == 2 and adapter.calls == 1
