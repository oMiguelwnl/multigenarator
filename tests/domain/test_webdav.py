from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from multilang.domain.webdav import (
    WebDAVConfig,
    WebDAVError,
    WebDAVFailureCode,
    WebDAVFetchResult,
    WebDAVRemoteCandidate,
)


def test_webdav_failure_codes_are_stable() -> None:
    assert [code.value for code in WebDAVFailureCode] == [
        "missing_config",
        "auth",
        "path_not_found",
        "network",
        "malformed_response",
        "unsupported_format",
        "empty_source",
    ]


@pytest.mark.parametrize("suffix", [".html", ".htm", ".txt"])
def test_webdav_remote_candidate_accepts_supported_suffixes(suffix: str) -> None:
    candidate = WebDAVRemoteCandidate(remote_path="/dav/export" + suffix, safe_name="export", suffix=suffix)

    assert candidate.suffix == suffix


def test_webdav_remote_candidate_rejects_unsupported_suffix() -> None:
    with pytest.raises(ValidationError):
        WebDAVRemoteCandidate(remote_path="/dav/private.pdf", safe_name="private", suffix=".pdf")


def test_webdav_config_masks_secret_in_repr_and_dump() -> None:
    config = WebDAVConfig(
        url="https://example.invalid/dav/",
        username="reader",
        secret="reader-secret",
        cache_dir=Path(".multilang/highlights/cache"),
    )

    assert config.secret.get_secret_value() == "reader-secret"
    assert "reader-secret" not in repr(config)
    assert "reader-secret" not in str(config.model_dump())


def test_webdav_error_redacts_message_and_details() -> None:
    error = WebDAVError(
        WebDAVFailureCode.AUTH,
        "failed for https://example.invalid/dav/private/export.html with secret=reader-secret",
        safe_details={"username": "reader", "path": "/dav/private/Private Book.html"},
    )

    assert error.code is WebDAVFailureCode.AUTH
    assert "reader-secret" not in str(error)
    assert "https://example.invalid/dav/private" not in str(error)
    assert "Private Book" not in str(error.safe_details)
    assert error.safe_details["username"] == "[REDACTED]"


def test_webdav_fetch_result_contract() -> None:
    result = WebDAVFetchResult(
        cached_path=Path(".multilang/highlights/cache/abc123.html"),
        content_hash="abc123",
        size_bytes=42,
        suffix=".html",
    )

    assert result.cached_path.name == "abc123.html"
