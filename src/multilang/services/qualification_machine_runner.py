"""Immutable offline machine review artifacts and explicit, bounded API runs."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.services.qualification_review import _json
from multilang.services.vocabulary_review import _plain_path, _read_bytes

MAX_BYTES = 128 * 1024**2


def json_bytes(value) -> bytes:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    data = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    if len(data) > MAX_BYTES:
        raise ValueError("machine artifact exceeds byte limit")
    return data


def read_json(path: Path, sha256: str | None = None):
    return _json(_read_bytes(path, sha256, limit=MAX_BYTES))


@contextmanager
def _locked(output: Path):
    output = _plain_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = _plain_path(output.parent / ("." + output.name + ".lock"))
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another machine operation holds this output lock") from None
        yield output
    finally:
        os.close(fd)


def verify_artifact(output: Path, *, kind: str | None = None) -> dict:
    output = _plain_path(output)
    manifest = read_json(output / "manifest.json")
    if not isinstance(manifest, dict) or set(manifest) != {
        "kind",
        "binding_sha256",
        "files",
        "production_eligible",
    }:
        raise ValueError("invalid machine artifact manifest")
    if manifest["production_eligible"] is not False or (kind and manifest["kind"] != kind):
        raise ValueError("machine artifact kind or authority drift")
    files = manifest["files"]
    if not isinstance(files, dict) or not 1 <= len(files) <= 16:
        raise ValueError("invalid machine artifact file inventory")
    total = 0
    for name, digest in files.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or name in {".", "..", "manifest.json"}
        ):
            raise ValueError("invalid machine artifact path")
        total += len(_read_bytes(output / name, digest, limit=MAX_BYTES))
        if total > MAX_BYTES:
            raise ValueError("aggregate machine artifact exceeds limit")
    if {p.name for p in output.iterdir()} != {*files, "manifest.json"}:
        raise ValueError("machine artifact file inventory drift")
    return manifest


def persist_artifact(output: Path, *, kind: str, binding: str, files: dict[str, bytes]) -> dict:
    if sum(map(len, files.values())) > MAX_BYTES:
        raise ValueError("aggregate machine artifact exceeds limit")
    if any(Path(name).name != name or name in {".", "..", "manifest.json"} for name in files):
        raise ValueError("invalid machine artifact path")
    manifest = {
        "kind": kind,
        "binding_sha256": binding,
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
        "production_eligible": False,
    }
    with _locked(output) as root:
        if root.exists():
            if verify_artifact(root, kind=kind) != manifest:
                raise ValueError("machine artifact input/output drift")
            return manifest
        with TemporaryDirectory(prefix=".machine-", dir=root.parent) as temporary:
            staging = Path(temporary) / "artifact"
            staging.mkdir(mode=0o700)
            for name, data in {**files, "manifest.json": json_bytes(manifest)}.items():
                with (staging / name).open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
            os.rename(staging, root)
    return manifest


def export_machine_request(request, output: Path) -> dict:
    from multilang.services.qualification_machine import MachineReviewRequest

    request = MachineReviewRequest.model_validate(request.model_dump(mode="json"))
    return persist_artifact(
        output,
        kind="machine-request",
        binding=request.request_sha256,
        files={
            "request.json": json_bytes(request),
            "messages.json": json_bytes(request.messages),
            "response-schema.json": json_bytes(request.response_schema),
        },
    )


def import_machine_response(request, response: bytes, *, metadata, output: Path):
    from multilang.services.qualification_machine import accept_machine_response

    if len(response) > MAX_BYTES:
        raise ValueError("machine response exceeds byte limit")
    submission = accept_machine_response(request, _json(response), metadata=metadata)
    persist_artifact(
        output,
        kind="machine-submission",
        binding=submission.submission_sha256,
        files={"submission.json": json_bytes(submission)},
    )
    return submission


def load_machine_submission(output: Path):
    from multilang.services.qualification_machine import (
        MachineReviewSubmission,
        accept_machine_response,
    )

    manifest = verify_artifact(output, kind="machine-submission")
    if set(manifest["files"]) != {"submission.json"}:
        raise ValueError("machine submission inventory drift")
    submission = MachineReviewSubmission.model_validate(read_json(output / "submission.json"))
    replay = accept_machine_response(
        submission.request, submission.response, metadata=submission.metadata
    )
    if replay != submission or submission.submission_sha256 != manifest["binding_sha256"]:
        raise ValueError("machine submission replay drift")
    return submission


def _write_once(path: Path, value):
    with _plain_path(path).open("xb") as handle:
        handle.write(json_bytes(value))
        handle.flush()
        os.fsync(handle.fileno())


def machine_preflight(request, *, transport, budget) -> dict:
    """Reservation is a conservative spending ceiling, not a live tariff quote."""
    tokens = transport.input_token_upper_bound(
        messages=request.messages, response_schema=request.response_schema
    )
    reservation = budget.reserve(
        input_tokens=tokens, max_output_tokens=transport.limits.max_output_tokens
    )
    return {
        "request_sha256": request.request_sha256,
        "input_token_upper_bound": tokens,
        "max_output_tokens": transport.limits.max_output_tokens,
        "reservation": reservation.model_dump(mode="json"),
        "provider_calls_executed": 0,
    }


def run_machine_review(
    request, *, transport, budget, output: Path, provider_calls_enabled: bool = False
):
    """One attempt per invocation. Resume retains every pre-call reservation.

    A timeout or process crash can still have incurred provider cost, so no
    reservation is refunded. A completed artifact is replayed without a call.
    API state is local bookkeeping, not a cryptographic billing attestation.
    """
    from multilang.services.qualification_ai_transport import MachineRunBudget
    from multilang.services.qualification_machine import (
        MachineExecutionMetadata,
        MachineReviewRequest,
    )

    request = MachineReviewRequest.model_validate(request.model_dump(mode="json"))
    budget = MachineRunBudget.model_validate(budget.model_dump(mode="json"))
    if request.actor.execution_surface != "api" or request.actor.model != transport.model:
        raise ValueError("API execution must match the declared actor model and surface")
    binding = {
        "request": request.model_dump(mode="json"),
        "budget": budget.model_dump(mode="json"),
        "model": transport.model,
        "limits": transport.limits.model_dump(mode="json"),
    }
    with _locked(output) as root:
        if root.exists():
            if read_json(root / "run.json") != binding:
                raise ValueError("machine run configuration drift")
        else:
            root.mkdir(mode=0o700)
            _write_once(root / "run.json", binding)
        tokens = transport.input_token_upper_bound(
            messages=request.messages, response_schema=request.response_schema
        )
        attempts = sorted(root.glob("attempt-*.json"))
        if len(attempts) > budget.max_calls:
            raise ValueError("machine run attempt inventory drift")
        cost = Decimal(0)
        for index, path in enumerate(attempts, 1):
            if path.name != f"attempt-{index:06d}.json":
                raise ValueError("machine run attempt sequence drift")
            reservation = budget.reserve(
                input_tokens=tokens,
                max_output_tokens=transport.limits.max_output_tokens,
                reserved_calls=index - 1,
                reserved_cost=cost,
            )
            if read_json(path) != reservation.model_dump(mode="json"):
                raise ValueError("machine run reservation drift")
            cost = reservation.cumulative_reserved_cost
        if (root / "result").exists():
            result = load_machine_submission(root / "result")
            if not attempts or result.request != request:
                raise ValueError("machine run result binding drift")
            return result
        if not provider_calls_enabled:
            raise ValueError("provider calls must be explicitly enabled")
        reservation = budget.reserve(
            input_tokens=tokens,
            max_output_tokens=transport.limits.max_output_tokens,
            reserved_calls=len(attempts),
            reserved_cost=cost,
        )
        _write_once(root / f"attempt-{reservation.call_number:06d}.json", reservation)
        try:
            response = transport.complete(
                messages=request.messages, response_schema=request.response_schema
            )
            metadata = MachineExecutionMetadata(
                executed_at=datetime.now(UTC),
                response_model=response.response_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )
            result = import_machine_response(
                request, json_bytes(response.payload), metadata=metadata, output=root / "result"
            )
            # Provider metadata is diagnostic; exact response is bound by the submission.
            if hasattr(response, "model_dump"):
                _write_once(root / f"transport-{reservation.call_number:06d}.json", response)
            return result
        except Exception:
            _write_once(
                root / f"failure-{reservation.call_number:06d}.json",
                {"status": "failed_or_unknown", "reservation_retained": True},
            )
            raise ValueError(
                "machine provider attempt failed; reservation retained, inspect inputs before retry"
            ) from None
