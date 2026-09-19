"""Replayable document partitions from original, hash-verified CoNLL-U bytes.

These are source annotations, not a model reanalysis or qualified lexical facts.
Complete selected documents and every original token frame remain inspectable;
the measurement denominator contains only explicitly eligible aligned UD tokens.
Legacy review, observation and leakage-key contracts are not reinterpreted.
"""

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, computed_field, model_validator

from multilang.domain.form_evidence import (
    LEXICAL_UPOS,
    CorpusEvidenceContext,
    EvidenceDocument,
    EvidenceOccurrence,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import sentence_hash
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact
from multilang.services.qualification_pipeline import ArtifactReference
from multilang.services.vocabulary_sources import (
    CorpusSentence,
    SourceLimits,
    _verified_lines,
    read_conllu,
)

_DENOMINATOR = "aligned-lexical-ud-annotation-tokens-v1"
_SCOPE = (
    "Complete selected source documents; denominator includes only aligned lexical UD "
    "annotation tokens with usable lemmas. Source annotations and senses remain unreviewed. "
    "Not model reanalysis, balanced general-language frequency or production qualification."
)


class DocumentPartitionInput(NativeContract):
    schema_version: Literal["document-partition-input-1"] = "document-partition-input-1"
    source: ArtifactReference
    language: SupportedLanguage
    split: Literal["calibration", "evaluation"]
    document_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=100000)
    limits: SourceLimits = Field(default_factory=SourceLimits)

    @model_validator(mode="after")
    def unique_selection(self):
        if len(set(self.document_ids)) != len(self.document_ids):
            raise ValueError("duplicate document selection")
        if len(self.document_ids) > self.limits.max_unique_entries:
            raise ValueError("document selection limit exceeded")
        return self


class PartitionTokenDisposition(NativeContract):
    token_index: int = Field(ge=1, strict=True)
    status: Literal["included", "excluded"]
    reason: Literal[
        "aligned_lexical_annotation",
        "unaligned_surface",
        "missing_lemma",
        "nonlexical_pos",
        "unsupported_pos",
        "unsupported_annotation_shape",
    ]


class PartitionSentence(NativeContract):
    source_order: int = Field(ge=0, strict=True)
    reference: CorpusSentence
    raw_conllu: str = Field(min_length=1, max_length=128 * 1024**2)
    token_dispositions: tuple[PartitionTokenDisposition, ...] = Field(max_length=16384)

    @computed_field
    @property
    def text_sha256(self) -> str:
        return sentence_hash(self.reference.text)

    @computed_field
    @property
    def frame_sha256(self) -> str:
        return sha256(self.raw_conllu.encode("utf-8")).hexdigest()


class PartitionDocument(NativeContract):
    document_id: Identifier
    source_order: int = Field(ge=0, strict=True)
    sentences: tuple[PartitionSentence, ...] = Field(min_length=1, max_length=100000)

    @computed_field
    @property
    def text_sha256(self) -> str:
        # Match native document-content identity: full ordered sentence texts,
        # independent of source path/container, document ID and sentence IDs.
        return canonical_sha256([row.reference.text for row in self.sentences])


class PartitionDocumentInventory(NativeContract):
    document_id: Identifier
    source_order: int = Field(ge=0, strict=True)
    sentence_count: int = Field(ge=1, strict=True)
    token_count: int = Field(ge=1, strict=True)
    text_sha256: Sha256
    sentence_text_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=100000)
    frame_sha256s: tuple[Sha256, ...] = Field(min_length=1, max_length=100000)


