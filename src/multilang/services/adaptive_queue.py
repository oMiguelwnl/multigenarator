"""Deterministic preparation priority; never writes rank, content or Anki scheduling."""

from __future__ import annotations

from collections.abc import Iterable

from multilang.domain.anki_semantics import SemanticCard
from multilang.domain.content import canonical_content_hash
from multilang.domain.learning import (
    AdaptivePolicy,
    AdaptiveQueueResult,
    DeferredCard,
    LearnerState,
    QueueEntry,
)


def build_adaptive_queue(
    *,
    cards: Iterable[SemanticCard],
    learner_state: LearnerState,
    policy: AdaptivePolicy | None = None,
) -> AdaptiveQueueResult:
    from multilang.services.semantic_anki import (
        summarize_cards,
        validate_semantic_cards,
    )

    policy = policy or AdaptivePolicy()
    learner_state = LearnerState.model_validate(learner_state.model_dump(mode="json"))
    items = tuple(cards)
    if len(items) > policy.max_cards:
        raise ValueError(
            "adaptive queue workload limit exceeded; mandatory forms cannot be truncated"
        )
    validate_semantic_cards(items, require_full_core=False)
    source_hash = canonical_content_hash(
        [
            card.model_dump(mode="json")
            for card in sorted(items, key=lambda c: c.card_id)
        ]
    )
    known = set(learner_state.known_card_ids)
    history = {
        state.semantic_card_id: state
        for item in learner_state.history
        for state in item.states
    }
    # Only explicit known flags establish mastery. A review count is not mastery.
    ranked: list[tuple[SemanticCard, dict[str, int]]] = []
    deferred: list[DeferredCard] = []
    for card in sorted(items, key=lambda c: c.card_id):
        reason = None
        if card.namespace not in {"core", learner_state.namespace}:
            reason = "private_namespace"
        elif card.card_id in known:
            reason = "known"
        elif card.inventory == "expansion" and not learner_state.expansion_enabled:
            reason = "expansion_disabled"
        elif card.prerequisite_card_id and card.prerequisite_card_id not in known:
            reason = "prerequisite"
        elif policy.require_ready_content and (
            card.content is None
            or card.content.review_status != "approved"
            or card.word_audio is None
            or card.word_audio.review_status != "approved"
        ):
            reason = "content_not_ready"
        if reason:
            deferred.append(DeferredCard(card_id=card.card_id, reason=reason))
            continue
        reading_weight = {"core_first": 100, "balanced": 2000, "reading_first": 6000}[
            policy.mode
        ]
        core_weight = {"core_first": 6000, "balanced": 2000, "reading_first": 100}[
            policy.mode
        ]
        previous = history.get(card.card_id)
        components = {
            "editorial_rank": max(0, 3001 - (card.rank or 3001)),
            "core_mode": core_weight if card.inventory == "core" else 0,
            "reading_mode": reading_weight
            if card.card_id in learner_state.reading_card_ids
            else 0,
            "review_difficulty": min(1000, previous.lapses * 100) if previous else 0,
            "override": learner_state.overrides.get(card.card_id, 0),
        }
        ranked.append((card, components))
    ranked.sort(key=lambda row: (-sum(row[1].values()), row[0].card_id))
    entries = tuple(
        QueueEntry(
            card_id=card.card_id,
            score=sum(parts.values()),
            components=parts,
            module=index // policy.module_size + 1,
            destination=card.destination,
        )
        for index, (card, parts) in enumerate(ranked)
    )
    policy_hash = canonical_content_hash(policy.model_dump(mode="json"))
    queue_hash = canonical_content_hash(
        {
            "source": source_hash,
            "policy": policy_hash,
            "learner": learner_state.model_dump(mode="json"),
            "entries": [e.model_dump() for e in entries],
        }
    )
    return AdaptiveQueueResult(
        namespace=learner_state.namespace,
        policy_sha256=policy_hash,
        source_snapshot_sha256=source_hash,
        queue_sha256=queue_hash,
        eligible=entries,
        deferred=tuple(deferred),
        counts=summarize_cards(items),
    )


def reset_adaptation(state: LearnerState) -> LearnerState:
    """Reset personal ordering preferences; retain separately revocable imported facts."""
    return LearnerState(
        namespace=state.namespace, history=state.history, revision=state.revision + 1
    )


def revoke_history(state: LearnerState, import_id: str) -> LearnerState:
    remaining = tuple(item for item in state.history if item.import_id != import_id)
    if len(remaining) == len(state.history):
        raise ValueError("unknown history import")
    return LearnerState.model_validate(
        state.model_dump(mode="json")
        | {"history": remaining, "revision": state.revision + 1}
    )


def override_priority(
    state: LearnerState, *, card_id: str, priority: int | None
) -> LearnerState:
    overrides = dict(state.overrides)
    if priority is None:
        overrides.pop(card_id, None)
    else:
        overrides[card_id] = priority
    return LearnerState.model_validate(
        state.model_dump(mode="json")
        | {"overrides": overrides, "revision": state.revision + 1}
    )
