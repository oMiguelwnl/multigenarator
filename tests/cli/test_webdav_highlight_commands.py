from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.webdav import (
    WebDAVError,
    WebDAVFailureCode,
    WebDAVFetchResult,
    WebDAVRemoteCandidate,
)


runner = CliRunner()


class FakeWebDAVService:
    def __init__(self, *, candidates=None, fetch_result=None, error: WebDAVError | None = None) -> None:
        self.candidates = candidates or []
        self.fetch_result = fetch_result
        self.error = error
        self.fetched_paths: list[str] = []

    def list_exports(self):
        if self.error:
            raise self.error
        return self.candidates

    def fetch_export(self, remote_path: str):
        self.fetched_paths.append(remote_path)
        if self.error:
            raise self.error
        return self.fetch_result


def test_list_webdav_highlights_prints_safe_candidates() -> None:
    service = FakeWebDAVService(
        candidates=[
            WebDAVRemoteCandidate(
                remote_path="/dav/private/Private Book.html?token=abc",
                safe_name="export.html",
                suffix=".html",
                size_bytes=123,
                modified_at="Mon",
            )
        ]
    )
    app = create_app(webdav_service_factory=lambda: service)

    result = runner.invoke(app, ["list-webdav-highlights"])

    assert result.exit_code == 0
    assert "candidate=export.html" in result.output
    assert "suffix=.html" in result.output
    assert "reader-secret" not in result.output
    assert "https://example.invalid" not in result.output
    assert "/dav/private/" not in result.output


def test_list_webdav_highlights_prints_error_code() -> None:
    app = create_app(
        webdav_service_factory=lambda: FakeWebDAVService(
            error=WebDAVError(WebDAVFailureCode.AUTH, "secret=reader-secret")
        )
    )

    result = runner.invoke(app, ["list-webdav-highlights"])

    assert result.exit_code == 1
    assert "webdav_error=auth" in result.output
    assert "reader-secret" not in result.output


def test_fetch_webdav_highlights_fetches_explicit_path_and_prints_preview(tmp_path: Path) -> None:
    cached = tmp_path / "cache" / "abc.html"
    cached.parent.mkdir()
    cached.write_text(
        "Synthetic Learner Reader\n- Your Highlight at Location 1\nEl jardín secreto brilla\n==========",
        encoding="utf-8",
    )
    service = FakeWebDAVService(
        fetch_result=WebDAVFetchResult(
            cached_path=cached,
            content_hash="abc",
            size_bytes=cached.stat().st_size,
            suffix=".html",
        )
    )
    app = create_app(webdav_service_factory=lambda: service)

    result = runner.invoke(
        app,
        [
            "fetch-webdav-highlights",
            "--language",
            "es",
            "--remote-path",
            "/dav/private/export.html",
        ],
    )

    assert result.exit_code == 0
    assert service.fetched_paths == ["/dav/private/export.html"]
    assert "webdav_content_hash=abc" in result.output
    assert "webdav_cached_file=" in result.output
    assert "imported_highlights=1" in result.output
    assert "planned_cards=" in result.output
    assert "/dav/private/export.html" not in result.output
    assert "El jardín secreto brilla" not in result.output


def test_fetch_webdav_highlights_distinguishes_empty_and_unsupported() -> None:
    empty_app = create_app(
        webdav_service_factory=lambda: FakeWebDAVService(
            error=WebDAVError(WebDAVFailureCode.EMPTY_SOURCE, "empty")
        )
    )
    unsupported_app = create_app(
        webdav_service_factory=lambda: FakeWebDAVService(
            error=WebDAVError(WebDAVFailureCode.UNSUPPORTED_FORMAT, "unsupported")
        )
    )

    empty = runner.invoke(
        empty_app,
        ["fetch-webdav-highlights", "--language", "es", "--remote-path", "/dav/private/empty.txt"],
    )
    unsupported = runner.invoke(
        unsupported_app,
        ["fetch-webdav-highlights", "--language", "es", "--remote-path", "/dav/private/export.pdf"],
    )

    assert empty.exit_code == 1
    assert unsupported.exit_code == 1
    assert "webdav_error=empty_source" in empty.output
    assert "webdav_error=unsupported_format" in unsupported.output
