"""Observe source-bound text without inferring senses or claiming full coverage."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import Field

from multilang.domain.form_evidence import (
    CorpusEvidenceContext,
    EvidenceDocument,
    EvidenceOccurrence,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import (
    ContextualAnalysis,
    ContextualAnalyzer,
    sentence_hash,
)
from multilang.services.qualification_corpora import AcquisitionLimits, read_document_corpus


class ObservationLimits(NativeContract):
    max_units: int = Field(default=1000, ge=1, le=10000)
    max_unit_characters: int = Field(default=16000, ge=1, le=64000)
    max_occurrences: int = Field(default=100000, ge=1, le=1000000)
    max_output_bytes: int = Field(default=128 * 1024**2, ge=1, le=512 * 1024**2)
    max_source_units: int = Field(default=50000, ge=1, le=100000)


class AnalyzedSourceUnit(NativeContract):
    source_sha256: Sha256
    document_id: Identifier
    sentence_id: Identifier
    document_start: int | None = Field(default=None, ge=0)
    document_end: int | None = Field(default=None, ge=1)
    text: str = Field(min_length=1, max_length=64000)
    analysis: ContextualAnalysis


class SkippedSourceUnit(NativeContract):
    document_id: Identifier
    sentence_id: Identifier
    text_sha256: Sha256
    nonspace_characters: int = Field(ge=0)
    reason: Literal["unit_character_limit", "unit_count_limit"]


class ObservationCoverage(NativeContract):
    source_document_count: int | None = Field(ge=0)
    measured_document_count: int | None = Field(ge=0)
    document_boundaries_known: bool = True
    source_unit_count: int = Field(ge=0)
    analyzed_unit_count: int = Field(ge=0)
    source_nonspace_characters: int = Field(ge=0)
    aligned_nonspace_characters: int = Field(ge=0)
    blocked_nonspace_characters: int = Field(ge=0)
    unaccounted_nonspace_characters: int = Field(ge=0)
    measured_lexical_tokens: int = Field(ge=0)
    excluded_nonlexical_tokens: int = Field(ge=0)
    statuses: dict[str, int]


class CorpusObservationResult(NativeContract):
    schema_version: Literal[1] = 1
    source_sha256: Sha256
    language: SupportedLanguage
    split: Literal["calibration", "evaluation"]
    context: CorpusEvidenceContext | None
    occurrences: tuple[EvidenceOccurrence, ...]
    analyses: tuple[AnalyzedSourceUnit, ...]
    skipped_units: tuple[SkippedSourceUnit, ...]
    coverage: ObservationCoverage
    model_fingerprints: tuple[Sha256, ...]
    sampling_description: str
    denominator_policy: Literal["exact-aligned-lexical-model-tokens-v1"] = (
        "exact-aligned-lexical-model-tokens-v1"
    )
    source_scope: Literal["wikimedia-provisional-document-pilot", "UD-train-grammar-only"]
    production_eligible: Literal[False] = False


def _observe(
    units: Iterable[tuple[str, str, int | None, int | None, str]],
    *,
    language,
    source_sha256,
    split,
    analyzer,
    limits,
    document_hashes,
    source_scope,
    sampling_description,
    document_boundaries_known=True,
):
    analyses, occurrences, skipped = [], [], []
    document_counts: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    unit_count = source_chars = aligned_chars = blocked_chars = nonlexical = output_bytes = 0
    for document_id, unit_id, start, end, text in units:
        unit_count += 1
        if unit_count > limits.max_source_units:
            raise ValueError("source unit limit exceeded")
        source_chars += sum(not char.isspace() for char in text)
        reason = (
            "unit_count_limit"
            if len(analyses) >= limits.max_units
            else "unit_character_limit"
            if len(text) > limits.max_unit_characters
            else None
        )
        if reason:
            skipped_unit = SkippedSourceUnit(
                document_id=document_id,
                sentence_id=unit_id,
                text_sha256=sentence_hash(text),
                nonspace_characters=sum(not c.isspace() for c in text),
                reason=reason,
            )
            output_bytes += len(skipped_unit.model_dump_json().encode())
            if output_bytes > limits.max_output_bytes:
                raise ValueError("observation output byte limit exceeded")
            skipped.append(skipped_unit)
            continue
        original = analyzer.analyze(language.value, text)
        analysis = ContextualAnalysis.model_validate(original.model_dump(mode="json"))
        if analysis.language != language.value or analysis.sentence_sha256 != sentence_hash(text):
            raise ValueError("analyzer source does not match corpus unit")
        if analysis.status not in {"complete", "inconclusive"} and analysis.tokens:
            raise ValueError("analyzer status cannot supply observed tokens")
        covered = 0
        for token in (*analysis.tokens, *analysis.blocked_spans):
            if token.end > len(text) or text[token.start : token.end] != token.text:
                raise ValueError("analyzer source span does not match corpus unit")
            covered += sum(not c.isspace() for c in token.text)
        if analysis.status == "complete" and covered != sum(not c.isspace() for c in text):
            raise ValueError("complete analyzer source does not cover corpus unit")
        statuses[analysis.status] += 1
        unit = AnalyzedSourceUnit(
            source_sha256=source_sha256,
            document_id=document_id,
            sentence_id=unit_id,
            document_start=start,
            document_end=end,
            text=text,
            analysis=analysis,
        )
        output_bytes += len(unit.model_dump_json().encode())
        if output_bytes > limits.max_output_bytes:
            raise ValueError("observation output byte limit exceeded")
        analyses.append(unit)
        aligned_chars += sum(sum(not c.isspace() for c in token.text) for token in analysis.tokens)
        blocked_chars += sum(
            sum(not c.isspace() for c in token.text) for token in analysis.blocked_spans
        )
        for token in analysis.tokens:
            if token.pos in {"PUNCT", "SYM", "X"}:
                nonlexical += 1
                continue
            occurrence = EvidenceOccurrence(
                language=language,
                split=split,
                source_sha256=source_sha256,
                document_id=document_id if document_boundaries_known else None,
                sentence_id=unit_id,
                sentence=text,
                start=token.start,
                end=token.end,
                text=token.text,
                lemma=token.lemma,
                pos=token.pos,
                features=dict(token.features),
                sense_id=None,
            )
            output_bytes += len(occurrence.model_dump_json().encode())
            if output_bytes > limits.max_output_bytes:
                raise ValueError("observation output byte limit exceeded")
            occurrences.append(occurrence)
            document_counts[document_id] += 1
            if len(occurrences) > limits.max_occurrences:
                raise ValueError("observation occurrence limit exceeded")
    context = None
    if occurrences:
        context = CorpusEvidenceContext(
            language=language,
            split=split,
            source_sha256s=(source_sha256,),
            token_count=len(occurrences),
            documents=tuple(
                EvidenceDocument(
                    source_sha256=source_sha256,
                    document_id=document_id,
                    text_sha256=document_hashes[document_id],
                    token_count=count,
                )
                for document_id, count in sorted(document_counts.items())
                if document_boundaries_known
            ),
            sampling_description=sampling_description,
        )
    result = CorpusObservationResult(
        source_sha256=source_sha256,
        language=language,
        split=split,
        context=context,
        occurrences=tuple(occurrences),
        analyses=tuple(analyses),
        skipped_units=tuple(skipped),
        coverage=ObservationCoverage(
            source_document_count=len(document_hashes) if document_boundaries_known else None,
            measured_document_count=len(document_counts) if document_boundaries_known else None,
            document_boundaries_known=document_boundaries_known,
            source_unit_count=unit_count,
            analyzed_unit_count=len(analyses),
            source_nonspace_characters=source_chars,
            aligned_nonspace_characters=aligned_chars,
            blocked_nonspace_characters=blocked_chars,
            unaccounted_nonspace_characters=source_chars - aligned_chars - blocked_chars,
            measured_lexical_tokens=len(occurrences),
            excluded_nonlexical_tokens=nonlexical,
            statuses=dict(sorted(statuses.items())),
        ),
        model_fingerprints=tuple(sorted({unit.analysis.model_fingerprint for unit in analyses})),
        sampling_description=sampling_description,
        source_scope=source_scope,
    )
    if len(result.model_dump_json().encode()) > limits.max_output_bytes:
        raise ValueError("observation output byte limit exceeded")
    return result


def observe_document_corpus(
    path: Path,
    expected_sha256: str,
    analyzer: ContextualAnalyzer,
    *,
    split: Literal["calibration", "evaluation"] = "calibration",
    limits: ObservationLimits | None = None,
    source_limits: AcquisitionLimits | None = None,
) -> CorpusObservationResult:
    """Preserve source documents while observing exact paragraph slices.

    Frequency denominators contain only aligned lexical model tokens. Blocked,
    unavailable and skipped text remains explicit, so these are conditional
    pilot measurements and never complete corpus or general-language counts.
    """
    limits = limits or ObservationLimits()
    documents = read_document_corpus(path, expected_sha256, limits=source_limits)
    if not documents:
        raise ValueError("cannot observe an empty document corpus")
    language = documents[0].language
    if any(doc.language != language or doc.split != split for doc in documents):
        raise ValueError("document language or split does not match observation request")
    units = []
    for document in documents:
        position = 0
        for paragraph in document.text.split("\n\n"):
            if paragraph.strip():
                units.append(
                    (
                        document.document_id,
                        f"paragraph:{position}:{position + len(paragraph)}",
                        position,
                        position + len(paragraph),
                        paragraph,
                    )
                )
                if len(units) > limits.max_source_units:
                    raise ValueError("source unit limit exceeded")
            position += len(paragraph) + 2
    return _observe(
        units,
        language=language,
        source_sha256=expected_sha256,
        split=split,
        analyzer=analyzer,
        limits=limits,
        document_hashes={d.document_id: d.text_sha256 for d in documents},
        source_scope="wikimedia-provisional-document-pilot",
        sampling_description=(
            "Explicit provisional document pilot. Paragraphs retain source document IDs. "
            "Denominator and document dispersion include only exact aligned lexical model tokens; "
            "blocked/unavailable/skipped text and nonlexical tokens are excluded. "
            "Not balanced general-language frequency; senses and variants remain unresolved."
        ),
    )


def observe_training_corpus(
    path: Path,
    expected_sha256: str,
    language: str,
    analyzer: ContextualAnalyzer,
    *,
    acquisition_receipt: dict,
    limits: ObservationLimits | None = None,
) -> CorpusObservationResult:
    """Observe catalog UD training text as a grammar-only calibration pilot.

    The explicit acquisition receipt must match the catalog train URL and hash.
    Test/development/reference inputs cannot be relabeled through this adapter.
    Treebank labels remain in the original source, never assigned as senses.
    """
    from multilang.services.vocabulary_preparation import source_catalog
    from multilang.services.vocabulary_sources import SourceLimits, read_conllu

    limits = limits or ObservationLimits(max_units=200)
    code = SupportedLanguage(language)
    catalog = source_catalog(language)["corpus"]
    if (
        acquisition_receipt.get("kind") != "corpus-train"
        or acquisition_receipt.get("language") != language
        or acquisition_receipt.get("sha256") != expected_sha256
        or acquisition_receipt.get("source_id") != catalog["source_id"]
        or acquisition_receipt.get("source_url") not in catalog["train_urls"]
    ):
        raise ValueError("catalog training acquisition receipt does not match source")
    units = []
    by_document: dict[str, list[tuple[str, str]]] = {}
    for sentence in read_conllu(
        path,
        language=language,
        expected_sha256=expected_sha256,
        limits=SourceLimits(
            max_bytes=64 * 1024**2,
            max_expanded_bytes=64 * 1024**2,
            max_records=1000000,
            max_line_bytes=128 * 1024,
        ),
    ):
        units.append((sentence.document_id, sentence.sentence_id, None, None, sentence.text))
        if len(units) > limits.max_source_units:
            raise ValueError("source unit limit exceeded")
        by_document.setdefault(sentence.document_id, []).append(
            (sentence.sentence_id, sentence.text)
        )
    return _observe(
        units,
        language=code,
        source_sha256=expected_sha256,
        split="calibration",
        analyzer=analyzer,
        limits=limits,
        document_hashes={
            key: canonical_sha256([text for _sentence_id, text in value])
            for key, value in by_document.items()
        },
        source_scope="UD-train-grammar-only",
        document_boundaries_known=f"source-{expected_sha256}" not in by_document,
        sampling_description=(
            "Bounded UD training prefix, grammar-only calibration pilot. Source document IDs retained; "
            "unknown document boundaries disable document counts and dispersion; source-container IDs "
            "remain only in original analyses. Denominator includes only "
            "exact aligned lexical model tokens in analyzed units; all skipped/blocked text is reported. "
            "Not balanced general-language frequency or independent linguistic evaluation."
        ),
    )
