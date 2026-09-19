"""Document partitions bind complete UD frames, not selected displayed excerpts."""

import gzip
import hashlib
import importlib
import json

import pytest

from multilang.services.qualification_machine_runner import verify_artifact
from multilang.services.vocabulary_sources import SourceLimits


def api():
    name = "multilang.services.qualification_evaluation_partitions"
    assert importlib.util.find_spec(name), "verified document partition service is missing"
    return importlib.import_module(name)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sentence(identifier, subject="We", verb="read"):
    return (
        f"# sent_id = {identifier}\n# text = {subject} {verb}.\n"
        f"1\t{subject}\t{subject.lower()}\tPRON\tPRP\tNumber=Plur\t2\tnsubj\t_\t_\n"
        f"2\t{verb}\t{verb}\tVERB\tVBP\tTense=Pres\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t.\t_\t2\tpunct\t_\t_\n\n"
    )


def source(tmp_path, text=None, *, compressed=False, name="source"):
    text = text or (
        "# newdoc_id = doc-a\n"
        + sentence("a-1")
        + sentence("a-2", "They", "write")
        + "# newdoc id = doc-b\n"
        + sentence("b-1", "Cats", "sleep")
    )
    path = tmp_path / (name + (".conllu.gz" if compressed else ".conllu"))
    raw = text.encode()
    path.write_bytes(gzip.compress(raw) if compressed else raw)
    return path


def spec(path, ids=("doc-a",), *, split="calibration", limits=None):
    return api().DocumentPartitionInput(
        source={"path": path, "sha256": digest(path)},
        language="en",
        split=split,
        document_ids=ids,
        limits=limits or SourceLimits(),
    )


def test_partition_preserves_complete_documents_frames_features_and_population(tmp_path):
    path = source(tmp_path, compressed=True)
    partition = api().prepare_evaluation_partition(spec(path, ("doc-b", "doc-a")))
    assert [doc.document_id for doc in partition.documents] == ["doc-a", "doc-b"]
    assert [doc.source_order for doc in partition.documents] == [0, 1]
    assert [len(doc.sentences) for doc in partition.documents] == [2, 1]
    first = partition.documents[0].sentences[0]
    assert first.source_order == 0
    assert first.reference.sentence_id == "a-1"
    assert first.reference.tokens[0].index == 1
    assert dict(first.reference.tokens[0].features) == {"Number": "Plur"}
    assert "\tPRP\tNumber=Plur\t2\tnsubj\t" in first.raw_conllu
    assert first.raw_conllu.startswith("# newdoc_id = doc-a\n")
    assert partition.source_document_count == 2
    assert partition.source_sentence_count == 3
    assert partition.source_token_count == 9
    assert partition.selected_token_count == 9
    assert partition.eligible_token_count == 6
    assert partition.excluded_token_count == 3
    assert partition.context.token_count == len(partition.occurrences) == 6
    assert [doc.token_count for doc in partition.context.documents] == [4, 2]
    assert all(row.sense_id is None for row in partition.occurrences)
    assert partition.annotation_origin == "unreviewed-ud-source-annotations"
    assert partition.denominator_policy == "aligned-lexical-ud-annotation-tokens-v1"
    assert partition.production_eligible is False
    assert api().verify_evaluation_partition(partition) == partition


def test_same_container_can_have_verified_disjoint_document_partitions(tmp_path):
    path = source(tmp_path)
    train = api().prepare_evaluation_partition(spec(path))
    test = api().prepare_evaluation_partition(spec(path, ("doc-b",), split="evaluation"))
    report = api().compare_evaluation_partitions(train, test)
    assert report.same_source_container is True
    assert report.calibration_partition_sha256 == train.partition_sha256
    assert report.evaluation_partition_sha256 == test.partition_sha256
    assert report.disjoint is True
    assert train.context.token_count == 4
    assert test.context.token_count == 2
    assert [row.sentence_id for row in test.occurrences] == ["b-1", "b-1"]


@pytest.mark.parametrize("mode", ["document", "sentence"])
def test_renamed_containers_and_ids_cannot_hide_duplicate_content(tmp_path, mode):
    original = source(tmp_path)
    text = "# newdoc_id = renamed\n" + sentence("renamed-1")
    if mode == "document":
        text += sentence("renamed-2", "They", "write")
    else:
        text += sentence("renamed-2", "Birds", "fly")
    copy = source(tmp_path, text, name="renamed-container")
    train = api().prepare_evaluation_partition(spec(original))
    test = api().prepare_evaluation_partition(spec(copy, ("renamed",), split="evaluation"))
    with pytest.raises(ValueError, match=f"{mode}.*overlap"):
        api().compare_evaluation_partitions(train, test)


