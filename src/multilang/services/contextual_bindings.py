"""Namespace-bound, signed contextual sense evidence for local generation."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import Field, model_validator

from multilang.domain.content import ContentRequest
from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualTargetMatcher,
    ReviewedSenseBinding,
    sentence_hash,
)
from multilang.services.vocabulary_sources import _modern_language


class ContextualBindingSet(NativeContract):
    namespace: str = Field(pattern=r"^(?:core|user:[^\x00-\x1f]{1,128})$")
    language: str
    profile_version: str = Field(min_length=1, max_length=128)
    bindings: tuple[ReviewedSenseBinding, ...] = Field(min_length=1, max_length=4096)
    receipt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_context(self):
        _modern_language(self.language)
        if any(binding.language != self.language for binding in self.bindings):
            raise ValueError("binding set language mismatch")
        if len({binding.sentence_sha256 for binding in self.bindings}) != 1:
            raise ValueError("binding set must describe exactly one source sentence")
        if len({(binding.start, binding.end) for binding in self.bindings}) != len(self.bindings):
            raise ValueError("binding set has ambiguous or duplicate token spans")
        return self


class ReviewedBindingStore:
    def __init__(self, root: Path, *, verifier: Callable):
        self.root, self.verifier = Path(root).absolute(), verifier

    def _path(self, namespace: str, language: str, sentence_sha256: str, version: str) -> Path:
        _modern_language(language)
        if not re.fullmatch(r"[a-f0-9]{64}", sentence_sha256):
            raise ValueError("sentence identifier must be a SHA-256")
        if not re.fullmatch(r"(?:core|user:[^\x00-\x1f]{1,128})", namespace):
            raise ValueError("binding namespace invalid")
        scope = canonical_sha256({"namespace": namespace, "profile_version": version})
        path = self.root / scope / language / f"{sentence_sha256}.json"
        if any(item.is_symlink() for item in (path, *path.parents)):
            raise ValueError("binding path cannot contain a symlink")
        return path

    def _verify(self, value: ContextualBindingSet) -> None:
        payload = value.model_dump(mode="json", exclude={"receipt_sha256"})
        if not self.verifier(value.receipt_sha256, payload, purpose="contextual-binding-set"):
            raise ValueError("binding set signature invalid, missing or expired")
        for binding in value.bindings:
            if not self.verifier(
                binding.review_receipt_sha256,
                binding.model_dump(mode="json", exclude={"review_receipt_sha256"}),
                purpose="contextual-sense-binding",
            ):
                raise ValueError("contextual sense signature invalid, missing or expired")

    def put(self, value: ContextualBindingSet) -> dict:
        value = ContextualBindingSet.model_validate(value.model_dump(mode="json"))
        path = self._path(
            value.namespace,
            value.language,
            value.bindings[0].sentence_sha256,
            value.profile_version,
        )
        self._verify(value)
        content = value.model_dump_json().encode()
        if len(content) > 8 * 1024**2:
            raise ValueError("binding set exceeds size limit")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.stat().st_size > 8 * 1024**2 or path.read_bytes() != content:
                raise ValueError("immutable binding set already exists with different evidence")
        else:
            with TemporaryDirectory(prefix=".binding-", dir=path.parent) as directory:
                temporary = Path(directory) / "set.json"
                temporary.write_bytes(content)
                os.link(temporary, path)
        return {
            "binding_set_sha256": canonical_sha256(value.model_dump(mode="json")),
            "binding_count": len(value.bindings),
            "namespace": value.namespace,
        }

    def load(
        self, namespace: str, language: str, sentence_sha256: str, profile_version: str
    ) -> tuple[ReviewedSenseBinding, ...]:
        path = self._path(namespace, language, sentence_sha256, profile_version)
        if not path.exists():
            return ()
        if not path.is_file() or path.stat().st_size > 8 * 1024**2:
            raise ValueError("binding set missing or oversized")
        value = ContextualBindingSet.model_validate_json(path.read_bytes())
        if (
            value.namespace != namespace
            or value.language != language
            or value.profile_version != profile_version
            or value.bindings[0].sentence_sha256 != sentence_sha256
        ):
            raise ValueError("binding set source or namespace mismatch")
        self._verify(value)
        return value.bindings


class StoredContextualTargetMatcher:
    """Use authenticated persisted bindings through the existing content callable."""

    def __init__(self, *, analyzer, store: ReviewedBindingStore):
        self.analyzer, self.store = analyzer, store

    def __call__(self, request: ContentRequest, sentence: str):
        bindings = self.store.load(
            request.namespace,
            request.language,
            sentence_hash(sentence),
            request.language_profile_version,
        )
        return ContextualTargetMatcher(analyzer=self.analyzer, bindings=bindings)(request, sentence)
