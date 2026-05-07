from __future__ import annotations

from pathlib import Path
from urllib.error import URLError

import pytest

from multilang.domain.webdav import WebDAVError, WebDAVFailureCode
from multilang.services.webdav_highlight_fetch import (
    WebDAVHighlightFetchService,
    WebDAVResponse,
)
from multilang.settings import Settings


class FakeTransport:
    def __init__(self, responses: list[WebDAVResponse | BaseException]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str, dict[str, str], float]] = []

    def request(self, method: str, url: str, *, headers, timeout: float) -> WebDAVResponse:
        self.requests.append((method, url, dict(headers), timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "webdav_url": "https://example.invalid/dav/private/",
        "webdav_username": "reader",
        "webdav_secret": "reader-secret",
        "webdav_cache_dir": tmp_path / ".multilang" / "highlights" / "cache",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def response(status: int, body: bytes = b"", headers: dict[str, str] | None = None) -> WebDAVResponse:
    return WebDAVResponse(status_code=status, body=body, headers=headers or {})


def propfind_xml() -> bytes:
    return b"""
    <d:multistatus xmlns:d="DAV:">
      <d:response><d:href>/dav/private/Private%20Book.html?token=abc</d:href><d:propstat><d:prop><d:getcontentlength>123</d:getcontentlength><d:getlastmodified>Mon</d:getlastmodified></d:prop></d:propstat></d:response>
      <d:response><d:href>/dav/private/notes.txt</d:href><d:propstat><d:prop><d:getcontentlength>9</d:getcontentlength></d:prop></d:propstat></d:response>
      <d:response><d:href>/dav/private/book.pdf</d:href></d:response>
    </d:multistatus>
    """


def test_list_exports_sends_propfind_and_filters_supported_suffixes(tmp_path: Path) -> None:
    transport = FakeTransport([response(207, propfind_xml())])
    service = WebDAVHighlightFetchService.from_settings(settings(tmp_path), transport=transport)

    candidates = service.list_exports()

    assert transport.requests[0][0] == "PROPFIND"
    assert transport.requests[0][2]["Depth"] == "1"
    assert transport.requests[0][3] == 30.0
    assert [candidate.suffix for candidate in candidates] == [".html", ".txt"]
    assert all(candidate.suffix != ".pdf" for candidate in candidates)
    output = "\n".join(candidate.safe_name for candidate in candidates)
    assert "reader-secret" not in output
    assert "https://example.invalid" not in output
    assert "/dav/private" not in output
    assert "?token=" not in output
    assert "Private Book" not in output


def test_missing_config_fails_before_request(tmp_path: Path) -> None:
    transport = FakeTransport([])

    with pytest.raises(WebDAVError) as exc_info:
        WebDAVHighlightFetchService.from_settings(
            settings(tmp_path, webdav_secret=None), transport=transport
        ).list_exports()

    assert exc_info.value.code is WebDAVFailureCode.MISSING_CONFIG
    assert transport.requests == []


@pytest.mark.parametrize(
    (status, code),
    [(401, WebDAVFailureCode.AUTH), (403, WebDAVFailureCode.AUTH), (404, WebDAVFailureCode.PATH_NOT_FOUND)],
)
def test_list_exports_maps_status_failures(tmp_path: Path, status: int, code: WebDAVFailureCode) -> None:
    service = WebDAVHighlightFetchService.from_settings(settings(tmp_path), transport=FakeTransport([response(status)]))

    with pytest.raises(WebDAVError) as exc_info:
        service.list_exports()

    assert exc_info.value.code is code


def test_list_exports_maps_network_and_malformed_xml(tmp_path: Path) -> None:
    network = WebDAVHighlightFetchService.from_settings(
        settings(tmp_path), transport=FakeTransport([URLError("network down reader-secret")])
    )
    malformed = WebDAVHighlightFetchService.from_settings(
        settings(tmp_path), transport=FakeTransport([response(207, b"<not xml")])
    )

    with pytest.raises(WebDAVError) as network_error:
        network.list_exports()
    with pytest.raises(WebDAVError) as malformed_error:
        malformed.list_exports()

    assert network_error.value.code is WebDAVFailureCode.NETWORK
    assert malformed_error.value.code is WebDAVFailureCode.MALFORMED_RESPONSE
    assert "reader-secret" not in str(network_error.value)


def test_fetch_export_writes_content_hash_cache_file(tmp_path: Path) -> None:
    body = b"Synthetic Learner Reader\n- Your Highlight at Location 1\nEl jardin brilla\n=========="
    service = WebDAVHighlightFetchService.from_settings(settings(tmp_path), transport=FakeTransport([response(200, body)]))

    result = service.fetch_export("/dav/private/export.html")

    assert result.content_hash == "dcb7bc9ddbfaa67a1dcefc53dc431822ad95803a7d5244da9a9a63eaab3e4682"
    assert result.cached_path == settings(tmp_path).webdav_cache_dir / f"{result.content_hash}.html"
    assert result.cached_path.read_bytes() == body
    assert result.size_bytes == len(body)


def test_fetch_rejects_unsupported_suffix_before_get(tmp_path: Path) -> None:
    transport = FakeTransport([])
    service = WebDAVHighlightFetchService.from_settings(settings(tmp_path), transport=transport)

    with pytest.raises(WebDAVError) as exc_info:
        service.fetch_export("/dav/private/export.pdf")

    assert exc_info.value.code is WebDAVFailureCode.UNSUPPORTED_FORMAT
    assert transport.requests == []


def test_fetch_empty_and_malformed_status_do_not_write_cache(tmp_path: Path) -> None:
    empty_cache = tmp_path / "empty"
    status_cache = tmp_path / "status"
    empty = WebDAVHighlightFetchService.from_settings(
        settings(tmp_path, webdav_cache_dir=empty_cache), transport=FakeTransport([response(200, b"  \n")])
    )
    bad_status = WebDAVHighlightFetchService.from_settings(
        settings(tmp_path, webdav_cache_dir=status_cache), transport=FakeTransport([response(500, b"Private Book")])
    )

    with pytest.raises(WebDAVError) as empty_error:
        empty.fetch_export("/dav/private/export.txt")
    with pytest.raises(WebDAVError) as status_error:
        bad_status.fetch_export("/dav/private/export.html")

    assert empty_error.value.code is WebDAVFailureCode.EMPTY_SOURCE
    assert status_error.value.code is WebDAVFailureCode.MALFORMED_RESPONSE
    assert not empty_cache.exists()
    assert not status_cache.exists()
    assert "reader-secret" not in str(status_error.value)
    assert "https://example.invalid/dav/private" not in str(status_error.value)
    assert "Private Book" not in str(status_error.value)
