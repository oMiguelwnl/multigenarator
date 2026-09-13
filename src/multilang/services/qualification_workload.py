"""Inspectable workload estimates; this module performs no provider calls."""

from decimal import Decimal
from typing import Literal

from pydantic import Field

from multilang.domain.language_profiles import NativeContract


class QualificationWorkload(NativeContract):
    headword_candidates: int
    observed_form_candidates: int
    selected_form_cards: int | None
    optional_role_cards: int
    expected_card_count: int | None
    content_units: int | None
    reviewed_grounding_cards: int
    text_requests: int | None
    word_audio_requests: int | None
    sentence_audio_requests: int | None
    cached_text_cards: int
    cached_word_audio: int
    cached_sentence_audio: int
    expected_cost: Decimal | None
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    price_basis: str | None
    cost_missing_reason: str | None
    export_bytes: int | None = None
    export_size_reason: str = "Exact package size requires completed text and audio media"
    blockers: tuple[str, ...]
    provider_calls_executed: Literal[0] = 0
    production_eligible: Literal[False] = False


def qualification_workload(
    *,
    headwords: int,
    observed_forms: int = 0,
    selected_forms: int | None = None,
    optional_role_cards: int = 0,
    reviewed_grounding_cards: int = 0,
    cached_text_cards: int = 0,
    cached_word_audio: int = 0,
    cached_sentence_audio: int = 0,
    text_request_price: Decimal | None = None,
    audio_request_price: Decimal | None = None,
    currency: str = "USD",
    price_basis: str | None = None,
) -> QualificationWorkload:
    """Counts must refer to the same frozen selection/cache inventory.

    Per-request prices are explicit estimates supplied by the operator, not live
    provider tariffs. Token/character prices must first be converted using actual
    text sizes. Counts never limit or truncate important forms.
    """
    numbers = [
        headwords,
        observed_forms,
        optional_role_cards,
        reviewed_grounding_cards,
        cached_text_cards,
        cached_word_audio,
        cached_sentence_audio,
    ]
    if selected_forms is not None:
        numbers.append(selected_forms)
    if any(type(n) is not int or not 0 <= n <= 1000000 for n in numbers):
        raise ValueError("workload counts must be bounded nonnegative integers")
    if selected_forms is not None and selected_forms > observed_forms:
        raise ValueError("selected forms exceed observed forms")
    prices = [Decimal(p) for p in (text_request_price, audio_request_price) if p is not None]
    if any(not p.is_finite() or not 0 <= p <= 1000000 for p in prices):
        raise ValueError("invalid price estimate")
    if prices and not (price_basis and price_basis.strip()):
        raise ValueError("price estimates require an explicit dated/source basis")
    if price_basis and len(price_basis) > 4000:
        raise ValueError("price basis exceeds limit")
    units = headwords + selected_forms if selected_forms is not None else None
    total = units + optional_role_cards if units is not None else None
    if units is not None and any(n > units for n in numbers[3:6]):
        raise ValueError("cache/grounding counts exceed selected workload")
    if units is not None and cached_sentence_audio > units:
        raise ValueError("cache counts exceed selected workload")
    text = units - cached_text_cards if units is not None else None
    word = units - cached_word_audio if units is not None else None
    sentence = units - cached_sentence_audio if units is not None else None
    cost = None
    if total is not None and text_request_price is not None and audio_request_price is not None:
        cost = Decimal(text) * Decimal(text_request_price) + Decimal(word + sentence) * Decimal(
            audio_request_price
        )
    blockers = []
    if selected_forms is None:
        blockers.append("reviewed_importance_selection")
    if units is None or reviewed_grounding_cards < units:
        blockers.append("reviewed_lexical_grounding")
    blockers.extend(
        (
            "provider_budget_authorization",
            "reviewed_content_and_audio",
            "language_qualification",
            "anki_client_acceptance",
        )
    )
    return QualificationWorkload(
        headword_candidates=headwords,
        observed_form_candidates=observed_forms,
        selected_form_cards=selected_forms,
        optional_role_cards=optional_role_cards,
        expected_card_count=total,
        content_units=units,
        reviewed_grounding_cards=reviewed_grounding_cards,
        text_requests=text,
        word_audio_requests=word,
        sentence_audio_requests=sentence,
        cached_text_cards=cached_text_cards,
        cached_word_audio=cached_word_audio,
        cached_sentence_audio=cached_sentence_audio,
        expected_cost=cost,
        currency=currency,
        price_basis=price_basis,
        cost_missing_reason=None
        if cost is not None
        else "Frozen reviewed selection and explicit text/audio pricing estimates are required",
        blockers=tuple(blockers),
    )
