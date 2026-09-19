"""Exact-request, single-attempt audio runner for the local Korean grammar course.

The plan is inert. Only a separate owner authorization bound to its exact hash
permits synthesis. A durable reservation precedes each Azure request: interrupted
or failed attempts require explicit recovery, never an automatic paid replay.
"""

from __future__ import annotations

import base64
import fcntl
import io
import json
import math
import os
import re
import unicodedata
import wave
from dataclasses import asdict
from hashlib import sha256
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import miniaudio
from pydantic import Field

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.korean import canonical_json_sha256
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.azure_speech_adapter import build_azure_ssml
from multilang.services.korean_audio import KoreanVoiceProfile, build_korean_audio_asset
from multilang.services.korean_audio_runtime import KoreanProfileAudioSynthesisService

_MAX_JSON_BYTES = 16 * 1024 * 1024
_SAFE_ID = re.compile(r"[a-zA-Z0-9_.:-]{1,128}\Z")


class KoreanGrammarProsodyProfile(KoreanVoiceProfile):
    """Explicit, text-scoped prosody exception; never labels the repair neutral."""

    profile_policy_version: Literal["korean-grammar-prosody-repair-v1"] = (
        "korean-grammar-prosody-repair-v1"
    )
    ssml_policy: Literal["bounded-prosody-repair"] = "bounded-prosody-repair"
    repair_text: str = Field(min_length=1, max_length=100)
    pause_after_text: str = Field(min_length=1, max_length=50)
    rate: Literal["-20%"] = "-20%"
    pause_ms: Literal[200] = 200


class KoreanGrammarProsodyRepairService(KoreanProfileAudioSynthesisService):
    """Reuse the single-attempt adapter with a separately hashed, bounded SSML profile."""

    def _prepare(self, job_id, item_key, kind, text) -> AudioAssetRecord:
        profile = self.profile
        if (
            not isinstance(profile, KoreanGrammarProsodyProfile)
            or text != profile.repair_text
            or not text.startswith(profile.pause_after_text + " ")
        ):
            raise ValueError("Grammar prosody repair text scope mismatch")
        prepared = super()._prepare(job_id, item_key, kind, text)
        if prepared.normalized_input.tts_text != text:
            raise ValueError("Grammar prosody repair text scope requires normalized text")
        prefix = profile.pause_after_text
        content = (
            f'<speak><prosody rate="{profile.rate}">{escape(prefix)}'
            f'<break time="{profile.pause_ms}ms" />{escape(text[len(prefix) :])}'
            "</prosody></speak>"
        )
        ssml = build_azure_ssml(text=content, locale=profile.locale, voice_id=profile.voice_id)
        normalized = NormalizedTtsInput(
            display_text=text,
            tts_text=text,
            ssml_text=ssml,
            synthesis_request_sha256=canonical_json_sha256(
                {
                    "asset_kind": kind.value,
                    "locale": profile.locale,
                    "voice_id": profile.voice_id,
                    "profile_sha256": profile.profile_sha256,
                    "text": text,
                    "ssml_text": ssml,
                }
            ),
        )
        path = Path(prepared.provenance.storage_path).with_name(
            f"{normalized.synthesis_request_sha256}.mp3"
        )
        result = prepared.model_copy(
            update={
                "normalized_input": normalized,
                "provenance": prepared.provenance.model_copy(
                    update={
                        "ssml_hash": normalized.ssml_hash,
                        "storage_path": str(path),
                        "synthesis_request_sha256": normalized.synthesis_request_sha256,
                    }
                ),
            }
        )
        self._validate_cost(result)
        return result