@pytest.mark.parametrize("ids", [("invented",), ("doc-a", "doc-a"), ()])
def test_selection_requires_real_unique_nonempty_document_ids(tmp_path, ids):
    path = source(tmp_path)
    with pytest.raises(ValueError, match="document|selection"):
        api().prepare_evaluation_partition(spec(path, ids))


def test_implicit_source_container_is_not_an_explicit_document(tmp_path):
    path = source(tmp_path, sentence("no-header"))
    with pytest.raises(ValueError, match="document|boundaries"):
        api().prepare_evaluation_partition(spec(path, ("source-" + digest(path),)))


@pytest.mark.parametrize("mode", ["document", "sentence"])
def test_duplicate_source_identifiers_are_rejected(tmp_path, mode):
    text = "# newdoc_id = doc-a\n" + sentence("first")
    text += (
        ("# newdoc id = doc-a\n" + sentence("second")) if mode == "document" else sentence("first")
    )
    path = source(tmp_path, text)
    with pytest.raises(ValueError, match=f"duplicate.*{mode}"):
        api().prepare_evaluation_partition(spec(path))


def test_repeated_document_header_in_one_frame_is_not_silently_collapsed(tmp_path):
    path = source(tmp_path, "# newdoc_id = doc-a\n# newdoc id = doc-a\n" + sentence("a-1"))
    with pytest.raises(ValueError, match="duplicate.*document"):
        api().prepare_evaluation_partition(spec(path))


def test_original_unicode_and_line_endings_are_preserved_even_when_annotations_are_ineligible(
    tmp_path,
):
    original = ("# newdoc_id = doc-a\n" + sentence("a-1", "Cafe\u0301s", "open")).replace(
        "\n", "\r\n"
    )
    path = source(tmp_path, original)
    partition = api().prepare_evaluation_partition(spec(path))
    frame = partition.documents[0].sentences[0]
    assert frame.raw_conllu == original
    assert frame.reference.text == "Cafe\u0301s open."
    assert partition.context is None
    assert partition.exclusion_counts == {"unsupported_annotation_shape": 2, "nonlexical_pos": 1}
    output = tmp_path / "unicode-partition"
    api().export_evaluation_partition(partition, output)
    restored = api().EvaluationDocumentPartition.model_validate_json(
        (output / "partition.json").read_bytes()
    )
    assert api().verify_evaluation_partition(restored) == partition
    assert path.read_bytes() == original.encode()


def test_replay_rejects_coordinated_internally_consistent_population_omission(tmp_path):
    path = source(tmp_path)
    complete = api().prepare_evaluation_partition(spec(path))
    # A self-consistent alternative source contains only one of doc-a's sentences.
    shortened = source(tmp_path, "# newdoc_id = doc-a\n" + sentence("a-1"), name="shortened")
    raw = (
        api()
        .prepare_evaluation_partition(spec(shortened))
        .model_dump(mode="json", exclude_computed_fields=True)
    )
    raw["spec"]["source"] = complete.spec.source.model_dump(mode="json")
    raw["context"]["source_sha256s"] = [complete.spec.source.sha256]
    raw["context"]["documents"][0]["source_sha256"] = complete.spec.source.sha256
    for occurrence in raw["occurrences"]:
        occurrence["source_sha256"] = complete.spec.source.sha256
    raw["documents"][0]["sentences"][0]["reference"]["source_sha256"] = complete.spec.source.sha256
    forged = api().EvaluationDocumentPartition.model_validate(raw)
    with pytest.raises(ValueError, match="replay.*drift"):
        api().verify_evaluation_partition(forged)


@pytest.mark.parametrize("mode", ["language", "split"])
def test_partition_comparison_rejects_incompatible_experiment_scope(tmp_path, mode):
    path = source(tmp_path)
    train = api().prepare_evaluation_partition(spec(path))
    other_spec = spec(path, ("doc-b",), split="evaluation")
    other_spec = other_spec.model_copy(
        update={"language": "pt"} if mode == "language" else {"split": "calibration"}
    )
    test = api().prepare_evaluation_partition(other_spec)
    with pytest.raises(ValueError, match="language|splits"):
        api().compare_evaluation_partitions(train, test)


