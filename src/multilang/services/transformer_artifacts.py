"""Explicit, bounded transformer snapshots and sealed offline Stanza injection.

Repository names are fixed here; checkpoint configurations must agree. Snapshot
commit IDs and every runtime file are bound into the profile manifest. No Hub
client/cache is used for preparation or inference.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
import shutil
from pathlib import Path
from urllib.request import urlopen

# Registry 1.10.0 default_accurate POS variants. Source: Stanza's official
# resources/default_packages.py; checkpoint configuration is checked at prepare.
TRANSFORMERS = {
    "en": ("electra-large", "google/electra-large-discriminator"),
    "da": ("scandibert", "vesteinn/ScandiBERT"),
    "fi": ("bert", "TurkuNLP/bert-base-finnish-cased-v1"),
    "ar": ("aubmind-electra", "aubmindlab/araelectra-base-discriminator"),
    "de": ("german-nlp-electra", "german-nlp-group/electra-base-german-uncased"),
    "es": ("bertin-roberta", "bertin-project/bertin-roberta-base-spanish"),
    "fr": ("camembert-large", "camembert/camembert-large"),
    "hi": ("muril-large-cased", "google/muril-large-cased"),
    "it": ("electra", "dbmdz/electra-base-italian-xxl-cased-discriminator"),
    "pl": ("herbert", "allegro/herbert-base-cased"),
    "pt": ("bertimbau", "neuralmind/bert-large-portuguese-cased"),
    "tr": ("bert", "dbmdz/bert-base-turkish-128k-cased"),
    "vi": ("phobert-large", "vinai/phobert-large"),
    "zh-hans": ("electra-large", "hfl/chinese-electra-180g-large-discriminator"),
}
TOKENIZER_FILES = {
    "config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.txt",
    "vocab.json",
    "merges.txt",
    "sentencepiece.bpe.model",
    "tokenizer.model",
    "spiece.model",
    "bpe.codes",
    "dict.txt",
}
WEIGHT_FILES = {"model.safetensors", "pytorch_model.bin"}
MAX_FILE_BYTES = 2 * 1024**3
MAX_TOTAL_BYTES = 8 * 1024**3


def _expected(manifest: dict) -> list[str]:
    package = manifest["processors"].get("pos", "")
    if package.endswith(("_charlm", "_nocharlm")) or "_" not in package:
        return []
    choice = TRANSFORMERS.get(manifest["model_language"])
    if not choice or not package.endswith("_" + choice[0]):
        raise ValueError("transformer dependency is not in the trusted catalog")
    return [choice[1]]


def transformer_runtime_available(manifest: dict) -> bool:
    """Inspect distribution metadata only; status must not import model runtimes."""
    if not _expected(manifest):
        return True
    try:
        for package in ("transformers", "sentencepiece"):
            importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def _base(repo: str, revision: str) -> str:
    return f"transformers/{hashlib.sha256(repo.encode()).hexdigest()}/{revision}"


def _fetch(url: str, maximum: int) -> bytes:
    with urlopen(url, timeout=60) as response:
        result = response.read(maximum + 1)
    if len(result) > maximum:
        raise ValueError("transformer response exceeds byte bounds")
    return result


def _validate_checkpoint(manifest: dict, root: Path, repo: str) -> None:
    import torch

    language = manifest["model_language"]
    package = manifest["processors"]["pos"]
    checkpoint = torch.load(
        root / language / "pos" / f"{package}.pt", map_location="cpu", weights_only=True
    )
    config = checkpoint.get("config", {})
    if config.get("bert_model") != repo:
        raise ValueError("checkpoint transformer differs from trusted dependency")
    # Stanza bypasses FoundationCache when fine-tuned transformer tensors are
    # embedded. Reject that layout rather than accidentally consulting HF cache.
    if (
        config.get("use_peft")
        or checkpoint.get("bert_lora")
        or any(name.startswith("bert_model.") for name in checkpoint.get("model", {}))
    ):
        raise ValueError("checkpoint transformer layout cannot use sealed offline cache")


def prepare_dependencies(manifest: dict, root: Path, *, existing_root: Path) -> list[dict]:
    from multilang.services.language_models import _file_digest, _plain_path

    dependencies = []
    for repo in _expected(manifest):
        _validate_checkpoint(manifest, root, repo)
        # Reuse only a complete dependency from an already verified profile.
        reused = None
        for candidate in sorted(existing_root.glob("*.manifest.json"))[:256]:
            from multilang.services.language_models import verify_model_manifest

            try:
                previous = verify_model_manifest(candidate)
            except (OSError, ValueError):
                # Reuse is optional. An unrelated invalid profile cannot block
                # preparation, and none of its unverified bytes may be reused.
                continue
            for dependency in previous.get("external_dependencies", []):
                if dependency["repo_id"] == repo:
                    reused = dependency
                    break
            if reused:
                break
        if reused:
            for relative in reused["files"]:
                target = _plain_path(root / relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(_plain_path(existing_root / relative), target)
            dependencies.append(reused)
            continue
        info = json.loads(_fetch(f"https://huggingface.co/api/models/{repo}", 4 * 1024**2))
        revision = info.get("sha")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("transformer revision is not an immutable commit")
        siblings = info.get("siblings")
        if not isinstance(siblings, list) or len(siblings) > 2048:
            raise ValueError("transformer repository file count exceeds bounds")
        names = {item.get("rfilename") for item in siblings if isinstance(item, dict)}
        weights = "model.safetensors" if "model.safetensors" in names else "pytorch_model.bin"
        selected = (names & TOKENIZER_FILES) | ({weights} if weights in names else set())
        if "config.json" not in selected or weights not in selected:
            raise ValueError("transformer snapshot requires config and unsharded model weights")
        if not selected & {
            "tokenizer.json",
            "vocab.txt",
            "vocab.json",
            "sentencepiece.bpe.model",
            "spiece.model",
            "tokenizer.model",
        }:
            raise ValueError("transformer snapshot requires tokenizer artifacts")
        files = {}
        total = 0
        for name in sorted(selected):
            maximum = MAX_FILE_BYTES if name in WEIGHT_FILES else 32 * 1024**2
            content = _fetch(f"https://huggingface.co/{repo}/resolve/{revision}/{name}", maximum)
            total += len(content)
            if total > MAX_TOTAL_BYTES:
                raise ValueError("transformer snapshot exceeds total byte bounds")
            relative = f"{_base(repo, revision)}/{name}"
            path = _plain_path(root / relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            files[relative] = _file_digest(path)
        dependencies.append({"repo_id": repo, "revision": revision, "files": files})
    return dependencies


def verify_dependencies(manifest: dict, root: Path) -> dict[str, str]:
    from multilang.services.language_models import _file_digest, _plain_path

    dependencies = manifest.get("external_dependencies")
    expected = _expected(manifest)
    if not isinstance(dependencies, list) or len(dependencies) != len(expected):
        raise ValueError("transformer dependency inventory differs from trusted catalog")
    all_files = {}
    for dependency, repo in zip(dependencies, expected, strict=True):
        if not isinstance(dependency, dict) or set(dependency) != {"repo_id", "revision", "files"}:
            raise ValueError("transformer dependency metadata is malformed")
        revision = dependency["revision"]
        if (
            dependency["repo_id"] != repo
            or not isinstance(revision, str)
            or not re.fullmatch(r"[0-9a-f]{40}", revision)
        ):
            raise ValueError("transformer dependency differs from trusted repository or revision")
        files = dependency["files"]
        if not isinstance(files, dict) or not 2 <= len(files) <= 32:
            raise ValueError("transformer dependency file count exceeds bounds")
        base = _base(repo, revision)
        names = set()
        total = 0
        for relative, digest in files.items():
            name = relative.removeprefix(base + "/")
            if relative != base + "/" + name or name not in TOKENIZER_FILES | WEIGHT_FILES:
                raise ValueError("transformer dependency path escapes trusted inventory")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("transformer dependency checksum is malformed")
            path = _plain_path(root / relative)
            maximum = MAX_FILE_BYTES if name in WEIGHT_FILES else 32 * 1024**2
            if not path.is_file() or path.stat().st_size > maximum:
                raise ValueError("transformer dependency missing or oversized")
            total += path.stat().st_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("transformer dependency total bytes exceed bounds")
            if _file_digest(path) != digest or manifest["files"].get(relative) != digest:
                raise ValueError("transformer dependency checksum mismatch")
            names.add(name)
        if "config.json" not in names or len(names & WEIGHT_FILES) != 1:
            raise ValueError("transformer dependency requires config and one model weight file")
        if not names & {
            "tokenizer.json",
            "vocab.txt",
            "vocab.json",
            "sentencepiece.bpe.model",
            "spiece.model",
            "tokenizer.model",
        }:
            raise ValueError("transformer dependency tokenizer files are missing")
        directory = _plain_path(root / base)
        actual = set()
        for child in directory.iterdir():
            _plain_path(child)
            actual.add(child.name)
            if len(actual) > 32:
                raise ValueError("transformer local inventory exceeds file bounds")
        if actual != names:
            raise ValueError("transformer local inventory differs from manifest")
        all_files.update(files)
    return all_files


class _SealedTransformers(dict):
    """Prevent Stanza's copied cache from consulting any ambient HF cache."""

    def __contains__(self, key):
        if not super().__contains__(key):
            raise ValueError("unverified transformer requested by model checkpoint")
        return True


def local_foundation_cache(manifest: dict, root: Path):
    from multilang.services.language_models import _plain_path

    verify_dependencies(manifest, root)
    from stanza.models.common.foundation_cache import BertRecord, FoundationCache

    cache = FoundationCache(local_files_only=True)
    records = {}
    for dependency in manifest["external_dependencies"]:
        from stanza.models.common.bert_embedding import BERT_ARGS, update_max_length
        from transformers import AutoModel, AutoTokenizer

        repo = dependency["repo_id"]
        local = str(_plain_path(root / _base(repo, dependency["revision"])))
        tokenizer_args = dict(BERT_ARGS.get(repo, {}))
        if not repo.startswith("vinai/phobert"):
            tokenizer_args["add_prefix_space"] = True
        model = AutoModel.from_pretrained(
            local,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=any(
                name.endswith("/model.safetensors") for name in dependency["files"]
            ),
        )
        tokenizer = AutoTokenizer.from_pretrained(
            local, **tokenizer_args, local_files_only=True, trust_remote_code=False
        )
        update_max_length(repo, tokenizer)
        records[repo] = BertRecord(model, tokenizer, {})
    cache.bert = _SealedTransformers(records)
    return cache
