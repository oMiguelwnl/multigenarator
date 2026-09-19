"""Course preparation is wired into the public Korean command family."""

import json

from typer.testing import CliRunner

from multilang.cli import create_app


def test_prepare_grammar_course_is_offline_and_emits_real_content(tmp_path):
    output = tmp_path / "course"
    result = CliRunner().invoke(create_app(), [
        "korean", "prepare-grammar-course", "--output-dir", str(output), "--no-analyze",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["grammar_card_count"] >= 80
    assert report["learner_ready"] is False
    assert (output / "index.html").is_file()
    assert (output / "course.json").is_file()


def test_prepare_grammar_course_preserves_existing_output(tmp_path):
    result = CliRunner().invoke(create_app(), [
        "korean", "prepare-grammar-course", "--output-dir", str(tmp_path), "--no-analyze",
    ])
    assert result.exit_code == 1
    assert "invalid_course_or_output_directory" in result.stdout
