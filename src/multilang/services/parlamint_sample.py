"""Prepare the official ParlaMint sample as bounded, formal-speech diagnostics.

Only unambiguous national-language sample members are selected. This package
does not turn parliamentary proceedings into general spoken-language coverage.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from multilang.services.vocabulary_review import _plain_path, _read_bytes

LANGUAGES = {
    "AT": "de",
    "CZ": "cs",
    "DK": "da",
    "ES": "es",
    "FI": "fi",
    "FR": "fr",
    "GB": "en",
    "GR": "el",
    "HR": "hr",
    "HU": "hu",
    "IT": "it",
    "NL": "nl",
    "PL": "pl",
    "PT": "pt",
    "SE": "sv",
    "TR": "tr",
}
SOURCE_URL = "https://www.clarin.si/repository/xmlui/handle/11356/1859"
DOWNLOAD_URL = (
    "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1859/"
    "ParlaMint-4.0.tar.gz?isAllowed=y&sequence=41"
)


def _member_code(name: str) -> str | None:
    parts = PurePosixPath(name).parts
    if len(parts) != 4 or parts[:2] != ("ParlaMint-4.0", "Samples"):
        return None
    folder, filename = parts[2:]
    if not folder.startswith("ParlaMint-"):
        return None
    code = folder.removeprefix("ParlaMint-")
    if not re.fullmatch(r"[A-Z]{2}", code):
        return None
    if not re.fullmatch(rf"ParlaMint-{code}_[A-Za-z0-9._-]+\.conllu", filename):
        return None
    return code


def prepare_sample(
    archive_path: Path,
    archive_sha256: str,
    output_dir: Path,
    *,
    languages: dict[str, str] | None = None,
    expected_members: int = 3,
    max_member_bytes: int = 8 * 1024**2,
    max_archive_expanded_bytes: int = 128 * 1024**2,
) -> dict:
    """Publish a pinned sample only after every selected archive member validates."""
    languages = LANGUAGES if languages is None else languages
    if not languages or any(
        not re.fullmatch(r"[A-Z]{2}", code) or not re.fullmatch(r"[a-z]{2}", language)
        for code, language in languages.items()
    ) or len(set(languages.values())) != len(languages):
        raise ValueError("invalid sample language mapping")
    if expected_members < 1 or max_member_bytes < 1 or max_archive_expanded_bytes < 1:
        raise ValueError("invalid sample size limit")
    archive = _read_bytes(_plain_path(archive_path), archive_sha256, limit=64 * 1024**2)
    selected: dict[str, list[tuple[str, bytes]]] = {language: [] for language in languages.values()}
    seen = set()
    expanded_bytes = 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as source:
        for position, member in enumerate(source):
            if position >= 10000:
                raise ValueError("archive member size limit exceeded")
            name = member.name
            parts = PurePosixPath(name).parts
            if not name or name.startswith("/") or ".." in parts:
                raise ValueError("unsafe archive member")
            if name in seen:
                raise ValueError("duplicate archive member")
            seen.add(name)
            expanded_bytes += member.size
            if expanded_bytes > max_archive_expanded_bytes:
                raise ValueError("archive expanded size limit exceeded")
            code = _member_code(name)
            if code not in languages:
                continue
            if member.issym() or member.islnk():
                raise ValueError("unsafe selected archive member")
            if not member.isfile() or member.size > max_member_bytes:
                raise ValueError("selected member size limit exceeded")
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError("selected member cannot be read")
            data = stream.read(max_member_bytes + 1)
            if len(data) != member.size or len(data) > max_member_bytes:
                raise ValueError("selected member size limit exceeded")
            if b"# newdoc id = " not in data or b"# sent_id = " not in data:
                raise ValueError("selected member lacks document or sentence identity")
            data.decode("utf-8")
            selected[languages[code]].append((name, data))
    if any(len(items) != expected_members for items in selected.values()):
        raise ValueError("sample member count differs from pinned version")

    destination = _plain_path(output_dir)
    if destination.exists():
        raise ValueError("sample output already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".parlamint-", dir=destination.parent) as temp:
        stage = Path(temp) / "result"
        (stage / "corpora").mkdir(parents=True)
        outputs = {}
        for language, items in sorted(selected.items()):
            payload = b"".join(data.rstrip(b"\n") + b"\n\n" for _, data in sorted(items))
            path = stage / "corpora" / f"{language}.conllu"
            path.write_bytes(payload)
            outputs[language] = {
                "path": f"corpora/{language}.conllu",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "members": [
                    {"name": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                    for name, data in sorted(items)
                ],
            }
        manifest = {
            "schema_version": "parlamint-formal-speech-sample-1",
            "status": "diagnostic_formal_speech_only",
            "source_url": SOURCE_URL,
            "download_url": DOWNLOAD_URL,
            "source_version": "4.0",
            "archive_sha256": archive_sha256,
            "archive_expanded_bytes": expanded_bytes,
            "license": "CC BY 4.0 with attribution obligations",
            "languages": outputs,
            "counting_unit": "source CoNLL-U annotated word occurrence",
            "limitations": [
                "Only three parliamentary documents per language; formal speech is not general conversation.",
                "Original sample is exposed development evidence, never an untouched holdout.",
                "Corpus annotation must be checked against inventory lemma/POS conventions.",
            ],
            "coverage_90_percent_verified": False,
            "production_eligible": False,
            "generation_status": "deferred_by_user",
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(stage, destination)
    return manifest
