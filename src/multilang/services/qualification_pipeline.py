"""Local source-to-review orchestration with explicit, immutable evidence inputs.

No acquisition, model inference, provider calls, or linguistic approval occurs
here. Finished output can be reused only after checking the frozen request and
all current input and output artifacts. An interrupted unpublished run can be
restarted safely because every operation is local and no source is modified.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import sentence_hash
from multilang.services.qualification_observations import CorpusObservationResult
from multilang.services.qualification_pilot import (
    EvaluationInput,
    PreparedVocabularyInput,
    SourceCategoryInput,
    _categories,
    _evaluation,
    _prepared_inputs,
    _seed_words,
    prepare_qualification_pilot,
)
from multilang.services.qualification_review import _json
from multilang.services.vocabulary_preparation import source_catalog
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_sources import SourceLimits, _verified_lines

Seed = Annotated[str, Field(min_length=1, max_length=512)]


class ArtifactReference(NativeContract):
    path: Path
    sha256: Sha256


class SeedProvenance(NativeContract):
    requested_language: SupportedLanguage
    effective_language: Identifier
    source: Literal["explicit", "wordfreq"]
    source_version: Identifier
    raw_seed_words: tuple[Seed, ...] = Field(min_length=1, max_length=100000)
    normalization: Literal["NFC-preserve-order-v1"] = "NFC-preserve-order-v1"
    selection_reason: str = Field(min_length=1, max_length=4000)
    seed_only: Literal[True] = True
    production_eligible: Literal[False] = False


class QualificationPipelineRequest(NativeContract):
    schema_version: Literal[1] = 1
    language: SupportedLanguage
    prepared_inputs: tuple[PreparedVocabularyInput, ...] = Field(min_length=1, max_length=32)
    seed_words: tuple[Seed, ...] = Field(min_length=1, max_length=100000)
    seed_provenance: SeedProvenance
    profile_sha256: Sha256
    rubric_sha256: Sha256
    observation: ArtifactReference | None = None
    evaluation_input: EvaluationInput | None = None
    source_categories: SourceCategoryInput | None = None
    headword_count: int = Field(default=20, ge=1, le=3000, strict=True)
    case_count: int = Field(default=200, ge=1, le=5000, strict=True)
    packet_item_limit: int = Field(default=500, ge=1, le=5000, strict=True)
    limits: SourceLimits = Field(default_factory=SourceLimits)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        source_catalog(self.language.value)
        if self.seed_provenance.requested_language != self.language:
            raise ValueError("seed requested language does not match pipeline language")
        _seed_words(self.seed_words)
        normalized = tuple(
            unicodedata.normalize("NFC", word) for word in self.seed_provenance.raw_seed_words
        )
        if normalized != self.seed_words:
            raise ValueError("seed provenance does not reproduce NFC seeds and original order")
        return self


def _dump(path: Path, value, *, limit: int = 128 * 1024**2) -> None:
    data = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    if len(data) > limit:
        raise ValueError("pipeline artifact byte limit exceeded")
    with _plain_path(path).open("xb") as handle:
        handle.write(data)
    path.chmod(0o600)


def _observation(reference, language, limits):
    if reference is None:
        return None
    result = CorpusObservationResult.model_validate(
        _json(
            _read_bytes(
                reference.path, reference.sha256, limit=min(limits.max_bytes, 512 * 1024**2)
            )
        )
    )
    if result.language != language or result.split != "calibration":
        raise ValueError("observation language or calibration split mismatch")
    if (
        result.coverage.measured_lexical_tokens != len(result.occurrences)
        or result.coverage.analyzed_unit_count != len(result.analyses)
        or len(result.occurrences) > min(limits.max_records, 1000000)
        or (result.context is None) != (not result.occurrences)
    ):
        raise ValueError("observation counts or context mismatch")
    if result.context is not None and (
        result.context.language != language
        or result.context.split != "calibration"
        or result.context.source_sha256s != (result.source_sha256,)
        or result.context.token_count != len(result.occurrences)
    ):
        raise ValueError("observation context provenance or denominator mismatch")
    fingerprints, observed_tokens, seen = set(), Counter(), set()
    statuses, documents = Counter(), Counter()
    source_chars = sum(unit.nonspace_characters for unit in result.skipped_units)
    aligned_chars = blocked_chars = nonlexical = 0
    for unit in result.analyses:
        analysis = unit.analysis
        unit_key = (unit.document_id, unit.sentence_id)
        if (
            unit_key in seen
            or unit.source_sha256 != result.source_sha256
            or analysis.language != language.value
            or analysis.sentence_sha256 != sentence_hash(unit.text)
        ):
            raise ValueError("observation analysis source mismatch")
        seen.add(unit_key)
        fingerprints.add(analysis.model_fingerprint)
        statuses[analysis.status] += 1
        source_chars += sum(not char.isspace() for char in unit.text)
        for token in (*analysis.tokens, *analysis.blocked_spans):
            if unit.text[token.start : token.end] != token.text:
                raise ValueError("observation analysis span mismatch")
        aligned_chars += sum(
            sum(not char.isspace() for char in token.text) for token in analysis.tokens
        )
        blocked_chars += sum(
            sum(not char.isspace() for char in token.text) for token in analysis.blocked_spans
        )
        for token in analysis.tokens:
            if token.pos in {"X", "SYM", "PUNCT"}:
                nonlexical += 1
                continue
            documents[unit.document_id] += 1
            observed_tokens[
                (
                    unit.document_id if result.coverage.document_boundaries_known else None,
                    unit.sentence_id,
                    unit.text,
                    token.start,
                    token.end,
                    token.text,
                    token.lemma,
                    token.pos,
                    canonical_sha256(dict(token.features)),
                )
            ] += 1
    if tuple(sorted(fingerprints)) != result.model_fingerprints:
        raise ValueError("observation model fingerprints mismatch")
    coverage = result.coverage
    if (
        coverage.source_unit_count != len(result.analyses) + len(result.skipped_units)
        or dict(coverage.statuses) != dict(statuses)
        or coverage.source_nonspace_characters != source_chars
        or coverage.aligned_nonspace_characters != aligned_chars
        or coverage.blocked_nonspace_characters != blocked_chars
        or coverage.unaccounted_nonspace_characters != source_chars - aligned_chars - blocked_chars
        or coverage.excluded_nonlexical_tokens != nonlexical
    ):
        raise ValueError("observation coverage does not match original analyses")
    if not coverage.document_boundaries_known:
        if (
            coverage.source_document_count is not None
            or coverage.measured_document_count is not None
            or (result.context is not None and result.context.documents)
        ):
            raise ValueError("observation has counts for unknown document boundaries")
    elif (
        coverage.measured_document_count != len(documents)
        or coverage.source_document_count is None
        or coverage.source_document_count < len(documents)
        or (
            result.context is not None
            and {doc.document_id: doc.token_count for doc in result.context.documents}
            != dict(documents)
        )
    ):
        raise ValueError("observation document denominators do not match original analyses")
    occurrences = Counter()
    for item in result.occurrences:
        if (
            item.language != language
            or item.split != "calibration"
            or item.source_sha256 != result.source_sha256
            or item.sense_id is not None
        ):
            raise ValueError("observation occurrence provenance mismatch")
        occurrences[
            (
                item.document_id,
                item.sentence_id,
                item.sentence,
                item.start,
                item.end,
                item.text,
                item.lemma,
                item.pos,
                canonical_sha256(dict(item.features)),
            )
        ] += 1
    if occurrences != observed_tokens:
        raise ValueError("observation occurrence does not match source analysis")
    return result


def _inputs(request):
    prepared = _prepared_inputs(request.prepared_inputs, request.language.value, request.limits)
    _categories(request.source_categories, request.limits)
    evaluation, _, _, _ = _evaluation(
        request.evaluation_input, request.language.value, request.case_count, request.limits
    )
    observation = _observation(request.observation, request.language, request.limits)
    evidence = {
        "language": request.language.value,
        "source_catalog_sha256": canonical_sha256(source_catalog(request.language.value)),
        "prepared_inputs": [
            {
                "manifest_file_sha256": ref.manifest_sha256,
                "preparation_sha256": manifest["preparation_sha256"],
                "dictionary_sha256": manifest["dictionary_sha256"],
            }
            for ref, manifest in prepared
        ],
        "observation": None
        if observation is None
        else {
            "file_sha256": request.observation.sha256,
            "source_sha256": observation.source_sha256,
            "source_scope": observation.source_scope,
            "sampling_description": observation.sampling_description,
            "denominator_policy": observation.denominator_policy,
            "coverage": observation.coverage.model_dump(mode="json"),
            "model_fingerprints": list(observation.model_fingerprints),
        },
        "evaluation": None
        if evaluation is None
        else {
            "manifest_file_sha256": request.evaluation_input.manifest_sha256,
            "evaluation_sha256": evaluation["evaluation_sha256"],
        },
        "source_categories_sha256": None
        if request.source_categories is None
        else request.source_categories.sha256,
        "redistribution_approved": False,
        "production_eligible": False,
    }
    return observation, evidence


def _inventory(root, limit):
    result, total = {}, 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            _plain_path(Path(directory) / name)
        for name in sorted(files):
            path = Path(directory) / name
            if path == root / "manifest.json":
                continue
            data = _read_bytes(path, limit=limit)
            total += len(data)
            if total > limit or len(result) >= 100000:
                raise ValueError("pipeline output inventory exceeds bounds")
            result[path.relative_to(root).as_posix()] = hashlib.sha256(data).hexdigest()
    return dict(sorted(result.items()))


def _resume(root, request, evidence):
    manifest = _json(_read_bytes(root / "manifest.json", limit=1024**2))
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or manifest.get("status") != "prepared"
        or manifest.get("production_eligible") is not False
        or manifest.get("request_sha256") != canonical_sha256(request)
        or manifest.get("source_evidence_sha256") != canonical_sha256(evidence)
        or manifest.get("pipeline_sha256")
        != canonical_sha256({k: v for k, v in manifest.items() if k != "pipeline_sha256"})
    ):
        raise ValueError("pipeline request or manifest checksum mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or any(
        not isinstance(name, str)
        or PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        for name, digest in files.items()
    ):
        raise ValueError("pipeline output inventory invalid")
    if files != _inventory(root, request["limits"]["max_output_bytes"]):
        raise ValueError("pipeline output inventory checksum mismatch")
    if (
        _json(_read_bytes(root / "request.json")) != request
        or _json(_read_bytes(root / "source-evidence.json")) != evidence
    ):
        raise ValueError("pipeline frozen request or source evidence mismatch")
    return manifest


def run_qualification_pipeline(request: QualificationPipelineRequest, output: Path) -> dict:
    """Prepare local review packets, or verify and reuse the same completed run."""
    request = QualificationPipelineRequest.model_validate(request.model_dump(mode="json"))
    output = _plain_path(output)
    observation, evidence = _inputs(request)
    payload = request.model_dump(mode="json")
    if output.exists():
        return _resume(output, payload, evidence)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".qualification-pipeline-", dir=output.parent) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir(mode=0o700)
        _dump(staging / "request.json", payload)
        provenance = request.seed_provenance.model_dump(mode="json")
        provenance["transformations"] = [
            {"rank": index + 1, "original": original, "normalized": normalized}
            for index, (original, normalized) in enumerate(
                zip(request.seed_provenance.raw_seed_words, request.seed_words, strict=True)
            )
            if original != normalized
        ]
        provenance["seed_words_sha256"] = canonical_sha256(list(request.seed_words))
        provenance["effective_language_is_frequency_qualification"] = False
        _dump(staging / "seed-provenance.json", provenance)
        _dump(staging / "source-evidence.json", evidence)
        pilot = prepare_qualification_pilot(
            language=request.language.value,
            prepared_inputs=request.prepared_inputs,
            seed_words=request.seed_words,
            profile_sha256=request.profile_sha256,
            rubric_sha256=request.rubric_sha256,
            output=staging / "pilot",
            evaluation_input=request.evaluation_input,
            headword_count=request.headword_count,
            case_count=request.case_count,
            evidence_context=None if observation is None else observation.context,
            occurrences=() if observation is None else observation.occurrences,
            source_categories=request.source_categories,
            packet_item_limit=request.packet_item_limit,
            limits=request.limits,
        )
        result = {
            "schema_version": 1,
            "status": "prepared",
            "language": request.language.value,
            "request_sha256": canonical_sha256(payload),
            "source_evidence_sha256": canonical_sha256(evidence),
            "pilot": {
                key: pilot[key]
                for key in (
                    "pilot_sha256",
                    "headword_count",
                    "lexical_candidate_count",
                    "inflection_candidate_count",
                    "dictionary_form_proposal_count",
                    "measurement_count",
                    "evaluation_case_count",
                    "blockers",
                    "packets",
                )
            },
            "files": _inventory(staging, request.limits.max_output_bytes),
            "provider_calls_executed": 0,
            "model_calls_executed": 0,
            "production_eligible": False,
            "limitations": [
                "Candidate spellings and senses are unreviewed; capitalizations remain distinct.",
                "Seed ordering does not establish qualified language-specific frequency.",
                "Local checks establish artifact consistency, not independent source authenticity.",
                "Corpus observations retain their declared scope and excluded-token coverage.",
                "No redistribution, human review, or production approval is created.",
            ],
        }
        result["pipeline_sha256"] = canonical_sha256(result)
        _dump(staging / "manifest.json", result, limit=1024**2)
        if output.exists():
            raise ValueError("pipeline output created concurrently")
        os.rename(staging, output)
    return result


def prepare_source_categories(
    dictionary: Path,
    dictionary_sha256: str,
    output: Path,
    *,
    language: str,
    limits: SourceLimits | None = None,
) -> SourceCategoryInput:
    """Freeze raw Wiktextract categories without changing source records or POS."""
    source_catalog(language)
    limits = limits or SourceLimits()
    output = _plain_path(output)
    if output.exists():
        raise ValueError("source category output already exists")
    categories = {}
    for line in _verified_lines(dictionary, dictionary_sha256, limits):
        if not line.strip():
            continue
        record = _json(line.encode())
        if not isinstance(record, dict):
            raise ValueError("source dictionary record must be an object")
        if record.get("lang_code") != language:
            continue
        category = record.get("pos")
        if isinstance(category, str) and 0 < len(category) <= 128:
            categories[canonical_sha256(record)] = category
        if len(categories) > limits.max_unique_entries:
            raise ValueError("source category count exceeds bounds")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".source-categories-", dir=output.parent) as temporary:
        path = Path(temporary) / "categories.json"
        _dump(path, categories, limit=min(limits.max_output_bytes, 16 * 1024**2))
        digest = hashlib.sha256(_read_bytes(path)).hexdigest()
        try:
            os.link(path, output)
        except FileExistsError:
            raise ValueError("source category output already exists") from None
    return SourceCategoryInput(path=output, sha256=digest)
