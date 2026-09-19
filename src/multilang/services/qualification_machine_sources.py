"""Bind review excerpts to local bytes; integrity is not linguistic or licensing authority."""

from pathlib import Path

from pydantic import Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.services.qualification_review import ReviewSource
from multilang.services.vocabulary_review import _read_bytes

_MAX_BYTES = 16 * 1024**2


class VerifiedReviewExcerpt(NativeContract):
    path: Path
    file_sha256: Sha256
    source_id: Identifier
    record_id: Identifier
    language: SupportedLanguage
    start: int = Field(ge=0, le=_MAX_BYTES, strict=True)
    end: int = Field(gt=0, le=_MAX_BYTES, strict=True)

    @model_validator(mode="after")
    def bounded_span(self):
        if not self.start < self.end or self.end - self.start > 64000:
            raise ValueError("review excerpt source span is invalid or exceeds limit")
        return self


def load_verified_review_excerpt(
    reference: VerifiedReviewExcerpt, *, language: SupportedLanguage
) -> ReviewSource:
    """Read a hash-verified UTF-8 character span without interpreting its contents."""
    reference = VerifiedReviewExcerpt.model_validate(reference.model_dump(mode="json"))
    if reference.language != SupportedLanguage(language):
        raise ValueError("review excerpt language does not match packet")
    raw = _read_bytes(reference.path, reference.file_sha256, limit=_MAX_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("review excerpt source must be UTF-8") from None
    if reference.end > len(text):
        raise ValueError("review excerpt span exceeds source text")
    return ReviewSource(
        source_id=reference.source_id,
        source_sha256=reference.file_sha256,
        record_id=reference.record_id,
        excerpt=text[reference.start : reference.end],
    )


__all__ = ["VerifiedReviewExcerpt", "load_verified_review_excerpt"]
