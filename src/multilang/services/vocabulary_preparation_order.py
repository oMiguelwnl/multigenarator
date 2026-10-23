"""Deterministic preparation order from existing source priorities.

The order is provisional. It is not a calibrated cross-source frequency rank.
"""

from __future__ import annotations

import copy

from multilang.services.vocabulary_adjudication import _hash


def _positive_int(value):
    return type(value) is int and value > 0


def order_identities(identities, source_rows, pending_review_units):
    """Keep every lexical identity, including those linked to form-only rows."""
    prepared = []
    for identity in identities:
        traces = []
        for uid in identity["review_unit_ids"]:
            row = source_rows[uid]
            group = row.get("source_group") or {}
            own = group.get("entry_id") == identity["source_entry_id"]
            traces.append(
                dict(
                    review_unit_id=uid,
                    inventory_row_sha256=_hash(row),
                    source_priority=group.get("source_priority"),
                    prior_provisional_order=group.get("provisional_order"),
                    prior_proposed_band=group.get("proposed_band"),
                    source_binding=row.get("source_binding"),
                    priority_role="own_lexical_entry" if own else "linked_form_or_context_not_used_for_order",
                    contains_open_questions=uid in pending_review_units,
                )
            )
        own_traces = [trace for trace in traces if trace["priority_role"] == "own_lexical_entry"]
        priorities = sorted({trace["source_priority"] for trace in own_traces if _positive_int(trace["source_priority"])})
        orders = sorted({trace["prior_provisional_order"] for trace in own_traces if _positive_int(trace["prior_provisional_order"])})
        if priorities:
            key = (0, priorities[0], orders[0] if orders else 10**12, identity["identity_id"])
        else:
            key = (1, orders[0] if orders else 10**12, 10**12, identity["identity_id"])
        row = copy.deepcopy(identity)
        row.update(
            preparation_order_basis="existing_source_priority_then_prior_provisional_order_not_final_lemma_frequency",
            priority_provenance=traces,
            contains_open_review_units=any(trace["contains_open_questions"] for trace in traces),
            source_priority_values=priorities,
            final_frequency_rank=None,
            frequency_status="pending_qualified_evidence",
            generation_status="deferred_by_user",
            production_eligible=False,
            human_approved=False,
        )
        prepared.append((key, row))
    prepared.sort(key=lambda item: item[0])
    result = []
    for order, (_, row) in enumerate(prepared, 1):
        row["preparation_order"] = order
        result.append(row)
    return result
