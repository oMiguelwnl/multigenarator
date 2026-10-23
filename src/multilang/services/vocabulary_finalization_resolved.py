"""Lossless adapters for source-bound Nordic preparation resolutions.

This module does not approve content, infer POS, join spellings or read files.
The original resolution remains in ``original_resolved_content``. Only the
working view is adapted; callers should publish their original snapshot rows.
"""

from __future__ import annotations

import copy
import hashlib
import json


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _append_unique(items, item):
    if item not in items:
        items.append(item)


def adapt_resolved(row):
    """Copy a row and normalize its explicitly reviewed resolution.

    ``resolved_sense_key`` preserves the derived candidate identifier when one
    exists, otherwise the ancestor candidate ID. ``resolved_identity_key`` is
    non-null only for an explicit homonym, not merely for a distinct sense.
    Normalized form selections carry both ``parent_candidate_id`` (ancestor)
    and ``parent_resolution_id`` (exact resolved sense). Retained derived forms
    are preparation associations, never generation or card approvals.

    Missing POS and unbound forms are preserved as pending, without inventing
    an analysis or preventing the remaining units from being consolidated.
    """
    result = copy.deepcopy(row)
    content = result.get("resolved_content")
    if content is None:
        return result
    if not isinstance(content, dict):
        raise ValueError("resolved_content must be an object")
    if content.get("review_unit_id", row.get("review_unit_id")) != row.get("review_unit_id"):
        raise ValueError("resolved review unit binding differs")
    result.setdefault("original_resolved_content", copy.deepcopy(content))
    questions = content.setdefault("unresolved_questions", [])
    if not isinstance(questions, list):
        raise ValueError("unresolved_questions must be a list")
    candidates = content.get("resolved_candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("resolved_candidates must be a list")
    by_resolution, by_ancestor = {}, {}
    for candidate in candidates:
        ancestor = candidate.get("source_candidate_id")
        key = (
            candidate.get("resolved_candidate_id")
            or candidate.get("derived_candidate_id")
            or ancestor
        )
        if not isinstance(ancestor, str) or not ancestor or not isinstance(key, str) or not key:
            raise ValueError("resolved candidate requires exact source and resolution identifiers")
        candidate["resolved_sense_key"] = key
        homonym = candidate.get("homonym")
        candidate["resolved_identity_key"] = (
            "homonym:" + _digest(homonym) if homonym is not None else None
        )
        if key in by_resolution:
            raise ValueError("duplicate resolved sense identifier")
        by_resolution[key] = candidate
        by_ancestor.setdefault(ancestor, []).append(candidate)
        pos = candidate.get("pos")
        if candidate.get("disposition") == "retained" and (
            not isinstance(pos, str)
            or not pos.strip()
            or pos.casefold() in {"x", "unknown", "unresolved", "none", "null"}
        ):
            candidate["disposition"] = "quarantined_preparation_missing_pos"
            _append_unique(
                questions,
                dict(
                    type="preparation_missing_pos",
                    source_candidate_id=ancestor,
                    resolved_sense_key=key,
                    question="Retained source resolution has no resolved POS; preserve without inference.",
                ),
            )

    def parent(identifier, *, exact=False):
        if not exact and len(by_ancestor.get(identifier, [])) > 1:
            return None
        if identifier in by_resolution:
            matches = [by_resolution[identifier]]
        else:
            matches = by_ancestor.get(identifier, [])
        return (
            matches[0]
            if len(matches) == 1 and matches[0].get("disposition") == "retained"
            else None
        )

    unresolved = content.setdefault("preparation_unbound_forms", [])

    def hold(form, reason):
        _append_unique(unresolved, dict(form=copy.deepcopy(form), reason=reason))
        _append_unique(
            questions,
            dict(
                type="preparation_form_binding", reason=reason, form_evidence_sha256=_digest(form)
            ),
        )

    raw_forms = content.get("resolved_forms")
    group = result.get("source_group") or {}
    review = result.get("imported_review") or {}
    if raw_forms is None:
        raw_forms = dict(
            source_forms=group.get("forms_for_review", []),
            selected_forms=review.get("selected_forms", []),
        )
    normalized = dict(
        source_forms=[],
        selected_forms=[],
        basis="source_bound_resolution_adapter_no_new_card_selection",
    )
    source_forms, selections = {}, {}

    def source(form):
        fid = form["form_id"]
        if fid in source_forms and source_forms[fid] != form:
            raise ValueError("conflicting normalized form identifier")
        source_forms[fid] = form

    def select(form):
        key = (form["form_id"], form["parent_resolution_id"])
        if key in selections and selections[key] != form:
            raise ValueError("conflicting normalized form selection")
        selections[key] = form

    derived = []
    if isinstance(raw_forms, dict):
        normalized.update(
            {
                k: copy.deepcopy(v)
                for k, v in raw_forms.items()
                if k not in {"source_forms", "selected_forms"}
            }
        )
        for form in raw_forms.get("source_forms", group.get("forms_for_review", [])):
            source(copy.deepcopy(form))
        for form in raw_forms.get("selected_forms", review.get("selected_forms", [])):
            identifier = form.get("parent_resolution_id") or form.get("parent_candidate_id")
            target = parent(identifier, exact=bool(form.get("parent_resolution_id")))
            if target is None:
                hold(form, "native_selection_has_no_unique_retained_resolution")
                continue
            selection = copy.deepcopy(form)
            selection["parent_resolution_id"] = target["resolved_sense_key"]
            select(selection)
    elif isinstance(raw_forms, list):
        derived.extend((form, None) for form in raw_forms)
    else:
        raise ValueError("resolved_forms must be an object or list")
    for candidate in candidates:
        forms = candidate.get("forms", [])
        if not isinstance(forms, list):
            raise ValueError("candidate forms must be a list")
        derived.extend((form, candidate["resolved_sense_key"]) for form in forms)
    for form, owner in derived:
        if form.get("disposition") != "retained":
            continue  # Original full resolution retains omitted/quarantined forms.
        identifiers = form.get("parent_candidate_ids")
        if identifiers is None:
            identifier = (
                form.get("parent_derived_candidate_id")
                or form.get("parent_resolved_candidate_id")
                or form.get("parent_resolution_id")
                or form.get("parent_candidate_id")
                or owner
            )
            identifiers = [identifier] if identifier else []
        evidence = copy.deepcopy(form.get("evidence") or [])
        if not evidence and isinstance(form.get("provenance"), dict):
            original = next(
                (
                    f
                    for f in group.get("forms_for_review", [])
                    if f["form_id"] == form.get("source_form_id")
                ),
                None,
            )
            if (
                original is not None
                and original == form["provenance"]
                and original.get("form") == form.get("form")
                and group.get("entry_id") in original.get("parent_entry_ids", [])
            ):
                evidence = [dict(kind="exact_frozen_form_provenance", source_form=original)]
        if not isinstance(identifiers, list) or not identifiers or not evidence:
            hold(form, "derived_form_requires_explicit_parent_and_evidence")
            continue
        exact = bool(
            form.get("parent_resolution_id")
            or form.get("parent_resolved_candidate_id")
            or form.get("parent_derived_candidate_id")
            or owner
        )
        targets = [parent(identifier, exact=exact) for identifier in identifiers]
        if any(target is None for target in targets):
            hold(form, "derived_form_parent_missing_ambiguous_or_quarantined")
            continue
        if owner and any(t["resolved_sense_key"] != owner for t in targets):
            hold(form, "embedded_form_parent_differs_from_owner")
            continue
        for target in targets:
            key = target["resolved_sense_key"]
            # The same paradigm spelling can have separate evidence for two homonyms.
            fid = "prepared-form:" + _digest(
                [
                    result.get("review_unit_id"),
                    key,
                    form.get("resolved_form_id"),
                    form.get("source_form_id"),
                    form,
                ]
            )
            normalized_source = dict(
                form_id=fid,
                form=form["form"],
                source_form_id=form.get("source_form_id"),
                resolved_form_id=form.get("resolved_form_id"),
                evidence_candidate_ids=[target["source_candidate_id"]],
                parent_entry_ids=[group["entry_id"]],
                parent_resolution_id=key,
                original_form=copy.deepcopy(form),
                evidence=evidence,
                selected_for_card=False,
                selected_for_generation=False,
            )
            source(normalized_source)
            select(
                dict(
                    form_id=fid,
                    form=form["form"],
                    parent_candidate_id=target["source_candidate_id"],
                    parent_resolution_id=key,
                    reason="explicit_retained_derived_form",
                    selected_for_card=False,
                    selected_for_generation=False,
                )
            )
    normalized["source_forms"] = list(source_forms.values())
    normalized["selected_forms"] = list(selections.values())
    content["resolved_forms"] = normalized
    return result
