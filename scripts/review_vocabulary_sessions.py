"""Divide, resume and record vocabulary reviews across assistant sessions.

This offline command does not invoke models, read .env or generate cards.
Each work item remains bound to an immutable partition plan and source request.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.qualification_machine_runner import json_bytes, read_json
from multilang.services.vocabulary_review import _plain_path
from multilang.services.vocabulary_session_partitions import (
    import_partition_response,
    next_partition_request,
    partition_progress,
    partition_vocabulary_sessions,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split", help="Create exclusive session assignments")
    split.add_argument("--packets", type=Path, required=True)
    split.add_argument("--manifest-sha256", required=True)
    split.add_argument("--requests", type=Path, required=True)
    split.add_argument("--reviews", type=Path, required=True)
    split.add_argument("--output", type=Path, required=True)
    split.add_argument("--max-units", type=int, default=256)
    split.add_argument("--max-evidence-bytes", type=int, default=256000)
    for operation in ("next", "import", "status"):
        command = commands.add_parser(operation)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--plan-sha256", required=True)
        command.add_argument("--work", type=Path, required=True)
        if operation != "status":
            command.add_argument("--session-id", required=True)
        if operation == "next":
            command.add_argument("--batch-size", type=int, default=8)
        elif operation == "import":
            command.add_argument("--request", type=Path, required=True)
            command.add_argument("--request-sha256", required=True)
            command.add_argument("--response", type=Path, required=True)
            command.add_argument("--context-id", required=True)
            command.add_argument(
                "--supersedes",
                type=Path,
                help="Exact prior review to replace while preserving its history",
            )
        else:
            command.add_argument(
                "--output",
                type=Path,
                help="Save the full status report to a new JSON file; never overwrite",
            )
    args = vars(parser.parse_args(argv))
    operation = args.pop("command")
    try:
        if operation == "split":
            result = partition_vocabulary_sessions(**args)
        elif operation == "next":
            result = next_partition_request(**args)
        elif operation == "import":
            args["response"] = read_json(args["response"])
            result = import_partition_response(**args)
        else:
            output = args.pop("output")
            result = partition_progress(**args)
            if output is not None:
                output = _plain_path(output)
                payload = json_bytes(result)
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as destination:
                    destination.write(payload)
        summary = {
            key: value
            for key, value in result.items()
            if value is None or isinstance(value, (str, int, float, bool))
        }
        if operation == "import":
            summary["reviewed_units"] = len(result["decisions"])
        if operation == "next" and "source_indices" in result:
            summary["source_indices"] = result["source_indices"]
        if operation == "status" and output is not None:
            summary["output"] = str(output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Session partition operation failed: {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
