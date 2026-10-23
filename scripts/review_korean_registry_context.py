#!/usr/bin/env python3
"""Offline contextual NIKL overlay; no models, native imports or generation."""

import argparse
import json
from pathlib import Path

from multilang.services.korean_registry_context_review import (
    context_review_status,
    import_context_response,
    next_context_request,
    prepare_context_review,
    read_response,
    validate_context_review,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    prepare = commands.add_parser("prepare")
    for name in ("base-plan", "base-work", "context-spec", "output"):
        prepare.add_argument("--" + name, type=Path, required=True)
    for name in ("base-plan-sha256", "context-spec-sha256"):
        prepare.add_argument("--" + name, required=True)
    for name in ("next", "validate", "import", "status"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--plan-sha256", required=True)
        command.add_argument("--work", type=Path, required=True)
        if name == "next":
            command.add_argument("--task-id", required=True)
            command.add_argument("--batch-size", type=int, default=8)
        if name in {"validate", "import"}:
            command.add_argument("--request", type=Path, required=name == "import")
            command.add_argument("--request-sha256", required=name == "import")
            command.add_argument("--response", type=Path, required=name == "import")
        if name == "import":
            command.add_argument("--context-id", required=True)
            command.add_argument("--supersedes", type=Path)
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    try:
        if args.get("response") is not None:
            args["response"] = read_response(args["response"])
        function = {
            "prepare": prepare_context_review,
            "next": next_context_request,
            "validate": validate_context_review,
            "import": import_context_response,
            "status": context_review_status,
        }[operation]
        result = function(**args)
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        parser.error("offline context validation failed; source content is not displayed")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
