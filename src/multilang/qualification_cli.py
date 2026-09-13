"""Local linguistic review, measurable criteria and reproducible pilot commands."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from pydantic import Field

from multilang.domain.form_evidence import CorpusEvidenceContext, EvidenceOccurrence
from multilang.domain.language_profiles import NativeContract
from multilang.services.vocabulary_review import _plain_path, _read_bytes


class MeasurementRequest(NativeContract):
    context: CorpusEvidenceContext
    occurrences: tuple[EvidenceOccurrence, ...] = Field(max_length=1000000)


def _json(path, digest):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        _read_bytes(path, digest, limit=128 * 1024**2), object_pairs_hook=unique_pairs
    )


def _write(output, value):
    payload = value.model_dump(mode="json") if isinstance(value, NativeContract) else value
    data = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    if len(data) > 128 * 1024**2:
        raise ValueError("output exceeds artifact limit")
    with _plain_path(output).open("xb") as handle:
        handle.write(data)
    typer.echo(
        json.dumps(
            {
                "output": str(output),
                "sha256": hashlib.sha256(data).hexdigest(),
                "production_eligible": False,
            },
            ensure_ascii=False,
        )
    )


def create_qualification_app(*, settings=None):
    from multilang.vocabulary_cli import _guard, _print

    cli = typer.Typer(
        help="Measure, review and calibrate linguistic qualification locally.",
        pretty_exceptions_show_locals=False,
    )

    def store():
        from multilang.native_runtime import _evidence_store
        from multilang.settings import Settings

        return _evidence_store(settings or Settings())

    def review_inputs(packet, packet_sha256, submission, submission_sha256):
        from multilang.services.qualification_review import (
            HumanReviewSubmission,
            load_review_packet,
        )

        return (
            load_review_packet(packet, expected_sha256=packet_sha256),
            HumanReviewSubmission.model_validate(_json(submission, submission_sha256)),
        )

    @cli.command("measure")
    @_guard
    def measure(request: Path, request_sha256: str, output: Path):
        from multilang.services.form_evidence import measure_form_evidence

        inputs = MeasurementRequest.model_validate(_json(request, request_sha256))
        _write(output, measure_form_evidence(inputs.context, inputs.occurrences))

    @cli.command("workload")
    @_guard
    def workload(request: Path, request_sha256: str, output: Path):
        from multilang.services.qualification_workload import qualification_workload

        _write(output, qualification_workload(**_json(request, request_sha256)))

    @cli.command("export-review")
    @_guard
    def export(packet: Path, packet_sha256: str, output: Path):
        from multilang.services.qualification_review import export_review, load_review_packet

        manifest = export_review(load_review_packet(packet, expected_sha256=packet_sha256), output)
        _print(manifest.model_dump(mode="json"))

    @cli.command("import-review")
    @_guard
    def import_decisions(
        packet: Path,
        packet_sha256: str,
        submission: Path,
        submission_sha256: str,
        reviewer: str,
        output: Path,
    ):
        from multilang.services.qualification_review import import_review

        result = import_review(
            packet_path=packet,
            packet_sha256=packet_sha256,
            submission_path=submission,
            submission_sha256=submission_sha256,
            expected_reviewer=reviewer,
            verifier=store(),
        )
        _write(output, result)

    @cli.command("review-payload")
    @_guard
    def payload(
        packet: Path, packet_sha256: str, submission: Path, submission_sha256: str, output: Path
    ):
        from multilang.services.qualification_review import review_signing_payload

        values = review_inputs(packet, packet_sha256, submission, submission_sha256)
        _write(
            output, {"purpose": "qualification-review", "payload": review_signing_payload(*values)}
        )

    @cli.command("calibrate")
    @_guard
    def calibrate(
        packet: Path,
        packet_sha256: str,
        submission: Path,
        submission_sha256: str,
        candidates: Path,
        candidates_sha256: str,
        reviewer: str,
        output: Path,
        false_positive_cost: str,
        false_negative_cost: str,
    ):
        from multilang.domain.lexical_identity import ImportantFormCriteria
        from multilang.services.importance_calibration import calibrate_importance

        grid = _json(candidates, candidates_sha256)
        if not isinstance(grid, list) or not 1 <= len(grid) <= 256:
            raise ValueError("candidate grid must contain 1..256 criteria")
        result = calibrate_importance(
            *review_inputs(packet, packet_sha256, submission, submission_sha256),
            candidates=[ImportantFormCriteria.model_validate(c) for c in grid],
            verifier=store(),
            expected_reviewer=reviewer,
            false_positive_cost=Decimal(false_positive_cost),
            false_negative_cost=Decimal(false_negative_cost),
        )
        _write(output, result)

    @cli.command("evaluate")
    @_guard
    def evaluate(
        calibration: Path,
        calibration_sha256: str,
        packet: Path,
        packet_sha256: str,
        submission: Path,
        submission_sha256: str,
        reviewer: str,
        output: Path,
    ):
        from multilang.services.importance_calibration import CalibrationResult, evaluate_importance

        frozen = CalibrationResult.model_validate(_json(calibration, calibration_sha256))
        _write(
            output,
            evaluate_importance(
                frozen,
                *review_inputs(packet, packet_sha256, submission, submission_sha256),
                verifier=store(),
                expected_reviewer=reviewer,
            ),
        )

    @cli.command("prepare-pilot")
    @_guard
    def pilot(request: Path, request_sha256: str, output: Path):
        from multilang.services.qualification_pilot import (
            EvaluationInput,
            PreparedVocabularyInput,
            SourceCategoryInput,
            prepare_qualification_pilot,
        )
        from multilang.services.vocabulary_sources import SourceLimits

        values = _json(request, request_sha256)
        values["prepared_inputs"] = [
            PreparedVocabularyInput(**v) for v in values["prepared_inputs"]
        ]
        if values.get("evaluation_input"):
            values["evaluation_input"] = EvaluationInput(**values["evaluation_input"])
        if values.get("source_categories"):
            values["source_categories"] = SourceCategoryInput.model_validate(
                values["source_categories"]
            )
        if values.get("limits"):
            values["limits"] = SourceLimits.model_validate(values["limits"])
        if values.get("evidence_context"):
            values["evidence_context"] = CorpusEvidenceContext.model_validate(
                values["evidence_context"]
            )
        if values.get("occurrences"):
            values["occurrences"] = [
                EvidenceOccurrence.model_validate(v) for v in values["occurrences"]
            ]
        result = prepare_qualification_pilot(**values, output=output)
        _print(result.model_dump(mode="json") if isinstance(result, NativeContract) else result)

    @cli.command("discover-corpus")
    @_guard
    def discover(
        language: str,
        project: str,
        output: Path,
        limit: Annotated[int, typer.Option(min=1, max=50)] = 25,
        strategy: Annotated[str, typer.Option()] = "alphabetical-prefix",
    ):
        from multilang.services.qualification_corpora import discover_wikimedia_pages

        _write(output, discover_wikimedia_pages(language, project, limit=limit, strategy=strategy))

    @cli.command("acquire-corpus")
    @_guard
    def acquire(
        language: str,
        project: str,
        output: Path,
        page_id: Annotated[list[int], typer.Option(min=1)],
        selection: Annotated[Path | None, typer.Option()] = None,
        selection_sha256: Annotated[str | None, typer.Option()] = None,
    ):
        from multilang.services.qualification_corpora import (
            PageSelection,
            acquire_wikimedia_documents,
        )

        if (selection is None) != (selection_sha256 is None):
            raise ValueError("selection and its SHA-256 must be supplied together")
        frozen = (
            PageSelection.model_validate(_json(selection, selection_sha256))
            if selection is not None else None
        )
        _print(
            acquire_wikimedia_documents(
                language, project, page_id, output, selection=frozen
            ).model_dump(mode="json")
        )

    @cli.command("vocabulary-input")
    @_guard
    def bridge(
        preparation: Path,
        packet: Path,
        packet_sha256: str,
        submission: Path,
        submission_sha256: str,
        reviewer: str,
        profile: Path,
        profile_sha256: str,
        source_id: str,
        source_version: str,
        output: Path,
    ):
        from multilang.domain.language_profiles import LanguageProfile
        from multilang.services.qualification_bridge import build_vocabulary_review_input

        original_packet, original_submission = review_inputs(
            packet, packet_sha256, submission, submission_sha256
        )
        _write(
            output,
            build_vocabulary_review_input(
                preparation_dir=preparation,
                packet=original_packet,
                submission=original_submission,
                expected_reviewer=reviewer,
                verifier=store(),
                profile=LanguageProfile.model_validate(_json(profile, profile_sha256)),
                source_id=source_id,
                source_version=source_version,
            ),
        )

    @cli.command("derive-corrections")
    @_guard
    def corrections(
        preparation: Path,
        packet: Path,
        packet_sha256: str,
        submission: Path,
        submission_sha256: str,
        reviewer: str,
        profile: Path,
        profile_sha256: str,
        source_id: str,
        source_version: str,
        output: Path,
    ):
        from multilang.domain.language_profiles import LanguageProfile
        from multilang.services.qualification_bridge import apply_reviewed_lexical_corrections

        original_packet, original_submission = review_inputs(
            packet, packet_sha256, submission, submission_sha256
        )
        result = apply_reviewed_lexical_corrections(
            preparation_dir=preparation,
            packet=original_packet,
            submission=original_submission,
            expected_reviewer=reviewer,
            verifier=store(),
            profile=LanguageProfile.model_validate(_json(profile, profile_sha256)),
            source_id=source_id,
            source_version=source_version,
            output=output,
        )
        _print(result.model_dump(mode="json"))

    @cli.command("observe-corpus")
    @_guard
    def observe(
        corpus: Path,
        corpus_sha256: str,
        output: Path,
        model_root: Path = Path(".multilang/models/stanza-1.10.0"),
        max_units: Annotated[int, typer.Option(min=1, max=10000)] = 1000,
    ):
        from multilang.services.contextual_morphology import LocalContextualMorphologyService
        from multilang.services.qualification_observations import (
            ObservationLimits,
            observe_document_corpus,
        )

        _write(
            output,
            observe_document_corpus(
                corpus,
                corpus_sha256,
                LocalContextualMorphologyService(model_root=model_root),
                limits=ObservationLimits(max_units=max_units),
            ),
        )

    @cli.command("observe-training")
    @_guard
    def observe_training(
        corpus: Path,
        corpus_sha256: str,
        language: str,
        receipt: Path,
        receipt_sha256: str,
        output: Path,
        model_root: Path = Path(".multilang/models/stanza-1.10.0"),
        max_units: Annotated[int, typer.Option(min=1, max=10000)] = 200,
    ):
        from multilang.services.contextual_morphology import LocalContextualMorphologyService
        from multilang.services.qualification_observations import (
            ObservationLimits,
            observe_training_corpus,
        )

        _write(
            output,
            observe_training_corpus(
                corpus,
                corpus_sha256,
                language,
                LocalContextualMorphologyService(model_root=model_root),
                acquisition_receipt=_json(receipt, receipt_sha256),
                limits=ObservationLimits(max_units=max_units),
            ),
        )

    return cli
