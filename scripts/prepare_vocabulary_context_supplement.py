"""Create or replay a bounded offline Wiktextract context supplement.

Requires externally pinned input hashes. No providers, decisions or review imports.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_context_supplement import (
    MAX_OUTPUT_BYTES,
    MAX_SOURCE_BYTES,
    create_context_supplement,
    validate_context_supplement,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("create", "validate"):
        command = commands.add_parser(operation)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument(
            "--specification",
            type=Path,
            required=True,
            help="Confined relative input JSON path under root",
        )
        command.add_argument("--specification-sha256", required=True)
        command.add_argument("--max-source-bytes", type=int, default=MAX_SOURCE_BYTES)
        command.add_argument("--max-output-bytes", type=int, default=MAX_OUTPUT_BYTES)
        if operation == "create":
            command.add_argument("--output", type=Path, required=True)
        else:
            command.add_argument("--supplement", type=Path, required=True)
            command.add_argument("--manifest-sha256", required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    try:
        result = (
            create_context_supplement if operation == "create" else validate_context_supplement
        )(**args)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError):
        # Exception text can contain source strings; never echo it to a terminal.
        parser.exit(
            2, "Context supplement failed: check pinned inputs, format, paths and byte limits.\n"
        )
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("status", "sense_count", "manifest_sha256", "policy_sha256")
                if k in result
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
