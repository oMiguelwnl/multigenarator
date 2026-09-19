"""Authority-bound Korean Azure synthesis, independent of the static voice registry."""

from __future__ import annotations

import json
import math
import os
import unicodedata
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioProvider,
    AudioReviewStatus,
    AudioSynthesisStatus,
)
from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.korean import KoreanFrequencyJobAuthority, canonical_json_sha256
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.domain.text_quality import ReviewStatus, ValidationStatus
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.provider_call_log_repository import (
    ProviderCallLogCreate,
    ProviderCallLogRepository,
)
from multilang.repositories.text_repository import TextRepository
from multilang.repositories.transactions import repository_transaction
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.audio_synthesis import AudioSynthesisBundle
from multilang.services.azure_speech_adapter import AzureSpeechAdapter
from multilang.services.generate_audio_items import GenerateAudioItemsResult
from multilang.services.generation_leases import GenerationLeaseManager
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    KoreanVoiceProfile,
    _canonical_sha256,
    _catalog_voice_mappings,
    _selected_catalog_voice,
    _validate_catalog_result_contract,
    _verify_phase31_for_authority,
    build_korean_audio_asset,
    build_korean_tts_input,
)
from multilang.services.korean_foundation_snapshot_fallback import (
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
)
from multilang.services.korean_frequency import load_korean_final_frequency_entries
from multilang.services.provider_retry import classify_provider_error
from multilang.settings import Settings

_MAX_MEDIA_BYTES = 10 * 1024 * 1024


def _read_json(path: Path) -> tuple[dict, bytes]:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > _MAX_MEDIA_BYTES:
        raise ValueError("Korean audio evidence file is invalid")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Korean audio evidence JSON is invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("Korean audio evidence must be an object")
    return payload, raw


def _artifact_hash(content: bytes) -> str:
    from hashlib import sha256

    return sha256(b"artifact:" + content).hexdigest()


def _mp3_duration(content: bytes) -> int:
    """Check complete 24 kHz/48 kbps mono MPEG-2 Layer III frames, not acoustics."""
    offset = 0
    if content.startswith(b"ID3"):
        if len(content) < 10 or any(value & 0x80 for value in content[6:10]):
            raise ValueError("invalid_media")
        offset = 10 + sum(value << (7 * (3 - index)) for index, value in enumerate(content[6:10]))
        if content[5] & 0x10:
            offset += 10
    frames = 0
    while offset < len(content):
        # ID3v1 is allowed only as the final 128-byte trailer.
        if len(content) - offset == 128 and content[offset : offset + 3] == b"TAG":
            offset += 128
            break
        header = content[offset : offset + 4]
        if (
            len(header) != 4
            or header[0] != 0xFF
            or header[1] & 0xFE != 0xF2
            or header[2] & 0xFC != 0x64
            or header[3] & 0xC0 != 0xC0
        ):
            raise ValueError("invalid_media")
        offset += 144 + ((header[2] >> 1) & 1)
        frames += 1
        if offset > len(content):
            raise ValueError("invalid_media")
    if frames < 2 or offset != len(content):
        raise ValueError("invalid_media")
    return frames * 24


def _validate_profile(profile: KoreanVoiceProfile) -> None:
    if (
        _canonical_sha256(profile.model_dump(mode="json", exclude={"profile_sha256"}))
        != profile.profile_sha256
    ):
        raise ValueError("Korean voice profile hash drift")


