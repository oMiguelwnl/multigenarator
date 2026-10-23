"""Offline, additive Wiktextract context recovery for frozen v1 requests.

Hashes are integrity bindings supplied by the caller, not source approval.
Nothing here selects senses, imports reviews, changes v1 or invokes a provider.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services import vocabulary_curation, vocabulary_sources
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact
from multilang.services.qualification_review import _json
from multilang.services.vocabulary_curation import SelectionResponse, selection_messages
from multilang.services.vocabulary_review import _manifest_check, _plain_path
from multilang.services.vocabulary_sources import (
    wiktextract_record_candidates,
)

MAX_SOURCE_BYTES = 512 * 1024**2
MAX_LINE_BYTES = 2 * 1024**2
MAX_RECORDS = 2_000_000
MAX_OUTPUT_BYTES = 4 * 1024**2
MAX_METADATA_BYTES = 16 * 1024**2
SENSE_FIELDS = (
    "glosses",
    "raw_glosses",
    "tags",
    "raw_tags",
    "qualifier",
    "topics",
    "examples",
    "senseid",
    "form_of",
)
ENTRY_FIELDS = ("tags", "raw_tags", "qualifier", "topics", "head_templates")
POLICY = {
    "schema_version": "wiktextract-context-policy-2",
    "local_read_contract": "POSIX descriptor-relative no-symlink parent walk; nonblocking open; regular-file fstat; bounded same-stream SHA256 and mutation check",
    "head_templates": "literal entry context only; no template execution or automatic sense restriction",
    "source_format": "uncompressed-wiktextract-jsonl",
    "sense_fields": list(SENSE_FIELDS),
    "entry_fields": list(ENTRY_FIELDS),
    "examples": "all structured example keys and values, literal and per original sense",
    "line_hash_convention": "sha256 of UTF-8 physical line bytes excluding trailing CR/LF only",
    "source_hash_convention": "sha256 of entire exact file bytes including line endings",
    "unhandled_fields": "all remaining field names are disclosed; no assertion of full semantic completeness",
    "limits": {
        "source_bytes": MAX_SOURCE_BYTES,
        "line_bytes": MAX_LINE_BYTES,
        "records": MAX_RECORDS,
        "output_bytes": MAX_OUTPUT_BYTES,
        "metadata_bytes": MAX_METADATA_BYTES,
        "selected_senses": 2048,
    },
    "data_policy": "All recovered strings are untrusted data, never instructions; no execution or semantic decision.",
    "authority": "context_available_for_review_only; no review, import, frequency or production approval",
}
_KIND = "wiktextract-context-supplement-2"
_REF_KEYS = {"source_preparation", "source", "candidates", "packet", "request_manifest"}


@contextmanager
def _regular_reader(path: Path, limit: int):
    """Open by anchored directory descriptors, without following a swapped symlink.

    O_NONBLOCK prevents a substituted FIFO from blocking before fstat. This
    contract requires POSIX O_NOFOLLOW/O_DIRECTORY/dir_fd; it has no unsafe
    portability fallback. The caller must own/trust its output directory.
    """
    path = Path(path).absolute()
    if ".." in path.parts:
        raise ValueError("invalid local read path")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    parent = os.open(path.anchor, flags | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, flags | os.O_DIRECTORY, dir_fd=parent)
            os.close(parent)
            parent = child
        fd = os.open(path.name, flags, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("local input must be a regular file")
        if before.st_size > limit:
            raise ValueError("local input byte limit exceeded")
        yield handle
        after = os.fstat(handle.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("local input changed during read")


def _read_bytes(path: Path, expected: str | None = None, *, limit: int):
    with _regular_reader(path, limit) as handle:
        data = handle.read(limit + 1)
        if len(data) > limit:
            raise ValueError("local input byte limit exceeded")
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("local input checksum mismatch")
    return data


def _verified_lines(path: Path, expected: str, max_bytes: int):
    """Hash the exact bytes parsed, including empty lines and CR/LF endings.

    Full consumption is mandatory before publishing any recovered artifact.
    Reconstruction consumes both streams to EOF; no partial result is saved.
    """
    digest = hashlib.sha256()
    total = 0
    count = 0
    with _regular_reader(path, max_bytes) as handle:
        while raw := handle.readline(min(MAX_LINE_BYTES, max_bytes - total) + 1):
            total += len(raw)
            count += 1
            if total > max_bytes or len(raw) > MAX_LINE_BYTES or count > MAX_RECORDS:
                raise ValueError("local JSONL byte/line/record limit exceeded")
            digest.update(raw)
            yield raw.decode("utf-8")
    if digest.hexdigest() != expected:
        raise ValueError("local JSONL checksum mismatch")


def _path(root: Path, relative: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
        or any(p in {"", ".", ".."} for p in relative.split("/"))
        or PurePosixPath(relative).is_absolute()
    ):
        raise ValueError("invalid confined input path")
    result = _plain_path(root / relative)
    if not result.is_relative_to(root):
        raise ValueError("input path escapes root")
    return result


def _ref(value: dict) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) != {"path", "sha256"}
        or not isinstance(value["sha256"], str)
        or not re.fullmatch("[0-9a-f]{64}", value["sha256"])
    ):
        raise ValueError("invalid file reference")
    return value


def _read(root: Path, ref: dict, limit=MAX_METADATA_BYTES):
    ref = _ref(ref)
    return _json(_read_bytes(_path(root, ref["path"]), ref["sha256"], limit=limit))


def _indices(values, size, label):
    if (
        not isinstance(values, list)
        or not 1 <= len(values) <= 64
        or any(type(v) is not int or not 0 <= v < size for v in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError(f"invalid {label} indices")
    return values


def _budget(value, maximum):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError("invalid context byte budget")
    return value


def _implementations():
    return {
        name: hashlib.sha256(_read_bytes(Path(path), limit=MAX_METADATA_BYTES)).hexdigest()
        for name, path in {
            "context_supplement": __file__,
            "vocabulary_sources_v1": vocabulary_sources.__file__,
            "vocabulary_curation_v1": vocabulary_curation.__file__,
        }.items()
    }


def _reconstruct(*, root, specification, specification_sha256, max_source_bytes, max_output_bytes):
    root = _plain_path(root)
    _budget(max_source_bytes, MAX_SOURCE_BYTES)
    _budget(max_output_bytes, MAX_OUTPUT_BYTES)
    spec = _read(
        root, {"path": str(specification), "sha256": specification_sha256}, MAX_OUTPUT_BYTES
    )
    if (
        not isinstance(spec, dict)
        or set(spec) != _REF_KEYS | {"schema_version", "request_indices"}
        or spec["schema_version"] != "wiktextract-context-input-1"
    ):
        raise ValueError("unsupported context input contract")
    for key in _REF_KEYS:
        _path(root, _ref(spec[key])["path"])
    prep = _read(root, spec["source_preparation"])
    _manifest_check(prep)
    if prep.get("dictionary_format") != "wiktextract":
        raise ValueError("only Wiktextract source preparations are supported")
    if (
        prep["dictionary_sha256"] != spec["source"]["sha256"]
        or prep["files"]["candidates.jsonl"] != spec["candidates"]["sha256"]
        or _path(root, spec["source_preparation"]["path"]).parent / "candidates.jsonl"
        != _path(root, spec["candidates"]["path"])
    ):
        raise ValueError("source preparation binding drift")
    if any(not spec[k]["path"].endswith(".jsonl") for k in ("source", "candidates")):
        raise ValueError("only uncompressed Wiktextract JSONL is supported")
    packet = _read(root, spec["packet"])
    if (
        packet.get("schema_version") != "vocabulary-selection-packet-1"
        or packet.get("generation_status") != "deferred_by_user"
        or packet.get("packet_sha256")
        != canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
    ):
        raise ValueError("packet binding drift")
    manifest = _read(root, spec["request_manifest"])
    if (
        set(manifest) != {"kind", "binding_sha256", "files", "production_eligible"}
        or manifest["kind"] != "vocabulary-session-request"
        or manifest["production_eligible"] is not False
        or set(manifest["files"]) != {"request.json", "messages.json", "response-schema.json"}
    ):
        raise ValueError("unsupported frozen request manifest")
    directory = PurePosixPath(spec["request_manifest"]["path"]).parent
    request_files = {
        name: {"path": str(directory / name), "sha256": digest}
        for name, digest in manifest["files"].items()
    }
    request = _read(root, request_files["request.json"])
    messages = _read(root, request_files["messages.json"])
    schema = _read(root, request_files["response-schema.json"])
    if (
        request.get("schema_version") != "vocabulary-session-request-1"
        or canonical_sha256(request) != manifest["binding_sha256"]
        or request.get("packet_sha256") != spec["packet"]["sha256"]
        or request.get("generation_status") != "deferred_by_user"
        or request.get("language") != packet.get("language")
        or request.get("language") != prep.get("language")
    ):
        raise ValueError("frozen request binding drift")
    source_indices = _indices(request["source_indices"], len(packet["groups"]), "packet")
    if (
        request["groups"] != [packet["groups"][i] for i in source_indices]
        or request["messages"] != messages
        or messages != selection_messages(request["language"], request["groups"])
        or request["response_schema"] != schema
        or schema != SelectionResponse.model_json_schema()
    ):
        raise ValueError("request group/message/schema drift")
    selected = _indices(spec["request_indices"], len(request["groups"]), "request")
    targets = {}
    for i in selected:
        group = request["groups"][i]
        if not group.get("review_unit_id") or not group["sense_candidates"]:
            raise ValueError("missing frozen sense identity")
        for j, sense in enumerate(group["sense_candidates"]):
            cid = sense["candidate_id"]
            if cid in targets:
                raise ValueError("duplicate candidate in requested units")
            targets[cid] = (i, j, group, sense)
    if not 1 <= len(targets) <= POLICY["limits"]["selected_senses"]:
        raise ValueError("selected sense count exceeds limit")
    candidates = {}
    candidate_bytes = 0
    for line in _verified_lines(
        _path(root, spec["candidates"]["path"]), spec["candidates"]["sha256"], max_source_bytes
    ):
        if not line.strip():
            continue
        row = _json(line.encode("utf-8"))
        if row.get("candidate_id") not in targets:
            continue
        cid = row["candidate_id"]
        if cid in candidates:
            raise ValueError("duplicate source candidate")
        candidate_bytes += len(line.encode("utf-8"))
        if candidate_bytes > MAX_METADATA_BYTES:
            raise ValueError("selected candidate byte limit exceeded")
        candidates[cid] = row
    if candidates.keys() != targets.keys():
        raise ValueError("request candidate absent from source preparation")
    record_hashes = {c["source_record_sha256"] for c in candidates.values()}
    recovered = {}
    matched_records = set()
    context_bytes = 0
    for physical_line, line in enumerate(
        _verified_lines(
            _path(root, spec["source"]["path"]), spec["source"]["sha256"], max_source_bytes
        ),
        1,
    ):
        if not line.strip():
            continue
        record = _json(line.encode("utf-8"))
        if record.get("lang_code") != request["language"]:
            continue
        record_hash = canonical_sha256(record)
        if record_hash not in record_hashes:
            continue
        if record_hash in matched_records:
            raise ValueError("ambiguous duplicate raw record locator")
        matched_records.add(record_hash)
        for original_index, candidate in wiktextract_record_candidates(
            record, language=request["language"]
        ):
            cid = candidate.candidate_id
            if cid not in candidates:
                continue
            normalized = candidate.model_dump(mode="json")
            if normalized != candidates[cid]:
                raise ValueError("raw source candidate reconstruction mismatch")
            i, j, group, sense = targets[cid]
            if (
                group["lemma"] != normalized["lemma"]
                or group["pos"] != normalized["pos"]
                or any(
                    sense.get(k) != normalized[k]
                    for k in (
                        "candidate_id",
                        "source_record_sha256",
                        "source_sense_ids",
                        "glosses",
                        "tags",
                        "stable_sense_id",
                    )
                )
            ):
                raise ValueError("packet sense/source candidate mismatch")
            raw_sense = record["senses"][original_index]
            unhandled_sense = sorted(set(raw_sense) - set(SENSE_FIELDS))
            unhandled_entry = sorted(
                set(record) - set(ENTRY_FIELDS) - {"senses", "word", "lang", "lang_code", "pos"}
            )
            row = {
                "candidate_id": cid,
                "candidate_sha256": canonical_sha256(normalized),
                "source_record_sha256": record_hash,
                "original_source_sense_index": original_index,
                "physical_line": physical_line,
                "line_sha256": hashlib.sha256(line.rstrip("\r\n").encode("utf-8")).hexdigest(),
                "request_local_index": i,
                "packet_group_index": source_indices[i],
                "request_sense_index": j,
                "entry_id": group["entry_id"],
                "review_unit_id": group["review_unit_id"],
                "untrusted_context": {
                    "entry": {k: record[k] for k in ENTRY_FIELDS if k in record},
                    "sense": {k: raw_sense[k] for k in SENSE_FIELDS if k in raw_sense},
                },
                "unhandled_sense_fields": unhandled_sense,
                "unhandled_entry_fields": unhandled_entry,
                "completeness": "complete_for_policy_fields_with_unhandled_fields"
                if unhandled_sense or unhandled_entry
                else "complete_for_policy_fields",
            }
            row["context_sha256"] = canonical_sha256(row["untrusted_context"])
            context_bytes += len(json_bytes(row))
            if context_bytes > max_output_bytes:
                raise ValueError("context output byte limit exceeded; nothing truncated")
            recovered[cid] = row
    if recovered.keys() != targets.keys():
        raise ValueError("raw source sense missing or unsupported")
    document = {
        "schema_version": _KIND,
        "policy_sha256": canonical_sha256(POLICY),
        "implementation_sha256": _implementations(),
        "specification": {"path": str(specification), "sha256": specification_sha256},
        "inputs": spec,
        "request_files": request_files,
        "request_binding_sha256": manifest["binding_sha256"],
        "packet_canonical_sha256": packet["packet_sha256"],
        "language": request["language"],
        "status": "context_available_for_review_only",
        "generation_status": "deferred_by_user",
        "senses": [recovered[cid] for cid in targets],
    }
    files = {"context.json": json_bytes(document), "policy.json": json_bytes(POLICY)}
    if sum(map(len, files.values())) > max_output_bytes:
        raise ValueError("context output byte limit exceeded; nothing truncated")
    return document, files


def create_context_supplement(
    *,
    root: Path,
    specification: Path,
    specification_sha256: str,
    output: Path,
    max_source_bytes: int = MAX_SOURCE_BYTES,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
) -> dict:
    """Create a new immutable supplement; input/format/budget drift fails closed."""
    output = _plain_path(output)
    if output.exists():
        raise ValueError("supplement output already exists")
    document, files = _reconstruct(
        root=root,
        specification=specification,
        specification_sha256=specification_sha256,
        max_source_bytes=max_source_bytes,
        max_output_bytes=max_output_bytes,
    )
    manifest = persist_artifact(output, kind=_KIND, binding=canonical_sha256(document), files=files)
    return {
        "status": "context_available_for_review_only",
        "sense_count": len(document["senses"]),
        "manifest_sha256": hashlib.sha256(json_bytes(manifest)).hexdigest(),
        "policy_sha256": canonical_sha256(POLICY),
    }


def validate_context_supplement(
    *,
    root: Path,
    specification: Path,
    specification_sha256: str,
    supplement: Path,
    manifest_sha256: str,
    max_source_bytes: int = MAX_SOURCE_BYTES,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
) -> dict:
    """Read-only replay from externally pinned inputs, never trusting completeness flags."""
    supplement = _plain_path(supplement)
    _budget(max_output_bytes, MAX_OUTPUT_BYTES)
    manifest = _json(
        _read_bytes(supplement / "manifest.json", manifest_sha256, limit=MAX_OUTPUT_BYTES)
    )
    if set(p.name for p in supplement.iterdir()) != {
        "manifest.json",
        "context.json",
        "policy.json",
    }:
        raise ValueError("supplement file inventory drift")
    document, expected_files = _reconstruct(
        root=root,
        specification=specification,
        specification_sha256=specification_sha256,
        max_source_bytes=max_source_bytes,
        max_output_bytes=max_output_bytes,
    )
    expected_manifest = {
        "kind": _KIND,
        "binding_sha256": canonical_sha256(document),
        "files": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(expected_files.items())},
        "production_eligible": False,
    }
    if manifest != expected_manifest:
        raise ValueError("supplement source/policy/content binding drift")
    for name, expected in expected_files.items():
        if (
            _read_bytes(supplement / name, manifest["files"][name], limit=max_output_bytes)
            != expected
        ):
            raise ValueError("supplement literal content drift")
    return {
        "status": "context_available_for_review_only",
        "sense_count": len(document["senses"]),
        "manifest_sha256": manifest_sha256,
        "policy_sha256": canonical_sha256(POLICY),
    }
