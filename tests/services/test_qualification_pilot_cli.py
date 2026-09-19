"""The local pilot CLI binds every input artifact by its exact byte hash."""

import importlib
import json
from hashlib import sha256

import typer
from typer.testing import CliRunner


def app():
    name = "multilang.qualification_pilot_cli"
    assert importlib.util.find_spec(name), "machine pilot CLI is missing"
    cli = typer.Typer()
    importlib.import_module(name).register_pilot_commands(cli)
    return cli


def save(path, value):
    from multilang.services.qualification_machine_runner import json_bytes

    path.write_bytes(json_bytes(value))
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def test_prepare_cli_binds_sources_and_resumes_immutably(tmp_path):
    from test_qualification_machine_pilot import pilot_fixture

    campaign, kwargs = pilot_fixture(tmp_path)
    config = {
        "campaign": save(tmp_path / "campaign.json", campaign),
        "profile": save(tmp_path / "profile.json", kwargs.pop("profile")),
        **kwargs,
    }
    config["preparation_dir"] = str(config["preparation_dir"])
    ref = save(tmp_path / "input.json", config)
    output = tmp_path / "plan"
    runner = CliRunner()
    command = ["pilot-prepare", ref["path"], ref["sha256"], str(output)]
    result = runner.invoke(app(), command)
    assert result.exit_code == 0, result.output
    before = (output / "plan.json").read_bytes()
    assert runner.invoke(app(), command).exit_code == 0
    assert (output / "plan.json").read_bytes() == before
    (tmp_path / "profile.json").write_text("{}")
    assert runner.invoke(app(), command).exit_code != 0
    assert json.loads((output / "manifest.json").read_text())["production_eligible"] is False


def test_audio_cli_and_export_reject_unbound_media(tmp_path):
    from test_qualification_machine_pilot import content_fixture

    content = content_fixture(tmp_path)[-1]
    config = {
        "content": save(tmp_path / "content.json", content),
        "locale": "en-US",
        "voice_id": "en-US-AriaNeural",
        "provider_model_version": "fixture",
    }
    ref = save(tmp_path / "audio-input.json", config)
    output = tmp_path / "audio-plan"
    result = CliRunner().invoke(
        app(), ["pilot-audio-plan", ref["path"], ref["sha256"], str(output)]
    )
    assert result.exit_code == 0, result.output
    assert len(json.loads((output / "audio-plan.json").read_text())["items"]) == 2


def test_request_import_completion_and_export_commands(tmp_path):
    from test_qualification_machine_pilot import audio_fixture, content_fixture

    plan, request, raw, proposal, judgment, analysis, content = content_fixture(tmp_path)
    runner, cli = CliRunner(), app()
    plan_ref = save(tmp_path / "plan.json", plan)
    config = {"plan": plan_ref, "actor": save(tmp_path / "actor.json", request.actor)}
    config_ref = save(tmp_path / "request-input.json", config)
    output = tmp_path / "request"
    result = runner.invoke(
        cli, ["pilot-request", config_ref["path"], config_ref["sha256"], str(output)]
    )
    assert result.exit_code == 0, result.output
    assert (output / "response-schema.json").is_file()
    config = {
        "request": {
            "path": str(output / "request.json"),
            "sha256": sha256((output / "request.json").read_bytes()).hexdigest(),
        },
        "response": save(tmp_path / "response.json", raw),
        "metadata": save(tmp_path / "metadata.json", proposal.metadata),
    }
    config_ref = save(tmp_path / "import-input.json", config)
    result = runner.invoke(
        cli,
        ["pilot-import", config_ref["path"], config_ref["sha256"], str(tmp_path / "submission")],
    )
    assert result.exit_code == 0, result.output
    config = {
        "plan": plan_ref,
        "proposal": save(tmp_path / "proposal.json", proposal),
        "judgment": save(tmp_path / "judgment.json", judgment),
        "analyses": save(tmp_path / "analyses.json", [analysis.model_dump(mode="json")]),
    }
    config_ref = save(tmp_path / "completion-input.json", config)
    result = runner.invoke(
        cli,
        ["pilot-complete", config_ref["path"], config_ref["sha256"], str(tmp_path / "completed")],
    )
    assert result.exit_code == 0, result.output
    audio, versions = audio_fixture(tmp_path, content)
    config = {
        "content": save(tmp_path / "content.json", content),
        "audio_plan": save(tmp_path / "audio.json", audio),
        "audio_versions": save(
            tmp_path / "versions.json", [v.model_dump(mode="json") for v in versions]
        ),
    }
    config_ref = save(tmp_path / "export-input.json", config)
    result = runner.invoke(
        cli, ["pilot-export", config_ref["path"], config_ref["sha256"], str(tmp_path / "export")]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "export" / "pilot.apkg").is_file()
