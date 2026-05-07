"""Typed WebDAV contracts for safe highlight fetching."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import AnyUrl, BaseModel, SecretStr

from multilang.security.redaction import redact_mapping, redact_sensitive_text


class WebDAVFailureCode(str, Enum):
    """Stable failure codes surfaced at WebDAV boundaries."""

    MISSING_CONFIG = "missing_config"
    AUTH = "auth"
    PATH_NOT_FOUND = "path_not_found"
    NETWORK = "network"
    MALFORMED_RESPONSE = "malformed_response"
    UNSUPPORTED_FORMAT = "unsupported_format"
    EMPTY_SOURCE = "empty_source"


class WebDAVConfig(BaseModel):
    """Runtime WebDAV settings with masked secret storage."""

    url: AnyUrl
    username: str
    secret: SecretStr
    timeout_seconds: float = 30.0
    cache_dir: Path = Path(".multilang/highlights/cache")


class WebDAVRemoteCandidate(BaseModel):
    """A supported remote export candidate from a WebDAV listing."""

    remote_path: str
    safe_name: str
    suffix: Literal[".html", ".htm", ".txt"]
    size_bytes: int | None = None
    modified_at: str | None = None


class WebDAVFetchResult(BaseModel):
    """Safe metadata for a fetched and cached WebDAV export."""

    cached_path: Path
    content_hash: str
    size_bytes: int
    suffix: Literal[".html", ".htm", ".txt"]


class WebDAVError(RuntimeError):
    """Redaction-safe WebDAV error with stable machine code."""

    code: WebDAVFailureCode

    def __init__(
        self,
        code: WebDAVFailureCode,
        message: str,
        *,
        safe_details: Mapping[str, object] | None = None,
    ) -> None:
        self.code = code
        self.message = redact_sensitive_text(message)
        self.safe_details = redact_mapping(safe_details or {})
        super().__init__(self.message)


__all__ = [
    "WebDAVConfig",
    "WebDAVError",
    "WebDAVFailureCode",
    "WebDAVFetchResult",
    "WebDAVRemoteCandidate",
]
