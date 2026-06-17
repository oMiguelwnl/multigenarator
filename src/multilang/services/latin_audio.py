"""Latin MVP audio metadata contracts and export-readiness validators."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from multilang.services.latin_source_pack import load_latin_mvp_source_pack


LatinAudioKind = Literal["word", "sentence"]
CURRENT_LATIN_AUDIO_PROVIDER = "google-translate-tts"
LATIN_FALLBACK_AUDIO_PROVIDERS = ("elevenlabs-italian", "azure-italian")
LATIN_RESEARCH_ONLY_AUDIO_PROVIDERS = ("finevoice",)
LATIN_LEGACY_AUDIO_PROVIDERS = ("espeak-ng",)
LatinAudioProvider = Literal[
    "espeak-ng",
    "elevenlabs-italian",
    "google-translate-tts",
    "finevoice",
    "azure-italian",
    "azure-multilingual-experimental",
]
LatinAudioReviewStatus = Literal["needs_playback_review", "approved", "rejected", "blocked"]
DEFAULT_LATIN_AUDIO_MANIFEST_PATH = Path("data") / "latin_mvp" / "latin-mvp-50-v1-audio.json"
LATIN_AUDIO_MEDIA_MARKERS = (b"RIFF", b"ID3")


def normalize_latin_audio_text(value: str) -> str:
    """Normalize generated Latin audio text for exact hash and source-pack comparison."""

    return " ".join(value.split())


def latin_audio_text_hash(value: str) -> str:
    """Return the SHA-256 hash used for auditable Latin audio generated text."""

    return sha256(normalize_latin_audio_text(value).encode("utf-8")).hexdigest()


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("required text field must not be blank")
    return stripped


def _strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _not_blank(value)


class LatinAudioArtifact(BaseModel):
    """One auditable Latin word or sentence audio artifact."""

    audio_kind: LatinAudioKind
    provider: LatinAudioProvider
    provider_version: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    pronunciation_policy: str = Field(min_length=1)
    generated_text: str = Field(min_length=1)
    text_hash: str = Field(min_length=64, max_length=64)
    playback_review_status: LatinAudioReviewStatus
    storage_path: str = Field(min_length=1)
    fallback_reason: str | None = None

    _strip_text = field_validator(
        "provider_version",
        "voice",
        "pronunciation_policy",
        "generated_text",
        "storage_path",
    )(_not_blank)
    _strip_optional_text_fields = field_validator("fallback_reason")(_strip_optional_text)

    @field_validator("generated_text")
    @classmethod
    def normalize_generated_text(cls, value: str) -> str:
        return normalize_latin_audio_text(value)

    @model_validator(mode="after")
    def validate_hash_and_fallback_reason(self) -> "LatinAudioArtifact":
        if self.text_hash != latin_audio_text_hash(self.generated_text):
            raise ValueError("text_hash must match normalized generated_text")
        if self.provider in {"elevenlabs-italian", "azure-italian", "finevoice", "azure-multilingual-experimental"} and self.fallback_reason is None:
            raise ValueError("fallback_reason is required for fallback or experimental providers")
        if self.playback_review_status == "blocked" and self.fallback_reason is None:
            raise ValueError("fallback_reason is required for blocked audio records")
        return self


class LatinAudioPair(BaseModel):
    """Word and sentence audio artifacts for one Latin MVP source-pack item."""

    item_key: str = Field(min_length=1)
    word: LatinAudioArtifact | None = None
    sentence: LatinAudioArtifact | None = None

    _strip_text = field_validator("item_key")(_not_blank)

    @model_validator(mode="after")
    def validate_artifact_kinds(self) -> "LatinAudioPair":
        if self.word is not None and self.word.audio_kind != "word":
            raise ValueError("word artifact audio_kind must be word")
        if self.sentence is not None and self.sentence.audio_kind != "sentence":
            raise ValueError("sentence artifact audio_kind must be sentence")
        return self


class LatinAudioManifest(BaseModel):
    """Validated Latin MVP audio manifest with one pair per source-pack item."""

    source_pack_version: Literal["latin-mvp-50-v1"] = "latin-mvp-50-v1"
    artifacts: list[LatinAudioPair]


class LatinAudioSummary(BaseModel):
    """Aggregate Latin audio readiness counts."""

    total_items: int
    approved_items: int
    blocked_items: int
    status_counts: dict[str, dict[str, int]]
    blocking_audio_by_item_key: dict[str, list[str]]


def load_latin_audio_manifest(path: Path | None = None) -> LatinAudioManifest:
    """Load and validate the committed Latin MVP audio manifest JSON."""

    manifest_path = path or DEFAULT_LATIN_AUDIO_MANIFEST_PATH
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return LatinAudioManifest.model_validate(payload)
    except FileNotFoundError as exc:
        raise ValueError("Latin MVP audio manifest is missing for latin-mvp-50-v1") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Latin MVP audio manifest JSON is malformed for latin-mvp-50-v1") from exc
    except Exception as exc:
        if exc.__class__.__module__.startswith("pydantic"):
            raise ValueError(f"Latin MVP audio manifest failed validation for latin-mvp-50-v1: {exc}") from exc
        raise


def _status_counts_for_kind(manifest: LatinAudioManifest, audio_kind: LatinAudioKind) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for pair in manifest.artifacts:
        artifact = getattr(pair, audio_kind)
        if artifact is None:
            counter["missing"] += 1
        else:
            counter[artifact.playback_review_status] += 1
    return {
        "missing": counter.get("missing", 0),
        **{status: counter.get(status, 0) for status in LatinAudioReviewStatus.__args__},
    }


def _storage_path_is_export_ready(storage_path: str, *, repo_root: Path) -> bool:
    path_text = storage_path.strip()
    if "\\" in path_text or ":" in path_text or path_text.startswith(("/", "~")):
        return False

    relative_path = Path(path_text)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return False

    root = repo_root.resolve()
    candidate = (root / relative_path).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        return False

    if not candidate.is_file():
        return False
    if candidate.stat().st_size <= 0:
        return False
    header = candidate.read_bytes()[: max(len(marker) for marker in LATIN_AUDIO_MEDIA_MARKERS)]
    return any(header.startswith(marker) for marker in LATIN_AUDIO_MEDIA_MARKERS)


def _readiness_issues(manifest: LatinAudioManifest, *, repo_root: Path | None = None) -> dict[str, list[str]]:
    readiness_repo_root = repo_root or Path.cwd()
    source_pack = load_latin_mvp_source_pack()
    issues: dict[str, list[str]] = {}
    expected_item_keys = [entry.item_key for entry in source_pack.entries]
    actual_item_keys = [pair.item_key for pair in manifest.artifacts]

    if manifest.source_pack_version != source_pack.source_pack_version:
        issues.setdefault("manifest", []).append("source_pack_version")
        return issues
    if actual_item_keys != expected_item_keys:
        issues.setdefault("manifest", []).append("item_key_order")
        return issues

    for entry, pair in zip(source_pack.entries, manifest.artifacts, strict=True):
        expected_text_by_kind = {
            "word": entry.target_form,
            "sentence": entry.latin_sentence,
        }
        for audio_kind, expected_text in expected_text_by_kind.items():
            artifact: LatinAudioArtifact | None = getattr(pair, audio_kind)
            if artifact is None:
                issues.setdefault(entry.item_key, []).append(f"audio_kind={audio_kind} field=missing")
                continue
            if artifact.playback_review_status != "approved":
                issues.setdefault(entry.item_key, []).append(
                    f"audio_kind={audio_kind} field=playback_review_status"
                )
            if normalize_latin_audio_text(artifact.generated_text) != normalize_latin_audio_text(expected_text):
                issues.setdefault(entry.item_key, []).append(f"audio_kind={audio_kind} field=generated_text")
            if artifact.text_hash != latin_audio_text_hash(artifact.generated_text):
                issues.setdefault(entry.item_key, []).append(f"audio_kind={audio_kind} field=text_hash")
            if not _storage_path_is_export_ready(artifact.storage_path, repo_root=readiness_repo_root):
                issues.setdefault(entry.item_key, []).append(f"audio_kind={audio_kind} field=storage_path")
    return issues


def summarize_latin_audio_manifest(manifest: LatinAudioManifest, *, repo_root: Path | None = None) -> LatinAudioSummary:
    """Summarize Latin audio approval and blocking state by item key and audio kind."""

    issues = _readiness_issues(manifest, repo_root=repo_root)
    item_blockers = {item_key: blockers for item_key, blockers in issues.items() if item_key != "manifest"}
    approved_items = len(manifest.artifacts) - len(item_blockers) if "manifest" not in issues else 0
    return LatinAudioSummary(
        total_items=len(manifest.artifacts),
        approved_items=approved_items,
        blocked_items=len(issues),
        status_counts={
            "word": _status_counts_for_kind(manifest, "word"),
            "sentence": _status_counts_for_kind(manifest, "sentence"),
        },
        blocking_audio_by_item_key=issues,
    )


def assert_latin_audio_manifest_export_ready(manifest: LatinAudioManifest, *, repo_root: Path | None = None) -> None:
    """Fail closed unless all 50 source-pack entries have approved exact-text word and sentence audio."""

    summary = summarize_latin_audio_manifest(manifest, repo_root=repo_root)
    if not summary.blocking_audio_by_item_key:
        return

    blockers = [
        f"latin_audio_export_blocked item_key={item_key} {' '.join(fields)}"
        for item_key, fields in summary.blocking_audio_by_item_key.items()
    ]
    raise ValueError("; ".join(blockers))


__all__ = [
    "CURRENT_LATIN_AUDIO_PROVIDER",
    "LATIN_FALLBACK_AUDIO_PROVIDERS",
    "LatinAudioArtifact",
    "DEFAULT_LATIN_AUDIO_MANIFEST_PATH",
    "LATIN_LEGACY_AUDIO_PROVIDERS",
    "LATIN_RESEARCH_ONLY_AUDIO_PROVIDERS",
    "assert_latin_audio_manifest_export_ready",
    "LatinAudioKind",
    "LatinAudioManifest",
    "LatinAudioPair",
    "LatinAudioProvider",
    "LatinAudioReviewStatus",
    "LatinAudioSummary",
    "latin_audio_text_hash",
    "load_latin_audio_manifest",
    "normalize_latin_audio_text",
    "summarize_latin_audio_manifest",
]
