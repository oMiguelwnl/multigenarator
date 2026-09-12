"""Explicit local model preparation; ordinary analysis never downloads models."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
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


def stanza_processors(registry: dict, language: str) -> dict[str, str]:
    entry = registry.get(language)
    if not isinstance(entry, dict) or "alias" in entry:
        raise ValueError("model language requires an explicit available registry entry")
    defaults = entry.get("packages", {}).get("default", entry.get("default_processors", {}))
    processors = {}
    for name in ("tokenize", "mwt", "pos", "lemma"):
        selected = defaults.get(name)
        if not selected and name == "mwt":
            continue
        if not isinstance(selected, str):
            raise ValueError(f"required {name} model is not available")
        choices = entry.get(name, {})
        lightweight = selected.removesuffix("_charlm") + "_nocharlm"
        if name in {"pos", "lemma"} and lightweight in choices:
            selected = lightweight
        if selected not in choices:
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
    if manifest["processors"] != stanza_processors(registry, spec.model_language):
        raise ValueError("model processors differ from pinned registry selection")
    required = _required_models(registry, spec.model_language, manifest["processors"])
    if set(manifest["files"]) != {"resources.json", *required}:
        raise ValueError("model manifest does not cover all required models and dependencies")
    for relative, expected in required.items():
        target = path.parent / relative
        stat = target.stat()
        state = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
        if _upstream_md5(target, state) != expected:
            raise ValueError("model bytes differ from pinned upstream artifact")
    return manifest


def model_status(language: str, root: Path) -> dict:
    spec = model_spec(language)
    try:
        version = importlib.metadata.version(spec.package)
    except importlib.metadata.PackageNotFoundError:
        return {
            "language": language,
            "backend": spec.backend,
            "available": False,
            "reason": "package_missing",
        }
    if spec.backend != "stanza":
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
        manifest = verify_model_manifest(Path(root) / f"{language}.manifest.json")
        if manifest.get("language") != language or manifest.get("package_version") != version:
            raise ValueError("model package or language drift")
        return {
            "language": language,
            "backend": spec.backend,
            "available": True,
            "package_version": version,
            "manifest_sha256": canonical_sha256(manifest),
            "qualified": False,
        }
    except (ValueError, OSError):
        return {
            "language": language,
            "backend": spec.backend,
            "available": False,
            "reason": "model_missing_or_drifted",
            "package_version": version,
        }


def prepare_model(language: str, root: Path) -> dict:
    """Explicit operator action fetching official pinned model resources for CPU."""
    spec = model_spec(language)
    root = _plain_path(root)
    root.mkdir(parents=True, exist_ok=True)
    if spec.backend != "stanza":
        status = model_status(language, root)
        if not status["available"]:
            raise ValueError("install the language dictionary/model package first")
        return status
    import stanza

    resource_path = root / "resources.json"
    _plain_path(resource_path)
    url = f"{STANZA_RESOURCES_URL}/resources_{STANZA_RESOURCES_VERSION}.json"
    with urlopen(url, timeout=60) as response:
        content = response.read(32 * 1024**2 + 1)
    if len(content) > 32 * 1024**2:
        raise ValueError("official model registry exceeds byte limit")
    if hashlib.sha256(content).hexdigest() != STANZA_RESOURCES_SHA256:
        raise ValueError("official model registry checksum mismatch")
    registry = json.loads(content)
    processors = stanza_processors(registry, spec.model_language)
    # Check every destination and ancestor before the vendor downloader can
    # follow a preexisting directory/file link outside the chosen model root.
    _plain_path(root / f"{language}.manifest.json")
    for relative in _required_models(registry, spec.model_language, processors):
        _plain_path(root / relative)
    # The pinned registry URL is explicit, never a value supplied by an API input.
    if resource_path.exists() and resource_path.read_bytes() != content:
        raise ValueError("model registry changed; prepare in a new version directory")
    if not resource_path.exists():
        resource_path.write_bytes(content)
    stanza.download(
        lang=spec.model_language,
        model_dir=str(root),
        package=None,
        processors=processors,
        resources_url=STANZA_RESOURCES_URL,
        resources_version=STANZA_RESOURCES_VERSION,
        download_json=False,
        verbose=False,
    )
    files = {"resources.json": _file_digest(resource_path)}
    for path in sorted((root / spec.model_language).rglob("*.pt")):
        _plain_path(path)
        files[path.relative_to(root).as_posix()] = _file_digest(path)
    if len(files) < 2:
        raise ValueError("no model artifacts downloaded")
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
    path = _plain_path(root / f"{language}.manifest.json")
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    verify_model_manifest(path)
    return model_status(language, root)


def load_stanza_pipeline(language: str, root: Path, *, threads: int = 1):
    import stanza
    import torch
    from stanza.pipeline.core import DownloadMethod

    spec = model_spec(language)
    if not 1 <= threads <= 8:
        raise ValueError("CPU model threads must be between 1 and 8")
    # Small sentence batches otherwise oversubscribe many-core shared machines.
    torch.set_num_threads(threads)
    manifest = verify_model_manifest(Path(root) / f"{language}.manifest.json")
    if (
        manifest.get("language") != language
        or manifest.get("backend") != "stanza"
        or manifest.get("package_version") != stanza.__version__
        or manifest.get("model_language") != spec.model_language
    ):
        raise ValueError("model package, backend or language drift")
    return stanza.Pipeline(
        lang=spec.model_language,
        dir=str(root),
        package=None,
        processors=manifest["processors"],
        download_method=DownloadMethod.NONE,
        resources_version=manifest["resource_version"],
        use_gpu=False,
        verbose=False,
    )
