"""Local pilot commands; every external artifact has an explicit byte checksum."""

from pathlib import Path

from pydantic import Field

from multilang.domain.audio import AudioFormat
from multilang.domain.language_profiles import Identifier, NativeContract
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact, read_json
from multilang.services.qualification_pipeline import ArtifactReference


class PilotPreparationInput(NativeContract):
    campaign: ArtifactReference
    profile: ArtifactReference
    preparation_dir: Path
    source_id: Identifier
    source_version: Identifier
    item_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=100)
    variant: Identifier


class PilotRequestInput(NativeContract):
    plan: ArtifactReference
    actor: ArtifactReference
    proposal: ArtifactReference | None = None


class PilotImportInput(NativeContract):
    request: ArtifactReference
    response: ArtifactReference
    metadata: ArtifactReference


class PilotCompletionInput(NativeContract):
    plan: ArtifactReference
    proposal: ArtifactReference
    judgment: ArtifactReference
    analyses: ArtifactReference


class PilotAudioInput(NativeContract):
    content: ArtifactReference
    locale: Identifier
    voice_id: Identifier
    provider_model_version: Identifier
    audio_format: AudioFormat = AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3


class PilotExportInput(NativeContract):
    content: ArtifactReference
    audio_plan: ArtifactReference
    audio_versions: ArtifactReference


def register_pilot_commands(cli):
    from multilang.domain.audio_version import AudioVersion
    from multilang.domain.language_profiles import LanguageProfile
    from multilang.services.contextual_morphology import ContextualAnalysis
    from multilang.services.qualification_machine import MachineActor, MachineExecutionMetadata
    from multilang.services.qualification_machine_campaign import MachineCampaign
    from multilang.services.qualification_machine_pilot import (
        MachinePilotAudioPlan,
        MachinePilotContent,
        MachinePilotPlan,
        PilotContentRequest,
        PilotContentSubmission,
        accept_pilot_content,
        build_machine_pilot,
        build_pilot_content_request,
        complete_pilot_content,
        export_machine_pilot,
        prepare_pilot_audio,
    )
    from multilang.vocabulary_cli import _guard, _print

    def load(reference, model=None):
        raw = read_json(reference.path, reference.sha256)
        return model.model_validate(raw) if model else raw

    def save(output, kind, binding, filename, value, **extra):
        return persist_artifact(
            output, kind=kind, binding=binding, files={filename: json_bytes(value), **extra}
        )

    @cli.command("pilot-prepare")
    @_guard
    def prepare(input: Path, input_sha256: str, output: Path):
        config = PilotPreparationInput.model_validate(read_json(input, input_sha256))
        plan = build_machine_pilot(
            load(config.campaign, MachineCampaign),
            preparation_dir=config.preparation_dir,
            profile=load(config.profile, LanguageProfile),
            source_id=config.source_id,
            source_version=config.source_version,
            item_ids=config.item_ids,
            variant=config.variant,
        )
        _print(save(output, "machine-pilot-plan", plan.plan_sha256, "plan.json", plan))

    @cli.command("pilot-request")
    @_guard
    def request(input: Path, input_sha256: str, output: Path):
        config = PilotRequestInput.model_validate(read_json(input, input_sha256))
        value = build_pilot_content_request(
            load(config.plan, MachinePilotPlan),
            actor=load(config.actor, MachineActor),
            proposal=load(config.proposal, PilotContentSubmission) if config.proposal else None,
        )
        _print(
            save(
                output,
                "machine-pilot-request",
                value.request_sha256,
                "request.json",
                value,
                **{
                    "messages.json": json_bytes(value.messages),
                    "response-schema.json": json_bytes(value.response_schema),
                },
            )
        )

    @cli.command("pilot-import")
    @_guard
    def import_response(input: Path, input_sha256: str, output: Path):
        config = PilotImportInput.model_validate(read_json(input, input_sha256))
        value = accept_pilot_content(
            load(config.request, PilotContentRequest),
            load(config.response),
            metadata=load(config.metadata, MachineExecutionMetadata),
        )
        _print(
            save(
                output,
                "machine-pilot-submission",
                value.submission_sha256,
                "submission.json",
                value,
            )
        )

    @cli.command("pilot-complete")
    @_guard
    def complete(input: Path, input_sha256: str, output: Path):
        config = PilotCompletionInput.model_validate(read_json(input, input_sha256))
        raw = load(config.analyses)
        if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
            raise ValueError("pilot requires a bounded analysis array")
        value = complete_pilot_content(
            load(config.plan, MachinePilotPlan),
            load(config.proposal, PilotContentSubmission),
            load(config.judgment, PilotContentSubmission),
            analyses=tuple(ContextualAnalysis.model_validate(item) for item in raw),
        )
        _print(save(output, "machine-pilot-content", value.content_sha256, "content.json", value))

    @cli.command("pilot-audio-plan")
    @_guard
    def audio_plan(input: Path, input_sha256: str, output: Path):
        config = PilotAudioInput.model_validate(read_json(input, input_sha256))
        value = prepare_pilot_audio(
            load(config.content, MachinePilotContent),
            locale=config.locale,
            voice_id=config.voice_id,
            provider_model_version=config.provider_model_version,
            audio_format=config.audio_format,
        )
        _print(
            save(
                output,
                "machine-pilot-audio-plan",
                value.audio_plan_sha256,
                "audio-plan.json",
                value,
            )
        )

    @cli.command("pilot-export")
    @_guard
    def export(input: Path, input_sha256: str, output: Path):
        config = PilotExportInput.model_validate(read_json(input, input_sha256))
        raw = load(config.audio_versions)
        if not isinstance(raw, list) or not 2 <= len(raw) <= 200:
            raise ValueError("pilot requires a bounded audio version array")
        _print(
            export_machine_pilot(
                load(config.content, MachinePilotContent),
                load(config.audio_plan, MachinePilotAudioPlan),
                audio_versions=tuple(AudioVersion.model_validate(item) for item in raw),
                output=output,
            )
        )
