import hashlib
import importlib
import json

import pytest

from multilang.domain.form_evidence import CorpusEvidenceContext, EvidenceOccurrence
from multilang.services.contextual_morphology import sentence_hash
from multilang.services.qualification_observations import CorpusObservationResult
from multilang.services.qualification_pipeline import (
    QualificationPipelineRequest,
    run_qualification_pipeline,
)
from multilang.services.qualification_review import ReviewPacket
from multilang.services.vocabulary_preparation import prepare_vocabulary


def api():
    return importlib.import_module("multilang.services.qualification_machine_evidence")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def published(tmp_path, *, count=3, examples=None):
    source = tmp_path / "dictionary.jsonl"
    record = {
        "lang_code": "pt",
        "word": "dia",
        "pos": "noun",
        "tags": ["common"],
        "forms": [{"form": "dias", "tags": ["plural"]}],
        "senses": [
            {
                "glosses": ["day"],
                "examples": [{"text": text} for text in (examples or ["Bom dia!"])],
            }
        ],
    }
    source.write_text(json.dumps(record) + "\n")
    prepared = tmp_path / "prepared"
    prepare_vocabulary(
        language="pt", dictionary=source, dictionary_sha256=sha(source), output=prepared
    )
    analyses, occurrences, chars = [], [], 0
    for index in range(count):
        text = "dia " + str(index)
        chars += len(text) - 1
        tokens = []
        for start, word, pos in ((0, "dia", "NOUN"), (4, str(index), "NUM")):
            tokens.append(
                dict(
                    text=word,
                    lemma=word,
                    pos=pos,
                    start=start,
                    end=start + len(word),
                    features=(),
                    sentence_sha256=sentence_hash(text),
                    model_fingerprint="c" * 64,
                )
            )
            occurrences.append(
                dict(
                    language="pt",
                    split="calibration",
                    source_sha256="d" * 64,
                    document_id=None,
                    sentence_id=f"sentence-{index}",
                    sentence=text,
                    start=start,
                    end=start + len(word),
                    text=word,
                    lemma=word,
                    pos=pos,
                    features={},
                )
            )
        analyses.append(
            dict(
                source_sha256="d" * 64,
                document_id="source-" + "d" * 64,
                sentence_id=f"sentence-{index}",
                text=text,
                analysis=dict(
                    language="pt",
                    status="complete",
                    sentence_sha256=sentence_hash(text),
                    tokens=tokens,
                    model_fingerprint="c" * 64,
                    reason="synthetic-fixture",
                ),
            )
        )
    observation = CorpusObservationResult.model_validate(
        dict(
            source_sha256="d" * 64,
            language="pt",
            split="calibration",
            context=dict(
                language="pt",
                split="calibration",
                source_sha256s=["d" * 64],
                token_count=len(occurrences),
                documents=[],
                sampling_description="Synthetic exact-span fixture",
            ),
            occurrences=occurrences,
            analyses=analyses,
            skipped_units=[],
            coverage=dict(
                source_document_count=None,
                measured_document_count=None,
                document_boundaries_known=False,
                source_unit_count=count,
                analyzed_unit_count=count,
                source_nonspace_characters=chars,
                aligned_nonspace_characters=chars,
                blocked_nonspace_characters=0,
                unaccounted_nonspace_characters=0,
                measured_lexical_tokens=len(occurrences),
                excluded_nonlexical_tokens=0,
                statuses={"complete": count},
            ),
            model_fingerprints=["c" * 64],
            sampling_description="Synthetic exact-span fixture",
            source_scope="UD-train-grammar-only",
        )
    )
    observation_path = tmp_path / "observation.json"
    observation_path.write_text(observation.model_dump_json())
    request = QualificationPipelineRequest(
        language="pt",
        prepared_inputs=[dict(directory=prepared, manifest_sha256=sha(prepared / "manifest.json"))],
        seed_words=("dia",),
        seed_provenance=dict(
            requested_language="pt",
            effective_language="pt",
            source="explicit",
            source_version="test-1",
            raw_seed_words=("dia",),
            selection_reason="Synthetic test",
        ),
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        headword_count=1,
        case_count=1,
        observation=dict(path=observation_path, sha256=sha(observation_path)),
    )
    output = tmp_path / "pipeline"
    manifest = run_qualification_pipeline(request, output)
    packets = [
        ReviewPacket.model_validate_json(
            (output / "pilot" / row["path"] / "packet.json").read_text()
        )
        for row in manifest["pilot"]["packets"]
        if row["split"] == "calibration"
    ]
    packet = ReviewPacket(
        packet_id="combined-subset",
        language="pt",
        split="calibration",
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        items=tuple(item for packet in packets for item in packet.items),
    )
    return output, packet


def enrich(root, packet):
    return api().enrich_machine_packet(
        packet, pipeline=root, manifest_sha256=sha(root / "manifest.json")
    )


def test_every_same_source_context_is_visible_with_exact_offsets_and_immutable_originals(tmp_path):
    root, parent = published(tmp_path)
    before = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}
    original = next(item for item in parent.items if item.kind == "form")
    assert len(original.sources) == 1
    result = enrich(root, parent)
    item = next(item for item in result.packet.items if item.kind == "form")
    provenance = next(row for row in result.item_provenance if row.item_id == item.item_id)
    assert result.parent_packet_sha256 == parent.packet_sha256
    assert result.packet.packet_sha256 != parent.packet_sha256
    assert provenance.coverage == "complete"
    assert provenance.raw_occurrence_count == provenance.included_occurrence_count == 3
    assert provenance.excluded_occurrence_count == provenance.duplicate_occurrence_count == 0
    assert len(provenance.occurrences) == 3
    for occurrence in provenance.occurrences:
        source = item.sources[occurrence.source_index]
        assert source.excerpt[occurrence.start : occurrence.end] == occurrence.text == "dia"
        assert source.record_id == occurrence.physical_sha256
        assert occurrence.status == "included"
    assert {
        source.excerpt
        for source in item.sources
        if source.source_id == "calibration-corpus-included"
    } == {"dia 0", "dia 1", "dia 2"}
    assert item.measurements == original.measurements
    assert item.measurement_sha256 == original.measurement_sha256
    assert item.evidence_source_keys == original.evidence_source_keys
    assert item.features == original.features
    assert before == {
        p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()
    }
    assert result.production_eligible is False


