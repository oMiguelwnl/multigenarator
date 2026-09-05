"""Deterministic request fingerprinting for generation jobs."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
import unicodedata

from multilang.domain.jobs import GenerationRequest
from multilang.domain.personal_sources import PersonalSourceRow


_KOREAN_ORDERED_SOURCE_FINGERPRINT_VERSION = "korean-ordered-source-v1"


def normalize_requested_item_keys(requested_item_keys: Iterable[str]) -> list[str]:
    """Normalize item keys so rerun decisions are deterministic."""

    normalized = {
        unicodedata.normalize("NFC", item).strip().lower()
        for item in requested_item_keys
        if item and item.strip()
    }
    return sorted(normalized)


def build_input_fingerprint(
    request: GenerationRequest,
    *,
    requested_item_keys: Iterable[str] = (),
) -> str:
    """Build a reproducible fingerprint for the requested input."""

    if request.source_type == "frequency":
        cards_per_level = request.resolved_cards_per_level()
        if request.level is None:
            return f"levels:1-3:cards:{cards_per_level}"
        return f"level:{request.level}:cards:{cards_per_level}"

    normalized = normalize_requested_item_keys(requested_item_keys)
    digest = sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    return f"items:{digest}"


def _length_frame(value: str) -> str:
    return f"{len(value.encode('utf-8'))}:{value}"


def build_korean_ordered_source_fingerprint(rows: Iterable[PersonalSourceRow]) -> str:
    """Hash Korean custom-list order, positions, and retained repeats."""

    frames = [_KOREAN_ORDERED_SOURCE_FINGERPRINT_VERSION]
    for row in rows:
        duplicate_of = (
            "" if row.duplicate_of_position is None else str(row.duplicate_of_position)
        )
        frames.append(
            "|".join(
                (
                    f"position={row.input_position}",
                    f"duplicate_of={duplicate_of}",
                    f"display={_length_frame(row.display_form)}",
                    f"duplicate_key={_length_frame(row.normalized_duplicate_key)}",
                )
            )
        )
    digest = sha256("\n".join(frames).encode("utf-8")).hexdigest()
    return f"{_KOREAN_ORDERED_SOURCE_FINGERPRINT_VERSION}:{digest}"


def build_run_key(
    request: GenerationRequest,
    *,
    requested_item_keys: Iterable[str] = (),
) -> str:
    """Build a deterministic run key from request identity."""

    fingerprint = build_input_fingerprint(request, requested_item_keys=requested_item_keys)
    return f"{request.language.value}:{request.source_type}:{fingerprint}"
