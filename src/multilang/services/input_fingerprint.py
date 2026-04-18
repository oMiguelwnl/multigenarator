"""Deterministic request fingerprinting for generation jobs."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256

from multilang.domain.jobs import GenerationRequest


def normalize_requested_item_keys(requested_item_keys: Iterable[str]) -> list[str]:
    """Normalize item keys so rerun decisions are deterministic."""

    normalized = {item.strip().lower() for item in requested_item_keys if item and item.strip()}
    return sorted(normalized)


def build_input_fingerprint(
    request: GenerationRequest,
    *,
    requested_item_keys: Iterable[str] = (),
) -> str:
    """Build a reproducible fingerprint for the requested input."""

    if request.source_type == "frequency":
        if request.level is None:
            raise ValueError("frequency requests require a level")
        return f"level:{request.level}"

    normalized = normalize_requested_item_keys(requested_item_keys)
    digest = sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    return f"items:{digest}"


def build_run_key(
    request: GenerationRequest,
    *,
    requested_item_keys: Iterable[str] = (),
) -> str:
    """Build a deterministic run key from request identity."""

    fingerprint = build_input_fingerprint(request, requested_item_keys=requested_item_keys)
    return f"{request.language.value}:{request.source_type}:{fingerprint}"
