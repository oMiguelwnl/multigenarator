from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
from multilang.domain.webdav import (
    WebDAVError,
    WebDAVFailureCode,
    WebDAVFetchResult,
    WebDAVRemoteCandidate,
)


runner = CliRunner()


def _korean_identity() -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form=None,
        canonical_nfc="물은",
        lemma="물",
        part_of_speech="NNG",
        sense_id="fixture:water:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="물", pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(
            analyzer_name="kiwi",
            analyzer_package_version="0.23.2",
            model_package_version="0.23.0",
            model_type="cong",
            enabled_dialects="standard",
            num_workers=1,
            integrate_allomorph=True,
            top_n=2,
            split_complex=False,
            compatible_jamo=False,
            normalize_coda=False,
            z_coda=False,
            typos=None,
            oov_handling="chr",
            policy_version="kiwi-top2-consensus-v1",
        ),
        status="resolved",
    )


def _write_korean_fixture(path: Path, private_text: str) -> None:
    path.write_text(
        "==========\nSynthetic Learner Reader\n"
        "- Your Highlight at location 7\n\n"
        f"{private_text}\n",
        encoding="utf-8",
    )


class _CountingKoreanResolver:
    def __init__(self, *, raises: bool = False) -> None:
        self.raises = raises
        self.calls: list[str] = []

    def resolve_korean_highlight_text(self, text: str) -> tuple[object, ...]:
        self.calls.append(text)
        if self.raises:
            raise RuntimeError(
                "C:/private/book.txt raw excerpt vendor dump traceback prompt"
            )
        return (SimpleNamespace(identity=_korean_identity(), word_position=0),)


class _InjectedRuntimeService:
    def __init__(self, grounding_service: object) -> None:
        self.grounding_service = grounding_service


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
        """
        <!doctype html><html><body>
        <div class="bookTitle">Synthetic Learner Reader</div>
        <div class="noteHeading">Highlight (<span>Location 1</span>)</div>
        <div class="noteText">El jardín secreto brilla</div>
        </body></html>
        """,
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


def test_standalone_local_and_webdav_korean_previews_share_one_offline_resolver(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import multilang.cli as cli_module

    private_text = "물은 비밀 문장입니다"
    local_path = tmp_path / "Local Korean Reader.txt"
    cached_path = tmp_path / "cache" / "remote.txt"
    cached_path.parent.mkdir()
    _write_korean_fixture(local_path, private_text)
    _write_korean_fixture(cached_path, private_text)
    webdav = FakeWebDAVService(
        fetch_result=WebDAVFetchResult(
            cached_path=cached_path,
            content_hash="safe-hash",
            size_bytes=cached_path.stat().st_size,
            suffix=".txt",
        )
    )
    morphology = object()
    morphology_factory_calls = 0
    grounding_instances: list[object] = []

    def morphology_factory() -> object:
        nonlocal morphology_factory_calls
        morphology_factory_calls += 1
        return morphology

    class FakeOfflineGroundingResolver(_CountingKoreanResolver):
        def __init__(self, *, lookup: object, korean_morphology: object) -> None:
            assert lookup is not None
            assert korean_morphology is morphology
            super().__init__()
            grounding_instances.append(self)

    def forbidden_runtime(*args: object, **kwargs: object) -> object:
        raise AssertionError("preview constructed provider/audio runtime")

    monkeypatch.setattr(
        cli_module,
        "KiwiKoreanMorphologyService",
        morphology_factory,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "LexicalGroundingService",
        FakeOfflineGroundingResolver,
        raising=False,
    )
    monkeypatch.setattr(cli_module, "build_runtime_service", forbidden_runtime)
    app = create_app(webdav_service_factory=lambda: webdav)

    local_result = runner.invoke(
        app,
        [
            "preview-kindle-highlights",
            "--language",
            "ko",
            "--input-file",
            str(local_path),
        ],
    )
    webdav_result = runner.invoke(
        app,
        [
            "fetch-webdav-highlights",
            "--language",
            "ko",
            "--remote-path",
            "/dav/private/reader.txt",
        ],
    )

    assert local_result.exit_code == 0
    assert webdav_result.exit_code == 0
    assert morphology_factory_calls == 1
    assert len(grounding_instances) == 1
    assert grounding_instances[0].calls == [private_text, private_text]
    assert all(
        line.split("=", 1)[0]
        in {
            "imported_highlights",
            "extracted_candidates",
            "rejected_highlights",
            "duplicate_candidates",
            "planned_cards",
        }
        for line in webdav_result.output.strip().splitlines()
    )
    assert private_text not in local_result.output
    assert private_text not in webdav_result.output
    assert str(local_path) not in local_result.output
    assert str(cached_path) not in webdav_result.output
    assert "/dav/private/reader.txt" not in webdav_result.output


def test_webdav_korean_preview_failure_is_nonzero_and_content_free(
    tmp_path: Path,
) -> None:
    private_text = "비밀 원문 prompt instruction"
    cached_path = tmp_path / "private" / "secret.txt"
    cached_path.parent.mkdir()
    _write_korean_fixture(cached_path, private_text)
    webdav = FakeWebDAVService(
        fetch_result=WebDAVFetchResult(
            cached_path=cached_path,
            content_hash="safe-hash",
            size_bytes=cached_path.stat().st_size,
            suffix=".txt",
        )
    )
    resolver = _CountingKoreanResolver(raises=True)
    app = create_app(
        service=_InjectedRuntimeService(resolver),
        webdav_service_factory=lambda: webdav,
    )

    result = runner.invoke(
        app,
        [
            "fetch-webdav-highlights",
            "--language",
            "ko",
            "--remote-path",
            "/dav/private/secret.txt",
        ],
    )

    assert result.exit_code == 1
    assert result.output.strip().splitlines() == [
        "webdav_error=malformed_response",
        "webdav_error_detail=korean_highlight_preview_error=korean_resolution_unavailable",
    ]
    assert resolver.calls == [private_text]
    assert private_text not in result.output
    assert str(cached_path) not in result.output
    assert "/dav/private/secret.txt" not in result.output
    assert "vendor dump" not in result.output
    assert "traceback" not in result.output
