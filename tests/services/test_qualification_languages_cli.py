import json

import typer
from test_qualification_machine_languages import fixture, request, sha
from typer.testing import CliRunner


def test_prepare_languages_exports_requests_and_rejects_wrong_hash(tmp_path):
    from multilang.qualification_languages_cli import register_language_commands

    cli = typer.Typer()
    register_language_commands(cli)

    @cli.command("noop")
    def noop():
        pass

    configuration = request([fixture(tmp_path)], item_limit=2)
    path = tmp_path / "configuration.json"
    path.write_text(configuration.model_dump_json())
    output = tmp_path / "languages"
    runner = CliRunner()
    args = ["prepare-languages", str(path), sha(path), str(output)]
    response = runner.invoke(cli, args)
    assert response.exit_code == 0, response.output
    index = json.loads(response.output)
    assert index["item_count"] == 2
    assert index["inventoried_languages"] == 23
    assert (output / "request-pt/request.json").exists()
    assert (output / "inventory/matrix.html").exists()
    assert runner.invoke(cli, args).exit_code == 0
    assert (
        runner.invoke(cli, ["prepare-languages", str(path), "a" * 64, str(output)]).exit_code != 0
    )