class EvaluationDocumentPartition(NativeContract):
    schema_version: Literal["evaluation-document-partition-1"] = "evaluation-document-partition-1"
    spec: DocumentPartitionInput
    source_documents: tuple[PartitionDocumentInventory, ...] = Field(
        min_length=1, max_length=100000
    )
    source_document_count: int = Field(ge=1, strict=True)
    source_sentence_count: int = Field(ge=1, strict=True)
    source_token_count: int = Field(ge=1, strict=True)
    documents: tuple[PartitionDocument, ...] = Field(min_length=1, max_length=100000)
    context: CorpusEvidenceContext | None
    occurrences: tuple[EvidenceOccurrence, ...] = Field(max_length=1000000)
    denominator_policy: Literal["aligned-lexical-ud-annotation-tokens-v1"] = _DENOMINATOR
    annotation_origin: Literal["unreviewed-ud-source-annotations"] = (
        "unreviewed-ud-source-annotations"
    )
    complete_document_population: Literal[True] = True
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def coherent_population(self):
        inventory = {row.document_id: row for row in self.source_documents}
        if (
            len(inventory) != len(self.source_documents)
            or self.source_document_count != len(inventory)
            or self.source_sentence_count != sum(row.sentence_count for row in inventory.values())
            or self.source_token_count != sum(row.token_count for row in inventory.values())
            or [row.source_order for row in self.source_documents] != list(range(len(inventory)))
        ):
            raise ValueError("partition source inventory mismatch")
        selected = tuple(row.document_id for row in self.documents)
        if len(set(selected)) != len(selected) or set(selected) != set(self.spec.document_ids):
            raise ValueError("partition document selection mismatch")
        if [row.source_order for row in self.documents] != sorted(
            row.source_order for row in self.documents
        ):
            raise ValueError("partition document order mismatch")
        for document in self.documents:
            proof = inventory.get(document.document_id)
            if proof is None or (
                proof.source_order != document.source_order
                or proof.text_sha256 != document.text_sha256
                or proof.sentence_count != len(document.sentences)
                or proof.token_count != sum(len(row.reference.tokens) for row in document.sentences)
                or proof.sentence_text_sha256s
                != tuple(row.text_sha256 for row in document.sentences)
                or proof.frame_sha256s != tuple(row.frame_sha256 for row in document.sentences)
            ):
                raise ValueError("partition selected document inventory mismatch")
            orders = [row.source_order for row in document.sentences]
            if orders != list(range(orders[0], orders[0] + len(orders))):
                raise ValueError("partition sentence order mismatch")
            for row in document.sentences:
                if (
                    row.reference.document_id != document.document_id
                    or row.reference.language != self.spec.language
                    or row.reference.source_sha256 != self.spec.source.sha256
                ):
                    raise ValueError("partition sentence source mismatch")
                dispositions, _ = _sentence_population(row.reference, self.spec.split)
                if row.token_dispositions != dispositions:
                    raise ValueError("partition token disposition drift")
        context, occurrences = _population(self.documents, self.spec)
        if self.context != context or self.occurrences != occurrences:
            raise ValueError("partition observation population or denominator drift")
        return self

    @computed_field
    @property
    def selected_token_count(self) -> int:
        return sum(len(row.reference.tokens) for doc in self.documents for row in doc.sentences)

    @computed_field
    @property
    def eligible_token_count(self) -> int:
        return len(self.occurrences)

    @computed_field
    @property
    def excluded_token_count(self) -> int:
        return self.selected_token_count - self.eligible_token_count

    @computed_field
    @property
    def exclusion_counts(self) -> dict[str, int]:
        return dict(
            sorted(
                Counter(
                    token.reason
                    for doc in self.documents
                    for row in doc.sentences
                    for token in row.token_dispositions
                    if token.status == "excluded"
                ).items()
            )
        )

    @computed_field
    @property
    def partition_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


class PartitionSeparationReport(NativeContract):
    schema_version: Literal["document-partition-separation-1"] = "document-partition-separation-1"
    calibration_partition_sha256: Sha256
    evaluation_partition_sha256: Sha256
    same_source_container: bool
    disjoint: Literal[True] = True
    production_eligible: Literal[False] = False


