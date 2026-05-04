"""Privacy regression tests for reusable redaction helpers."""

from __future__ import annotations

from pathlib import Path

from multilang.security.redaction import (
    SENSITIVE_VALUE_REDACTION,
    redact_exception,
    redact_mapping,
    redact_sensitive_text,
)


def test_redacts_credentials_and_authorization_shapes() -> None:
    text = (
        "Authorization: Bearer token-123\n"
        "Authorization: Basic abc123\n"
        "password=hunter2 username=reader api_key=key-123 secret=secret-123 token=token-456"
    )

    redacted = redact_sensitive_text(text)

    assert "hunter2" not in redacted
    assert "reader" not in redacted
    assert "key-123" not in redacted
    assert "secret-123" not in redacted
    assert "token-123" not in redacted
    assert redacted.count(SENSITIVE_VALUE_REDACTION) >= 6


def test_redacts_webdav_urls_and_raw_highlight_paths() -> None:
    text = "GET https://example.invalid/dav/private/file.html from .multilang/highlights/raw/export.html"

    redacted = redact_sensitive_text(text)

    assert "example.invalid" not in redacted
    assert ".multilang/highlights/raw/export.html" not in redacted
    assert SENSITIVE_VALUE_REDACTION in redacted


def test_redacts_book_metadata_labels() -> None:
    text = "Title: Synthetic Secret Book\nAuthor: Example Writer\nBook: Volume 1\nLocation: 42"

    redacted = redact_sensitive_text(text)

    assert "Synthetic Secret Book" not in redacted
    assert "Example Writer" not in redacted
    assert "Volume 1" not in redacted
    assert "42" not in redacted
    assert "Title:" in redacted
    assert "Author:" in redacted


def test_redacts_caller_supplied_private_terms_with_non_ascii_text() -> None:
    redacted = redact_sensitive_text(
        "highlight snippet: café privado",
        extra_terms=("café privado",),
    )

    assert "café privado" not in redacted
    assert SENSITIVE_VALUE_REDACTION in redacted


def test_redact_mapping_preserves_safe_keys_and_redacts_nested_scalars() -> None:
    values = {
        "safe": "kept",
        "username": "reader",
        "nested": {"path": ".multilang/highlights/raw/source.txt", "count": 3},
        "items": ["ok", "token=list-token"],
    }

    redacted = redact_mapping(values)

    assert redacted["safe"] == "kept"
    assert redacted["username"] == SENSITIVE_VALUE_REDACTION
    assert redacted["nested"]["path"] == SENSITIVE_VALUE_REDACTION
    assert redacted["nested"]["count"] == 3
    assert redacted["items"] == ["ok", f"token={SENSITIVE_VALUE_REDACTION}"]


def test_redact_exception_returns_redacted_message() -> None:
    exc = RuntimeError("Authorization: Bearer exception-token")

    assert "exception-token" not in redact_exception(exc)


def test_gitignore_covers_future_highlight_artifacts_and_local_secrets() -> None:
    patterns = set(Path(".gitignore").read_text(encoding="utf-8").splitlines())

    assert {
        ".env",
        ".env.*",
        "!.env.example",
        ".multilang/",
        ".multilang/highlights/raw/",
        ".multilang/highlights/cache/",
        ".multilang/highlights/sync/",
        "kindle-highlights*.html",
        "kindle-highlights*.txt",
        "webdav-secrets*.json",
    }.issubset(patterns)
