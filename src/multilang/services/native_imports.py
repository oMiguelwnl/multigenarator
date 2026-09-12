"""Bounded import adapters; source facts never come from inferred LLM fields."""

import csv
import ipaddress
import json
import socket
from hashlib import sha256
from io import StringIO
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import LexicalIdentity
from multilang.domain.ranking import CorpusObservation


class ImportSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    source_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    language: SupportedLanguage
    profile_version: str = Field(min_length=1, max_length=64)
    normalizer_version: str = Field(min_length=1, max_length=64)
    analyzer_version: str = Field(min_length=1, max_length=64)
    license_id: str = Field(min_length=1, max_length=128)
    attribution: str = Field(min_length=1, max_length=4000)
    redistribution_approved: bool = False
    approval_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class DictionaryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    lemma: str = Field(min_length=1, max_length=512)
    pos: str = Field(min_length=1, max_length=64)
    sense: str = Field(min_length=1, max_length=128)


class DictionaryImporter:
    def __init__(self, *, max_bytes: int = 8_000_000, max_records: int = 6000):
        self.max_bytes, self.max_records = max_bytes, max_records

    def _verify(self, data: bytes, source: ImportSource) -> str:
        if len(data) > self.max_bytes:
            raise ValueError("import byte limit exceeded")
        if sha256(data).hexdigest() != source.sha256:
            raise ValueError("source checksum mismatch")
        if source.redistribution_approved and not source.approval_sha256:
            raise ValueError("redistribution requires approval receipt")
        return data.decode("utf-8-sig", errors="strict")

    def _identities(self, rows: list[dict], source: ImportSource) -> tuple[LexicalIdentity, ...]:
        if not rows or len(rows) > self.max_records:
            raise ValueError("import record limit exceeded or empty source")
        entries = [DictionaryEntry.model_validate(row) for row in rows]
        identities = tuple(
            LexicalIdentity(
                language=source.language,
                normalized_lemma=entry.lemma,
                part_of_speech=entry.pos,
                sense_id=entry.sense,
                profile_version=source.profile_version,
                normalizer_version=source.normalizer_version,
                analyzer_version=source.analyzer_version,
                source_id=source.source_id,
                source_version=source.version,
                source_sha256=source.sha256,
            )
            for entry in entries
        )
        if len({identity.lexical_identity_id for identity in identities}) != len(identities):
            raise ValueError("duplicate lexical identity in source")
        return identities

    def parse(self, data: bytes, source: ImportSource) -> tuple[LexicalIdentity, ...]:
        rows = json.loads(self._verify(data, source))
        if not isinstance(rows, list):
            raise ValueError("dictionary source must be an array")
        return self._identities(rows, source)


class CSVImporter(DictionaryImporter):
    def parse(self, data: bytes, source: ImportSource) -> tuple[LexicalIdentity, ...]:
        reader = csv.DictReader(StringIO(self._verify(data, source)))
        if reader.fieldnames != ["lemma", "pos", "sense"]:
            raise ValueError("CSV header must be lemma,pos,sense")
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) > self.max_records:
                raise ValueError("import record limit exceeded")
        return self._identities(rows, source)


class CorpusImporter(DictionaryImporter):
    def parse(self, data: bytes, source: ImportSource) -> tuple[CorpusObservation, ...]:
        rows = json.loads(self._verify(data, source))
        if not isinstance(rows, list) or len(rows) > self.max_records:
            raise ValueError("corpus record limit exceeded or invalid source")
        return tuple(CorpusObservation.model_validate(row) for row in rows)


class ExternalAPIImporter(DictionaryImporter):
    """Fetch only operator-registered HTTPS hosts; redirects are never followed.

    Host registration is trusted configuration, not a caller-supplied bypass.
    Use a deployment egress allowlist as well for DNS/network isolation.
    """

    def __init__(self, *, allowed_hosts: set[str], **kwargs):
        super().__init__(**kwargs)
        self.allowed_hosts = frozenset(allowed_hosts)

    def validate_url(self, url: str) -> None:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.hostname not in self.allowed_hosts
            or parts.username
            or parts.password
            or parts.fragment
            or parts.port not in {None, 443}
        ):
            raise ValueError("external source URL is not approved")
        try:
            address = ipaddress.ip_address(parts.hostname)
        except ValueError:
            return
        if not address.is_global:
            raise ValueError("private network source forbidden")

    def fetch(self, url: str, source: ImportSource) -> tuple[LexicalIdentity, ...]:
        self.validate_url(url)
        hostname = urlsplit(url).hostname
        addresses = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(
            not ipaddress.ip_address(address[4][0]).is_global for address in addresses
        ):
            raise ValueError("private network source forbidden")
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
            with client.stream("GET", url, headers={"Accept": "application/json"}) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError("import byte limit exceeded")
                    chunks.append(chunk)
        return self.parse(b"".join(chunks), source)