def _sentence_population(sentence, split):
    dispositions, occurrences = [], []
    for token in sentence.tokens:
        occurrence = None
        if token.pos in {"PUNCT", "SYM", "X", None}:
            reason = "nonlexical_pos"
        elif token.pos not in LEXICAL_UPOS:
            reason = "unsupported_pos"
        elif (
            token.start is None
            or token.end is None
            or sentence.text[token.start : token.end] != token.text
        ):
            reason = "unaligned_surface"
        elif token.lemma is None or not token.lemma.strip():
            reason = "missing_lemma"
        else:
            try:
                occurrence = EvidenceOccurrence(
                    language=sentence.language,
                    split=split,
                    source_sha256=sentence.source_sha256,
                    document_id=sentence.document_id,
                    sentence_id=sentence.sentence_id,
                    sentence=sentence.text,
                    start=token.start,
                    end=token.end,
                    text=token.text,
                    lemma=token.lemma,
                    pos=token.pos,
                    features=token.features,
                    sense_id=None,
                )
            except ValidationError:
                reason = "unsupported_annotation_shape"
            else:
                reason = "aligned_lexical_annotation"
        dispositions.append(
            PartitionTokenDisposition(
                token_index=token.index,
                status="included" if occurrence is not None else "excluded",
                reason=reason,
            )
        )
        if occurrence is not None:
            occurrences.append(occurrence)
    return tuple(dispositions), tuple(occurrences)


def _population(documents, spec):
    occurrences, evidence_documents = [], []
    for document in documents:
        observed = []
        for sentence in document.sentences:
            _, values = _sentence_population(sentence.reference, spec.split)
            observed.extend(values)
        occurrences.extend(observed)
        if observed:
            evidence_documents.append(
                EvidenceDocument(
                    source_sha256=spec.source.sha256,
                    document_id=document.document_id,
                    text_sha256=document.text_sha256,
                    token_count=len(observed),
                )
            )
    context = (
        CorpusEvidenceContext(
            language=spec.language,
            split=spec.split,
            source_sha256s=(spec.source.sha256,),
            token_count=len(occurrences),
            documents=tuple(evidence_documents),
            sampling_description=_SCOPE,
        )
        if occurrences
        else None
    )
    return context, tuple(occurrences)


def _frames(spec):
    """Keep raw MWT, empty-node, dependency and metadata rows the reader does not expose."""
    frame, size, has_rows = [], 0, False
    for line in _verified_lines(spec.source.path, spec.source.sha256, spec.limits):
        frame.append(line)
        size += len(line.encode("utf-8"))
        if size > spec.limits.max_output_bytes:
            raise ValueError("raw CoNLL-U frame byte limit exceeded")
        stripped = line.rstrip("\r\n")
        if stripped and not stripped.startswith("#"):
            has_rows = True
        elif not stripped and has_rows:
            yield "".join(frame)
            frame, size, has_rows = [], 0, False
    if has_rows:
        yield "".join(frame)


def _declared_document(frame):
    declarations = []
    for line in frame.splitlines():
        if line.startswith("#"):
            key, separator, value = line[1:].strip().partition(" = ")
            if separator and key in {"newdoc id", "newdoc_id"}:
                declarations.append(value)
    if len(declarations) > 1:
        raise ValueError("duplicate CoNLL-U document declarations in one sentence frame")
    return declarations[0] if declarations else None