def _read(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= _MAX_JSON_BYTES:
        raise ValueError("Invalid grammar audio file")
    return path.read_bytes()


def _write(path: Path, payload: dict) -> None:
    if path.is_symlink():
        raise ValueError("Invalid grammar audio path")
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        json.dump(payload, file, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
        temporary = file.name
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def plan_grammar_audio(
    *, service: KoreanProfileAudioSynthesisService, rows: list[dict], source_files: list[Path]
) -> dict:
    """Prepare exact SSML and unique transport requests without any provider calls."""
    if not rows or len(rows) > 1000 or not source_files:
        raise ValueError("Grammar audio inventory is empty or exceeds bounds")
    if service.profile.provider_policy_sha256 != service.policy.policy_sha256:
        raise ValueError("Grammar profile and policy binding drift")
    for role in AudioAssetKind:
        if f"ordinary-grammar-{role.value}-audio" not in service.profile.usage_scope:
            raise ValueError("Grammar audio scope is missing")
    roles, requests, seen = [], {}, set()
    for row in rows:
        entry, role, text = row["entry_id"], AudioAssetKind(row["role"]), row["text"]
        if not isinstance(entry, str) or not _SAFE_ID.fullmatch(entry) or (entry, role) in seen:
            raise ValueError("Grammar audio role identity is invalid or duplicated")
        seen.add((entry, role))
        prepared = service._prepare("korean-grammar-course", entry, role, text)
        if text != prepared.normalized_input.tts_text:
            raise ValueError("Grammar audio text must already be normalized")
        transport = canonical_json_sha256(
            {
                "ssml": prepared.normalized_input.ssml_text,
                "profile_sha256": service.profile.profile_sha256,
                "format": service.profile.output_format,
                "provider_sdk_version": service.sdk_version,
            }
        )
        if transport not in requests:
            requests[transport] = {
                "transport_sha256": transport,
                "prepared": prepared.model_dump(mode="json"),
                "role_indexes": [],
                "estimated_cost_usd": service.estimated_cost(prepared),
                "ssml_utf8_bytes": len(prepared.normalized_input.ssml_text.encode("utf-8")),
            }
        requests[transport]["role_indexes"].append(len(roles))
        roles.append(
            {
                "entry_id": entry,
                "role": role.value,
                "text": text,
                "transport_sha256": transport,
                "prepared": prepared.model_dump(mode="json"),
            }
        )
    sources = []
    for path in source_files:
        path = Path(path)
        raw = _read(path)
        sources.append(
            {"path": str(path.resolve()), "sha256": sha256(raw).hexdigest(), "byte_size": len(raw)}
        )
    payload = {
        "schema_version": "korean-grammar-audio-plan-v1",
        "profile_sha256": service.profile.profile_sha256,
        "provider_policy_sha256": service.policy.policy_sha256,
        "price_usd_per_million_characters": service.price_per_million_characters,
        "source_files": sources,
        "roles": roles,
        "requests": list(requests.values()),
        "role_count": len(roles),
        "unique_provider_requests": len(requests),
        "unique_text_characters": sum(
            len(r["prepared"]["normalized_input"]["tts_text"]) for r in requests.values()
        ),
        "ssml_utf8_bytes": sum(r["ssml_utf8_bytes"] for r in requests.values()),
        "max_estimated_cost_usd": round(sum(r["estimated_cost_usd"] for r in requests.values()), 9),
        "cost_basis": "all_utf8_ssml_bytes_as_billable_characters_conservative_bound",
        "max_attempts_per_request": 1,
        "max_concurrency": 1,
        "synthesis_authorized": False,
    }
    return {**payload, "plan_sha256": canonical_json_sha256(payload)}


def _validate_run(
    plan: dict, service: KoreanProfileAudioSynthesisService, authorization: dict
) -> None:
    regenerated = plan_grammar_audio(
        service=service,
        rows=plan["roles"],
        source_files=[Path(source["path"]) for source in plan["source_files"]],
    )
    if regenerated != plan:
        raise ValueError("Grammar audio plan or source drift")
    cap = authorization.get("max_estimated_cost_usd")
    calls = authorization.get("max_provider_calls")
    if (
        authorization.get("authorized") is not True
        or authorization.get("plan_sha256") != plan["plan_sha256"]
        or type(cap) not in (int, float)
        or not math.isfinite(cap)
        or cap < plan["max_estimated_cost_usd"]
        or type(calls) is not int
        or calls < plan["unique_provider_requests"]
    ):
        raise ValueError("Explicit plan-bound owner budget authorization required")


def run_grammar_audio(
    *,
    plan: dict,
    service: KoreanProfileAudioSynthesisService,
    state_dir: Path,
    authorization: dict,
    continue_after_failure: bool = False,
) -> dict:
    """Synthesize or reuse all media, returning integrity evidence only.

    Serial execution is intentional for this small course. The process lock spans
    the whole run; the per-request durable journal also blocks replays after crashes.
    """
    _validate_run(plan, service, authorization)
    state_dir = Path(state_dir)
    if state_dir.is_symlink():
        raise ValueError("Invalid grammar audio state path")
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "run.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Grammar audio run already active") from None
        state_path = state_dir / "state.json"
        state = (
            json.loads(_read(state_path))
            if state_path.exists()
            else {
                "plan_sha256": plan["plan_sha256"],
                "requests": {},
            }
        )
        if state.get("plan_sha256") != plan["plan_sha256"]:
            raise ValueError("Grammar audio journal belongs to another plan")
        output_roles = [None] * len(plan["roles"])
        blocked = []
        for request in plan["requests"]:
            key = request["transport_sha256"]
            prepared = AudioAssetRecord.model_validate(request["prepared"])
            checkpoint = state["requests"].get(key)
            if checkpoint is not None:
                if checkpoint["status"] != "complete":
                    if continue_after_failure:
                        blocked.append(key)
                        continue
                    raise ValueError("Grammar audio recovery required; request already reserved")
                record = AudioAssetRecord.model_validate(checkpoint["audio_asset"])
                if not service.reusable(prepared, record):
                    raise ValueError("Grammar audio recovery required; cached media drift")
            else:
                state["requests"][key] = {
                    "status": "reserved",
                    "estimated_cost_usd": request["estimated_cost_usd"],
                }
                _write(state_path, state)
                record = service.synthesize_prepared_asset(prepared)
                if record.provenance.status is not AudioSynthesisStatus.SYNTHESIZED:
                    if continue_after_failure:
                        blocked.append(key)
                        continue
                    raise ValueError("Grammar audio recovery required; provider call failed")
                if not service.reusable(prepared, record):
                    raise ValueError("Grammar audio recovery required; synthesized media invalid")
                state["requests"][key] = {
                    "status": "complete",
                    "estimated_cost_usd": request["estimated_cost_usd"],
                    "audio_asset": record.model_dump(mode="json"),
                }
                _write(state_path, state)
            content = _read(Path(record.provenance.storage_path))
            for index in request["role_indexes"]:
                row = plan["roles"][index]
                role_asset = AudioAssetRecord.model_validate(row["prepared"])
                bound = build_korean_audio_asset(
                    job_id=role_asset.job_id,
                    item_key=role_asset.item_key,
                    asset_kind=role_asset.asset_kind,
                    normalized_input=role_asset.normalized_input,
                    profile=service.profile,
                    storage_path=record.provenance.storage_path,
                    media_bytes=content,
                    duration_ms=record.provenance.duration_ms,
                    fallback_used=False,
                )
                bound = bound.model_copy(
                    update={
                        "provenance": bound.provenance.model_copy(
                            update={"provider_sdk_version": service.sdk_version}
                        )
                    }
                )
                output_roles[index] = {
                    "entry_id": row["entry_id"],
                    "role": row["role"],
                    "transport_sha256": key,
                    "media_sha256": sha256(content).hexdigest(),
                    "synthesis_origin_request_sha256": record.provenance.synthesis_request_sha256,
                    "audio_asset": bound.model_dump(mode="json"),
                }
        result = {
            "schema_version": "korean-grammar-audio-integrity-v1",
            "plan_sha256": plan["plan_sha256"],
            "status": "blocked_uncertainty" if blocked else "automated_integrity_passed",
            "acoustic_review_status": "not_reviewed",
            "is_human": False,
            "unique_provider_requests": len(plan["requests"]),
            "roles": [row for row in output_roles if row is not None],
            "blocked_transports": blocked,
        }
        _write(state_dir / "media-manifest.json", result)
        return result


class GrammarAudioCallLogger:
    """Local fsynced telemetry; no production database or raw credentials."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def insert(self, record) -> None:
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            file.flush()
            os.fsync(file.fileno())


def _spoken_identity(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFC", text)
        if not c.isspace() and not unicodedata.category(c).startswith("P")
    )


def _wav_and_signal(content: bytes, *, max_audio_seconds: int = 15) -> tuple[bytes, dict]:
    decoded = miniaudio.decode(
        content, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=16000
    )
    samples = decoded.samples
    if not samples or len(samples) > max_audio_seconds * 16000:
        raise ValueError("Grammar acoustic analysis duration exceeds authorized budget")
    rms = math.sqrt(sum(int(s) ** 2 for s in samples) / len(samples)) / 32768
    silence = sum(abs(s) < 164 for s in samples) / len(samples)
    clipping = sum(abs(s) >= 32760 for s in samples) / len(samples)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(samples.tobytes())
    return buffer.getvalue(), {
        "duration_ms": len(samples) / 16,
        "rms": rms,
        "silence_fraction": silence,
        "clipping_fraction": clipping,
        "integrity_passed": rms >= 0.005 and silence <= 0.90 and clipping <= 0.005,
        "validator": "korean-grammar-pcm-signal-v1",
    }


class AzureGrammarAudioAnalysis:
    """Fixed-region bounded Azure REST analysis without automatic retries."""

    def __init__(self, settings):
        if settings.azure_speech_region != "eastus" or not settings.azure_speech_key:
            raise ValueError("Grammar audio analysis requires the authorized East US resource")
        self.key = settings.azure_speech_key

    def __call__(self, *, wav_bytes: bytes, mode: str, reference_text: str) -> dict:
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Accept": "application/json",
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        }
        if mode == "pronunciation":
            parameters = {
                "ReferenceText": reference_text,
                "GradingSystem": "HundredMark",
                "Granularity": "Phoneme",
                "Dimension": "Comprehensive",
                "EnableMiscue": True,
                "EnableProsodyAssessment": False,
            }
            headers["Pronunciation-Assessment"] = base64.b64encode(
                json.dumps(parameters).encode()
            ).decode("ascii")
        elif mode != "asr":
            raise ValueError("Unknown grammar audio analysis mode")
        request = Request(
            "https://eastus.stt.speech.microsoft.com/speech/recognition/conversation/"
            "cognitiveservices/v1?language=ko-KR&format=detailed&profanity=raw",
            data=wav_bytes,
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("Grammar audio analysis response exceeds bounds")
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("Invalid grammar audio analysis response")
        return result


def analyze_grammar_audio(
    *,
    manifest: dict,
    mode: str,
    state_dir: Path,
    authorization: dict,
    requester,
    selected_transports: list[str] | None = None,
) -> dict:
    """Collect exact-byte acoustic evidence, without inferring pronunciation approval."""
    if mode not in {"asr", "pronunciation"}:
        raise ValueError("Unknown grammar audio analysis mode")
    unique = {}
    for row in manifest["roles"]:
        unique.setdefault(row["transport_sha256"], row)
    if selected_transports is not None:
        if not set(selected_transports).issubset(unique):
            raise ValueError("Analysis selection is outside the media manifest")
        unique = {key: row for key, row in unique.items() if key in selected_transports}
    manifest_hash = canonical_json_sha256(manifest)
    authorization_hash = canonical_json_sha256(authorization)
    cap = authorization.get("max_estimated_cost_usd")
    count = authorization.get("max_calls")
    seconds_cap = authorization.get("max_audio_seconds", 15)
    if (
        authorization.get("authorized") is not True
        or authorization.get("manifest_sha256") != manifest_hash
        or type(count) is not int
        or count < len(unique)
        or type(seconds_cap) is not int
        or not 1 <= seconds_cap <= 15
        or type(cap) not in (int, float)
        or not math.isfinite(cap)
        or cap < len(unique) * seconds_cap / 3600
    ):
        raise ValueError("Explicit analysis budget authorization required")
    state_dir = Path(state_dir)
    if state_dir.is_symlink():
        raise ValueError("Invalid grammar audio analysis path")
    state_dir.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(state_dir / "run.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Grammar audio analysis already active") from None
        state_path = state_dir / "state.json"
        state = (
            json.loads(_read(state_path))
            if state_path.exists()
            else {
                "manifest_sha256": manifest_hash,
                "mode": mode,
                "authorization_sha256": authorization_hash,
                "requests": {},
            }
        )
        if state["manifest_sha256"] != manifest_hash or state["mode"] != mode:
            raise ValueError("Grammar analysis journal drift")
        if state.get("authorization_sha256") != authorization_hash:
            raise ValueError("Grammar analysis authorization drift; explicit recovery required")
        pending = set(unique).difference(state["requests"])
        cumulative_count = len(state["requests"]) + len(pending)
        if cumulative_count > count or cumulative_count * seconds_cap / 3600 > cap:
            raise ValueError("Grammar cumulative analysis budget exceeded")
        for key, row in unique.items():
            asset = AudioAssetRecord.model_validate(row["audio_asset"])
            path = Path(asset.provenance.storage_path)
            content = _read(path)
            if (
                sha256(content).hexdigest() != row["media_sha256"]
                or inspect_local_mp3(path) is None
            ):
                raise ValueError("Grammar analysis media drift")
            wav, signal = _wav_and_signal(content, max_audio_seconds=seconds_cap)
            checkpoint = state["requests"].get(key)
            if checkpoint:
                if checkpoint["status"] != "complete":
                    raise ValueError("Grammar audio analysis recovery required")
                if checkpoint["result"]["wav_sha256"] != sha256(wav).hexdigest():
                    raise ValueError("Grammar analysis decoder drift")
                continue
            state["requests"][key] = {"status": "reserved", "max_cost_usd": seconds_cap / 3600}
            _write(state_path, state)
            try:
                response = requester(
                    wav_bytes=wav, mode=mode, reference_text=asset.normalized_input.tts_text
                )
            except Exception as exc:
                code = "timeout" if isinstance(exc, TimeoutError) else "provider_error"
                if isinstance(exc, HTTPError):
                    code = f"http_{exc.code}"
                state["requests"][key]["error_code"] = code
                _write(state_path, state)
                raise ValueError("Grammar audio analysis recovery required") from None
            alternatives = response.get("NBest", [])
            best = alternatives[0] if alternatives else {}
            transcript = best.get("Lexical", response.get("DisplayText", ""))
            result = {
                "transport_sha256": key,
                "media_sha256": row["media_sha256"],
                "wav_sha256": sha256(wav).hexdigest(),
                "source_text": asset.normalized_input.tts_text,
                "mode": mode,
                "provider": "azure-speech",
                "locale": "ko-KR",
                "region": "eastus",
                "model_version": "service-managed-not-disclosed",
                "signal": signal,
                "estimated_cost_usd": math.ceil(signal["duration_ms"] / 1000) / 3600,
                "transcript": transcript,
                "transcript_matches": response.get("RecognitionStatus") == "Success"
                and _spoken_identity(transcript)
                == _spoken_identity(asset.normalized_input.tts_text),
                "provider_response": response,
                "provider_response_sha256": canonical_json_sha256(response),
            }
            state["requests"][key] = {
                "status": "complete",
                "max_cost_usd": seconds_cap / 3600,
                "result": result,
            }
            _write(state_path, state)
        results = [
            checkpoint["result"]
            for checkpoint in state["requests"].values()
            if checkpoint["status"] == "complete"
        ]
        unresolved = [
            key
            for key, checkpoint in state["requests"].items()
            if checkpoint["status"] != "complete"
        ]
        report = {
            "schema_version": "korean-grammar-acoustic-evidence-v1",
            "manifest_sha256": manifest_hash,
            "mode": mode,
            "items": results,
            "acoustic_review_status": "not_reviewed",
            "is_human": False,
            "provider_call_count": len(state["requests"]),
            "max_cost_usd": len(state["requests"]) * seconds_cap / 3600,
            "estimated_cost_usd": sum(item["estimated_cost_usd"] for item in results)
            + len(unresolved) * seconds_cap / 3600,
            "unresolved_requests": unresolved,
            "authorization_sha256": authorization_hash,
        }
        _write(state_dir / "report.json", report)
        return report
