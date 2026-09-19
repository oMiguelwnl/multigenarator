"""CLI wiring for source-backed offline machine qualification."""

import hashlib
import json

from test_qualification_machine_runner import metadata_fixture, request_fixture, response_fixture
from typer.testing import CliRunner


def write(path, value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    path.write_text(json.dumps(value))
    return str(path), hashlib.sha256(path.read_bytes()).hexdigest()


def test_qualification_cli_mounts_ai_and_finishes_offline_roundtrip(tmp_path):
    from multilang.qualification_cli import create_qualification_app
    from multilang.services.qualification_machine import MachineActor
    from multilang.services.qualification_machine_runner import read_json

    cli = create_qualification_app()
    runner = CliRunner()
    help_result = runner.invoke(cli, ["ai", "--help"])
    assert help_result.exit_code == 0, help_result.output
    request = request_fixture()
    packet_args = write(tmp_path / "packet.json", request.packet)
    actor_args = write(tmp_path / "actor.json", request.actor)
    proposed = tmp_path / "proposed"
    result = runner.invoke(
        cli, ["ai", "propose", *packet_args, *actor_args, "run-1", str(proposed)]
    )
    assert result.exit_code == 0, result.output
    req = read_json(proposed / "request.json")
    req_args = write(tmp_path / "request.json", req)
    response_args = write(tmp_path / "response.json", response_fixture(request))
    metadata_args = write(tmp_path / "metadata.json", metadata_fixture())
    first = tmp_path / "first"
    result = runner.invoke(
        cli, ["ai", "import-response", *req_args, *response_args, *metadata_args, str(first)]
    )
    assert result.exit_code == 0, result.output
    judge = MachineActor(
        actor_id="synthetic-judge",
        context_id="context-2",
        execution_surface="mock",
        model="mock-model",
        provider="mock",
    )
    judge_args = write(tmp_path / "judge.json", judge)
    judge_dir = tmp_path / "judge-request"
    result = runner.invoke(cli, ["ai", "judge", str(first), *judge_args, "run-2", str(judge_dir)])
    assert result.exit_code == 0, result.output
    judge_request_args = write(
        tmp_path / "judge-request.json", read_json(judge_dir / "request.json")
    )
    second = tmp_path / "second"
    result = runner.invoke(
        cli,
        ["ai", "import-response", *judge_request_args, *response_args, *metadata_args, str(second)],
    )
    assert result.exit_code == 0, result.output
    output = tmp_path / "result"
    result = runner.invoke(cli, ["ai", "reconcile", str(first), str(second), str(output)])
    assert result.exit_code == 0, result.output
    assert read_json(output / "result.json")["decisions"][0]["status"] == "machine_agreement"
    assert (output / "report.html").is_file()


def test_cli_json_errors_do_not_echo_source_or_provider_secrets(tmp_path):
    from multilang.qualification_cli import create_qualification_app

    bad_args = write(tmp_path / "bad.json", {"secret": "sensitive-provider-value"})
    result = CliRunner().invoke(
        create_qualification_app(), ["ai", "pipeline", *bad_args, str(tmp_path / "out")]
    )
    assert result.exit_code != 0
    assert "sensitive-provider-value" not in result.output


def test_cli_enriches_existing_source_evidence(tmp_path):
    from test_qualification_pipeline import request as pipeline_request

    from multilang.qualification_cli import create_qualification_app
    from multilang.services.qualification_pipeline import run_qualification_pipeline

    pipeline = tmp_path / "pipeline"
    manifest = run_qualification_pipeline(pipeline_request(tmp_path), pipeline)
    manifest_sha = hashlib.sha256((pipeline / "manifest.json").read_bytes()).hexdigest()
    name = next(name for name in manifest["files"] if name.endswith("packet.json"))
    result = CliRunner().invoke(
        create_qualification_app(),
        [
            "ai",
            "enrich",
            str(pipeline / name),
            manifest["files"][name],
            str(pipeline),
            manifest_sha,
            str(tmp_path / "enriched"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "enriched" / "packet.json").is_file()
    assert (
        json.loads((tmp_path / "enriched" / "enrichment.json").read_text())["production_eligible"]
        is False
    )
