"""Korean frequency source retrieval and validation helpers."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from bs4 import BeautifulSoup

from multilang.domain.korean import (
    KOREAN_FREQUENCY_EXPECTED_FILENAME,
    KOREAN_FREQUENCY_LANDING_URL,
    KOREAN_FREQUENCY_RETRIEVAL_SCHEMA_VERSION,
    KOREAN_FREQUENCY_SOURCE_ID,
    KoreanFrequencyBuildResult,
    KoreanFrequencyBundleManifest,
    KoreanFrequencyEntry,
    KoreanFrequencyJobAuthority,
    KoreanFrequencyRetrievalResult,
    canonical_json_sha256,
    raw_bytes_sha256,
    validate_korean_frequency_accounting,
)
_MAX_LANDING_BYTES = 2_000_000
_MAX_SOURCE_BYTES = 20_000_000
# Official selected source attachment: 한국어 학습용 어휘 목록.txt
_SOURCE_PATH = KOREAN_FREQUENCY_EXPECTED_FILENAME
_RESULT_PATH = "retrieval-result.json"
_BUNDLE_MANIFEST_PATH = "manifest.json"
_BUILD_RESULT_PATH = "build-result.json"
_COMMON_DOWNLOAD_STORED_NAME = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_[0-9]+\.txt$"
)

UrlOpen = Callable[[object, int], object]
Resolver = Callable[..., object]


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise ValueError("redirect response not permitted")


_NO_REDIRECT_OPENER = build_opener(_NoRedirectHandler)


def _default_urlopen_no_redirect(request: object, timeout: int) -> object:
    return _NO_REDIRECT_OPENER.open(request, timeout=timeout)


def _read_bounded(response: object, *, limit: int) -> bytes:
    reader = getattr(response, "read")
    payload = reader(limit + 1)
    if not isinstance(payload, bytes):
        raise ValueError("response body must be bytes")
    if len(payload) > limit:
        raise ValueError("response body exceeds configured bound")
    return payload


def _require_unredirected_response(response: object, expected_url: str) -> None:
    getter = getattr(response, "geturl", None)
    if not callable(getter):
        raise ValueError("response URL unavailable for redirect validation")
    if getter() != expected_url:
        raise ValueError("redirect response not permitted")


def _require_public_dns(url: str, resolver: Resolver | None) -> None:
    if resolver is None:
        return
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.korean.go.kr":
        raise ValueError("source URL must use the official HTTPS host")
    try:
        records = resolver(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("public DNS resolution failed") from exc
    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for record in records:
        try:
            sockaddr = record[4]
            address = sockaddr[0]
            addresses.append(ipaddress.ip_address(str(address).split("%", 1)[0]))
        except (IndexError, TypeError, ValueError) as exc:
            raise ValueError("public DNS resolution failed") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("public DNS resolution required")


def _official_attachment_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "www.korean.go.kr":
        raise ValueError("attachment target must use the official source host")
    if parsed.path != "/common/download.do":
        raise ValueError("attachment target must use the official source path")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    if set(query) != {"file_path", "c_file_name", "o_file_name"} or any(len(values) != 1 for values in query.values()):
        raise ValueError("attachment target must use the official source query")
    if query["file_path"][0] != "etcData":
        raise ValueError("attachment target must use the official source query")
    if query["o_file_name"][0] != KOREAN_FREQUENCY_EXPECTED_FILENAME:
        raise ValueError("attachment target must use the accepted TXT filename")
    if not _COMMON_DOWNLOAD_STORED_NAME.fullmatch(query["c_file_name"][0]):
        raise ValueError("attachment target must use the official stored filename")
    encoded_query = urlencode(
        {
            "file_path": "etcData",
            "c_file_name": query["c_file_name"][0],
            "o_file_name": KOREAN_FREQUENCY_EXPECTED_FILENAME,
        },
        quote_via=quote,
    )
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", encoded_query, ""))


def resolve_nikl_frequency_attachment_url(landing_bytes: bytes) -> str:
    """Resolve the exact TXT attachment URL from official landing-page bytes."""

    if not isinstance(landing_bytes, bytes) or not landing_bytes:
        raise ValueError("landing response is empty")
    soup = BeautifulSoup(landing_bytes, "html.parser")
    matches: list[str] = []
    for anchor in soup.find_all("a"):
        label = " ".join(anchor.get_text(" ").split())
        if label != KOREAN_FREQUENCY_EXPECTED_FILENAME:
            continue
        href = anchor.get("href")
        if not isinstance(href, str) or not href.strip():
            raise ValueError("attachment link is malformed")
        matches.append(_official_attachment_url(urljoin(KOREAN_FREQUENCY_LANDING_URL, href.strip())))
    if len(matches) != 1:
        raise ValueError("landing response must contain exactly one accepted TXT attachment")
    return matches[0]


def _content_disposition_filename(headers: object) -> str | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        return None
    raw = getter("Content-Disposition") or getter("content-disposition")
    if not isinstance(raw, str):
        return None
    for part in raw.split(";"):
        part = part.strip()
        if part.lower().startswith("filename*="):
            value = part.split("=", 1)[1].strip().strip('"')
            if value.lower().startswith("utf-8''"):
                return unquote(value[7:])
        if part.lower().startswith("filename="):
            return unquote(part.split("=", 1)[1].strip().strip('"'))
    return None


def _decode_source_txt(payload: bytes, *, expected_encoding: str | None = None) -> tuple[str, str]:
    encodings = (expected_encoding,) if expected_encoding is not None else ("utf-8", "cp949")
    for encoding in encodings:
        try:
            return payload.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("source TXT must be valid utf-8 or cp949")


def _validate_source_txt_schema(payload: bytes, *, expected_encoding: str | None = None) -> str:
    text, encoding = _decode_source_txt(payload, expected_encoding=expected_encoding)
    rows = [line for line in text.splitlines() if line.strip()]
    if not rows:
        raise ValueError("source TXT is empty")
    if not all("\t" in row and len(row.split("\t")) >= 3 for row in rows):
        raise ValueError("source TXT does not match expected lexical schema")
    return encoding


def _safe_output_dir(output_dir: Path) -> Path:
    path = Path(output_dir)
    if path.exists() and (not path.is_dir() or path.is_symlink()):
        raise ValueError("output directory is unsafe")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("output directory is unsafe")
    return path


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temp_path, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            raise


def validate_korean_source_retrieval_result(
    result_file: Path,
    *,
    source_file: Path | None = None,
) -> KoreanFrequencyRetrievalResult:
    """Read-only validation of a retrieval result and optional source bytes."""

    try:
        result = KoreanFrequencyRetrievalResult.model_validate_json(Path(result_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("retrieval result is invalid") from exc
    if source_file is not None:
        try:
            payload = Path(source_file).read_bytes()
        except OSError as exc:
            raise ValueError("source file is unavailable") from exc
        _validate_source_txt_schema(payload, expected_encoding=result.text_encoding)
        if raw_bytes_sha256(payload) != result.source_bytes_sha256 or len(payload) != result.source_byte_count:
            raise ValueError("source bytes do not match retrieval result")
    return result


def _load_json_model(path: Path, model: type[object], *, error: str) -> object:
    try:
        raw = Path(path).read_text(encoding="utf-8")
        return model.model_validate_json(raw)  # type: ignore[attr-defined]
    except (OSError, ValueError) as exc:
        raise ValueError(error) from exc


def _safe_bundle_child(bundle_dir: Path, relative_path: str) -> Path:
    child = bundle_dir / relative_path
    try:
        metadata = child.lstat()
    except OSError as exc:
        raise ValueError("bundle member is unavailable") from exc
    if not child.is_file() or child.is_symlink():
        raise ValueError("bundle member is unsafe")
    if child.parent != bundle_dir or metadata.st_size <= 0:
        raise ValueError("bundle member is unsafe")
    return child


def _jsonl_row_count(payload: bytes) -> int:
    if not payload.endswith(b"\n"):
        raise ValueError("bundle JSONL member must end with newline")
    rows = [line for line in payload.splitlines() if line]
    for line in rows:
        try:
            json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("bundle JSONL member is invalid") from exc
    return len(rows)


def _source_snapshot_entry_count(payload: bytes) -> int:
    text, _encoding = _decode_source_txt(payload)
    rows = [line for line in text.splitlines() if line.strip()]
    if rows and rows[0].split("\t")[:5] == ["순위", "단어", "품사", "풀이", "등급"]:
        return len(rows) - 1
    return len(rows)


def _expected_manifest_bundle_sha256(manifest: KoreanFrequencyBundleManifest) -> str:
    return canonical_json_sha256(
        manifest.model_dump(mode="json", exclude={"bundle_sha256"})
    )


def validate_korean_source_build_result(
    result_file: Path,
    *,
    bundle_dir: Path | None = None,
) -> KoreanFrequencyBuildResult:
    """Read-only validation of an inactive Korean frequency build result."""

    result = _load_json_model(
        Path(result_file),
        KoreanFrequencyBuildResult,
        error="build result is invalid",
    )
    assert isinstance(result, KoreanFrequencyBuildResult)
    if bundle_dir is None:
        return result

    root = Path(bundle_dir)
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise ValueError("bundle root is unavailable") from exc
    if not root.is_dir() or root.is_symlink() or root_metadata.st_size < 0:
        raise ValueError("bundle root is unsafe")

    manifest_path = _safe_bundle_child(root, _BUNDLE_MANIFEST_PATH)
    manifest = _load_json_model(
        manifest_path,
        KoreanFrequencyBundleManifest,
        error="bundle manifest is invalid",
    )
    assert isinstance(manifest, KoreanFrequencyBundleManifest)
    if _expected_manifest_bundle_sha256(manifest) != manifest.bundle_sha256:
        raise ValueError("bundle manifest root hash drift")
    if result.bundle_sha256 != manifest.bundle_sha256:
        raise ValueError("build result bundle hash drift")
    if result.inventory_sha256 != manifest.inventory_sha256:
        raise ValueError("build result inventory hash drift")
    if result.rejection_sha256 != manifest.rejection_sha256:
        raise ValueError("build result rejection hash drift")
    if result.report_sha256 != manifest.report_sha256:
        raise ValueError("build result report hash drift")
    if result.accepted_count != manifest.entry_count:
        raise ValueError("build result accepted count drift")
    if result.rejection_count != manifest.rejection_count:
        raise ValueError("build result rejection count drift")
    if result.level_counts != manifest.level_counts:
        raise ValueError("build result level count drift")

    declared = {_BUNDLE_MANIFEST_PATH, _BUILD_RESULT_PATH}
    for member in manifest.members:
        declared.add(member.relative_path)
        child = _safe_bundle_child(root, member.relative_path)
        payload = child.read_bytes()
        if raw_bytes_sha256(payload) != member.sha256:
            raise ValueError("bundle member hash drift")
        if len(payload) != member.byte_count:
            raise ValueError("bundle member byte count drift")
        if member.kind in {"curated-inventory", "rejections", "source-snapshot"}:
            row_count = _jsonl_row_count(payload) if member.kind != "source-snapshot" else _source_snapshot_entry_count(payload)
            if row_count != member.row_count:
                raise ValueError("bundle member row count drift")

    actual = set()
    for child in root.iterdir():
        if child.is_symlink() or not child.is_file():
            raise ValueError("bundle root contains unsafe member")
        actual.add(child.name)
    if actual != declared:
        raise ValueError("bundle root contains undeclared members")
    return result


def load_korean_final_frequency_entries(
    *,
    job_id: str,
    bundle_root: Path,
    binding_receipt_sha256: str,
    authority: KoreanFrequencyJobAuthority,
    repo_root: Path | None = None,
) -> tuple[KoreanFrequencyEntry, ...]:
    """Load final Korean entries only after rehashing the bound authority."""

    if not str(job_id or "").strip():
        raise ValueError("Korean frequency runtime requires job_id")
    if not isinstance(authority, KoreanFrequencyJobAuthority):
        authority = KoreanFrequencyJobAuthority.model_validate(authority)
    root = Path(bundle_root)
    manifest_path = _safe_bundle_child(root, _BUNDLE_MANIFEST_PATH)
    result_path = _safe_bundle_child(root, _BUILD_RESULT_PATH)
    build_result = validate_korean_source_build_result(result_path, bundle_dir=root)
    manifest = _load_json_model(
        manifest_path,
        KoreanFrequencyBundleManifest,
        error="bundle manifest is invalid",
    )
    assert isinstance(manifest, KoreanFrequencyBundleManifest)
    _verify_korean_runtime_authority(
        authority=authority,
        manifest_path=manifest_path,
        manifest=manifest,
        build_result=build_result,
        build_result_sha256=raw_bytes_sha256(build_result.model_dump_json().encode("utf-8")),
        binding_receipt_sha256=binding_receipt_sha256,
        repo_root=repo_root,
    )
    inventory_member = next(
        (member for member in manifest.members if member.kind == "curated-inventory"),
        None,
    )
    if inventory_member is None:
        raise ValueError("Korean frequency runtime authority drift")
    entries = _load_korean_inventory_entries(_safe_bundle_child(root, inventory_member.relative_path))
    level_counts = validate_korean_frequency_accounting(
        entries,
        source_candidate_count=manifest.entry_count + manifest.rejection_count,
        rejection_count=manifest.rejection_count,
    )
    if level_counts != manifest.level_counts:
        raise ValueError("Korean frequency runtime authority drift")
    if any(entry.retrieval_sha256 != build_result.source_bytes_sha256 for entry in entries):
        raise ValueError("Korean frequency runtime authority drift")
    if any(entry.bundle_sha256 != build_result.source_bytes_sha256 for entry in entries):
        raise ValueError("Korean frequency runtime authority drift")
    return entries


def _verify_korean_runtime_authority(
    *,
    authority: KoreanFrequencyJobAuthority,
    manifest_path: Path,
    manifest: KoreanFrequencyBundleManifest,
    build_result: KoreanFrequencyBuildResult,
    build_result_sha256: str,
    binding_receipt_sha256: str,
    repo_root: Path | None,
) -> None:
    expected = {
        "frequency_bundle_locator_sha256": raw_bytes_sha256(manifest_path.read_bytes()),
        "frequency_bundle_content_sha256": manifest.bundle_sha256,
        "source_retrieval_sha256": build_result.retrieval_sha256,
        "source_build_result_sha256": build_result_sha256,
        "source_review_aggregate_sha256": binding_receipt_sha256,
    }
    for field, value in expected.items():
        if getattr(authority, field) != value:
            raise ValueError("Korean frequency runtime authority drift")


def _load_korean_inventory_entries(path: Path) -> tuple[KoreanFrequencyEntry, ...]:
    payload = path.read_bytes()
    if not payload.endswith(b"\n"):
        raise ValueError("Korean frequency runtime authority drift")
    entries: list[KoreanFrequencyEntry] = []
    for line in payload.splitlines():
        if not line:
            continue
        try:
            entries.append(KoreanFrequencyEntry.model_validate_json(line.decode("utf-8")))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("Korean frequency runtime authority drift") from exc
    return tuple(entries)


def project_korean_match_status(status: object) -> str:
    value = getattr(status, "value", status)
    if value == "matched":
        return "match"
    if value == "mismatch":
        return "mismatch"
    return "inconclusive"


class KoreanFrequencySourceRetriever:
    """Bounded official-source retriever with injectable transport for tests."""

    def __init__(self, *, urlopen: UrlOpen | None = None, resolver: Resolver | None = None) -> None:
        self._urlopen = urlopen or _default_urlopen_no_redirect
        self._resolver = resolver if resolver is not None else (socket.getaddrinfo if urlopen is None else None)

    def retrieve_to_directory(self, output_dir: Path) -> tuple[KoreanFrequencyRetrievalResult, Path]:
        target_dir = _safe_output_dir(output_dir)
        _require_public_dns(KOREAN_FREQUENCY_LANDING_URL, self._resolver)
        landing_request = Request(KOREAN_FREQUENCY_LANDING_URL, headers={"Accept": "text/html"}, method="GET")
        with self._urlopen(landing_request, 10) as landing_response:
            _require_unredirected_response(landing_response, KOREAN_FREQUENCY_LANDING_URL)
            landing_bytes = _read_bounded(landing_response, limit=_MAX_LANDING_BYTES)
        attachment_url = resolve_nikl_frequency_attachment_url(landing_bytes)
        _require_public_dns(attachment_url, self._resolver)
        attachment_request = Request(attachment_url, headers={"Accept": "text/plain"}, method="GET")
        with self._urlopen(attachment_request, 20) as attachment_response:
            _require_unredirected_response(attachment_response, attachment_url)
            source_bytes = _read_bounded(attachment_response, limit=_MAX_SOURCE_BYTES)
            filename = _content_disposition_filename(getattr(attachment_response, "headers", None))
        if filename is not None and filename != KOREAN_FREQUENCY_EXPECTED_FILENAME:
            raise ValueError("attachment filename does not match accepted TXT")
        text_encoding = _validate_source_txt_schema(source_bytes)
        source_path = target_dir / _SOURCE_PATH
        result_path = target_dir / _RESULT_PATH
        result = KoreanFrequencyRetrievalResult(
            source_id=KOREAN_FREQUENCY_SOURCE_ID,
            landing_url=KOREAN_FREQUENCY_LANDING_URL,
            accepted_filename=KOREAN_FREQUENCY_EXPECTED_FILENAME,
            landing_sha256=raw_bytes_sha256(landing_bytes),
            attachment_url=attachment_url,
            attachment_sha256=raw_bytes_sha256(source_bytes),
            source_bytes_sha256=raw_bytes_sha256(source_bytes),
            source_byte_count=len(source_bytes),
            retrieved_at="transport-controlled",
            text_encoding=text_encoding,
            schema_version=KOREAN_FREQUENCY_RETRIEVAL_SCHEMA_VERSION,
        )
        try:
            _atomic_write_bytes(source_path, source_bytes)
            _atomic_write_bytes(
                result_path,
                (json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"),
            )
            validate_korean_source_retrieval_result(result_path, source_file=source_path)
        except Exception:
            for path in (source_path, result_path):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            raise
        return result, result_path


__all__ = [
    "KoreanFrequencySourceRetriever",
    "resolve_nikl_frequency_attachment_url",
    "load_korean_final_frequency_entries",
    "project_korean_match_status",
    "validate_korean_source_build_result",
    "validate_korean_source_retrieval_result",
]