class KoreanProfileAudioSynthesisService:
    """Prepare exact requests and persistable pending-review media using an explicit profile."""

    def __init__(
        self,
        *,
        profile: KoreanVoiceProfile,
        provider_policy: KoreanProviderPolicy,
        adapter: object,
        settings: Settings,
        provider_call_logger: object,
        source_type: str = "frequency",
    ) -> None:
        _validate_profile(profile)
        if getattr(adapter, "provider", None) != AudioProvider.AZURE:
            raise ValueError("Korean audio requires an Azure adapter")
        if settings.audio_provider != "azure" or settings.audio_fallback_providers:
            raise ValueError("Korean audio forbids provider fallback")
        if settings.azure_speech_region != profile.region:
            raise ValueError("Korean audio region drift")
        price = settings.korean_azure_tts_usd_per_million_characters
        if (
            not isinstance(price, (int, float))
            or isinstance(price, bool)
            or not math.isfinite(price)
            or price <= 0
            or settings.korean_azure_tts_pricing_voice_id != profile.voice_id
        ):
            raise ValueError("Korean audio requires explicit finite voice-bound pricing")
        for kind in AudioAssetKind:
            if f"ordinary-{source_type}-{kind.value}-audio" not in profile.usage_scope:
                raise ValueError("Korean voice profile does not authorize this source")
            route = provider_policy.route_for(KoreanProviderTask(f"{kind.value}_audio"))
            if (
                not route.enabled
                or route.provider != "azure-speech"
                or route.model != profile.voice_id
            ):
                raise ValueError("Korean audio route does not authorize the selected voice")
        self.profile = profile
        self.policy = provider_policy
        self.adapter = adapter
        self.settings = settings
        self.price_per_million_characters = float(price)
        self.logger = provider_call_logger
        self.sdk_version = getattr(adapter, "provider_sdk_version", None) or version(
            "azure-cognitiveservices-speech"
        )
        self.root = settings.audio_storage_dir.resolve()

    def estimated_cost(self, prepared: AudioAssetRecord) -> float:
        # Full UTF-8 SSML bytes overestimate billable characters, including tags
        # and escaping, without pretending this is invoiced usage or LLM tokens.
        size = len((prepared.normalized_input.ssml_text or "").encode("utf-8"))
        return size * self.price_per_million_characters / 1_000_000

    def _validate_cost(self, prepared: AudioAssetRecord) -> None:
        route = self.policy.route_for(KoreanProviderTask(f"{prepared.asset_kind.value}_audio"))
        cost = self.estimated_cost(prepared)
        if not math.isfinite(cost) or cost <= 0 or cost > route.budget.max_estimated_cost_usd:
            raise ValueError("Korean audio cost budget exceeded")

    def prepare_item_assets(self, *, language, display_word, text_record) -> AudioSynthesisBundle:
        if (
            language is not SupportedLanguage.KO
            or text_record.review_status is not ReviewStatus.ACCEPTED
            or text_record.validation_status is not ValidationStatus.PASSED
        ):
            raise ValueError("Korean audio requires accepted, validated Korean text")
        return AudioSynthesisBundle(
            word_asset=self._prepare(
                text_record.job_id, text_record.item_key, AudioAssetKind.WORD, display_word
            ),
            sentence_asset=self._prepare(
                text_record.job_id,
                text_record.item_key,
                AudioAssetKind.SENTENCE,
                text_record.example_sentence or "",
            ),
        )

    def _prepare(self, job_id, item_key, kind, text) -> AudioAssetRecord:
        normalized = build_korean_tts_input(text, asset_kind=kind, profile=self.profile)
        route = self.policy.route_for(KoreanProviderTask(f"{kind.value}_audio"))
        if (
            len((normalized.ssml_text or normalized.tts_text).encode("utf-8"))
            > route.budget.max_input_tokens
        ):
            raise ValueError("Korean audio input budget exceeded")
        if any(
            "JAMO" in unicodedata.name(char, "") or "HANGUL LETTER" in unicodedata.name(char, "")
            for char in normalized.tts_text
        ):
            raise ValueError("Korean ordinary audio cannot synthesize unexplained jamo")
        path = (
            self.root
            / self.profile.profile_sha256
            / kind.value
            / f"{normalized.synthesis_request_sha256}.mp3"
        )
        asset = build_korean_audio_asset(
            job_id=job_id,
            item_key=item_key,
            asset_kind=kind,
            normalized_input=normalized,
            profile=self.profile,
            storage_path=path,
            media_bytes=b"",
            duration_ms=None,
            fallback_used=False,
        )
        self._validate_cost(asset)
        return asset.model_copy(
            update={
                "provenance": asset.provenance.model_copy(
                    update={
                        "status": AudioSynthesisStatus.PENDING,
                        "artifact_sha256": None,
                        "audio_review_status": AudioReviewStatus.NOT_REVIEWED,
                        "provider_sdk_version": self.sdk_version,
                    }
                )
            }
        )

    def reusable(self, prepared: AudioAssetRecord, existing: AudioAssetRecord | None) -> bool:
        if existing is None:
            return False
        old, new = existing.provenance, prepared.provenance
        if (
            old.status is not AudioSynthesisStatus.SYNTHESIZED
            or old.fallback_used
            or old.audio_review_status
            not in {AudioReviewStatus.SYNTHESIZED_PENDING, AudioReviewStatus.APPROVED}
            or existing.normalized_input.tts_text != prepared.normalized_input.tts_text
            or existing.normalized_input.ssml_text != prepared.normalized_input.ssml_text
        ):
            return False
        for field in (
            "provider",
            "voice_id",
            "locale",
            "format",
            "text_hash",
            "ssml_hash",
            "provider_sdk_version",
            "voice_profile_sha256",
            "catalog_receipt_sha256",
            "synthesis_request_sha256",
        ):
            if getattr(old, field) != getattr(new, field):
                return False
        try:
            path = Path(old.storage_path)
            if (
                path.is_symlink()
                or not path.resolve().is_relative_to(self.root)
                or not path.is_file()
            ):
                return False
            if not 0 < path.stat().st_size <= _MAX_MEDIA_BYTES:
                return False
            content = path.read_bytes()
            measured = inspect_local_mp3(path, expected_byte_size=old.byte_size,
                artifact_hash_prefix=b"artifact:")
            return (
                len(content) == old.byte_size
                and _artifact_hash(content) == old.artifact_sha256
                and measured is not None
                and measured.artifact_sha256 == old.artifact_sha256
                and measured.duration_ms == _mp3_duration(content)
                and abs(_mp3_duration(content) - (old.duration_ms or 0)) <= 100
            )
        except (OSError, ValueError):
            return False

    def synthesize_prepared_asset(self, prepared: AudioAssetRecord) -> AudioAssetRecord:
        self._validate_cost(prepared)
        route = self.policy.route_for(KoreanProviderTask(f"{prepared.asset_kind.value}_audio"))
        attempt = 0
        telemetry_complete = False

        def invoke():
            nonlocal attempt, telemetry_complete
            attempt += 1
            started = perf_counter()
            record = None
            error = None
            try:
                # SSML bytes conservatively bound input size without claiming TTS token usage.
                if (
                    len(
                        (
                            prepared.normalized_input.ssml_text
                            or prepared.normalized_input.tts_text
                        ).encode("utf-8")
                    )
                    > route.budget.max_input_tokens
                ):
                    raise ValueError("Korean audio input budget exceeded")
                parent = Path(prepared.provenance.storage_path).parent
                if not parent.resolve().is_relative_to(self.root):
                    raise ValueError("invalid_media_path")
                parent.mkdir(parents=True, exist_ok=True)
                if not parent.resolve().is_relative_to(self.root):
                    raise ValueError("invalid_media_path")
                with TemporaryDirectory(prefix=".synthesis-", dir=parent) as temporary:
                    target = Path(temporary) / "audio.mp3"
                    response = self.adapter.synthesize(
                        ssml_text=prepared.normalized_input.ssml_text,
                        voice_id=self.profile.voice_id,
                        locale=self.profile.locale,
                        output_path=target,
                        audio_format=self.profile.output_format,
                        timeout_seconds=min(
                            route.budget.timeout_seconds, route.budget.max_latency_ms / 1000
                        ),
                    )
                    if (
                        response.storage_path != target
                        or target.is_symlink()
                        or not target.is_file()
                        or not 0 < target.stat().st_size <= _MAX_MEDIA_BYTES
                        or response.fallback_used
                        or response.provider not in {None, AudioProvider.AZURE}
                        or response.voice_id not in {None, self.profile.voice_id}
                        or response.locale not in {None, self.profile.locale}
                        or response.audio_format not in {None, prepared.provenance.format}
                    ):
                        raise ValueError("invalid_media")
                    content = target.read_bytes()
                    duration = _mp3_duration(content)
                    measured = inspect_local_mp3(target, expected_byte_size=len(content))
                    if (
                        measured is None
                        or measured.duration_ms != duration
                        or response.byte_size != len(content)
                        or not response.duration_ms
                        or abs(response.duration_ms - duration) > 100
                        or int((perf_counter() - started) * 1000) > route.budget.max_latency_ms
                    ):
                        raise ValueError("invalid_media")
                    final = (
                        parent
                        / f"{prepared.provenance.synthesis_request_sha256}-{_artifact_hash(content)}.mp3"
                    )
                    if final.is_symlink():
                        raise ValueError("invalid_media_path")
                    os.replace(target, final)
                    record = build_korean_audio_asset(
                        job_id=prepared.job_id,
                        item_key=prepared.item_key,
                        asset_kind=prepared.asset_kind,
                        normalized_input=prepared.normalized_input,
                        profile=self.profile,
                        storage_path=final,
                        media_bytes=content,
                        duration_ms=duration,
                        fallback_used=False,
                    )
                    record = record.model_copy(
                        update={
                            "provenance": record.provenance.model_copy(
                                update={"provider_sdk_version": self.sdk_version}
                            )
                        }
                    )
                    return record
            except Exception as exc:
                error = classify_provider_error(exc)
                raise
            finally:
                self.logger.insert(
                    ProviderCallLogCreate(
                        job_id=prepared.job_id,
                        item_key=prepared.item_key,
                        operation=route.task.value,
                        provider=route.provider,
                        model=route.model,
                        voice_id=self.profile.voice_id,
                        status="success" if record is not None else "failure",
                        attempt=attempt,
                        latency_ms=max(0, int((perf_counter() - started) * 1000)),
                        error_code=error,
                        error_summary="Korean audio attempt failed" if error else None,
                        prompt_hash=prepared.provenance.synthesis_request_sha256,
                        response_hash=record.provenance.artifact_sha256 if record else None,
                        route_policy_sha256=route.route_policy_sha256,
                        budget_snapshot_sha256=route.budget_snapshot_sha256,
                        cache_key_sha256=route.cache_key_sha256(
                            item_sha256=canonical_json_sha256(prepared.item_key),
                            input_sha256=prepared.provenance.synthesis_request_sha256,
                        ),
                        response_schema_sha256=route.response_schema_sha256,
                        estimated_cost=self.estimated_cost(prepared),
                    )
                )
                telemetry_complete = True

        try:
            # Azure has no idempotency key for synthesis. A timeout or disconnect
            # can follow a billable request, so a failed call requires an explicit
            # later invocation rather than an automatic potentially duplicate call.
            return invoke()
        except Exception as exc:
            if not telemetry_complete:
                # The provider may already have synthesized billable bytes. Keep
                # the persisted pending assets and lease reservation for recovery;
                # a telemetry storage error must never silently authorize replay.
                raise ValueError(
                    "Korean audio telemetry persistence failed; recovery required"
                ) from None
            unknown_outcome = classify_provider_error(exc) in {
                "timeout",
                "network_error",
                "server_error",
            }
            return prepared.model_copy(
                update={
                    "provenance": prepared.provenance.model_copy(
                        update={
                            "status": AudioSynthesisStatus.FAILED,
                            "rejection_reason_code": "provider_outcome_unknown"
                            if unknown_outcome
                            else "synthesis_failed",
                        }
                    )
                }
            )


