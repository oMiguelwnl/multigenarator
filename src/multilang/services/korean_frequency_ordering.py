"""Fail closed for the legacy Korean frequency generation contract.

The v1 inventory establishes source identity and contiguous inventory positions,
not qualified frequency ordering. In particular, its historical NIKL source_rank
can be a source-row ordinal. Source/rights review receipts do not repair that.

There is deliberately no approval flag, version-label exception, or caller-built
attestation. A future contract must verify ordering policy against the exact
inventory, source snapshot and lexical identities before enabling generation.
Historical source validation and semantic preparation remain separate operations.
"""

from typing import NoReturn

from multilang.domain.jobs import SupportedLanguage


class KoreanFrequencyOrderingError(ValueError):
    """The requested frequency generation lacks qualified rank provenance."""


def require_candidate_frequency_ordering(
    candidate: object, *, deck_language: SupportedLanguage, source_type: str | None = None,
) -> None:
    """Reject future generation from explicit legacy Korean frequency evidence.

    Persisted rows expose ``lexical_evidence``; domain candidates expose
    ``korean_frequency_evidence``. Explicit ko/frequency also identifies older
    rows without that evidence. This is the current legacy contract, not an
    implicit policy for a future v2 reader. Generic rank fields and lemma text
    deliberately do not establish frequency origin.
    """
    explicit_source = source_type or getattr(candidate, "source_type", None)
    value = getattr(candidate, "candidate", candidate)
    has_evidence = any(
        getattr(value, name, None) is not None
        for name in ("korean_frequency_evidence", "lexical_evidence")
    )
    if has_evidence or (deck_language == SupportedLanguage.KO and explicit_source == "frequency"):
        reject_legacy_korean_frequency_ordering()


def reject_legacy_korean_frequency_ordering() -> NoReturn:
    """Reject every v1 generation request, including an empty inventory."""

    raise KoreanFrequencyOrderingError(
        "Korean frequency ordering is unqualified: the v1 contract does not bind "
        "frequency ranks to verified source evidence and lexical identities. "
        "Continue offline inventory preparation and ordering qualification; "
        "a qualified replacement generation contract is not implemented yet. "
        "Historical source validation and semantic review remain available."
    )
