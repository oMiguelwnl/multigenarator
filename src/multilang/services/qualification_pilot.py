"""Bounded, reproducible source-backed pilots without invented review authority.

Dictionary forms are proposals. Held-out UD observations only create evaluation
review packets; they never supply calibration counts, sense labels, or ratings.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.form_evidence import CorpusEvidenceContext, EvidenceOccurrence
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import ContextualAnalysis, sentence_hash
from multilang.services.form_evidence import measure_form_evidence
from multilang.services.qualification_review import (
    CaseReviewItem,
    FormReviewItem,
    LexicalReviewItem,
    ReviewPacket,
    ReviewSource,
    ReviewToken,
    _json,
    export_review,
)
from multilang.services.vocabulary_preparation import _OutputBudget, source_catalog
from multilang.services.vocabulary_review import _manifest_check, _plain_path, _read_bytes
from multilang.services.vocabulary_sources import (
    CorpusSentence,
    LexicalSenseCandidate,
    SourceLimits,
    _verified_lines,
)

_LEXICAL_POS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN SCONJ VERB".split()
)
_PENDING_SOURCE_CATEGORIES = frozenset(
    {
        "conj",
        "adnominal",
        "contraction",
        "phrase",
        "prep_phrase",
        "proverb",
        "character",
        "syllable",
        "root",
        "romanization",
        "soft-redirect",
        "affix",
        "prefix",
        "suffix",
        "infix",
        "combining_form",
    }
)


class PreparedVocabularyInput(NativeContract):
    directory: Path
    manifest_sha256: Sha256


class EvaluationInput(NativeContract):
    directory: Path
    manifest_sha256: Sha256


class SourceCategoryInput(NativeContract):
    path: Path
    sha256: Sha256


def _categories(input_, limits):
    if input_ is None:
        return {}, None
    input_ = SourceCategoryInput.model_validate(input_.model_dump())
    values = _json(_read_bytes(input_.path, input_.sha256, limit=16 * 1024**2))
    if (
        not isinstance(values, dict)
        or len(values) > limits.max_unique_entries
        or any(
            not isinstance(key, str)
            or not re.fullmatch(r"[0-9a-f]{64}", key)
            or not isinstance(value, str)
            or not 1 <= len(value) <= 128
            for key, value in values.items()
        )
    ):
        raise ValueError("source category sidecar is outside bounds")
    return values, input_


def _eligible_pos(candidate, categories):
    category = categories.get(candidate.source_record_sha256)
    return (
        candidate.pos in _LEXICAL_POS
        and category not in _PENDING_SOURCE_CATEGORIES
        and not (candidate.pos == "CCONJ" and category is None)
    )


def _identifier(text: str) -> str:
    # Originals remain in the copied source record if a source identifier exceeds
    # the presentation contract. This projection never creates a lexical sense.
    return (
        text
        if 0 < len(text) <= 128 and text.strip() == text
        else "source:" + canonical_sha256(text)
    )


def _prepared_inputs(inputs, language, limits):
    if not 1 <= len(inputs) <= 32:
        raise ValueError("pilot requires between one and 32 prepared inputs")
    result, total = [], 0
    seen = set()
    for item in sorted(inputs, key=lambda item: item.manifest_sha256):
        item = PreparedVocabularyInput.model_validate(item.model_dump())
        root = _plain_path(item.directory)
        manifest = _json(_read_bytes(root / "manifest.json", item.manifest_sha256, limit=1024**2))
        if not isinstance(manifest, dict):
            raise ValueError("preparation manifest must be an object")
        _manifest_check(manifest)
        if manifest.get("language") != language:
            raise ValueError("prepared vocabulary language mismatch")
        if item.manifest_sha256 in seen:
            continue
        seen.add(item.manifest_sha256)
        for filename, digest in sorted(manifest["files"].items()):
            data = _read_bytes(root / filename, digest, limit=limits.max_bytes)
            total += len(data)
            if total > limits.max_expanded_bytes:
                raise ValueError("pilot input aggregate byte limit exceeded")
        result.append((item, manifest))
    return result


def _candidates(inputs, limits):
    count = 0
    for item, manifest in inputs:
        for line in _verified_lines(
            item.directory / "candidates.jsonl", manifest["files"]["candidates.jsonl"], limits
        ):
            if not line.strip():
                continue
            count += 1
            if count > limits.max_records:
                raise ValueError("pilot input candidate record limit exceeded")
            candidate = LexicalSenseCandidate.model_validate(_json(line.encode()))
            if candidate.language.value != manifest["language"]:
                raise ValueError("candidate language differs from prepared manifest")
            yield candidate, manifest


def _seed_words(words):
    if not 1 <= len(words) <= 100000:
        raise ValueError("pilot seed list is outside bounds")
    ordered = {}
    for word in words:
        if (
            not isinstance(word, str)
            or not word.strip()
            or len(word) > 512
            or not unicodedata.is_normalized("NFC", word)
        ):
            raise ValueError("seed words must be bounded NFC text")
        ordered.setdefault(word.casefold(), word)
    return ordered


def _source(candidate, manifest, categories):
    category = categories.get(candidate.source_record_sha256, "unavailable")
    header = f"Source category: {category}; legacy normalized POS: {candidate.pos}.\n"
    if not _eligible_pos(candidate, categories):
        header += "Requires explicit source-category/POS correction before acceptance.\n"
    return ReviewSource(
        source_id="prepared-dictionary",
        source_sha256=manifest["dictionary_sha256"],
        record_id=candidate.candidate_id,
        excerpt=(header + "\n".join(candidate.glosses))[:64000],
    )


def _lexical_item(candidate, manifest, categories, *, excluded=False):
    glosses = tuple(
        part
        for gloss in candidate.glosses
        for part in (gloss[i : i + 4096] for i in range(0, len(gloss), 4096))
    )
    return LexicalReviewItem(
        item_id=("unresolved:" if excluded else "lexical:") + candidate.candidate_id,
        sources=(_source(candidate, manifest, categories),),
        candidate_id=candidate.candidate_id,
        candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
        lemma=candidate.lemma,
        pos=candidate.pos if _eligible_pos(candidate, categories) else "X",
        glosses=glosses,
        source_sense_ids=tuple(_identifier(s) for s in candidate.source_sense_ids),
    )


def _evaluation(input_, language, count, limits):
    if input_ is None:
        return None, [], [], set()
    input_ = EvaluationInput.model_validate(input_.model_dump())
    root = _plain_path(input_.directory)
    manifest = _json(_read_bytes(root / "manifest.json", input_.manifest_sha256, limit=1024**2))
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or manifest.get("language") != language
        or manifest.get("corpus_split") != "test"
        or manifest.get("qualification") is not False
        or manifest.get("canonical_ranking_input") is not False
        or manifest.get("evaluation_sha256")
        != canonical_sha256({k: v for k, v in manifest.items() if k != "evaluation_sha256"})
    ):
        raise ValueError("invalid held-out evaluation manifest")
    rows, all_hashes = [], set()
    for line in _verified_lines(
        root / "observations.jsonl", manifest["observations_sha256"], limits
    ):
        if not line.strip():
            continue
        if len(rows) >= 5000:
            raise ValueError("evaluation observation limit exceeded")
        row = _json(line.encode())
        reference = CorpusSentence.model_validate(row["reference"])
        analysis = ContextualAnalysis.model_validate(row["analysis"])
        if (
            reference.language.value != language
            or analysis.language != language
            or reference.source_sha256 != manifest["corpus_sha256"]
            or analysis.sentence_sha256 != sentence_hash(reference.text)
            or analysis.model_fingerprint not in manifest["model_fingerprints"]
        ):
            raise ValueError("evaluation observation provenance mismatch")
        for token in (*analysis.tokens, *analysis.blocked_spans):
            if reference.text[token.start : token.end] != token.text:
                raise ValueError("evaluation analysis span mismatch")
        all_hashes.add(sentence_hash(reference.text))
        rows.append((canonical_sha256(row), row, reference, analysis))
    if len(rows) != manifest["sample_sentence_count"]:
        raise ValueError("evaluation manifest observation count mismatch")
    chosen, items = sorted(rows, key=lambda row: row[0])[:count], []
    for row_sha, _, reference, analysis in chosen:
        tokens = tuple(
            ReviewToken(
                text=token.text,
                lemma=token.lemma,
                pos=token.pos,
                start=token.start,
                end=token.end,
                features=token.features,
            )
            for token in reference.tokens
            if token.start is not None
            and token.end is not None
            and token.lemma is not None
            and token.pos is not None
        )
        tags = [
            "source_annotation_proposal",
            "not_independently_reviewed",
            "analysis_" + analysis.status,
        ]
        if len(tokens) != len(reference.tokens):
            tags.append("unaligned_or_missing_reference_components")
        if analysis.blocked_spans:
            tags.append("model_has_blocked_source_spans")
        items.append(
            CaseReviewItem(
                item_id="case:" + row_sha,
                sources=(
                    ReviewSource(
                        source_id="ud-evaluation",
                        source_sha256=reference.source_sha256,
                        record_id=_identifier(reference.sentence_id),
                        document_id=_identifier(reference.document_id),
                        sentence_id=_identifier(reference.sentence_id),
                        excerpt=reference.text,
                    ),
                ),
                text=reference.text,
                proposal_tokens=tokens,
                model_fingerprint=analysis.model_fingerprint,
                behavior_tags=tuple(tags),
            )
        )
    return manifest, [row[1] for row in chosen], items, all_hashes


def _dictionary_forms(selected, headwords, limit):
    proposals = {}
    lookup = {word.casefold() for word in headwords}
    for candidate, manifest in selected.values():
        if candidate.kind == "lexeme":
            forms = [
                (candidate.lemma, form.get("form"), "dictionary_form", form)
                for form in candidate.forms
                if isinstance(form.get("form"), str)
            ]
        else:
            forms = [
                (
                    parent,
                    candidate.lemma,
                    "dictionary_inflection",
                    {
                        "tags": list(candidate.tags),
                        "form_of": list(candidate.form_of),
                        "glosses": list(candidate.glosses),
                    },
                )
                for parent in candidate.form_of
                if parent.casefold() in lookup
            ]
        for lemma, surface, kind, raw in forms:
            if not surface or surface == lemma:
                continue
            proposal = {
                "kind": kind,
                "lemma": lemma,
                "pos": candidate.pos,
                "text": surface,
                "source_record_sha256": candidate.source_record_sha256,
                "dictionary_sha256": manifest["dictionary_sha256"],
                "source_data": raw,
            }
            key = canonical_sha256(proposal)
            if key not in proposals:
                if len(proposals) >= limit:
                    raise ValueError("dictionary form proposal limit exceeded")
                proposals[key] = {**proposal, "supporting_candidate_ids": []}
            proposals[key]["supporting_candidate_ids"].append(candidate.candidate_id)
    return [
        {**proposal, "supporting_candidate_ids": sorted(set(proposal["supporting_candidate_ids"]))}
        for _, proposal in sorted(proposals.items())
    ]


def _dictionary_form_item(proposal):
    digest = canonical_sha256(proposal)
    return FormReviewItem(
        item_id="dictionary-form:" + digest,
        candidate_id="dictionary-form:" + digest,
        candidate_sha256=digest,
        lemma=proposal["lemma"],
        pos=proposal["pos"],
        text=proposal["text"],
        sources=(
            ReviewSource(
                source_id="dictionary-form",
                source_sha256=proposal["dictionary_sha256"],
                record_id=proposal["source_record_sha256"],
                excerpt=json.dumps(proposal["source_data"], ensure_ascii=False)[:64000],
            ),
        ),
        missing_reasons=(
            "Unobserved dictionary proposal; requires separate corpus occurrences",
            "Dictionary tags are source proposals, not numerical importance ratings",
            "Canonical sense and exact contextual analysis require independent review",
        ),
    )


def _measured_items(context, occurrences, headwords, prohibited_sources, evaluation_texts):
    if context is None:
        if occurrences:
            raise ValueError("measurements require an explicit calibration corpus context")
        return None, []
    context = CorpusEvidenceContext.model_validate(context.model_dump())
    if context.split != "calibration":
        raise ValueError("pilot form measurements require calibration split")
    if set(context.source_sha256s) & prohibited_sources:
        raise ValueError("held-out evaluation source cannot enter calibration")
    if any(sentence_hash(item.sentence) in evaluation_texts for item in occurrences):
        raise ValueError("held-out evaluation sentence cannot enter calibration")
    report = measure_form_evidence(context, occurrences)
    selected, items = set(headwords), []
    measured_groups = {
        measurement.group_sha256 for measurement in report.measurements
        if measurement.lemma in selected
    }
    documents = {(doc.source_sha256, doc.document_id): doc for doc in context.documents}
    examples_by_group = {}
    evidence_keys_by_group = {}
    for occurrence in occurrences:
        group = occurrence.group_sha256
        if group not in measured_groups:
            continue
        examples_by_group.setdefault(group, {}).setdefault(
            occurrence.source_sha256, occurrence
        )
        keys = evidence_keys_by_group.setdefault(group, set())
        keys.add(canonical_sha256(["source", occurrence.source_sha256]))
        keys.add(canonical_sha256(["sentence-text", sentence_hash(occurrence.sentence)]))
        document = documents.get((occurrence.source_sha256, occurrence.document_id))
        if document is not None:
            keys.add(canonical_sha256(["document-content", document.text_sha256]))
        if len(keys) > 100000:
            raise ValueError("form evidence source key limit exceeded")
    for measurement in report.measurements:
        if measurement.lemma not in selected:
            continue
        examples = examples_by_group[measurement.group_sha256]
        sources = tuple(
            ReviewSource(
                source_id="calibration-corpus",
                source_sha256=source_sha,
                record_id=measurement.group_sha256,
                document_id=example.document_id,
                sentence_id=example.sentence_id,
                excerpt=example.sentence,
            )
            for source_sha, example in sorted(examples.items())
        )
        measurements = {
            "observed_count": measurement.observed_count,
            "frequency_per_million": measurement.frequency_per_million,
        }
        if measurement.document_count is not None:
            measurements["document_count"] = measurement.document_count
        if measurement.dispersion is not None:
            measurements["dispersion"] = measurement.dispersion
        items.append(
            FormReviewItem(
                item_id="observed-form:" + measurement.group_sha256,
                candidate_id="observed-form:" + measurement.group_sha256,
                candidate_sha256=measurement.measurement_sha256,
                evidence_source_keys=tuple(sorted(evidence_keys_by_group[measurement.group_sha256])),
                sources=sources,
                lemma=measurement.lemma,
                pos=measurement.pos,
                text=measurement.text,
                features=measurement.features,
                canonical_sense_id=measurement.sense_id,
                measurement_sha256=measurement.measurement_sha256,
                measurements=measurements,
                proposed_ratings=measurement.evidence_values,
                missing_reasons=tuple(
                    f"{name}: {reason}"
                    for name, reason in sorted(measurement.missing_reasons.items())
                )
                + (
                    () if measurement.sense_id else ("Canonical sense requires independent review",)
                ),
            )
        )
    return report, items


def prepare_qualification_pilot(
    *,
    language: str,
    prepared_inputs: tuple[PreparedVocabularyInput, ...],
    seed_words: tuple[str, ...],
    profile_sha256: str,
    rubric_sha256: str,
    output: Path,
    evaluation_input: EvaluationInput | None = None,
    headword_count: int = 100,
    case_count: int = 200,
    evidence_context: CorpusEvidenceContext | None = None,
    occurrences: Iterable[EvidenceOccurrence] = (),
    source_categories: SourceCategoryInput | None = None,
    packet_item_limit: int = 500,
    limits: SourceLimits | None = None,
) -> dict:
    """Create all review material atomically, using only supplied local artifacts."""
    source_catalog(language)
    if (
        not 1 <= headword_count <= 3000
        or not 1 <= case_count <= 5000
        or not 1 <= packet_item_limit <= 5000
    ):
        raise ValueError("pilot headword/case/packet counts are outside bounds")
    if not re.fullmatch(r"[0-9a-f]{64}", profile_sha256) or not re.fullmatch(
        r"[0-9a-f]{64}", rubric_sha256
    ):
        raise ValueError("pilot profile and rubric checksums are required")
    limits = limits or SourceLimits()
    output = _plain_path(output)
    if output.exists():
        raise ValueError("pilot output already exists")
    prepared = _prepared_inputs(prepared_inputs, language, limits)
    categories, source_categories = _categories(source_categories, limits)
    seeds = _seed_words(seed_words)
    ranks = {word: index for index, word in enumerate(seeds)}
    available, observed_seed_words = set(), set()
    for candidate, _ in _candidates(prepared, limits):
        key = candidate.lemma.casefold()
        if key in ranks:
            observed_seed_words.add(key)
            if candidate.kind == "lexeme" and _eligible_pos(candidate, categories):
                available.add(candidate.lemma)
        if len(available) > limits.max_unique_entries:
            raise ValueError("pilot headword population limit exceeded")
    headwords = sorted(available, key=lambda word: (ranks[word.casefold()], word))[:headword_count]
    selected_spellings, selected_keys = set(headwords), {word.casefold() for word in headwords}
    last_rank = max((ranks[word.casefold()] for word in headwords), default=len(seeds))
    selected, unknown = {}, {}
    for candidate, manifest in _candidates(prepared, limits):
        match = candidate.lemma in selected_spellings or (
            candidate.kind == "inflection"
            and any(parent.casefold() in selected_keys for parent in candidate.form_of)
        )
        destination = (
            selected
            if match
            else unknown
            if (
                not _eligible_pos(candidate, categories)
                and candidate.lemma.casefold() in ranks
                and ranks[candidate.lemma.casefold()] <= last_rank
            )
            else None
        )
        if destination is not None:
            if (
                candidate.candidate_id in destination
                and destination[candidate.candidate_id][0] != candidate
            ):
                raise ValueError("conflicting source candidate identity")
            destination[candidate.candidate_id] = (candidate, manifest)
            if len(selected) + len(unknown) > limits.max_unique_entries:
                raise ValueError("pilot selected candidate limit exceeded")
    selected, unknown = dict(sorted(selected.items())), dict(sorted(unknown.items()))
    evaluation_manifest, observation_rows, cases, eval_texts = _evaluation(
        evaluation_input, language, case_count, limits
    )
    prohibited_sources = {
        manifest["corpus"]["sha256"]
        for _, manifest in prepared
        if manifest.get("corpus", {}).get("split") == "test" and manifest["corpus"].get("sha256")
    }
    if evaluation_manifest is not None:
        prohibited_sources.add(evaluation_manifest["corpus_sha256"])
    checked_occurrences = []
    for item in occurrences:
        if len(checked_occurrences) >= min(limits.max_records, 1000000):
            raise ValueError("pilot occurrence limit exceeded")
        checked_occurrences.append(EvidenceOccurrence.model_validate(item.model_dump()))
    if evidence_context is not None and evidence_context.language.value != language:
        raise ValueError("calibration corpus language mismatch")
    report, measured_items = _measured_items(
        evidence_context,
        checked_occurrences,
        headwords,
        prohibited_sources,
        eval_texts,
    )
    form_proposals = _dictionary_forms(selected, headwords, limits.max_unique_entries)
    if len(form_proposals) > limits.max_unique_entries:
        raise ValueError("dictionary form proposal limit exceeded")
    lexical = [
        _lexical_item(candidate, manifest, categories)
        for candidate, manifest in selected.values()
        if candidate.kind == "lexeme"
    ]
    unresolved = [
        _lexical_item(candidate, manifest, categories, excluded=True)
        for candidate, manifest in unknown.values()
    ]
    dictionary_form_items = [_dictionary_form_item(proposal) for proposal in form_proposals]
    unknown_report = [
        {
            "candidate_id": candidate.candidate_id,
            "lemma": candidate.lemma,
            "pos": candidate.pos,
            "source_pos": categories.get(candidate.source_record_sha256),
            "selected_headword": candidate.lemma in selected_spellings,
            "reason": "source_category_requires_review"
            if categories.get(candidate.source_record_sha256) in _PENDING_SOURCE_CATEGORIES
            else "unresolved_or_unqualified_pos_mapping",
        }
        for candidate, _ in (*selected.values(), *unknown.values())
        if not _eligible_pos(candidate, categories)
    ]
    blockers = [
        "independent_linguistic_review",
        "source_redistribution_review",
        "important_form_policy_calibration",
        "reviewed_content_and_audio",
        "provider_budget",
        "anki_client_acceptance",
    ]
    if len(headwords) < headword_count:
        blockers.append("insufficient_source_backed_headwords")
    if unknown_report:
        blockers.append("unresolved_source_pos")
    if evidence_context is None:
        blockers.append("missing_calibration_corpus")
    if len(cases) < case_count:
        blockers.append("insufficient_evaluation_cases")
    budget = _OutputBudget(limits.max_output_bytes)
    packets, file_hashes = [], {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".qualification-pilot-", dir=output.parent) as directory:
        staging = Path(directory) / "pilot"
        staging.mkdir(mode=0o700)

        def jsonl(filename, values):
            with (staging / filename).open("w", encoding="utf-8") as handle:
                for value in values:
                    budget.write(
                        handle, json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
                    )
            (staging / filename).chmod(0o600)

        jsonl(
            "candidates.jsonl",
            (candidate.model_dump(mode="json") for candidate, _ in selected.values()),
        )
        jsonl(
            "unknown-pos-candidates.jsonl",
            (candidate.model_dump(mode="json") for candidate, _ in unknown.values()),
        )
        jsonl("form-proposals.jsonl", form_proposals)
        jsonl("evaluation-observations.jsonl", observation_rows)
        jsonl(
            "calibration-occurrences.jsonl",
            (item.model_dump(mode="json") for item in checked_occurrences),
        )
        if report is not None:
            budget.dump(staging / "measurements.json", report.model_dump(mode="json"))
            budget.dump(staging / "corpus-context.json", evidence_context.model_dump(mode="json"))
        groups = (
            ("lexical", "calibration", lexical),
            ("unresolved", "pilot", unresolved),
            ("dictionary-forms", "pilot", dictionary_form_items),
            ("measured-forms", "calibration", measured_items),
            ("case", "evaluation", cases),
        )
        for group, split, items in groups:
            chunks, current, size = [], [], 0
            for item in items:
                item_size = len(item.model_dump_json().encode())
                if item_size > 8 * 1024**2:
                    raise ValueError("individual pilot review item exceeds byte limit")
                if current and (
                    len(current) >= packet_item_limit or size + item_size > 8 * 1024**2
                ):
                    chunks.append(current)
                    current, size = [], 0
                current.append(item)
                size += item_size
            if current:
                chunks.append(current)
            for index, chunk in enumerate(chunks, 1):
                packet = ReviewPacket(
                    packet_id=f"{language}:{group}:"
                    + canonical_sha256([item.item_sha256 for item in chunk]),
                    language=SupportedLanguage(language),
                    split=split,
                    profile_sha256=profile_sha256,
                    rubric_sha256=rubric_sha256,
                    items=tuple(chunk),
                )
                relative = f"review/{group}-{index:03d}"
                exported = export_review(packet, staging / relative)
                budget.written += sum(
                    path.stat().st_size for path in (staging / relative).iterdir()
                )
                if budget.written > budget.limit:
                    raise ValueError("pilot output byte limit exceeded")
                packets.append(
                    {
                        "kind": "case" if group == "case" else group,
                        "split": split,
                        "path": relative,
                        "packet_sha256": exported.packet_sha256,
                        "packet_file_sha256": exported.packet_file_sha256,
                        "item_count": exported.item_count,
                    }
                )
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                with path.open("rb") as handle:
                    file_hashes[path.relative_to(staging).as_posix()] = hashlib.file_digest(
                        handle, "sha256"
                    ).hexdigest()
                path.chmod(0o600)
        result = {
            "schema_version": 1,
            "language": language,
            "production_eligible": False,
            "selection_policy": "seed-casefold-rank-exact-nfc-spelling-resolved-pos-1",
            "seed_selection_sha256": canonical_sha256(list(seeds.values())),
            "selected_headwords": headwords,
            "requested_headword_count": headword_count,
            "headword_count": len(headwords),
            "missing_seed_words": [
                word for key, word in seeds.items() if key not in observed_seed_words
            ],
            "lexical_candidate_count": len(lexical),
            "inflection_candidate_count": sum(c.kind == "inflection" for c, _ in selected.values()),
            "dictionary_form_proposal_count": len(form_proposals),
            "measurement_count": len(measured_items),
            "evaluation_case_count": len(cases),
            "requested_evaluation_case_count": case_count,
            "unknown_pos_candidates": unknown_report,
            "source_category_candidate_counts": dict(
                sorted(
                    Counter(
                        categories.get(candidate.source_record_sha256, "unavailable")
                        for candidate, _ in (*selected.values(), *unknown.values())
                    ).items()
                )
            ),
            "blockers": blockers,
            "prepared_inputs": [
                {
                    "manifest_file_sha256": item.manifest_sha256,
                    "preparation_sha256": manifest["preparation_sha256"],
                    "dictionary_sha256": manifest["dictionary_sha256"],
                }
                for item, manifest in prepared
            ],
            "evaluation_input": None
            if evaluation_manifest is None
            else {
                "manifest_file_sha256": evaluation_input.manifest_sha256,
                "evaluation_sha256": evaluation_manifest["evaluation_sha256"],
                "model_fingerprints": evaluation_manifest["model_fingerprints"],
            },
            "source_categories_sha256": None
            if source_categories is None
            else source_categories.sha256,
            "measurement_context_sha256": None if report is None else report.context_sha256,
            "profile_sha256": profile_sha256,
            "rubric_sha256": rubric_sha256,
            "packets": packets,
            "files": file_hashes,
            "workload": {
                "headword_candidate_count": len(headwords),
                "lexical_sense_candidate_count": len(lexical),
                "dictionary_form_proposal_count": len(form_proposals),
                "observed_form_candidate_count": len(measured_items),
                "approved_core_cards": 0,
                "approved_important_form_cards": 0,
                "important_form_cards": None,
                "provider_calls_executed": 0,
                "cost_estimate": None,
            },
        }
        result["pilot_sha256"] = canonical_sha256(result)
        budget.dump(staging / "manifest.json", result)
        (staging / "manifest.json").chmod(0o600)
        if output.exists():
            raise ValueError("pilot output created concurrently")
        os.rename(staging, output)
    return result