def synthesize_korean_frequency_audio(
    *,
    database_url: str,
    authority: KoreanAudioAuthority,
    catalog_result_file: Path,
    voice_profile_file: Path,
    provider_policy_file: Path,
    frequency_bundle_root: Path,
    job_authority: KoreanFrequencyJobAuthority,
    max_items: int | None = None,
    missing_only: bool = False,
    settings: Settings | None = None,
    adapter: object | None = None,
    phase31_verifier: Callable = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
    entry_loader: Callable = load_korean_final_frequency_entries,
) -> GenerateAudioItemsResult:
    """Revalidate evidence before constructing Azure and persist exact pending-review assets."""
    from hashlib import sha256

    if max_items is not None and max_items < 1:
        raise ValueError("Korean audio max_items must be positive")
    if job_authority.stage not in {"pilot_audio", "full"}:
        raise ValueError("Korean audio authority stage is not authorized")
    for field in KoreanAudioAuthority.model_fields:
        if field in {"job_id", "region"}:
            continue
        target = "source_review_aggregate_sha256" if field == "binding_receipt_sha256" else field
        if getattr(authority, field) != getattr(job_authority, target):
            raise ValueError("Korean audio job authority drift")
    _verify_phase31_for_authority(job_authority, phase31_verifier=phase31_verifier)
    profile_data, _ = _read_json(voice_profile_file)
    profile = KoreanVoiceProfile.model_validate(profile_data)
    _validate_profile(profile)
    catalog, raw_catalog = _read_json(catalog_result_file)
    if (
        profile.catalog_result_file_sha256 != sha256(raw_catalog).hexdigest()
        or profile.catalog_locator_sha256 != authority.catalog_locator_sha256
        or profile.catalog_content_sha256 != authority.catalog_content_sha256
        or profile.profile_authority_sha256 != authority.profile_sample_authority_sha256
    ):
        raise ValueError("Korean audio profile authority drift")
    _validate_catalog_result_contract(
        catalog,
        job_id=catalog.get("job_id", ""),
        expected_hashes={
            "provider_policy_sha256": profile.provider_policy_sha256,
            "pilot_authority_sha256": profile.pilot_authority_sha256,
            "catalog_locator_sha256": profile.catalog_locator_sha256,
            "catalog_content_sha256": profile.catalog_content_sha256,
        },
    )
    voices = _catalog_voice_mappings(catalog)
    _selected_catalog_voice(voices, selected_voice_id=profile.voice_id, region=profile.region)
    if (
        canonical_json_sha256({"catalog_locale": "ko-KR", "voices": catalog["voices"]})
        != authority.catalog_content_sha256
    ):
        raise ValueError("Korean audio catalog content drift")
    policy = KoreanProviderPolicy.model_validate(_read_json(provider_policy_file)[0])
    if policy.policy_sha256 != authority.provider_policy_sha256:
        raise ValueError("Korean audio provider policy drift")
    entries = entry_loader(
        job_id=authority.job_id,
        bundle_root=frequency_bundle_root,
        binding_receipt_sha256=authority.binding_receipt_sha256,
        authority=job_authority,
        repo_root=Path.cwd(),
    )
    inventory = {entry.final_rank: entry for entry in entries}
    runtime_settings = settings or Settings(database_url=database_url)
    if runtime_settings.database_url != database_url:
        raise ValueError("Korean audio database settings drift")
    engine = create_engine(database_url)
    try:
        with (
            GenerationLeaseManager(engine).hold(authority.job_id) as lease,
            Session(engine) as session,
        ):
            jobs = JobRepository(session)
            job = jobs.get_job(authority.job_id)
            if job is None or job.language != "ko" or job.source_type != "frequency":
                raise ValueError("Korean audio requires a Korean frequency job")
            if jobs.load_korean_authority(authority.job_id) != job_authority:
                raise ValueError("Korean audio bound job authority drift")
            jobs.require_korean_attempt_authority(
                authority.job_id,
                "production_audio" if job_authority.stage == "full" else "pilot_audio_sample",
            )
            lexical, texts, audio = (
                LexicalRepository(session),
                TextRepository(session),
                AudioRepository(session),
            )
            records = texts.list_accepted_records(authority.job_id)
            pairs = []
            for record in records:
                candidate = lexical.get_candidate_for_item(authority.job_id, record.item_key)
                entry = inventory.get(candidate.frequency_rank) if candidate is not None else None
                if (
                    entry is None
                    or candidate.display_form != entry.lexical_identity.canonical_nfc
                    or candidate.lemma_key != entry.lexical_identity.lexical_key
                    or candidate.frequency_level != entry.level
                ):
                    raise ValueError("Korean audio candidate inventory drift")
                if job_authority.stage == "full" and not record.text_review_receipt_sha256:
                    raise ValueError("Korean production audio requires text review")
                pairs.append((candidate, record))
            service = KoreanProfileAudioSynthesisService(
                profile=profile,
                provider_policy=policy,
                adapter=adapter or AzureSpeechAdapter(runtime_settings),
                settings=runtime_settings,
                provider_call_logger=ProviderCallLogRepository(session),
            )
            result = GenerateAudioItemsResult()
            work = []
            for candidate, record in pairs:
                bundle = service.prepare_item_assets(
                    language=SupportedLanguage.KO,
                    display_word=candidate.display_form,
                    text_record=record,
                )
                prepared_assets = (bundle.word_asset, bundle.sentence_asset)
                existing_assets = tuple(
                    audio.get_asset(authority.job_id, record.item_key, asset.asset_kind)
                    for asset in prepared_assets
                )
                reusable = tuple(
                    missing_only and service.reusable(prepared, existing)
                    for prepared, existing in zip(prepared_assets, existing_assets)
                )
                if all(reusable):
                    result.processed_items += 2
                    result.reused_items += 2
                    continue
                work.append((record, prepared_assets, existing_assets, reusable))
                if max_items is not None and len(work) >= max_items:
                    break
            for kind in AudioAssetKind:
                route = policy.route_for(KoreanProviderTask(f"{kind.value}_audio"))
                if len(work) > route.budget.max_batch_items:
                    raise ValueError("Korean audio batch budget exceeded")
                estimated_cost = sum(
                    service.estimated_cost(prepared)
                    for _, prepared_assets, _, reusable in work
                    for prepared, reuse in zip(prepared_assets, reusable)
                    if prepared.asset_kind is kind and not reuse
                )
                if (
                    not math.isfinite(estimated_cost)
                    or estimated_cost > route.budget.max_estimated_cost_usd
                ):
                    raise ValueError("Korean audio cost budget exceeded")
            for record, prepared_assets, existing_assets, reusable in work:
                lease.begin_item(f"audio:{record.item_key}")
                with repository_transaction(session):
                    lease.fence(session)
                    for prepared, reuse in zip(prepared_assets, reusable):
                        if not reuse:
                            audio.upsert_audio_asset(prepared)
                final_assets = []
                for prepared, existing, reuse in zip(prepared_assets, existing_assets, reusable):
                    if reuse:
                        final = existing
                        result.reused_items += 1
                    else:
                        final = service.synthesize_prepared_asset(prepared)
                        with repository_transaction(session):
                            lease.fence(session)
                            audio.upsert_audio_asset(final)
                    result.processed_items += 1
                    result.failed_items += final.provenance.status is AudioSynthesisStatus.FAILED
                    final_assets.append(final)
                    if final.provenance.rejection_reason_code == "provider_outcome_unknown":
                        # Leave the stage-specific reservation for explicit recovery;
                        # no later asset or item may create a duplicate paid attempt.
                        return result
                with repository_transaction(session):
                    lease.fence(session)
                    if all(asset.ready_for_korean_final_export for asset in final_assets):
                        jobs.record_item_success(
                            authority.job_id,
                            item_key=record.item_key,
                            completed_stage=JobStage.SYNTHESIZE_AUDIO,
                        )
                    lease.finish_item(session)
                lease.current_item_sha256 = None
            return result
    finally:
        engine.dispose()
