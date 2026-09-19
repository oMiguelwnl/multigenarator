"""Explicit downloads from the packaged source catalog and one-pass extraction."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unicodedata
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_preparation import source_catalog
from multilang.services.vocabulary_sources import SourceLimits, _modern_language, _verified_lines


def _plain_path(path: Path) -> Path:
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("source path must not contain symlinks")
    return path


def _digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _catalog_source(language: str, kind: str, index: int) -> tuple[dict, str]:
    catalog = source_catalog(language)
    if kind in {"corpus-test", "corpus-train", "corpus-dev"}:
        source = catalog["corpus"]
        if kind == "corpus-dev":
            urls = source.get("dev_urls")
            if not isinstance(urls, list) or not urls:
                raise ValueError("no catalogued development corpus for this language")
        else:
            urls = source["test_urls" if kind == "corpus-test" else "train_urls"]
    elif kind == "dictionary":
        source = catalog["lexical_sources"][0]
        urls = [source["url"]]
    elif kind == "lexical-supplement":
        if len(catalog["lexical_sources"]) < 2:
            raise ValueError("no lexical supplement is registered for this language")
        source = catalog["lexical_sources"][1]
        urls = [source["url"]]
    elif kind == "glosses":
        source = catalog["lexical_sources"][0].get("gloss_source")
        if not isinstance(source, dict):
            raise ValueError("no gloss source is registered for this language")
        urls = [source["url"]]
    else:
        raise ValueError("unknown catalog source kind")
    if not 0 <= index < len(urls):
        raise ValueError("catalog source index is outside available files")
    url = urls[index]
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.hostname
        not in {"kaikki.org", "raw.githubusercontent.com", "wordnetcode.princeton.edu"}
        or parsed.port not in {None, 443}
    ):
        raise ValueError("catalog source is not an approved public download origin")
    return source, url


def acquire_source(
    language: str,
    kind: str,
    root: Path,
    *,
    index: int = 0,
    max_bytes: int = 4 * 1024**3,
    client: httpx.Client | None = None,
) -> dict:
    """Download only a selected catalog entry; a download is not rights approval.

    Redirects are rejected, including redirects returned by otherwise trusted
    hosts. Content-addressed files and receipts permit frozen reproducible reuse.
    """
    source, url = _catalog_source(language, kind, index)
    if not 1 <= max_bytes <= 8 * 1024**3:
        raise ValueError("download byte limit must be between 1 byte and 8 GiB")
    root = _plain_path(root)
    root.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        http = client or stack.enter_context(
            httpx.Client(
                timeout=httpx.Timeout(60, connect=20), follow_redirects=False, trust_env=False
            )
        )
        staging = Path(
            stack.enter_context(tempfile.TemporaryDirectory(prefix=".acquire-", dir=root))
        )
        temporary = staging / "download"
        size = 0
        hasher = hashlib.sha256()
        with http.stream(
            "GET", url, follow_redirects=False, headers={"Accept-Encoding": "identity"}
        ) as response:
            response.raise_for_status()
            declared = response.headers.get("content-length")
            if declared is not None and int(declared) > max_bytes:
                raise ValueError("download exceeds byte limit")
            with temporary.open("xb") as handle:
                for chunk in response.iter_raw(chunk_size=1024**2):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("download exceeds byte limit")
                    hasher.update(chunk)
                    handle.write(chunk)
        if size == 0:
            raise ValueError("download is empty")
        if declared is not None and int(declared) != size:
            raise ValueError("download length mismatch")
        digest = hasher.hexdigest()
        suffix = (
            ".jsonl.gz"
            if url.endswith(".jsonl.gz")
            else (
                ".tar.gz"
                if url.endswith(".tar.gz")
                else ".conllu"
                if url.endswith(".conllu")
                else ".txt"
            )
        )
        destination = _plain_path(root / (digest + suffix))
        if destination.exists():
            if _digest(destination) != digest:
                raise ValueError("existing content-addressed source changed")
        else:
            # Link avoids overwriting a concurrently acquired source file.
            try:
                os.link(temporary, destination)
            except FileExistsError:
                if _digest(destination) != digest:
                    raise ValueError("concurrent source content mismatch") from None
        receipt = {
            "schema_version": 1,
            "language": language,
            "kind": kind,
            "index": index,
            "source_id": source["source_id"],
            "source_url": url,
            "sha256": digest,
            "file": destination.name,
            "bytes": size,
            "license": source.get("license"),
            "license_urls": source.get("license_urls")
            or ([source["license_url"]] if source.get("license_url") else []),
            "attribution": source.get("attribution"),
            "restrictions": source.get("restrictions"),
            "redistribution_approved": False,
            "linguistic_review_approved": False,
        }
        receipt_name = canonical_sha256(receipt) + ".receipt.json"
        receipt_path = _plain_path(root / receipt_name)
        if not receipt_path.exists():
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        return receipt


def split_wiktextract(
    source: Path,
    source_sha256: str,
    output: Path,
    lemma_filters: dict[str, set[str]],
    *,
    limits: SourceLimits | None = None,
    max_output_bytes: int = 4 * 1024**3,
) -> dict:
    """Select real records for all languages once, without expanding the dump.

    Casefold affects candidate selection only. Stored spelling and language are
    never changed; Serbo-Croatian is not silently reclassified as Croatian.
    """
    if not lemma_filters or max_output_bytes < 1:
        raise ValueError("language filters and a positive output limit are required")
    filters = {
        _modern_language(code).value: {
            unicodedata.normalize("NFC", word).casefold() for word in words
        }
        for code, words in lemma_filters.items()
    }
    output = _plain_path(output)
    if output.exists():
        raise ValueError("split output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    limits = limits or SourceLimits(
        max_bytes=4 * 1024**3,
        max_expanded_bytes=32 * 1024**3,
        max_records=40_000_000,
        max_line_bytes=16 * 1024**2,
    )
    with tempfile.TemporaryDirectory(prefix=".split-", dir=output.parent) as directory:
        staging = Path(directory) / "result"
        staging.mkdir()
        counts = dict.fromkeys(filters, 0)
        written = 0
        with ExitStack() as stack:
            handles = {
                code: stack.enter_context((staging / f"{code}.jsonl").open("w", encoding="utf-8"))
                for code in filters
            }
            for line in _verified_lines(source, source_sha256, limits):
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("dictionary record must be an object")
                code = record.get("lang_code")
                word = record.get("word")
                if (
                    code not in filters
                    or not isinstance(word, str)
                    or unicodedata.normalize("NFC", word).casefold() not in filters[code]
                ):
                    continue
                written += len(line.encode("utf-8"))
                if written > max_output_bytes:
                    raise ValueError("selected dictionary output exceeds byte limit")
                handles[code].write(line if line.endswith("\n") else line + "\n")
                counts[code] += 1
        result = {
            "schema_version": 1,
            "source_sha256": source_sha256,
            "selection_policy": "NFC-casefold-candidate-filter-only",
            "production_eligible": False,
            "redistribution_approved": False,
            "languages": {
                code: {
                    "record_count": counts[code],
                    "sha256": _digest(staging / f"{code}.jsonl"),
                    "filter_sha256": canonical_sha256(sorted(filters[code])),
                    "filter_word_count": len(filters[code]),
                    "file": f"{code}.jsonl",
                }
                for code in sorted(filters)
            },
        }
        (staging / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
        if output.exists():
            raise ValueError("split output created concurrently")
        os.rename(staging, output)
        return result
