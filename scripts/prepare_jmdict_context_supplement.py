"""Create/validate pinned offline JMdict context. No selection, import or provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.jmdict_context_supplement import (
    create_jmdict_context_supplement,
    validate_jmdict_context_supplement,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("create", "validate"):
        command = commands.add_parser(operation)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--specification", type=Path, required=True)
        command.add_argument("--specification-sha256", required=True)
        if operation == "create":
            command.add_argument("--output", type=Path, required=True)
        else:
            command.add_argument("--supplement", type=Path, required=True)
            command.add_argument("--manifest-sha256", required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    try:
        result = (
            create_jmdict_context_supplement
            if operation == "create"
            else validate_jmdict_context_supplement
        )(**args)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError):
        parser.exit(
            2,
            "JMdict context failed: check pinned bindings, supported format, paths and budgets.\n",
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
