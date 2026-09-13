"""Bounded public-document acquisition for explicitly provisional corpus pilots.

The adapter freezes bytes, document boundaries, revision IDs and source claims.
It never creates a linguistic approval, assigns a sense, or asserts that a small
sample represents general-language frequency. No download occurs on import.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from collections.abc import Callable, Iterable
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

import httpx
from pydantic import AwareDatetime, Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_acquisition import _plain_path
from multilang.services.vocabulary_sources import SourceLimits, _modern_language, _verified_lines

Project = Literal["wikipedia", "wikinews", "wikibooks"]
_REGISTERS = {"wikipedia": "encyclopedic", "wikinews": "news", "wikibooks": "instructional"}
_USER_AGENT = "MultilangQualification/0.1 (local, bounded linguistic corpus pilot)"


def _origin(language: str, project: str) -> tuple[SupportedLanguage, str]:
    code = _modern_language(language)
    if project not in _REGISTERS:
        raise ValueError("unsupported Wikimedia project")
    wiki_code = {"nb": "no", "zh-hans": "zh"}.get(code.value, code.value)
    return code, f"{wiki_code}.{project}.org"


class AcquisitionLimits(NativeContract):
    max_documents: int = Field(default=100, ge=1, le=1000)
    max_response_bytes: int = Field(default=2 * 1024**2, ge=1, le=16 * 1024**2)
    max_document_bytes: int = Field(default=128 * 1024, ge=1, le=1024**2)
    max_total_bytes: int = Field(default=64 * 1024**2, ge=1, le=256 * 1024**2)
    max_requests: int = Field(default=500, ge=1, le=5000)
    attempts: int = Field(default=3, ge=1, le=3)
    max_retry_seconds: int = Field(default=30, ge=0, le=30)


class SourceDocument(NativeContract):
    language: SupportedLanguage
    project: Project
    source_id: Identifier
    document_id: Identifier
    page_id: int = Field(ge=1)
    revision_id: Identifier
    title: str = Field(min_length=1, max_length=1024)
    source_url: str = Field(max_length=2048)
    text_register: Literal["encyclopedic", "news", "instructional"]
    variant: Literal["unresolved"] = "unresolved"
    published_at: AwareDatetime
    acquired_at: AwareDatetime
    raw_sha256: Sha256
    revision_raw_sha256: Sha256
    publication_raw_sha256: Sha256
    text_sha256: Sha256
    text: str = Field(min_length=1, max_length=1024**2)
    license_id: Identifier
    license_url: str = Field(max_length=2048)
    license_evidence_sha256: Sha256
    attribution: str = Field(min_length=1, max_length=2048)
    split: Literal["calibration", "evaluation", "reference"] = "calibration"
    transformation: Literal["html-paragraph-prose-NFC-v1"] = "html-paragraph-prose-NFC-v1"
    redistribution_approved: Literal[False] = False
    linguistic_review_approved: Literal[False] = False

    @model_validator(mode="after")
    def consistent(self) -> Self:
        _, host = _origin(self.language.value, self.project)
        if (
            self.source_id != f"wikimedia:{host}"
            or self.document_id != f"{host}:{self.page_id}"
            or not self.revision_id.isascii()
            or not self.revision_id.isdigit()
            or int(self.revision_id) < 1
            or self.source_url != f"https://{host}/w/index.php?oldid={self.revision_id}"
            or self.text_register != _REGISTERS[self.project]
        ):
            raise ValueError("document provenance mismatch")
        if self.text != unicodedata.normalize("NFC", self.text):
            raise ValueError("document text must be NFC")
        if hashlib.sha256(self.text.encode()).hexdigest() != self.text_sha256:
            raise ValueError("document text checksum mismatch")
        return self


class SourceIssue(NativeContract):
    page_id: int | None = Field(default=None, ge=1)
    reason: Identifier
    retry_after: str | None = Field(default=None, max_length=128)
    retry_not_before: AwareDatetime | None = None


class PageSelection(NativeContract):
    language: SupportedLanguage
    project: Project
    page_ids: tuple[int, ...] = Field(max_length=1000)
    selection_policy: Literal["bounded-allpages-prefix-v1", "bounded-recent-new-pages-v1"] = (
        "bounded-allpages-prefix-v1"
    )
    representative: Literal[False] = False
    continuation_available: bool
    raw_response: str = Field(max_length=16 * 1024**2)
    acquired_at: AwareDatetime

    @model_validator(mode="after")
    def selection_matches_response(self) -> Self:
        _origin(self.language.value, self.project)
        try:
            key = (
                "recentchanges"
                if self.selection_policy == "bounded-recent-new-pages-v1"
                else "allpages"
            )
            pages = json.loads(self.raw_response)["query"][key]
            if not isinstance(pages, list):
                raise ValueError
            ids = []
            for page in pages:
                if type(page["pageid"]) is not int or page["pageid"] < 1 or page["ns"] != 0:
                    raise ValueError
                ids.append(page["pageid"])
            if len(set(ids)) != len(ids) or tuple(sorted(ids)) != self.page_ids:
                raise ValueError
        except (KeyError, TypeError, ValueError, RecursionError):
            raise ValueError("selection IDs do not match frozen listing") from None
        return self

    @computed_field
    @property
    def response_sha256(self) -> str:
        return hashlib.sha256(self.raw_response.encode()).hexdigest()


class CorpusAcquisitionManifest(NativeContract):
    schema_version: Literal[1] = 1
    language: SupportedLanguage
    project: Project
    source_id: Identifier
    acquired_at: AwareDatetime
    requested_page_ids: tuple[int, ...]
    selection_policy: Literal[
        "explicit-page-ids-v1", "bounded-allpages-prefix-v1", "bounded-recent-new-pages-v1"
    ]
    selection_sha256: Sha256
    document_count: int = Field(ge=0)
    text_bytes: int = Field(ge=0)
    documents_sha256: Sha256
    document_ids: tuple[str, ...]
    files: dict[str, Sha256]
    blockers: tuple[SourceIssue, ...] = ()
    exclusions: tuple[SourceIssue, ...] = ()
    network_bytes: int = Field(ge=0)
    request_count: int = Field(ge=0)
    limits: AcquisitionLimits
    representative: Literal[False] = False
    production_eligible: Literal[False] = False
    limitations: tuple[str, ...] = (
        "Pilot sampling does not establish balanced general-language frequency.",
        "Language variety, source rights and linguistic content require review.",
        "Wikibooks chapters can share a book; document dispersion is provisional.",
    )


class SourceUnavailable(ValueError):
    """A safe, bounded failure code; never includes remote HTML or request secrets."""

    def __init__(self, reason, *, retry_after=None, retry_not_before=None):
        super().__init__(reason)
        self.retry_after = retry_after
        self.retry_not_before = retry_not_before

    def issue(self, page_id=None):
        return SourceIssue(
            page_id=page_id,
            reason=str(self),
            retry_after=self.retry_after,
            retry_not_before=self.retry_not_before,
        )


class _Fetcher:
    def __init__(self, client, host, limits, sleep, raw=None):
        self.client, self.host, self.limits = client, host, limits
        self.sleep, self.raw = sleep, raw
        self.bytes = self.requests = 0

    def get(self, **params):
        for attempt in range(self.limits.attempts):
            if self.bytes >= self.limits.max_total_bytes:
                raise SourceUnavailable("total_byte_limit")
            self.requests += 1
            if self.requests > self.limits.max_requests:
                raise SourceUnavailable("request_limit")
            retry_after = None
            try:
                with self.client.stream(
                    "GET",
                    f"https://{self.host}/w/api.php",
                    params={"format": "json", "formatversion": 2, "maxlag": 5, **params},
                    headers={"User-Agent": _USER_AGENT, "Accept-Encoding": "identity"},
                    follow_redirects=False,
                ) as response:
                    if response.is_redirect:
                        raise SourceUnavailable("redirect_forbidden")
                    retry_after = response.headers.get("retry-after")
                    status = response.status_code
                    if status in {429, 500, 502, 503, 504}:
                        code = f"http_{status}"
                    elif status != 200:
                        raise SourceUnavailable(f"http_{status}")
                    else:
                        if response.headers.get("content-encoding", "identity") != "identity":
                            raise SourceUnavailable("unexpected_content_encoding")
                        declared = response.headers.get("content-length")
                        if declared is not None:
                            try:
                                size = int(declared)
                            except ValueError:
                                raise SourceUnavailable("invalid_content_length") from None
                            if size < 0 or size > self.limits.max_response_bytes:
                                raise SourceUnavailable("response_byte_limit")
                        chunks, size = [], 0
                        for chunk in response.iter_bytes(chunk_size=65536):
                            size += len(chunk)
                            self.bytes += len(chunk)
                            if size > self.limits.max_response_bytes:
                                raise SourceUnavailable("response_byte_limit")
                            if self.bytes > self.limits.max_total_bytes:
                                raise SourceUnavailable("total_byte_limit")
                            chunks.append(chunk)
                        data = b"".join(chunks)
                        try:
                            value = json.loads(data)
                        except (ValueError, UnicodeError, RecursionError):
                            raise SourceUnavailable("invalid_json") from None
                        if not isinstance(value, dict):
                            raise SourceUnavailable("invalid_response")
                        if self.raw is not None:
                            digest = hashlib.sha256(data).hexdigest()
                            destination = self.raw / (digest + ".json")
                            if not destination.exists():
                                destination.write_bytes(data)
                        if "error" not in value:
                            return value, data
                        code = "api_error"
                        error = value["error"]
                        if isinstance(error, dict) and error.get("code") == "maxlag":
                            code = "maxlag"
                        else:
                            raise SourceUnavailable(code)
            except httpx.HTTPError:
                code = "network_unavailable"
            delay = 2**attempt
            deadline = None
            if retry_after is not None:
                if len(retry_after) > 128:
                    raise SourceUnavailable("invalid_retry_after")
                try:
                    delay = max(0, int(retry_after))
                except ValueError:
                    try:
                        deadline = parsedate_to_datetime(retry_after)
                        delay = max(0, (deadline - datetime.now(UTC)).total_seconds())
                    except (ValueError, TypeError, OverflowError):
                        raise SourceUnavailable("invalid_retry_after") from None
                try:
                    deadline = datetime.now(UTC) + timedelta(seconds=delay)
                except OverflowError:
                    raise SourceUnavailable("invalid_retry_after") from None
            if attempt + 1 == self.limits.attempts:
                raise SourceUnavailable(code, retry_after=retry_after, retry_not_before=deadline)
            if delay > self.limits.max_retry_seconds:
                raise SourceUnavailable(
                    "retry_deferred", retry_after=retry_after, retry_not_before=deadline
                )
            self.sleep(delay)
        raise AssertionError("unreachable")


def _http(client):
    return (
        nullcontext(client)
        if client is not None
        else httpx.Client(
            timeout=httpx.Timeout(30, connect=10), trust_env=False, follow_redirects=False
        )
    )


def discover_wikimedia_pages(
    language: str,
    project: str,
    *,
    limit: int = 50,
    client: httpx.Client | None = None,
    limits: AcquisitionLimits | None = None,
    sleep: Callable[[float], None] = time.sleep,
    strategy: Literal["alphabetical-prefix", "recent-new-pages"] = "alphabetical-prefix",
) -> PageSelection:
    """Freeze a bounded namespace-zero listing, explicitly an alphabetical prefix.

    This convenience listing is not random or representative. Callers preparing
    stratified samples should pass their explicit page IDs to acquisition.
    """
    code, host = _origin(language, project)
    limits = limits or AcquisitionLimits()
    if type(limit) is not int or not 1 <= limit <= min(limits.max_documents, 500):
        raise ValueError("page selection limit exceeded")
    if strategy == "recent-new-pages":
        key, policy = "recentchanges", "bounded-recent-new-pages-v1"
        params = dict(
            list=key,
            rcnamespace=0,
            rctype="new",
            rcshow="!redirect",
            rcprop="ids|timestamp|title",
            rclimit=limit,
        )
    elif strategy == "alphabetical-prefix":
        key, policy = "allpages", "bounded-allpages-prefix-v1"
        params = dict(list=key, apnamespace=0, apfilterredir="nonredirects", aplimit=limit)
    else:
        raise ValueError("invalid source selection strategy")
    with _http(client) as http:
        value, raw = _Fetcher(http, host, limits, sleep).get(action="query", **params)
    try:
        pages = value["query"][key]
        if not isinstance(pages, list) or len(pages) > limit:
            raise ValueError
        ids = []
        for page in pages:
            page_id = page["pageid"]
            if type(page_id) is not int or page_id < 1 or page["ns"] != 0:
                raise ValueError
            ids.append(page_id)
        if len(set(ids)) != len(ids):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise SourceUnavailable("invalid_page_listing") from None
    return PageSelection(
        language=code,
        project=project,
        page_ids=tuple(sorted(ids)),
        selection_policy=policy,
        continuation_available="continue" in value,
        raw_response=raw.decode("utf-8"),
        acquired_at=datetime.now(UTC),
    )


def wikimedia_license(language, project, published_at, rights) -> tuple[str, str]:
    """Record researched source claims; this is not a redistribution decision."""
    _origin(language, project)
    url = rights.get("url", "") if isinstance(rights, dict) else ""
    parsed = urlsplit(url) if isinstance(url, str) else urlsplit("")
    path = parsed.path.rstrip("/")
    if (
        parsed.scheme == "https"
        and parsed.netloc == "creativecommons.org"
        and not parsed.query
        and not parsed.fragment
    ):
        path = re.sub(r"/deed\.[a-zA-Z-]{2,16}$", "", path)
        url = "https://creativecommons.org" + path
    else:
        url = ""
    if project == "wikinews":
        if language == "en" and published_at < datetime(2005, 9, 25, tzinfo=UTC):
            return "public-domain-source-claim", "https://en.wikinews.org/wiki/Wikinews:Copyright"
        if language == "en" and published_at < datetime(2024, 12, 17, tzinfo=UTC):
            return "CC-BY-2.5", "https://creativecommons.org/licenses/by/2.5/"
        if (
            language in {"pt", "en"}
            and published_at >= datetime(2024, 12, 17, tzinfo=UTC)
            and url.rstrip("/") == "https://creativecommons.org/licenses/by/4.0"
        ):
            return "CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/"
    elif url.rstrip("/") == "https://creativecommons.org/licenses/by-sa/4.0":
        return "CC-BY-SA-4.0", "https://creativecommons.org/licenses/by-sa/4.0/"
    return "unresolved", "https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use"


class _Prose(HTMLParser):
    _IGNORE = {"script", "style", "table", "nav", "aside", "sup", "math", "pre", "code"}
    _VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        parent_blocked = bool(self.stack and self.stack[-1][1])
        parent_p = bool(self.stack and self.stack[-1][2])
        classes = dict(attrs).get("class", "") or ""
        blocked = (
            parent_blocked
            or tag in self._IGNORE
            or any(
                name in classes.split()
                for name in ("reference", "reflist", "navbox", "metadata", "noprint")
            )
        )
        if tag == "br" and parent_p and not blocked:
            self.parts.append(" ")
        if tag not in self._VOID:
            self.stack.append((tag, blocked, parent_p or tag == "p"))
            if len(self.stack) > 256:
                raise SourceUnavailable("html_depth_limit")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self._VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                if tag == "p" and not self.stack[index][1]:
                    self.parts.append("\n\n")
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack and self.stack[-1][2] and not self.stack[-1][1]:
            self.parts.append(data)


def _page_revision(fetcher, page_id, *, first=False):
    params = {"rvdir": "newer", "rvlimit": 1} if first else {}
    value, raw = fetcher.get(
        action="query",
        prop="revisions",
        pageids=page_id,
        rvslots="main",
        rvprop="ids|timestamp|content",
        **params,
    )
    try:
        pages = value["query"]["pages"]
        if not isinstance(pages, list) or len(pages) != 1:
            raise ValueError
        page = pages[0]
        if page["pageid"] != page_id or page["ns"] != 0 or "missing" in page:
            raise ValueError
        (revision,) = page["revisions"]
        if type(revision["revid"]) is not int or revision["revid"] < 1:
            raise ValueError
        if revision["slots"]["main"]["contentmodel"] != "wikitext":
            raise ValueError
        timestamp = datetime.fromisoformat(revision["timestamp"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise SourceUnavailable("invalid_revision") from None
    return page, revision, timestamp, hashlib.sha256(raw).hexdigest()


def _acquire_document(fetcher, language, project, page_id, rights, rights_sha, acquired_at, split):
    page, revision, _modified, revision_sha = _page_revision(fetcher, page_id)
    _page, _first, published, publication_sha = _page_revision(fetcher, page_id, first=True)
    value, raw = fetcher.get(action="parse", oldid=revision["revid"], prop="text|revid")
    try:
        parsed = value["parse"]
        if parsed["pageid"] != page_id or parsed["revid"] != revision["revid"]:
            raise SourceUnavailable("revision_mismatch")
        html = parsed["text"]
        if not isinstance(html, str):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, SourceUnavailable):
            raise
        raise SourceUnavailable("invalid_parsed_revision") from None
    prose = _Prose()
    prose.feed(html)
    prose.close()
    # The original HTML and revision are retained. This declared transformation
    # normalizes paragraph whitespace/NFC before any token offsets are assigned.
    text = unicodedata.normalize(
        "NFC",
        "\n\n".join(
            " ".join(paragraph.split())
            for paragraph in "".join(prose.parts).split("\n\n")
            if paragraph.strip()
        ),
    )
    if not text:
        raise SourceUnavailable("no_paragraph_prose")
    if len(text.encode()) > fetcher.limits.max_document_bytes:
        raise SourceUnavailable("document_byte_limit")
    license_id, license_url = wikimedia_license(language.value, project, published, rights)
    host = fetcher.host
    return SourceDocument(
        language=language,
        project=project,
        source_id=f"wikimedia:{host}",
        document_id=f"{host}:{page_id}",
        page_id=page_id,
        revision_id=str(revision["revid"]),
        title=page["title"],
        source_url=f"https://{host}/w/index.php?oldid={revision['revid']}",
        text_register=_REGISTERS[project],
        published_at=published,
        acquired_at=acquired_at,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        revision_raw_sha256=revision_sha,
        publication_raw_sha256=publication_sha,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        text=text,
        license_id=license_id,
        license_url=license_url,
        license_evidence_sha256=rights_sha,
        attribution=f"Contributors to {host}; article and history linked by the source permalink.",
        split=split,
    )


def acquire_wikimedia_documents(
    language: str,
    project: str,
    page_ids: Iterable[int],
    output: Path,
    *,
    limits: AcquisitionLimits | None = None,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    selection: PageSelection | None = None,
    split: Literal["calibration", "evaluation", "reference"] = "calibration",
) -> CorpusAcquisitionManifest:
    """Acquire explicit public IDs, preserving failures in a frozen pilot manifest."""
    code, host = _origin(language, project)
    limits = limits or AcquisitionLimits()
    ids = []
    for page_id in page_ids:
        if type(page_id) is not int or page_id < 1:
            raise ValueError("page IDs must be positive integers")
        ids.append(page_id)
        if len(ids) > limits.max_documents:
            raise ValueError("document limit exceeded")
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("explicit unique page IDs are required")
    if split not in {"calibration", "evaluation", "reference"}:
        raise ValueError("invalid corpus split")
    ids = sorted(ids)
    output = _plain_path(output)
    if output.exists():
        raise ValueError("corpus output already exists")
    selection_data: dict = {"policy": "explicit-page-ids-v1", "page_ids": ids}
    if selection is not None:
        selection = PageSelection.model_validate(selection.model_dump(mode="json"))
        if (
            selection.language != code
            or selection.project != project
            or list(selection.page_ids) != ids
        ):
            raise ValueError("selection does not match requested source IDs")
        selection_data = selection.model_dump(mode="json")
    output.parent.mkdir(parents=True, exist_ok=True)
    acquired_at = datetime.now(UTC)
    with tempfile.TemporaryDirectory(prefix=".corpus-", dir=output.parent) as directory:
        staging = Path(directory) / "package"
        raw_root = staging / "raw"
        raw_root.mkdir(parents=True)
        blockers, exclusions, documents, seen = [], [], [], set()
        with _http(client) as http:
            fetcher = _Fetcher(http, host, limits, sleep, raw_root)
            try:
                value, raw = fetcher.get(
                    action="query", meta="siteinfo", siprop="general|rightsinfo"
                )
                query = value.get("query")
                if not isinstance(query, dict):
                    raise SourceUnavailable("invalid_rights_metadata")
                rights = query.get("rightsinfo", {})
                if not isinstance(rights, dict):
                    raise SourceUnavailable("invalid_rights_metadata")
                rights_sha = hashlib.sha256(raw).hexdigest()
            except SourceUnavailable as exc:
                blockers.append(exc.issue())
            else:
                for position, page_id in enumerate(ids):
                    try:
                        document = _acquire_document(
                            fetcher,
                            code,
                            project,
                            page_id,
                            rights,
                            rights_sha,
                            acquired_at,
                            split,
                        )
                    except SourceUnavailable as exc:
                        blockers.append(exc.issue(page_id))
                        if exc.retry_not_before is not None or str(exc) in {
                            "retry_deferred",
                            "total_byte_limit",
                            "request_limit",
                            "http_429",
                        }:
                            blockers.extend(
                                SourceIssue(
                                    page_id=remaining,
                                    reason="not_attempted_source_deferred",
                                    retry_after=exc.retry_after,
                                    retry_not_before=exc.retry_not_before,
                                )
                                for remaining in ids[position + 1 :]
                            )
                            break
                        continue
                    if document.text_sha256 in seen:
                        exclusions.append(SourceIssue(page_id=page_id, reason="duplicate_text"))
                        continue
                    seen.add(document.text_sha256)
                    documents.append(document)
        document_bytes = b"".join((doc.model_dump_json() + "\n").encode() for doc in documents)
        if len(document_bytes) > limits.max_total_bytes:
            raise ValueError("serialized document byte limit exceeded")
        (staging / "documents.jsonl").write_bytes(document_bytes)
        (staging / "selection.json").write_text(
            json.dumps(selection_data, ensure_ascii=False) + "\n"
        )
        files = {
            str(path.relative_to(staging)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(staging.rglob("*"))
            if path.is_file()
        }
        manifest = CorpusAcquisitionManifest(
            language=code,
            project=project,
            source_id=f"wikimedia:{host}",
            acquired_at=acquired_at,
            requested_page_ids=tuple(ids),
            selection_policy=(selection.selection_policy if selection else "explicit-page-ids-v1"),
            selection_sha256=canonical_sha256(selection_data),
            document_count=len(documents),
            text_bytes=sum(len(doc.text.encode()) for doc in documents),
            documents_sha256=files["documents.jsonl"],
            document_ids=tuple(doc.document_id for doc in documents),
            files=files,
            blockers=tuple(blockers),
            exclusions=tuple(exclusions),
            network_bytes=fetcher.bytes,
            request_count=fetcher.requests,
            limits=limits,
        )
        (staging / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
        # A single directory rename publishes only complete packages. A complete
        # manifest with zero documents is meaningful evidence of source failure.
        if output.exists():
            raise ValueError("corpus output already exists")
        os.rename(staging, output)
    return manifest


def read_document_corpus(
    path: Path,
    expected_sha256: str,
    *,
    limits: AcquisitionLimits | None = None,
) -> tuple[SourceDocument, ...]:
    """Verify bounded local records; a checksum is provenance, not review approval."""
    limits = limits or AcquisitionLimits()
    source_limits = SourceLimits(
        max_bytes=limits.max_total_bytes,
        max_expanded_bytes=limits.max_total_bytes,
        max_line_bytes=min(16 * 1024**2, limits.max_document_bytes * 6 + 16384),
        max_records=limits.max_documents,
    )
    documents, ids, hashes = [], set(), set()
    for line in _verified_lines(path, expected_sha256, source_limits):
        document = SourceDocument.model_validate_json(line)
        if len(document.text.encode()) > limits.max_document_bytes:
            raise ValueError("document byte limit exceeded")
        if document.document_id in ids or document.text_sha256 in hashes:
            raise ValueError("duplicate document or text in corpus")
        ids.add(document.document_id)
        hashes.add(document.text_sha256)
        documents.append(document)
    return tuple(documents)
