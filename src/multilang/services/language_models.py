"""Explicit local model preparation; ordinary analysis never downloads models."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256

STANZA_RESOURCES_VERSION = "1.10.0"
STANZA_RESOURCES_URL = "https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main"
STANZA_RESOURCES_SHA256 = "3efb2833a67c0184fac2ea9986c04f9585bfb89fb943a4ab1a6bcbed641d6be0"


@dataclass(frozen=True)
class ModelSpec:
    language: str
    backend: str
    model_language: str
    package: str


def model_spec(language: str) -> ModelSpec:
    language = SupportedLanguage(language).value
    if language == "la":
        raise ValueError("Classical Latin requires its isolated analysis pipeline")
    if language == "ko":
        return ModelSpec(language, "kiwi", language, "kiwipiepy")
    if language == "ja":
        return ModelSpec(language, "fugashi", language, "fugashi")
    return ModelSpec(language, "stanza", "zh-hans" if language == "zh" else language, "stanza")


MODEL_PROFILES = ("fast", "balanced", "accurate")


def _profile(profile: str) -> str:
    if profile not in MODEL_PROFILES:
        raise ValueError("unsupported model profile")
    return profile


def _manifest_path(root: Path, language: str, profile: str) -> Path:
    _profile(profile)
    suffix = "" if profile == "fast" else f".{profile}"
    return _plain_path(Path(root) / f"{language}{suffix}.manifest.json")


def stanza_processors(registry: dict, language: str, *, profile: str = "fast") -> dict[str, str]:
    _profile(profile)
    entry = registry.get(language)
    if not isinstance(entry, dict) or "alias" in entry:
        raise ValueError("model language requires an explicit available registry entry")
    package = "default_accurate" if profile == "accurate" else "default"
    defaults = entry.get("packages", {}).get(package)
    if defaults is None and profile != "accurate":
        defaults = entry.get("default_processors", {})
    if not isinstance(defaults, dict):
        raise ValueError("requested profile is unsupported by the pinned registry")
    processors = {}
    for name in ("tokenize", "mwt", "pos", "lemma"):
        selected = defaults.get(name)
        if not selected and name == "mwt":
            continue
        if not isinstance(selected, str):
            raise ValueError(f"required {name} model is not available")
        choices = entry.get(name, {})
        lightweight = selected.removesuffix("_charlm") + "_nocharlm"
        if profile == "fast" and name in {"pos", "lemma"} and lightweight in choices:
            selected = lightweight
        if selected not in choices and (name, selected) != ("lemma", "identity"):
            raise ValueError(f"required {name} model is not available")
        processors[name] = selected
    return processors


def _plain_path(path: Path) -> Path:
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("model path must not contain symlinks")
    return path


@lru_cache(maxsize=512)
def _stat_bound_digest(path: Path, state: tuple) -> str:
    with path.open("rb") as handle:
        before = path.stat()
        if state != (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino):
            raise ValueError("model file changed before hashing")
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        after = path.stat()
        if state != (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino):
            raise ValueError("model file changed during hashing")
        return digest


def _file_digest(path: Path) -> str:
    stat = path.stat()
    return _stat_bound_digest(path, (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino))


@lru_cache(maxsize=512)
def _upstream_md5(path: Path, state: tuple) -> str:
    # Upstream uses MD5 for artifacts inside the SHA-256-pinned registry. Our
    # manifest additionally checks SHA-256; this is not an authentication token.
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "md5").hexdigest()


def _required_models(registry: dict, language: str, processors: dict) -> dict[str, str]:
    pending = list(processors.items())
    required = {}
    while pending:
        processor, package = pending.pop()
        if (processor, package) == ("lemma", "identity"):
            continue
        if any(
            not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", value)
            for value in (language, processor, package)
        ):
            raise ValueError("model dependency path is invalid")
        path = f"{language}/{processor}/{package}.pt"
        if path in required:
            continue
        entry = registry.get(language, {}).get(processor, {}).get(package)
        if not isinstance(entry, dict) or not re.fullmatch(r"[0-9a-f]{32}", entry.get("md5", "")):
            raise ValueError("model dependency is absent from pinned registry")
        required[path] = entry["md5"]
        if len(required) > 64:
            raise ValueError("model dependency count exceeds bounds")
        pending.extend((item["model"], item["package"]) for item in entry.get("dependencies", ()))
    return required


def package_artifact_fingerprint(package: str) -> str:
    """Hash actual installed model bytes, with stat-bound reuse between sentences."""
    distribution = importlib.metadata.distribution(package)
    artifacts = {}
    for relative in distribution.files or ():
        name = str(relative)
        if ".dist-info/" in name or (
            Path(name).suffix
            not in {".mdl", ".dict", ".morph", ".txt", ".bin", ".dic", ".def", ".csv"}
            and Path(name).name not in {"dicrc", "mecabrc"}
        ):
            continue
        path = _plain_path(distribution.locate_file(relative))
        if not path.is_file() or path.stat().st_size > 2 * 1024**3:
            raise ValueError("installed model artifact is missing or oversized")
        artifacts[name] = _file_digest(path)
    if not artifacts or len(artifacts) > 256:
        raise ValueError("installed model artifacts are missing or exceed bounds")
    return canonical_sha256(artifacts)


def verify_model_manifest(path: Path) -> dict:
    path = _plain_path(path)
    if not path.is_file() or path.stat().st_size > 1024**2:
        raise ValueError("model manifest is missing or oversized")
    manifest = json.loads(path.read_bytes())
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise ValueError("model manifest files are required")
    if not manifest["files"] or len(manifest["files"]) > 256:
        raise ValueError("model manifest file count is outside bounds")
    total_bytes = 0
    for relative, expected in manifest["files"].items():
        name = PurePosixPath(relative)
        if (
            name.is_absolute()
            or not name.parts
            or ".." in name.parts
            or "\\" in relative
            or "\x00" in relative
        ):
            raise ValueError("model manifest path escapes its root")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("model manifest checksum is malformed")
        target = _plain_path(path.parent / name)
        if not target.is_file() or target.stat().st_size > 2 * 1024**3:
            raise ValueError("model file is missing or oversized")
        total_bytes += target.stat().st_size
        if total_bytes > 12 * 1024**3:
            raise ValueError("model manifest total bytes exceed bounds")
        if _file_digest(target) != expected:
            raise ValueError("model file checksum mismatch")
    fields = {
        "language",
        "backend",
        "model_language",
        "package_version",
        "resource_version",
        "processors",
        "files",
        "qualified",
    }
    profile = _profile(manifest.get("profile", "fast"))
    if profile != "fast":
        fields |= {"profile", "external_dependencies"}
    if path.name != _manifest_path(path.parent, manifest.get("language"), profile).name:
        raise ValueError("model manifest filename conflicts with profile")
    if (
        set(manifest) != fields
        or manifest["backend"] != "stanza"
        or manifest["qualified"] is not False
    ):
        raise ValueError("model manifest metadata is incomplete or unsupported")
    spec = model_spec(manifest["language"])
    if (
        spec.backend != "stanza"
        or manifest["model_language"] != spec.model_language
        or manifest["resource_version"] != STANZA_RESOURCES_VERSION
        or not isinstance(manifest["package_version"], str)
    ):
        raise ValueError("model manifest differs from pinned language/resource version")
    if manifest["files"].get("resources.json") != STANZA_RESOURCES_SHA256:
        raise ValueError("model manifest must include the pinned registry checksum")
    registry = json.loads((path.parent / "resources.json").read_bytes())
    if manifest["processors"] != stanza_processors(registry, spec.model_language, profile=profile):
        raise ValueError("model processors differ from pinned registry selection")
    required = _required_models(registry, spec.model_language, manifest["processors"])
    external_files = {}
    if profile != "fast":
        from multilang.services.transformer_artifacts import verify_dependencies

        external_files = verify_dependencies(manifest, path.parent)
    if set(manifest["files"]) != {"resources.json", *required, *external_files}:
        raise ValueError("model manifest does not cover all required models and dependencies")
    for relative, expected in required.items():
        target = path.parent / relative
        stat = target.stat()
        state = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
        if _upstream_md5(target, state) != expected:
            raise ValueError("model bytes differ from pinned upstream artifact")
    return manifest


def model_status(language: str, root: Path, *, profile: str = "fast") -> dict:
    spec = model_spec(language)
    _profile(profile)
    if spec.backend != "stanza" and profile != "fast":
        return {
            "language": language,
            "backend": spec.backend,
            "profile": profile,
            "available": False,
            "reason": "unsupported_profile",
        }
    profile_fields = {"profile": profile} if profile != "fast" else {}
    if spec.backend == "stanza" and profile != "fast":
        try:
            registry = _read_registry(Path(root))
        except (OSError, ValueError):
            registry = None
        if registry is not None:
            try:
                stanza_processors(registry, spec.model_language, profile=profile)
            except ValueError:
                return {
                    "language": language,
                    "backend": spec.backend,
                    **profile_fields,
                    "available": False,
                    "reason": "unsupported_profile",
                }
    try:
        version = importlib.metadata.version(spec.package)
    except importlib.metadata.PackageNotFoundError:
        return {
            "language": language,
            "backend": spec.backend,
            "available": False,
            "reason": "package_missing",
            **profile_fields,
        }
    if spec.backend != "stanza":
        if language == "ja":
            from multilang.services.japanese_analysis import japanese_dictionary_identity

            try:
                return {"language": language, "backend": spec.backend, "available": True,
                        "package_version": version, **japanese_dictionary_identity(), "qualified": False}
            except (ImportError, OSError, ValueError):
                return {"language": language, "backend": spec.backend, "available": False,
                        "reason": "dictionary_or_model_package_missing"}
        auxiliary = "kiwipiepy-model" if language == "ko" else "unidic-lite"
        try:
            auxiliary_version = importlib.metadata.version(auxiliary)
            fingerprint = package_artifact_fingerprint(auxiliary)
        except (importlib.metadata.PackageNotFoundError, OSError, ValueError):
            return {
                "language": language,
                "backend": spec.backend,
                "available": False,
                "reason": "dictionary_or_model_package_missing",
            }
        return {
            "language": language,
            "backend": spec.backend,
            "available": True,
            "package_version": version,
            "model_package": auxiliary,
            "model_package_version": auxiliary_version,
            "model_artifact_sha256": fingerprint,
            "qualified": False,
        }
    try:
        manifest = verify_model_manifest(_manifest_path(root, language, profile))
        if manifest.get("language") != language or manifest.get("package_version") != version:
            raise ValueError("model package or language drift")
        if manifest.get("external_dependencies"):
            from multilang.services.transformer_artifacts import transformer_runtime_available

            if not transformer_runtime_available(manifest):
                return {
                    "language": language,
                    "backend": spec.backend,
                    **profile_fields,
                    "available": False,
                    "reason": "transformer_runtime_missing",
                    "package_version": version,
                }
        return {
            "language": language,
            "backend": spec.backend,
            "available": True,
            "package_version": version,
            "manifest_sha256": canonical_sha256(manifest),
            **({"profile": profile} if profile != "fast" else {}),
            "qualified": False,
        }
    except (ValueError, OSError):
        return {
            "language": language,
            "backend": spec.backend,
            "available": False,
            "reason": "model_missing_or_drifted",
            **profile_fields,
            "package_version": version,
        }


def _read_registry(root: Path) -> dict:
    path = _plain_path(root / "resources.json")
    if not path.is_file() or path.stat().st_size > 32 * 1024**2:
        raise ValueError("pinned registry missing or oversized")
    if _file_digest(path) != STANZA_RESOURCES_SHA256:
        raise ValueError("pinned registry checksum mismatch")
    return json.loads(path.read_bytes())


def available_model_profiles(language: str, root: Path) -> dict:
    """Inventory capabilities and verified preparation state without network access."""
    spec = model_spec(language)
    options = {}
    seen = {}
    for profile in MODEL_PROFILES:
        option = {"profile": profile, "supported": False, "available": False}
        if spec.backend != "stanza":
            option.update(model_status(language, root, profile=profile))
            option["supported"] = profile == "fast"
        else:
            try:
                registry = _read_registry(Path(root))
                processors = stanza_processors(registry, spec.model_language, profile=profile)
                option.update(supported=True, processors=processors)
                key = json.dumps(processors, sort_keys=True)
                if key in seen:
                    option["equivalent_to"] = seen[key]
                else:
                    seen[key] = profile
                option.update(model_status(language, root, profile=profile))
            except (OSError, ValueError):
                option["reason"] = "registry_missing_or_profile_unsupported"
        options[profile] = option
    return {"language": language, "backend": spec.backend, "profiles": options}


def prepare_model(language: str, root: Path, *, profile: str = "fast") -> dict:
    """Explicit preparation; publish a manifest only after validating staged bytes."""
    spec = model_spec(language)
    _profile(profile)
    if spec.backend != "stanza":
        if profile != "fast":
            raise ValueError("unsupported profile for native backend")
        status = model_status(language, root)
        if not status["available"]:
            raise ValueError("install the language dictionary/model package first")
        return status
    import stanza

    root = _plain_path(root)
    root.mkdir(parents=True, exist_ok=True)
    destination = _manifest_path(root, language, profile)
    if destination.exists():
        status = model_status(language, root, profile=profile)
        if not status["available"]:
            if status.get("reason") == "transformer_runtime_missing":
                raise ValueError("transformer runtime missing; install the NLP dependencies first")
            raise ValueError("existing model manifest conflicts or has drifted")
        return status
    resource_path = _plain_path(root / "resources.json")
    if resource_path.exists():
        registry = _read_registry(root)
        content = resource_path.read_bytes()
    else:
        url = f"{STANZA_RESOURCES_URL}/resources_{STANZA_RESOURCES_VERSION}.json"
        with urlopen(url, timeout=60) as response:
            content = response.read(32 * 1024**2 + 1)
        if len(content) > 32 * 1024**2:
            raise ValueError("official model registry exceeds byte limit")
        if hashlib.sha256(content).hexdigest() != STANZA_RESOURCES_SHA256:
            raise ValueError("official model registry checksum mismatch")
        registry = json.loads(content)
    processors = stanza_processors(registry, spec.model_language, profile=profile)
    if profile != "fast":
        from multilang.services.transformer_artifacts import transformer_runtime_available

        if not transformer_runtime_available(
            {"model_language": spec.model_language, "processors": processors}
        ):
            raise ValueError("transformer runtime missing; install the NLP dependencies first")
    required = _required_models(registry, spec.model_language, processors)
    for relative in required:
        _plain_path(root / relative)
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=root) as temporary:
        staging = Path(temporary)
        (staging / "resources.json").write_bytes(content)
        for relative, expected in required.items():
            source = root / relative
            if source.exists():
                if not source.is_file() or source.stat().st_size > 2 * 1024**3:
                    raise ValueError("shared model artifact is invalid")
                stat = source.stat()
                state = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
                if _upstream_md5(source, state) != expected:
                    raise ValueError("shared model artifact conflicts with pinned registry")
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        stanza.download(
            lang=spec.model_language,
            model_dir=str(staging),
            package=None,
            processors=processors,
            resources_url=STANZA_RESOURCES_URL,
            resources_version=STANZA_RESOURCES_VERSION,
            download_json=False,
            verbose=False,
        )
        files = {"resources.json": STANZA_RESOURCES_SHA256}
        for relative in required:
            target = _plain_path(staging / relative)
            if not target.is_file() or target.stat().st_size > 2 * 1024**3:
                raise ValueError("model artifact missing or oversized")
            stat = target.stat()
            state = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
            if _upstream_md5(target, state) != required[relative]:
                raise ValueError("model bytes differ from pinned upstream artifact")
            files[relative] = _file_digest(target)
        manifest = {
            "language": language,
            "backend": spec.backend,
            "model_language": spec.model_language,
            "package_version": stanza.__version__,
            "resource_version": STANZA_RESOURCES_VERSION,
            "processors": processors,
            "files": files,
            "qualified": False,
        }
        if profile != "fast":
            from multilang.services.transformer_artifacts import prepare_dependencies

            dependencies = prepare_dependencies(manifest, staging, existing_root=root)
            manifest.update(profile=profile, external_dependencies=dependencies)
            for dependency in dependencies:
                files.update(dependency["files"])
        staged_manifest = staging / destination.name
        staged_manifest.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        verify_model_manifest(staged_manifest)
        # Preflight conflicts before publishing any files. Existing model bytes are
        # never overwritten; a failed prepare leaves no selectable new manifest.
        for relative, expected in files.items():
            target = _plain_path(root / relative)
            if target.exists() and _file_digest(target) != expected:
                raise ValueError("prepared model artifact conflicts with existing bytes")
        for relative in files:
            target = _plain_path(root / relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(staging / relative, target)
            except FileExistsError:
                if _file_digest(target) != files[relative]:
                    raise ValueError("model artifact changed during publication") from None
        try:
            os.link(staged_manifest, destination)
        except FileExistsError:
            if destination.read_bytes() != staged_manifest.read_bytes():
                raise ValueError("model manifest changed during publication") from None
    return model_status(language, root, profile=profile)


def load_stanza_pipeline(language: str, root: Path, *, threads: int = 1, profile: str = "fast"):
    import stanza
    import torch
    from stanza.pipeline.core import DownloadMethod

    spec = model_spec(language)
    _profile(profile)
    if spec.backend != "stanza":
        raise ValueError("unsupported Stanza backend/profile")
    if not 1 <= threads <= 8:
        raise ValueError("CPU model threads must be between 1 and 8")
    # Small sentence batches otherwise oversubscribe many-core shared machines.
    torch.set_num_threads(threads)
    manifest = verify_model_manifest(_manifest_path(root, language, profile))
    if (
        manifest.get("language") != language
        or manifest.get("backend") != "stanza"
        or manifest.get("package_version") != stanza.__version__
        or manifest.get("model_language") != spec.model_language
    ):
        raise ValueError("model package, backend or language drift")
    options = {}
    if profile != "fast":
        from multilang.services.transformer_artifacts import local_foundation_cache

        options["foundation_cache"] = local_foundation_cache(manifest, Path(root))
    return stanza.Pipeline(
        **options,
        lang=spec.model_language,
        dir=str(root),
        package=None,
        processors=manifest["processors"],
        download_method=DownloadMethod.NONE,
        resources_version=manifest["resource_version"],
        use_gpu=False,
        verbose=False,
    )
