"""Personal audio uses explicit scope, immutable pending media, and evidence-bound review."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.audio import AudioAssetKind, AudioProvider, AudioReviewStatus
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean import canonical_json_sha256
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.review import AudioReviewEvidence
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
from multilang.repositories.text_repository import TextRepository
from multilang.services.audio_synthesis import AudioSynthesisResponse
from multilang.services.korean_audio import build_korean_tts_input
from multilang.services.korean_learning_runtime import KoreanLearningRuntime
from multilang.services.korean_personal_audio import (
    PersonalAudioAuthority,
    PersonalAudioRecoveryAuthority,
    PersonalAudioReviewAuthority,
    PersonalVoiceAuthority,
    bind_personal_voice_profile,
    recover_personal_audio,
    regenerate_personal_audio,
    reject_personal_audio,
    review_personal_audio,
)
from multilang.settings import Settings


def digest(value):
    return sha256(value.encode()).hexdigest()


VOICE = "ko-KR-SunHiNeural"
MP3 = (bytes.fromhex("fff364c0") + bytes(140)) * 12


class AzureDouble:
    provider = AudioProvider.AZURE
    provider_sdk_version = "offline-fixture"

    def __init__(self, *, unknown=False):
        self.calls = []
        self.unknown = unknown

    def synthesize(self, **kwargs):
        self.calls.append(kwargs)
        if self.unknown:
            raise TimeoutError("private source filename and private provider diagnostic")
        kwargs["output_path"].write_bytes(MP3)
        return AudioSynthesisResponse(storage_path=kwargs["output_path"], byte_size=len(MP3), duration_ms=288)


@pytest.fixture
def personal(tmp_path):
    url = f"sqlite+pysqlite:///{tmp_path / 'personal.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    # Exercise the real migration's append-only guards, not only ORM metadata.
    import runpy
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    migration = runpy.run_path(str(Path(__file__).resolve().parents[2]
        / "alembic/versions/20260828_19_grammar_personal_sources.py"))
    with engine.begin() as connection, Operations.context(MigrationContext.configure(connection)):
        migration["_create_append_only_guards"]()
    session = Session(engine)
    settings = Settings(_env_file=None, database_url=url, audio_storage_dir=tmp_path / "audio",
        azure_speech_region="koreacentral", audio_provider="azure", audio_fallback_providers=[],
        korean_azure_tts_usd_per_million_characters=1, korean_azure_tts_pricing_voice_id=VOICE)
    runtime = KoreanLearningRuntime(session, settings=settings)
    job = JobRepository(session).create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
        run_key="personal-audio", source_fingerprint="fixture", total_items=1)
    budget = KoreanProviderBudget(max_attempts=1, max_input_tokens=4096, max_output_tokens=0,
        max_total_tokens=4096, max_estimated_cost_usd=1, max_latency_ms=60000,
        timeout_seconds=60, max_batch_items=1, max_concurrency=1)
    policy = KoreanProviderPolicy(routes=tuple(KoreanProviderRoute(task=task,
        provider="azure-speech" if task.value.endswith("audio") else "fixture-ai",
        model=VOICE if task.value.endswith("audio") else "fixture-judge",
        budget=budget, cache_namespace=task.value, response_schema_sha256=digest(task.value)) for task in KoreanProviderTask))
    job.korean_provider_policy = policy.model_dump(mode="json")
    job.korean_provider_policy_sha256 = policy.policy_sha256
    session.commit()
    lexical = LexicalRepository(session)
    lexical.upsert_candidate(job_id=job.id, run_key=job.run_key, item_key="row-1", source_type="word-list",
        normalized_source="집", candidate=LexicalCardCandidate(submitted_form="집", display_form="집", lemma="집",
            lemma_key="ko:home", definitions_html="casa", definition_language="pt", translation_target_language="pt",
            grounding_status=GroundingStatus.GROUNDED, provenance=LexicalProvenance(source="private-file-name")))
    candidate = lexical.get_candidate_for_item(job.id, "row-1")
    from multilang.domain.korean import (
        KoreanAnalyzerFingerprint,
        KoreanLexicalIdentity,
        KoreanSignatureItem,
    )
    fingerprint = KoreanAnalyzerFingerprint(analyzer_name="kiwi", analyzer_package_version="0.20.4",
        model_package_version="0.20.4-model", model_type="cong", enabled_dialects="standard",
        num_workers=1, integrate_allomorph=True, top_n=2, split_complex=False,
        compatible_jamo=False, normalize_coda=False, z_coda=False, typos=None,
        oov_handling="chr", policy_version="kiwi-top2-consensus-v1")
    identity = KoreanLexicalIdentity(submitted_form="집", canonical_nfc="집", lemma="집", part_of_speech="NNG",
        sense_id="house", register="standard", morpheme_signature=(KoreanSignatureItem(form="집", pos="NNG"),),
        analyzer_fingerprint=fingerprint, status="resolved")
    candidate.korean_identity = identity.model_dump(mode="json")
    candidate.lemma_key = identity.lexical_key
    session.commit()
    TextRepository(session).upsert_text_record(TextQualityRecord(job_id=job.id, item_key="row-1", lexical_candidate_id=candidate.id,
        example_sentence="집에 가요.", translation_text="Vou para casa.", generation_status=TextGenerationStatus.GENERATED,
        review_status=ReviewStatus.ACCEPTED, validation_status=ValidationStatus.PASSED, confidence_label=ConfidenceLabel.HIGH,
        sentence_provenance=TextProvenance(source="fixture"), translation_provenance=TextProvenance(source="fixture"),
        text_review_receipt_sha256=digest("text-review")))
    receipt = _review_current_text(runtime, job.id, "initial-text-review")
    catalog = {"catalog_locale": "ko-KR", "voices": [{"voice_id": VOICE, "locale": "ko-KR", "region": "koreacentral"}],
        "catalog_query_count": 1, "synthesis_attempt_count": 0}
    catalog_hash = canonical_json_sha256(catalog)
    voice_authority = PersonalVoiceAuthority(source_types=("word-list", "kindle-highlights"), voice_id=VOICE,
        region="koreacentral", catalog_result_file_sha256=catalog_hash,
        catalog_content_sha256=canonical_json_sha256({"catalog_locale": "ko-KR", "voices": catalog["voices"]}),
        provider_policy_sha256=policy.policy_sha256)
    binding = bind_personal_voice_profile(authority=voice_authority, catalog=catalog,
        catalog_file_sha256=catalog_hash, provider_policy=policy)
    normalized = build_korean_tts_input("집", asset_kind=AudioAssetKind.WORD, profile=binding.profile)
    authority = PersonalAudioAuthority(job_id=job.id, item_id="row-1", source_type="word-list", field="word_audio",
        actor_id="operator", request_id="generate-1", expected_pointer_version=0,
        voice_binding_sha256=binding.binding_sha256, provider_policy_sha256=policy.policy_sha256,
        spoken_text_sha256=digest("집"), text_review_receipt_sha256=receipt,
        synthesis_request_sha256=normalized.synthesis_request_sha256,
        audio_root_sha256=digest(str(settings.audio_storage_dir.resolve())),
        pricing_usd_per_million_characters=1, max_estimated_cost_usd=1)
    kwargs = dict(authority=authority, binding=binding, catalog=catalog, catalog_file_sha256=catalog_hash, provider_policy=policy)
    yield SimpleNamespace(runtime=runtime, job_id=job.id, kwargs=kwargs, settings=settings, session=session)
    session.close()
    engine.dispose()


def _review_current_text(runtime, job_id, request_id):
    import runpy
    from pathlib import Path

    from multilang.services import korean_personal_text_review
    runtime._snapshot_fields(job_id, "row-1")
    snapshot = korean_personal_text_review.prepare_personal_text_evidence(runtime, job_id=job_id, item_id="row-1")
    fixture_builder = runpy.run_path(str(Path(__file__).with_name("test_korean_personal_text_review.py")))["_evidence"]
    result = korean_personal_text_review.apply_personal_text_evidence(runtime, job_id=job_id, item_id="row-1",
        evidence=fixture_builder(snapshot), actor_id="operator", request_id=request_id)
    assert korean_personal_text_review.personal_text_review_current(runtime.session, job_id, "row-1")
    return result["receipt_sha256"]


def generate(personal, adapter=None):
    adapter = adapter or AzureDouble()
    result = regenerate_personal_audio(personal.runtime, **personal.kwargs, adapter=adapter)
    return result, adapter


def review_inputs(personal, result):
    evidence = AudioReviewEvidence(evidence_id="review-1", status="ai_acoustic_review_passed",
        policy_sha256=personal.kwargs["provider_policy"].policy_sha256, integrity_sha256=result["integrity_sha256"],
        request_sha256=result["synthesis_request_sha256"], profile_sha256=personal.kwargs["binding"].profile.profile_sha256,
        artifact_sha256=result["artifact_sha256"], final_path=result["relative_path"],
        revision_content_sha256=result["revision_content_sha256"], acoustic_review_sha256=digest("acoustic-review"))
    authority = PersonalAudioReviewAuthority(job_id=personal.job_id, item_id="row-1", field="word_audio",
        revision_id=result["revision_id"], expected_pointer_version=result["pointer_version"], actor_id="reviewer",
        request_id="review-1", generation_authority_sha256=personal.kwargs["authority"].authority_sha256,
        review_evidence_sha256=canonical_json_sha256(evidence.model_dump(mode="json")))
    return authority, evidence


def test_personal_audio_is_pending_replay_free_and_exact_review_promotes(personal):
    result, adapter = generate(personal)
    asset = AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD)
    assert asset.provenance.audio_review_status is AudioReviewStatus.SYNTHESIZED_PENDING
    replay, _ = generate(personal, adapter)
    assert replay["replayed"] and len(adapter.calls) == 1
    authority, evidence = review_inputs(personal, result)
    reviewed = review_personal_audio(personal.runtime, authority=authority, evidence=evidence)
    assert reviewed["status"] == "approved"
    assert AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD).ready_for_korean_final_export
    assert review_personal_audio(personal.runtime, authority=authority, evidence=evidence)["replayed"]
    audit = json.dumps(personal.runtime._job(personal.job_id).resume_state, ensure_ascii=False)
    assert "private-file-name" not in audit and "집" not in audit
    imported = list(personal.runtime._job(personal.job_id).resume_state["korean_personal_audio_reviews"].values())
    assert imported[0]["evidence"] == evidence.model_dump(mode="json")


@pytest.mark.parametrize("change", ["scope", "budget", "stale", "text", "request"])
def test_personal_audio_preflight_refuses_before_provider(personal, change):
    updates = {"scope": {"source_type": "kindle-highlights"}, "budget": {"max_estimated_cost_usd": 0},
        "stale": {"expected_pointer_version": 7}, "text": {"spoken_text_sha256": digest("drift")},
        "request": {"synthesis_request_sha256": digest("drift")}}[change]
    personal.kwargs["authority"] = personal.kwargs["authority"].model_copy(update=updates)
    adapter = AzureDouble()
    with pytest.raises(ValueError):
        generate(personal, adapter)
    assert not adapter.calls


def test_personal_audio_unknown_outcome_never_replays_paid_attempt(personal):
    adapter = AzureDouble(unknown=True)
    for _ in range(2):
        with pytest.raises(ValueError, match="recovery_required"):
            generate(personal, adapter)
    assert len(adapter.calls) == 1
    assert "private" not in json.dumps(personal.runtime._job(personal.job_id).resume_state)


@pytest.mark.parametrize("drift", ["bytes", "text", "request", "profile", "manual"])
def test_personal_audio_review_rejects_drift(personal, drift):
    result, _ = generate(personal)
    authority, evidence = review_inputs(personal, result)
    if drift == "bytes":
        (personal.settings.audio_storage_dir / result["relative_path"]).write_bytes(b"invalid")
    elif drift == "text":
        candidate = LexicalRepository(personal.session).get_candidate_for_item(personal.job_id, "row-1")
        candidate.lemma = "학교"
        personal.session.commit()
    else:
        field = {"request": "request_sha256", "profile": "profile_sha256", "manual": "status"}[drift]
        evidence = evidence.model_copy(update={field: "automated_integrity_passed" if drift == "manual" else digest("drift")})
        authority = authority.model_copy(update={"review_evidence_sha256": canonical_json_sha256(evidence.model_dump(mode="json"))})
    with pytest.raises(ValueError):
        review_personal_audio(personal.runtime, authority=authority, evidence=evidence)
    assert not AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD).ready_for_korean_final_export


def test_personal_audio_preserves_approved_asset(personal):
    result, _ = generate(personal)
    authority, evidence = review_inputs(personal, result)
    review_personal_audio(personal.runtime, authority=authority, evidence=evidence)
    personal.kwargs["authority"] = personal.kwargs["authority"].model_copy(update={
        "request_id": "generate-2", "expected_pointer_version": result["pointer_version"] + 1})
    adapter = AzureDouble()
    with pytest.raises(ValueError, match="approved"):
        generate(personal, adapter)
    assert not adapter.calls


def test_explicit_rejection_allows_new_immutable_revision_without_deleting_old_media(personal):
    result, adapter = generate(personal)
    authority, evidence = review_inputs(personal, result)
    reviewed = review_personal_audio(personal.runtime, authority=authority, evidence=evidence)
    rejected = reject_personal_audio(personal.runtime, job_id=personal.job_id, item_id="row-1", field="word_audio",
        revision_id=result["revision_id"], expected_pointer_version=reviewed["pointer_version"], actor_id="operator", request_id="reject-1")
    asset = AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD)
    assert asset.provenance.audio_review_status is AudioReviewStatus.REJECTED
    personal.kwargs["authority"] = personal.kwargs["authority"].model_copy(update={
        "request_id": "generate-2", "expected_pointer_version": rejected["pointer_version"]})
    second, _ = generate(personal, adapter)
    assert len(adapter.calls) == 2 and second["relative_path"] != result["relative_path"]
    assert (personal.settings.audio_storage_dir / result["relative_path"]).read_bytes() == MP3
    assert not AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD).ready_for_korean_final_export
    entries = list(personal.runtime._job(personal.job_id).resume_state["korean_personal_audio"].values())
    assert entries[-1]["before"]["artifact_sha256"] == result["artifact_sha256"]
    assert entries[-1]["after"]["revision_sha256"] != entries[-1]["before"]["revision_sha256"]


def test_unknown_outcome_recovery_requires_ack_then_only_new_request_can_attempt(personal):
    from multilang.services.generation_leases import GenerationLeaseManager
    unknown = AzureDouble(unknown=True)
    with pytest.raises(ValueError, match="recovery_required"):
        generate(personal, unknown)
    entry = next(iter(personal.runtime._job(personal.job_id).resume_state["korean_personal_audio"].values()))
    recovery = PersonalAudioRecoveryAuthority(job_id=personal.job_id, item_id="row-1", field="word_audio",
        revision_id=entry["revision_id"], expected_pointer_version=entry["pointer_version"],
        generation_authority_sha256=personal.kwargs["authority"].authority_sha256,
        synthesis_request_sha256=personal.kwargs["authority"].synthesis_request_sha256,
        actor_id="operator", request_id="recover-1", acknowledge_unknown_outcome=True)
    with pytest.raises(ValueError, match="lease_recovery_required"):
        recover_personal_audio(personal.runtime, authority=recovery)
    manager = GenerationLeaseManager(personal.session.get_bind())
    manager.recover(personal.job_id, expected_item_sha256=manager.status(personal.job_id)["inflight_item_sha256"], acknowledge_unknown_outcome=True)
    recovered = recover_personal_audio(personal.runtime, authority=recovery)
    assert recover_personal_audio(personal.runtime, authority=recovery)["replayed"]
    with pytest.raises(ValueError, match="request_abandoned"):
        generate(personal, unknown)
    personal.kwargs["authority"] = personal.kwargs["authority"].model_copy(update={
        "request_id": "generate-2", "expected_pointer_version": recovered["pointer_version"]})
    _, fresh = generate(personal)
    assert len(unknown.calls) == len(fresh.calls) == 1


def test_frequency_profile_cannot_be_reused_as_personal_authority(personal):
    binding = personal.kwargs["binding"]
    personal.kwargs["binding"] = binding.model_copy(update={"profile": binding.profile.model_copy(update={
        "usage_scope": ("ordinary-frequency-word-audio", "ordinary-frequency-sentence-audio")})})
    adapter = AzureDouble()
    with pytest.raises(ValueError, match="voice_binding_drift"):
        generate(personal, adapter)
    assert not adapter.calls


def test_personal_audio_lease_blocks_second_worker_before_provider(personal):
    from multilang.services.generation_leases import GenerationLeaseManager
    personal.session.rollback()
    with GenerationLeaseManager(personal.session.get_bind()).hold(personal.job_id):
        adapter = AzureDouble()
        with pytest.raises(ValueError, match="already running"):
            generate(personal, adapter)
        assert not adapter.calls


def test_highlight_sentence_audio_sends_only_generated_sentence(personal):
    job = personal.runtime._job(personal.job_id)
    candidate = LexicalRepository(personal.session).get_candidate_for_item(personal.job_id, "row-1")
    job.source_type = candidate.source_type = "kindle-highlights"
    personal.session.commit()
    receipt = _review_current_text(personal.runtime, personal.job_id, "highlight-text-review")
    normalized = build_korean_tts_input("집에 가요.", asset_kind=AudioAssetKind.SENTENCE, profile=personal.kwargs["binding"].profile)
    personal.kwargs["authority"] = personal.kwargs["authority"].model_copy(update={"source_type": "kindle-highlights",
        "field": "sentence_audio", "spoken_text_sha256": digest("집에 가요."),
        "text_review_receipt_sha256": receipt,
        "synthesis_request_sha256": normalized.synthesis_request_sha256})
    _, adapter = generate(personal)
    assert len(adapter.calls) == 1 and "집에 가요." in adapter.calls[0]["ssml_text"]
    assert "private" not in str(adapter.calls)


def test_manual_audio_approval_without_evidence_is_refused(personal):
    result, _ = generate(personal)
    with pytest.raises(ValueError, match="audio_review_evidence_required"):
        personal.runtime.review_decide(job_id=personal.job_id, item_id="row-1", field="word_audio",
            revision_id=result["revision_id"], expected_pointer_version=result["pointer_version"],
            actor_id="operator", request_id="manual-approve", decision="approved")


def test_cli_binds_generates_promotes_and_rejects_with_explicit_files(personal, tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from multilang.cli import create_app
    from multilang.services import korean_personal_audio

    files = {name: tmp_path / f"{name}.json" for name in ("catalog", "voice", "policy", "profile", "generation", "review", "evidence")}
    files["catalog"].write_text(json.dumps(personal.kwargs["catalog"], ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    files["voice"].write_text(personal.kwargs["binding"].authority.model_dump_json())
    files["policy"].write_text(personal.kwargs["provider_policy"].model_dump_json())
    files["generation"].write_text(personal.kwargs["authority"].model_dump_json())
    runner = CliRunner()
    app = create_app(korean_learning_service=personal.runtime)
    bound = runner.invoke(app, ["korean", "review", "bind-audio-profile", "--authority-file", str(files["voice"]),
        "--catalog-file", str(files["catalog"]), "--provider-policy-file", str(files["policy"]), "--output-file", str(files["profile"])])
    assert bound.exit_code == 0, bound.output
    adapter = AzureDouble()
    monkeypatch.setattr(korean_personal_audio, "AzureSpeechAdapter", lambda _: adapter)
    command = ["korean", "review", "regenerate-audio", "--authority-file", str(files["generation"]),
        "--profile-file", str(files["profile"]), "--catalog-file", str(files["catalog"]), "--provider-policy-file", str(files["policy"])]
    generated = runner.invoke(app, command)
    assert generated.exit_code == 0, generated.output
    result = json.loads(generated.output)
    assert runner.invoke(app, command).exit_code == 0 and len(adapter.calls) == 1
    authority, evidence = review_inputs(personal, result)
    files["review"].write_text(authority.model_dump_json())
    files["evidence"].write_text(evidence.model_dump_json())
    reviewed = runner.invoke(app, ["korean", "review", "apply-audio-review", "--authority-file", str(files["review"]),
        "--evidence-file", str(files["evidence"])])
    assert reviewed.exit_code == 0, reviewed.output
    reviewed_payload = json.loads(reviewed.output)
    rejected = runner.invoke(app, ["korean", "review", "reject-audio", "--job-id", personal.job_id, "--item-id", "row-1",
        "--field", "word_audio", "--revision-id", result["revision_id"], "--expected-pointer-version", str(reviewed_payload["pointer_version"]),
        "--actor-id", "operator", "--request-id", "cli-reject"])
    assert rejected.exit_code == 0, rejected.output
    assert not AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD).ready_for_korean_final_export


def test_stale_pointer_during_synthesis_never_publishes_active_projection(personal):
    from sqlalchemy import update

    from multilang.db.models import ReviewCurrentPointerModel

    class ConcurrentAzure(AzureDouble):
        def synthesize(self, **kwargs):
            response = super().synthesize(**kwargs)
            with Session(personal.session.get_bind()) as other, other.begin():
                other.execute(update(ReviewCurrentPointerModel).where(ReviewCurrentPointerModel.job_id == personal.job_id,
                    ReviewCurrentPointerModel.field_name == "word_audio").values(pointer_version=99, review_status="rejected"))
            return response

    adapter = ConcurrentAzure()
    with pytest.raises(ValueError, match="recovery_required"):
        generate(personal, adapter)
    assert len(adapter.calls) == 1
    assert AudioRepository(personal.session).get_asset(personal.job_id, "row-1", AudioAssetKind.WORD) is None


def test_review_cannot_rebind_current_projection_to_different_generation_request(personal):
    from multilang.services.korean_personal_audio import _integrity

    result, _ = generate(personal)
    authority, evidence = review_inputs(personal, result)
    repository = AudioRepository(personal.session)
    asset = repository.get_asset(personal.job_id, "row-1", AudioAssetKind.WORD)
    changed = asset.model_copy(update={
        "normalized_input": asset.normalized_input.model_copy(update={"synthesis_request_sha256": digest("other request")}),
        "provenance": asset.provenance.model_copy(update={"synthesis_request_sha256": digest("other request")}),
    })
    repository.upsert_audio_asset(changed)
    evidence = evidence.model_copy(update={"request_sha256": digest("other request"),
        "integrity_sha256": _integrity(changed, result["relative_path"])})
    authority = authority.model_copy(update={"review_evidence_sha256": canonical_json_sha256(evidence.model_dump(mode="json"))})
    with pytest.raises(ValueError, match="review_evidence_drift"):
        review_personal_audio(personal.runtime, authority=authority, evidence=evidence)


def test_legacy_acceptance_flags_without_current_text_evidence_never_call_azure(personal):
    job = personal.runtime._job(personal.job_id)
    job.resume_state = {key: value for key, value in job.resume_state.items() if key != "korean_personal_text_reviews"}
    personal.session.commit()
    adapter = AzureDouble()
    with pytest.raises(ValueError, match="accepted_text_required"):
        generate(personal, adapter)
    assert not adapter.calls