def test_unaligned_multiword_tokens_and_missing_annotations_have_explicit_skip_reasons(tmp_path):
    text = (
        "# newdoc_id = doc-a\n# sent_id = contracted\n# text = du pain.\n"
        "1-2\tdu\t_\t_\t_\t_\t_\t_\t_\t_\n"
        "1\tde\tde\tADP\t_\t_\t3\tcase\t_\t_\n"
        "2\tle\tle\tDET\t_\t_\t3\tdet\t_\t_\n"
        "3\tpain\t_\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3.1\tghost\tghost\tNOUN\t_\t_\t_\t_\t_\t_\n"
        "4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_\n\n"
    )
    path = source(tmp_path, text)
    partition = api().prepare_evaluation_partition(spec(path))
    frame = partition.documents[0].sentences[0]
    assert "1-2\tdu" in frame.raw_conllu and "3.1\tghost" in frame.raw_conllu
    assert [row.token_index for row in frame.token_dispositions] == [1, 2, 3, 4]
    assert [row.reason for row in frame.token_dispositions] == [
        "unaligned_surface",
        "unaligned_surface",
        "missing_lemma",
        "nonlexical_pos",
    ]
    assert partition.context is None and partition.occurrences == ()
    assert partition.eligible_token_count == 0
    assert partition.excluded_token_count == partition.selected_token_count == 4


@pytest.mark.parametrize(
    "field", ["source", "context", "occurrences", "frames", "selection", "inventory"]
)
def test_verification_rejects_forged_partition_content(tmp_path, field):
    path = source(tmp_path)
    partition = api().prepare_evaluation_partition(spec(path))
    raw = partition.model_dump(mode="json", exclude_computed_fields=True)
    if field == "source":
        raw["spec"]["source"]["sha256"] = "0" * 64
    elif field == "context":
        raw["context"]["token_count"] += 1
        raw["context"]["documents"][0]["token_count"] += 1
    elif field == "occurrences":
        raw["occurrences"] = raw["occurrences"][:1]
    elif field == "frames":
        raw["documents"][0]["sentences"][0]["raw_conllu"] += "# invented\n"
    elif field == "selection":
        raw["spec"]["document_ids"] = ["doc-b"]
    else:
        raw["source_document_count"] += 1
    with pytest.raises(ValueError):
        forged = api().EvaluationDocumentPartition.model_validate(raw)
        api().verify_evaluation_partition(forged)


def test_verification_checks_original_file_even_when_partition_is_internally_unchanged(tmp_path):
    path = source(tmp_path)
    partition = api().prepare_evaluation_partition(spec(path))
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum"):
        api().verify_evaluation_partition(partition)


@pytest.mark.parametrize(
    "limit",
    [
        "max_bytes",
        "max_expanded_bytes",
        "max_line_bytes",
        "max_records",
        "max_tokens_per_sentence",
        "max_output_bytes",
        "max_unique_entries",
    ],
)
def test_source_selection_and_output_limits_fail_closed(tmp_path, limit):
    path = source(tmp_path, compressed=True)
    with pytest.raises(ValueError, match="limit|bounded"):
        api().prepare_evaluation_partition(
            spec(path, ("doc-a", "doc-b"), limits=SourceLimits(**{limit: 1}))
        )


def test_symlink_source_or_output_cannot_bypass_verified_readers(tmp_path):
    path = source(tmp_path)
    linked = tmp_path / "linked.conllu"
    linked.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        api().prepare_evaluation_partition(spec(linked))
    partition = api().prepare_evaluation_partition(spec(path))
    target = tmp_path / "out-link"
    target.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        api().export_evaluation_partition(partition, target / "out")


def test_partition_export_is_immutable_replayable_and_does_not_modify_source(tmp_path):
    path = source(tmp_path)
    before = path.read_bytes()
    partition = api().prepare_evaluation_partition(spec(path))
    output = tmp_path / "partition"
    manifest = api().export_evaluation_partition(partition, output)
    assert verify_artifact(output, kind="evaluation-document-partition") == manifest
    saved = api().EvaluationDocumentPartition.model_validate_json(
        (output / "partition.json").read_bytes()
    )
    assert api().verify_evaluation_partition(saved) == partition
    assert api().export_evaluation_partition(partition, output) == manifest
    assert path.read_bytes() == before
    changed = api().prepare_evaluation_partition(spec(path, ("doc-b",), split="evaluation"))
    with pytest.raises(ValueError, match="drift"):
        api().export_evaluation_partition(changed, output)
    assert json.loads((output / "manifest.json").read_text())["production_eligible"] is False
