#!/usr/bin/env python3
"""Offline Korean source-row proposals; no providers or deck generation."""

import argparse
import json
from pathlib import Path

from multilang.services.korean_registry_review import (
    import_registry_response,
    next_registry_request,
    prepare_registry_review,
    read_response,
    registry_review_status,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    prepare = commands.add_parser("prepare")
    for name in ("registry", "bundle", "supplement"):
        prepare.add_argument("--" + name, type=Path, required=True)
        prepare.add_argument("--" + name + "-manifest-sha256", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--max-units", type=int, default=256)
    prepare.add_argument("--max-evidence-bytes", type=int, default=256000)
    for name in ("next", "import", "status"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--plan-sha256", required=True)
        command.add_argument("--work", type=Path, required=True)
        if name != "status":
            command.add_argument("--task-id", required=True)
        if name == "next":
            command.add_argument("--batch-size", type=int, default=8)
        if name == "import":
            command.add_argument("--request", type=Path, required=True)
            command.add_argument("--request-sha256", required=True)
            command.add_argument("--response", type=Path, required=True)
            command.add_argument("--context-id", required=True)
            command.add_argument("--supersedes", type=Path)
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    try:
        if operation == "import":
            args["response"] = read_response(args["response"])
        function = {
            "prepare": prepare_registry_review,
            "next": next_registry_request,
            "import": import_registry_response,
            "status": registry_review_status,
        }[operation]
        result = function(**args)
    except (ValueError, OSError, KeyError, TypeError):
        parser.error("offline review validation failed; no source content is displayed")
    allowed = {
        "status",
        "plan",
        "plan_sha256",
        "pending_units",
        "existing_aliases",
        "task_count",
        "task_id",
        "request",
        "request_sha256",
        "unit_count",
        "review",
        "review_sha256",
        "counts_observed",
        "total_units",
        "reviewed_units",
        "unreviewed_units",
        "uncertain_units",
        "include_proposals",
        "exclude_proposals",
        "first_pass_complete_tasks",
        "production_eligible",
    }
    print(
        json.dumps(
            {k: v for k, v in result.items() if k in allowed}, ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
