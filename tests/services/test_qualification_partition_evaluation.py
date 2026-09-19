"""A new contract proves the whole feature population before sharing a corpus."""

import hashlib
import importlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from multilang.domain.lexical_identity import ImportantFormCriteria
from multilang.services.qualification_machine import (
    MachineActor,
    accept_machine_response,
    build_machine_request,
    reconcile_machine_reviews,
)


def _api():
    return importlib.import_module("multilang.services.qualification_partition_evaluation")


def _fixture(tmp_path):
    partitions = importlib.import_module("multilang.services.qualification_evaluation_partitions")
    refs = importlib.import_module("multilang.services.qualification_evaluation_references")
    reviews = importlib.import_module("multilang.services.qualification_partition_review")
    from multilang.services.form_evidence import measure_form_evidence

    corpus = tmp_path / "source.conllu"
    corpus.write_text(
        "# newdoc_id = train\n# sent_id = s1\n# text = went cats dogs\n"
        "1\twent\tgo\tVERB\t_\tTense=Past\t0\troot\t_\t_\n"
        "2\tcats\tcat\tNOUN\t_\tNumber=Plur\t1\tobj\t_\t_\n"
        "3\tdogs\tdog\tNOUN\t_\tNumber=Plur\t1\tobj\t_\t_\n\n"
        "# newdoc_id = test\n# sent_id = s2\n# text = cats went dogs\n"
        "1\tcats\tcat\tNOUN\t_\tNumber=Plur\t2\tnsubj\t_\t_\n"
        "2\twent\tgo\tVERB\t_\tTense=Past\t0\troot\t_\t_\n"
        "3\tdogs\tdog\tNOUN\t_\tNumber=Plur\t2\tobj\t_\t_\n\n"
    )
    dictionary = tmp_path / "dict.jsonl"
    dictionary.write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {
                    "lang_code": "en",
                    "word": "go",
                    "pos": "verb",
                    "senses": [{"glosses": ["move"]}],
                    "forms": [{"form": "went", "tags": ["past"]}],
                },
                {
                    "lang_code": "en",
                    "word": "cat",
                    "pos": "noun",
                    "senses": [{"glosses": ["animal"]}],
                    "forms": [{"form": "cats", "tags": ["plural"]}],
                },
                {
                    "lang_code": "en",
                    "word": "dog",
                    "pos": "noun",
                    "senses": [{"glosses": ["animal"]}],
                    "forms": [{"form": "dogs", "tags": ["plural"]}],
                },
            ]
        )
        + "\n"
    )

    def ref(p):
        return {"path": p, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    registry = refs.prepare_dictionary_references(
        refs.DictionaryReferenceInput(
            dictionary=ref(dictionary),
            language="en",
            terms=[
                {"lemma": "go", "pos": "VERB"},
                {"lemma": "cat", "pos": "NOUN"},
                {"lemma": "dog", "pos": "NOUN"},
            ],
        )
    )
    bundles = []
    for split, doc in [("calibration", "train"), ("evaluation", "test")]:
        partition = partitions.prepare_evaluation_partition(
            partitions.DocumentPartitionInput(
                source=ref(corpus), language="en", split=split, document_ids=[doc]
            )
        )
        measured = measure_form_evidence(partition.context, partition.occurrences)
        bundle = reviews.prepare_partition_review(
            partition,
            registry,
            group_sha256s=tuple(m.group_sha256 for m in measured.measurements),
            profile_sha256="a" * 64,
            rubric_sha256="b" * 64,
            packet_id=split,
        )
        bundles.append(bundle)
    policy = ImportantFormCriteria(
        policy_id="partition-test",
        version="1",
        weights={"frequency": "0.25", "irregularity": "0.75"},
        minimum_score="0.25",
        attestation_threshold=1,
        analysis_confidence_threshold="0.9",
        missing_evidence="reject",
    )
    experiment = _api().freeze_partition_experiment(
        *bundles,
        candidates=(policy,),
        false_positive_cost="2",
        false_negative_cost="1",
        frozen_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    return experiment


def _qualify(packet):
    request = build_machine_request(
        packet,
        actor=MachineActor(actor_id="proposer", execution_surface="mock", context_id="proposal"),
        run_id="first",
    )
    decisions = []
    for item in packet.items:
        source = item.sources[0]
        decisions.append(
            {
                "kind": "form",
                "item_id": item.item_id,
                "item_sha256": item.item_sha256,
                "decision": "accepted",
                "reason": "Explicit mock label for testing independent evaluation arithmetic.",
                "citations": [
                    {
                        "source_index": 0,
                        "source_sha256": source.source_sha256,
                        "start": 0,
                        "end": len(source.excerpt),
                        "quote": source.excerpt,
                    }
                ],
                "include": item.text == "went",
                "ratings": {"irregularity": "1" if item.text == "went" else "0"},
                "proposed_sense_id": "motion" if item.text == "went" else "animal",
                "machine_analysis_rating": "1",
            }
        )

    def accept(r):
        response = {"decisions": decisions}
        return accept_machine_response(
            r, json.dumps(response).encode(), metadata={"executed_at": datetime.now(UTC)}
        )

    proposal = accept(request)
    judgment = accept(
        build_machine_request(
            packet,
            actor=MachineActor(actor_id="judge", execution_surface="mock", context_id="judgment"),
            run_id="second",
            proposal=proposal,
        )
    )
    return reconcile_machine_reviews(packet, proposal, judgment)


def test_new_contract_accepts_separate_documents_and_shared_verified_dictionary(tmp_path):
    api = _api()
    experiment = _fixture(tmp_path)
    trained = api.calibrate_partition_importance(
        experiment, _qualify(experiment.calibration.packet)
    )
    result = api.evaluate_partition_importance(
        experiment, trained, _qualify(experiment.evaluation.packet)
    )
    assert result.evaluation.metrics.true_positive == 1
    assert result.evaluation.metrics.true_negative == 2
    assert result.evaluation.metrics.false_positive == 0
    assert result.production_eligible is False
    from multilang.services.qualification_machine_calibration import evaluate_machine_importance

    with pytest.raises(ValueError, match="source overlap"):
        evaluate_machine_importance(trained.calibration, result.evaluation.evaluation_qualification)


def test_changed_frequency_and_hidden_lineage_cannot_enter_new_contract(tmp_path):
    api = _api()
    experiment = _fixture(tmp_path)
    for field, value in [
        ("measurements", {"observed_count": 999}),
        ("evidence_source_keys", ("f" * 64,)),
    ]:
        packet = experiment.calibration.packet
        changed = packet.items[0].model_copy(update={field: value})
        forged = packet.model_copy(update={"items": (changed, *packet.items[1:])})
        with pytest.raises(ValueError, match="packet|bundle|measurement"):
            api.calibrate_partition_importance(experiment, _qualify(forged))


def test_changed_registry_or_grid_after_calibration_is_rejected(tmp_path):
    api = _api()
    experiment = _fixture(tmp_path)
    trained = api.calibrate_partition_importance(
        experiment, _qualify(experiment.calibration.packet)
    )
    policy = experiment.candidate_criteria[0].model_copy(update={"minimum_score": "0.9"})
    changed = experiment.model_copy(update={"candidate_criteria": (policy,)})
    with pytest.raises(ValueError, match="experiment|binding"):
        api.evaluate_partition_importance(changed, trained, _qualify(experiment.evaluation.packet))


def test_frozen_protocol_precedes_declared_labels(tmp_path):
    api = _api()
    experiment = _fixture(tmp_path)
    result = _qualify(experiment.calibration.packet)
    future = experiment.model_copy(update={"frozen_at": datetime.now(UTC) + timedelta(days=1)})
    with pytest.raises(ValueError, match="before|frozen|timestamp"):
        api.calibrate_partition_importance(future, result)


def test_selection_does_not_change_measurement_population(tmp_path):
    _api()
    experiment = _fixture(tmp_path)
    reviews = importlib.import_module("multilang.services.qualification_partition_review")
    all_items = experiment.calibration
    one = reviews.prepare_partition_review(
        all_items.partition,
        all_items.references,
        group_sha256s=all_items.group_sha256s[:1],
        profile_sha256="a" * 64,
        rubric_sha256="b" * 64,
        packet_id="one-only",
    )
    assert one.population_sha256 == all_items.population_sha256
    assert one.packet.items[0].measurements == all_items.packet.items[0].measurements
    assert one.packet.items[0].proposed_ratings == all_items.packet.items[0].proposed_ratings


def test_metrics_do_not_depend_on_callers_decimal_precision(tmp_path):
    api = _api()
    experiment = _fixture(tmp_path)
    policy = experiment.candidate_criteria[0].model_dump(mode="json", exclude_computed_fields=True)
    policy["minimum_score"] = "0"
    experiment = experiment.model_copy(
        update={"candidate_criteria": (ImportantFormCriteria.model_validate(policy),)}
    )
    trained = api.calibrate_partition_importance(
        experiment, _qualify(experiment.calibration.packet)
    )
    qualification = _qualify(experiment.evaluation.packet)
    with localcontext() as arithmetic:
        arithmetic.prec = 2
        result = api.evaluate_partition_importance(experiment, trained, qualification)
    with localcontext() as arithmetic:
        arithmetic.prec = 50
        assert result.evaluation.metrics.precision == Decimal(1) / 3


def test_public_cli_prepares_hash_bound_document_partition(tmp_path):
    from typer.testing import CliRunner

    from multilang.cli import app

    experiment = _fixture(tmp_path)
    path = tmp_path / "input.json"
    path.write_text(experiment.calibration.partition.spec.model_dump_json())
    output = tmp_path / "cli-partition"
    run = CliRunner().invoke(
        app,
        [
            "native",
            "vocabulary",
            "qualification",
            "ai",
            "evaluation",
            "prepare-partition",
            str(path),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            str(output),
        ],
    )
    assert run.exit_code == 0, run.output
    assert json.loads((output / "partition.json").read_text())["spec"]["split"] == "calibration"
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["binding_sha256"] == experiment.calibration.partition.partition_sha256