def prepare_evaluation_partition(spec: DocumentPartitionInput) -> EvaluationDocumentPartition:
    """Read bounded original bytes, selecting full real documents and source UD annotations."""
    if isinstance(spec, DocumentPartitionInput):
        spec = spec.model_dump(mode="json")
    spec = DocumentPartitionInput.model_validate(spec)
    requested = set(spec.document_ids)
    documents, inventory = [], []
    active_id, texts, frame_hashes, token_count, selected_frames = None, [], [], 0, []
    seen_documents, seen_sentences = set(), set()
    output_size = source_sentence_count = source_token_count = 0

    def finish_document():
        if active_id is None:
            return
        order = len(inventory)
        inventory.append(
            PartitionDocumentInventory(
                document_id=active_id,
                source_order=order,
                sentence_count=len(texts),
                token_count=token_count,
                text_sha256=canonical_sha256(texts),
                sentence_text_sha256s=tuple(sentence_hash(text) for text in texts),
                frame_sha256s=tuple(frame_hashes),
            )
        )
        if active_id in requested:
            documents.append(
                PartitionDocument(
                    document_id=active_id,
                    source_order=order,
                    sentences=tuple(selected_frames),
                )
            )

    parsed = read_conllu(
        spec.source.path,
        language=spec.language.value,
        expected_sha256=spec.source.sha256,
        limits=spec.limits,
    )
    for index, (reference, raw) in enumerate(zip(parsed, _frames(spec), strict=True)):
        declared = _declared_document(raw)
        if declared is not None:
            if declared in seen_documents:
                raise ValueError("duplicate source document identifier")
            finish_document()
            active_id, texts, frame_hashes, token_count, selected_frames = declared, [], [], 0, []
            seen_documents.add(declared)
            if len(seen_documents) > min(100000, spec.limits.max_unique_entries):
                raise ValueError("source document inventory limit exceeded")
        if active_id is None or reference.document_id != active_id:
            raise ValueError("source document boundaries are unknown or inconsistent")
        key = (active_id, reference.sentence_id)
        if key in seen_sentences:
            raise ValueError("duplicate source sentence identifier within document")
        seen_sentences.add(key)
        if len(seen_sentences) > min(100000, spec.limits.max_records):
            raise ValueError("source sentence inventory limit exceeded")
        texts.append(reference.text)
        frame_hashes.append(sha256(raw.encode("utf-8")).hexdigest())
        token_count += len(reference.tokens)
        source_sentence_count += 1
        source_token_count += len(reference.tokens)
        if active_id in requested:
            dispositions, _ = _sentence_population(reference, spec.split)
            frame = PartitionSentence(
                source_order=index,
                reference=reference,
                raw_conllu=raw,
                token_dispositions=dispositions,
            )
            selected_frames.append(frame)
            output_size += len(json_bytes(frame))
            if output_size > spec.limits.max_output_bytes:
                raise ValueError("partition output byte limit exceeded")
    finish_document()
    if requested - seen_documents:
        raise ValueError("requested document IDs are missing from the original corpus")
    context, occurrences = _population(documents, spec)
    partition = EvaluationDocumentPartition(
        spec=spec,
        source_documents=tuple(inventory),
        source_document_count=len(inventory),
        source_sentence_count=source_sentence_count,
        source_token_count=source_token_count,
        documents=tuple(documents),
        context=context,
        occurrences=occurrences,
    )
    if len(json_bytes(partition)) > spec.limits.max_output_bytes:
        raise ValueError("partition output byte limit exceeded")
    return partition


def verify_evaluation_partition(
    partition: EvaluationDocumentPartition,
) -> EvaluationDocumentPartition:
    """Reconstruct all frames, membership and denominators from the verified original file."""
    partition = EvaluationDocumentPartition.model_validate(
        partition.model_dump(mode="json", exclude_computed_fields=True)
    )
    replay = prepare_evaluation_partition(partition.spec)
    if replay != partition:
        raise ValueError("evaluation partition source replay detected drift")
    return replay


def compare_evaluation_partitions(calibration, evaluation) -> PartitionSeparationReport:
    calibration = verify_evaluation_partition(calibration)
    evaluation = verify_evaluation_partition(evaluation)
    if calibration.spec.split != "calibration" or evaluation.spec.split != "evaluation":
        raise ValueError("partition comparison requires calibration then evaluation splits")
    if calibration.spec.language != evaluation.spec.language:
        raise ValueError("partition comparison language mismatch")
    if {doc.text_sha256 for doc in calibration.documents} & {
        doc.text_sha256 for doc in evaluation.documents
    }:
        raise ValueError("calibration/evaluation document content overlap")
    calibration_sentences = {
        row.text_sha256 for doc in calibration.documents for row in doc.sentences
    }
    evaluation_sentences = {
        row.text_sha256 for doc in evaluation.documents for row in doc.sentences
    }
    if calibration_sentences & evaluation_sentences:
        raise ValueError("calibration/evaluation sentence content overlap")
    return PartitionSeparationReport(
        calibration_partition_sha256=calibration.partition_sha256,
        evaluation_partition_sha256=evaluation.partition_sha256,
        same_source_container=calibration.spec.source.sha256 == evaluation.spec.source.sha256,
    )


def export_evaluation_partition(partition: EvaluationDocumentPartition, output: Path) -> dict:
    partition = verify_evaluation_partition(partition)
    files = {"partition.json": json_bytes(partition), "input.json": json_bytes(partition.spec)}
    if sum(map(len, files.values())) > partition.spec.limits.max_output_bytes:
        raise ValueError("partition artifact output byte limit exceeded")
    return persist_artifact(
        output,
        kind="evaluation-document-partition",
        binding=partition.partition_sha256,
        files=files,
    )
