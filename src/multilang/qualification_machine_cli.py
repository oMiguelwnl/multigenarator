"""Machine qualification commands mounted in the existing vocabulary workflow."""

from decimal import Decimal
from pathlib import Path

import typer

from multilang.domain.language_profiles import NativeContract
from multilang.services.qualification_ai_transport import AITransportLimits, MachineRunBudget
from multilang.services.qualification_machine_runner import (
    export_machine_request,
    import_machine_response,
    json_bytes,
    load_machine_submission,
    persist_artifact,
    read_json,
)


class MachineAPIConfig(NativeContract):
    limits: AITransportLimits
    budget: MachineRunBudget


def create_machine_qualification_app(*, settings=None):
    from multilang.qualification_cli import _write
    from multilang.vocabulary_cli import _guard, _print

    cli = typer.Typer(
        help="Source-bound AI proposals, judgments and explicit machine drafts.",
        pretty_exceptions_show_locals=False,
    )

    def request_input(path, digest):
        from multilang.services.qualification_machine import MachineReviewRequest

        return MachineReviewRequest.model_validate(read_json(path, digest))

    def result_input(path, digest):
        from multilang.services.qualification_machine import MachineQualificationResult

        return MachineQualificationResult.model_validate(read_json(path, digest))

    @cli.command("pipeline")
    @_guard
    def pipeline(request: Path, request_sha256: str, output: Path):
        from multilang.services.qualification_pipeline import (
            QualificationPipelineRequest,
            run_qualification_pipeline,
        )

        _print(
            run_qualification_pipeline(
                QualificationPipelineRequest.model_validate(read_json(request, request_sha256)),
                output,
            )
        )

    @cli.command("propose")
    @_guard
    def propose(
        packet: Path, packet_sha256: str, actor: Path, actor_sha256: str, run_id: str, output: Path
    ):
        from multilang.services.qualification_machine import MachineActor, build_machine_request
        from multilang.services.qualification_review import load_review_packet

        request = build_machine_request(
            load_review_packet(packet, expected_sha256=packet_sha256),
            actor=MachineActor.model_validate(read_json(actor, actor_sha256)),
            run_id=run_id,
        )
        _print(export_machine_request(request, output))

    @cli.command("source-categories")
    @_guard
    def source_categories(dictionary: Path, dictionary_sha256: str, language: str, output: Path):
        from multilang.services.qualification_pipeline import prepare_source_categories

        value = prepare_source_categories(dictionary, dictionary_sha256, output, language=language)
        _print(value.model_dump(mode="json"))

    @cli.command("enrich")
    @_guard
    def enrich(
        packet: Path, packet_sha256: str, pipeline: Path, manifest_sha256: str, output: Path
    ):
        from multilang.domain.lexical_identity import canonical_sha256
        from multilang.services.qualification_machine_evidence import enrich_machine_packet
        from multilang.services.qualification_review import load_review_packet

        value = enrich_machine_packet(
            load_review_packet(packet, expected_sha256=packet_sha256),
            pipeline=pipeline,
            manifest_sha256=manifest_sha256,
        )
        _print(
            persist_artifact(
                output,
                kind="machine-evidence",
                binding=canonical_sha256(value.model_dump(mode="json")),
                files={
                    "enrichment.json": json_bytes(value),
                    "packet.json": json_bytes(value.packet),
                },
            )
        )

    @cli.command("prepare-reviews")
    @_guard
    def prepare_reviews(
        pipeline: Path,
        manifest_sha256: str,
        actor: Path,
        actor_sha256: str,
        output: Path,
        item_limit: int = 20,
        enrich_sources: bool = True,
    ):
        from multilang.services.qualification_machine import MachineActor
        from multilang.services.qualification_machine_batch import export_pipeline_machine_requests

        result = export_pipeline_machine_requests(
            pipeline,
            manifest_sha256=manifest_sha256,
            actor=MachineActor.model_validate(read_json(actor, actor_sha256)),
            output=output,
            item_limit=item_limit,
            enrich_sources=enrich_sources,
        )
        _print({key: value for key, value in result.items() if key != "requests"})

    @cli.command("judge")
    @_guard
    def judge(proposal: Path, actor: Path, actor_sha256: str, run_id: str, output: Path):
        from multilang.services.qualification_machine import MachineActor, build_machine_request

        submission = load_machine_submission(proposal)
        request = build_machine_request(
            submission.request.packet,
            actor=MachineActor.model_validate(read_json(actor, actor_sha256)),
            run_id=run_id,
            proposal=submission,
        )
        _print(export_machine_request(request, output))

    @cli.command("import-response")
    @_guard
    def import_response(
        request: Path,
        request_sha256: str,
        response: Path,
        response_sha256: str,
        metadata: Path,
        metadata_sha256: str,
        output: Path,
    ):
        from multilang.services.qualification_machine import MachineExecutionMetadata
        from multilang.services.vocabulary_review import _read_bytes

        submission = import_machine_response(
            request_input(request, request_sha256),
            _read_bytes(response, response_sha256, limit=2 * 1024**2),
            metadata=MachineExecutionMetadata.model_validate(read_json(metadata, metadata_sha256)),
            output=output,
        )
        _print(
            {
                "output": str(output),
                "submission_sha256": submission.submission_sha256,
                "production_eligible": False,
            }
        )

    @cli.command("reconcile")
    @_guard
    def reconcile(proposal: Path, judgment: Path, output: Path):
        from collections import Counter

        from multilang.services.qualification_machine import reconcile_machine_reviews
        from multilang.services.qualification_machine_draft import render_machine_report

        first, second = load_machine_submission(proposal), load_machine_submission(judgment)
        result = reconcile_machine_reviews(first.request.packet, first, second)
        manifest = persist_artifact(
            output,
            kind="machine-result",
            binding=result.result_sha256,
            files={
                "result.json": json_bytes(result),
                "report.html": render_machine_report(result).encode(),
            },
        )
        _print({**manifest, "counts": dict(Counter(item.status for item in result.decisions))})

    @cli.command("draft")
    @_guard
    def draft(
        result: Path,
        result_sha256: str,
        preparation: Path,
        profile: Path,
        profile_sha256: str,
        source_id: str,
        source_version: str,
        output: Path,
    ):
        from multilang.domain.language_profiles import LanguageProfile
        from multilang.services.qualification_machine_draft import build_machine_vocabulary_draft

        value = build_machine_vocabulary_draft(
            preparation_dir=preparation,
            qualification=result_input(result, result_sha256),
            profile=LanguageProfile.model_validate(read_json(profile, profile_sha256)),
            source_id=source_id,
            source_version=source_version,
        )
        _print(
            persist_artifact(
                output,
                kind="machine-vocabulary-draft",
                binding=value.draft_sha256,
                files={
                    "draft.json": json_bytes(value),
                    "pending-native-review.json": json_bytes(value.pending_native_review),
                },
            )
        )

    @cli.command("calibrate")
    @_guard
    def calibrate(
        result: Path,
        result_sha256: str,
        criteria: Path,
        criteria_sha256: str,
        false_positive_cost: str,
        false_negative_cost: str,
        output: Path,
    ):
        from multilang.domain.lexical_identity import ImportantFormCriteria
        from multilang.services.qualification_machine_calibration import (
            calibrate_machine_importance,
        )

        raw = read_json(criteria, criteria_sha256)
        if not isinstance(raw, list) or not 1 <= len(raw) <= 256:
            raise ValueError("machine calibration requires a bounded criteria array")
        _write(
            output,
            calibrate_machine_importance(
                result_input(result, result_sha256),
                candidates=tuple(ImportantFormCriteria.model_validate(item) for item in raw),
                false_positive_cost=Decimal(false_positive_cost),
                false_negative_cost=Decimal(false_negative_cost),
            ),
        )

    @cli.command("evaluate")
    @_guard
    def evaluate(
        calibration: Path, calibration_sha256: str, result: Path, result_sha256: str, output: Path
    ):
        from multilang.services.qualification_machine_calibration import (
            MachineCalibrationResult,
            evaluate_machine_importance,
        )

        _write(
            output,
            evaluate_machine_importance(
                MachineCalibrationResult.model_validate(read_json(calibration, calibration_sha256)),
                result_input(result, result_sha256),
            ),
        )

    def transport_input(request, config, *, use_credentials):
        from multilang.services.qualification_ai_transport import QualificationAITransport
        from multilang.settings import Settings

        if request.actor.execution_surface != "api" or not request.actor.model:
            raise ValueError("API requests require a declared API actor and model")
        key, enabled = None, False
        if use_credentials:
            active = settings or Settings()
            enabled = active.native_provider_calls_enabled
            # Credentials are read only after an explicitly requested API run.
            if active.litellm_api_key:
                key = active.litellm_api_key
            elif request.actor.model.startswith("openrouter/"):
                key = active.openrouter_api_key
            elif request.actor.model.startswith(("openai/", "gpt-")):
                key = active.openai_api_key
        return QualificationAITransport(
            model=request.actor.model, limits=config.limits, api_key=key
        ), enabled

    @cli.command("preflight")
    @_guard
    def preflight(
        request: Path, request_sha256: str, config: Path, config_sha256: str, output: Path
    ):
        from multilang.services.qualification_machine_runner import machine_preflight

        value = request_input(request, request_sha256)
        options = MachineAPIConfig.model_validate(read_json(config, config_sha256))
        transport, _ = transport_input(value, options, use_credentials=False)
        _write(output, machine_preflight(value, transport=transport, budget=options.budget))

    @cli.command("run-api")
    @_guard
    def run_api(request: Path, request_sha256: str, config: Path, config_sha256: str, output: Path):
        from multilang.services.qualification_machine_runner import run_machine_review

        value = request_input(request, request_sha256)
        options = MachineAPIConfig.model_validate(read_json(config, config_sha256))
        transport, enabled = transport_input(value, options, use_credentials=True)
        submission = run_machine_review(
            value,
            transport=transport,
            budget=options.budget,
            output=output,
            provider_calls_enabled=enabled,
        )
        _print(
            {
                "output": str(output),
                "submission_sha256": submission.submission_sha256,
                "production_eligible": False,
            }
        )

    from multilang.qualification_evaluation_cli import create_partition_evaluation_app
    from multilang.qualification_followup_cli import register_followup_commands
    from multilang.qualification_languages_cli import register_language_commands
    from multilang.qualification_pilot_cli import register_pilot_commands
    from multilang.qualification_revision_cli import register_revision_commands

    register_followup_commands(cli)
    register_language_commands(cli)
    register_pilot_commands(cli)
    register_revision_commands(cli)
    cli.add_typer(create_partition_evaluation_app(), name="evaluation")
    return cli
