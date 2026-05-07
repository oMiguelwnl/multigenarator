"""Injectable WebDAV listing/fetch adapter for Kindle highlight exports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import base64
import hashlib
import os
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from multilang.domain.webdav import (
    WebDAVConfig,
    WebDAVError,
    WebDAVFailureCode,
    WebDAVFetchResult,
    WebDAVRemoteCandidate,
)
from multilang.security.redaction import redact_exception, redact_sensitive_text
from multilang.settings import Settings

SUPPORTED_SUFFIXES = (".html", ".htm", ".txt")


@dataclass(slots=True)
class WebDAVResponse:
    status_code: int
    body: bytes
    headers: Mapping[str, str]


class WebDAVTransport(Protocol):
    def request(self, method: str, url: str, *, headers: Mapping[str, str], timeout: float) -> WebDAVResponse: ...


class UrllibWebDAVTransport:
    """WebDAV transport implemented with stdlib urllib."""

    def request(self, method: str, url: str, *, headers: Mapping[str, str], timeout: float) -> WebDAVResponse:
        request = Request(url, headers=dict(headers), method=method)
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - operator-supplied WebDAV URL
            return WebDAVResponse(
                status_code=response.status,
                body=response.read(),
                headers=dict(response.headers.items()),
            )


class WebDAVHighlightFetchService:
    """List and fetch explicit Kindle export files from a WebDAV server."""

    def __init__(self, config: WebDAVConfig | None, *, transport: WebDAVTransport | None = None) -> None:
        self.config = config
        self.transport = transport or UrllibWebDAVTransport()

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        transport: WebDAVTransport | None = None,
    ) -> "WebDAVHighlightFetchService":
        if not settings.webdav_url or not settings.webdav_username or not settings.webdav_secret:
            return cls(None, transport=transport)
        return cls(
            WebDAVConfig(
                url=settings.webdav_url,
                username=settings.webdav_username,
                secret=settings.webdav_secret,
                timeout_seconds=settings.webdav_timeout_seconds,
                cache_dir=settings.webdav_cache_dir,
            ),
            transport=transport,
        )

    def list_exports(self) -> list[WebDAVRemoteCandidate]:
        config = self._require_config()
        response = self._request("PROPFIND", str(config.url), headers={"Depth": "1"})
        self._raise_for_status(response.status_code, operation="list")
        try:
            root = ET.fromstring(response.body)
        except ET.ParseError as exc:
            raise WebDAVError(WebDAVFailureCode.MALFORMED_RESPONSE, redact_exception(exc)) from exc

        candidates: list[WebDAVRemoteCandidate] = []
        for response_node in root.findall("{DAV:}response"):
            href_node = response_node.find("{DAV:}href")
            if href_node is None or not href_node.text:
                continue
            remote_path = href_node.text
            suffix = _suffix_for_path(remote_path)
            if suffix not in SUPPORTED_SUFFIXES:
                continue
            candidates.append(
                WebDAVRemoteCandidate(
                    remote_path=remote_path,
                    safe_name=_safe_candidate_name(remote_path),
                    suffix=suffix,
                    size_bytes=_optional_int(_prop_text(response_node, "getcontentlength")),
                    modified_at=_prop_text(response_node, "getlastmodified"),
                )
            )
        return candidates

    def fetch_export(self, remote_path: str) -> WebDAVFetchResult:
        config = self._require_config()
        if not remote_path:
            raise WebDAVError(WebDAVFailureCode.PATH_NOT_FOUND, "missing WebDAV remote path")
        suffix = _suffix_for_path(remote_path)
        if suffix not in SUPPORTED_SUFFIXES:
            raise WebDAVError(WebDAVFailureCode.UNSUPPORTED_FORMAT, "unsupported WebDAV export format")
        response = self._request("GET", urljoin(str(config.url), remote_path), headers={})
        self._raise_for_status(response.status_code, operation="fetch")
        if not response.body or not response.body.strip():
            raise WebDAVError(WebDAVFailureCode.EMPTY_SOURCE, "empty WebDAV export")

        content_hash = hashlib.sha256(response.body).hexdigest()
        config.cache_dir.mkdir(parents=True, exist_ok=True)
        target = config.cache_dir / f"{content_hash}{suffix}"
        temporary = config.cache_dir / f".{content_hash}{suffix}.tmp"
        temporary.write_bytes(response.body)
        os.replace(temporary, target)
        return WebDAVFetchResult(
            cached_path=target,
            content_hash=content_hash,
            size_bytes=len(response.body),
            suffix=suffix,
        )

    def _require_config(self) -> WebDAVConfig:
        if self.config is None:
            raise WebDAVError(WebDAVFailureCode.MISSING_CONFIG, "missing WebDAV configuration")
        return self.config

    def _request(self, method: str, url: str, *, headers: Mapping[str, str]) -> WebDAVResponse:
        config = self._require_config()
        request_headers = {**headers, "Authorization": _basic_auth(config)}
        try:
            return self.transport.request(
                method,
                url,
                headers=request_headers,
                timeout=config.timeout_seconds,
            )
        except HTTPError as exc:
            return WebDAVResponse(status_code=exc.code, body=exc.read(), headers=dict(exc.headers.items()))
        except (OSError, URLError) as exc:
            raise WebDAVError(
                WebDAVFailureCode.NETWORK,
                redact_exception(
                    exc,
                    extra_terms=(
                        config.username,
                        config.secret.get_secret_value(),
                        str(config.url),
                    ),
                ),
            ) from exc

    @staticmethod
    def _raise_for_status(status_code: int, *, operation: str) -> None:
        if status_code in {200, 207}:
            return
        if status_code in {401, 403}:
            raise WebDAVError(WebDAVFailureCode.AUTH, f"WebDAV {operation} authentication failed")
        if status_code == 404:
            raise WebDAVError(WebDAVFailureCode.PATH_NOT_FOUND, f"WebDAV {operation} path not found")
        raise WebDAVError(WebDAVFailureCode.MALFORMED_RESPONSE, f"WebDAV {operation} returned status {status_code}")


def _basic_auth(config: WebDAVConfig) -> str:
    token = f"{config.username}:{config.secret.get_secret_value()}".encode("utf-8")
    return "Basic " + base64.b64encode(token).decode("ascii")


def _suffix_for_path(path: str) -> str:
    parsed_path = unquote(urlparse(path).path)
    return Path(parsed_path).suffix.lower()


def _safe_candidate_name(remote_path: str) -> str:
    name = Path(unquote(urlparse(remote_path).path)).name
    safe = redact_sensitive_text(name)
    if safe == name and any(label in name.lower() for label in ("private", "book", "author", "title")):
        safe = f"export{Path(name).suffix.lower()}"
    return safe or f"export{_suffix_for_path(remote_path)}"


def _prop_text(response_node: ET.Element, local_name: str) -> str | None:
    node = response_node.find(f".//{{DAV:}}{local_name}")
    if node is None or node.text is None:
        return None
    return node.text


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


__all__ = [
    "UrllibWebDAVTransport",
    "WebDAVHighlightFetchService",
    "WebDAVResponse",
    "WebDAVTransport",
]