def test_lexical_paradigms_examples_and_raw_record_identity_are_preserved(tmp_path):
    root, packet = published(tmp_path)
    result = enrich(root, packet)
    item = next(item for item in result.packet.items if item.kind == "lexical")
    source = next(
        source for source in item.sources if source.source_id == "prepared-candidate-record"
    )
    projection = json.loads(source.excerpt)
    assert projection["candidate"]["forms"] == [{"form": "dias", "tags": ["plural"]}]
    assert projection["candidate"]["glosses"] == ["day"]
    assert projection["candidate"]["examples"] == ["Bom dia!"]
    assert projection["candidate"]["tags"] == ["common"]
    assert projection["candidate"]["form_of"] == []
    assert projection["candidate_sha256"] == item.candidate_sha256
    assert projection["source_record_sha256"] == source.record_id
    assert projection["projection_complete"] is True


@pytest.mark.parametrize("tamper", ["parent", "manifest_hash", "source"])
def test_unanchored_parent_or_tampered_pipeline_is_rejected(tmp_path, tamper):
    root, packet = published(tmp_path)
    digest = sha(root / "manifest.json")
    if tamper == "parent":
        item = packet.items[0].model_copy(update={"lemma": "invented"})
        packet = packet.model_copy(update={"items": (item, *packet.items[1:])})
    elif tamper == "manifest_hash":
        digest = "f" * 64
    else:
        (root / "pilot/calibration-occurrences.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="parent|checksum|inventory"):
        api().enrich_machine_packet(packet, pipeline=root, manifest_sha256=digest)


def test_source_cap_exposes_missing_contexts_without_changing_counts(tmp_path):
    root, packet = published(tmp_path, count=130)
    result = enrich(root, packet)
    item = next(item for item in result.packet.items if item.kind == "form")
    provenance = next(row for row in result.item_provenance if row.item_id == item.item_id)
    assert len(item.sources) <= 128
    assert provenance.included_occurrence_count == item.measurements["observed_count"] == 130
    assert provenance.coverage == "partial"
    assert "review_source_limit" in provenance.blockers
    assert provenance.omitted_occurrence_count > 0
    assert (
        sum(row.source_index is None for row in provenance.occurrences)
        == provenance.omitted_occurrence_count
    )
    notice = json.loads(
        next(source.excerpt for source in item.sources if source.source_id == "enrichment-coverage")
    )
    assert notice["coverage"] == "partial"
    assert notice["omitted_occurrence_count"] == provenance.omitted_occurrence_count


def test_bounded_lexical_projection_marks_omissions_and_preserves_non_nfc_source_strings(tmp_path):
    examples = ["cafe\u0301 " + "x" * 2000 for _ in range(60)]
    root, packet = published(tmp_path, examples=examples)
    result = enrich(root, packet)
    item = next(item for item in result.packet.items if item.kind == "lexical")
    source = next(
        source for source in item.sources if source.source_id == "prepared-candidate-record"
    )
    projection = json.loads(source.excerpt)
    provenance = next(row for row in result.item_provenance if row.item_id == item.item_id)
    assert len(source.excerpt) <= 64000
    assert projection["projection_complete"] is False
    assert projection["omitted_counts"]["examples"] > 0
    assert projection["candidate"]["examples"][0] == examples[0]
    assert provenance.coverage == "partial"
    assert "lexical_projection_truncated" in provenance.blockers


def test_ambiguous_and_duplicate_occurrences_are_not_presented_as_accepted_counts():
    from multilang.services.form_evidence import measure_form_evidence

    context = CorpusEvidenceContext(
        language="pt", split="calibration", source_sha256s=("a" * 64,), token_count=4
    )
    first = EvidenceOccurrence(
        language="pt",
        split="calibration",
        source_sha256="a" * 64,
        sentence_id="first",
        sentence="dia",
        start=0,
        end=3,
        text="dia",
        lemma="dia",
        pos="NOUN",
    )
    ambiguous = first.model_copy(update={"sentence_id": "ambiguous"})
    competitor = ambiguous.model_copy(update={"lemma": "diar", "pos": "VERB"})
    occurrences = (first, first, ambiguous, competitor)
    report = measure_form_evidence(context, occurrences)
    measurement = report.measurements[0]
    rows = api()._classify_occurrences(context, occurrences, measurement)
    assert measurement.observed_count == 1
    assert sum(row.status == "included" for row in rows) == 1
    assert sum(row.status == "excluded_ambiguous" for row in rows) == 1
    assert sum(row.duplicate_record_count for row in rows) == 1


def test_enrichment_contract_rejects_forged_offset_provenance(tmp_path):
    root, packet = published(tmp_path)
    result = enrich(root, packet)
    raw = result.model_dump(mode="json", exclude_computed_fields=True)
    proof = next(row for row in raw["item_provenance"] if row["occurrences"])
    proof["occurrences"][0]["start"] = 1
    with pytest.raises(ValueError, match="provenance"):
        api().MachineEvidenceEnrichment.model_validate(raw)
