from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.jobs import GenerationRequest
from multilang.domain.webdav import WebDAVError, WebDAVFailureCode, WebDAVFetchResult


runner = CliRunner()


class FakeWebDAVService:
    def __init__(self, result: WebDAVFetchResult | None = None, error: WebDAVError | None = None) -> None:
        self.result = result
        self.error = error
        self.paths: list[str] = []

    def fetch_export(self, remote_path: str):
        self.paths.append(remote_path)
        if self.error is not None:
            raise self.error
        return self.result


def test_generate_webdav_remote_path_sets_cached_input_file(tmp_path: Path) -> None:
    cached = tmp_path / ".multilang" / "highlights" / "cache" / "abc.html"
    cached.parent.mkdir(parents=True)
    cached.write_text("<html></html>", encoding="utf-8")
    webdav = FakeWebDAVService(
        WebDAVFetchResult(cached_path=cached, content_hash="abc", size_bytes=12, suffix=".html")
    )
    captured: list[GenerationRequest] = []
    app = create_app(generate_executor=lambda request: captured.append(request), webdav_service_factory=lambda: webdav)

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "es",
            "--source",
            "highlights",
            "--webdav-remote-path",
            "/dav/private/export.html",
        ],
    )

    assert result.exit_code == 0
    assert captured[0].source_type == "kindle-highlights"
    assert captured[0].input_file == cached
    assert webdav.paths == ["/dav/private/export.html"]
    assert "webdav_content_hash=abc" in result.output
    assert "webdav_size_bytes=12" in result.output
    assert "reader-secret" not in result.output
    assert "https://example.invalid" not in result.output
    assert "/dav/private/export.html" not in result.output


def test_generate_webdav_remote_path_validation_errors(tmp_path: Path) -> None:
    local = tmp_path / "local.html"
    local.write_text("x", encoding="utf-8")
    app = create_app(generate_executor=lambda request: None, webdav_service_factory=lambda: FakeWebDAVService())

    wrong_source = runner.invoke(
        app,
        ["generate", "--language", "es", "--source", "word-list", "--webdav-remote-path", "/dav/private/export.html"],
    )
    both_inputs = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "es",
            "--source",
            "highlights",
            "--input-file",
            str(local),
            "--webdav-remote-path",
            "/dav/private/export.html",
        ],
    )

    assert wrong_source.exit_code != 0
    assert both_inputs.exit_code != 0
    assert "--webdav-remote-path is only valid when --source highlights" in wrong_source.output
    assert "--input-file and --webdav-remote-path are mutually exclusive" in both_inputs.output


def test_generate_webdav_missing_config_fails_before_generation() -> None:
    called = False

    def execute(_: GenerationRequest) -> None:
        nonlocal called
        called = True

    app = create_app(
        generate_executor=execute,
        webdav_service_factory=lambda: FakeWebDAVService(
            error=WebDAVError(WebDAVFailureCode.MISSING_CONFIG, "missing secret=reader-secret")
        ),
    )

    result = runner.invoke(
        app,
        ["generate", "--language", "es", "--source", "highlights", "--webdav-remote-path", "/dav/private/export.html"],
    )

    assert result.exit_code == 1
    assert called is False
    assert "webdav_error=missing_config" in result.output
    assert "reader-secret" not in result.output
    assert "/dav/private/export.html" not in result.output
