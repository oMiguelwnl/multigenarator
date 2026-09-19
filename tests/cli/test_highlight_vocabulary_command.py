from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.webdav import WebDAVFetchResult


@pytest.fixture
def vocabulary_export(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("".join(f"Book (Author)\n- Your Highlight at Location 1\n\n{entry}\n==========\n"
                            for entry in ["take off", "a", "Take Off"]))
    return path


def test_preview_vocabulary_counts_entries_without_exposing_them(vocabulary_export):
    result = CliRunner().invoke(create_app(), [
        "preview-kindle-highlights", "--language", "en", "--input-file", str(vocabulary_export),
        "--highlight-input", "vocabulary",
    ])
    assert result.exit_code == 0, result.output
    assert "extracted_candidates=2" in result.output
    assert "duplicate_candidates=1" in result.output
    assert "planned_cards=2" in result.output
    assert "take off" not in result.output


@pytest.mark.parametrize("remote", [False, True])
def test_generation_receives_vocabulary_mode(vocabulary_export, remote):
    captured = []
    webdav = SimpleNamespace(fetch_export=lambda _: WebDAVFetchResult(
        cached_path=vocabulary_export, content_hash="abc", size_bytes=42, suffix=".txt"))
    app = create_app(generate_executor=captured.append, webdav_service_factory=lambda: webdav)
    args = ["generate", "--language", "en", "--source", "highlights", "--highlight-input", "vocabulary"]
    args += ["--webdav-remote-path", "/export.txt"] if remote else ["--input-file", str(vocabulary_export)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert captured[0].highlight_input == "vocabulary"


def test_fetch_preview_uses_vocabulary_mode(vocabulary_export):
    webdav = SimpleNamespace(fetch_export=lambda _: WebDAVFetchResult(
        cached_path=vocabulary_export, content_hash="abc", size_bytes=42, suffix=".txt"))
    result = CliRunner().invoke(create_app(webdav_service_factory=lambda: webdav), [
        "fetch-webdav-highlights", "--language", "en", "--remote-path", "/export.txt",
        "--highlight-input", "vocabulary",
    ])
    assert result.exit_code == 0, result.output
    assert "planned_cards=2" in result.output


def test_vocabulary_flag_rejects_wrong_source_before_generation(vocabulary_export):
    captured = []
    result = CliRunner().invoke(create_app(generate_executor=captured.append), [
        "generate", "--language", "en", "--source", "word-list", "--input-file", str(vocabulary_export),
        "--highlight-input", "vocabulary",
    ])
    assert result.exit_code != 0
    assert "only valid when --source" in result.output
    assert "highlights" in result.output
    assert not captured
