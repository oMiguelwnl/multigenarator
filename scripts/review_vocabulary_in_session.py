"""Prepare, import and resume vocabulary reviews in the current assistant session.

This entry point does not load Settings, .env, provider clients or generation jobs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.qualification_machine_runner import read_json
from multilang.services.vocabulary_session_campaign import (
    prepare_next_session_review,
    write_session_progress,
)
from multilang.services.vocabulary_session_review import import_session_review


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("next", "report"):
        command = commands.add_parser(name)
        command.add_argument("--packets", type=Path, required=True)
        command.add_argument("--manifest-sha256", required=True)
        command.add_argument("--requests", type=Path, required=True)
        command.add_argument("--reviews", type=Path, required=True)
        if name == "next":
            command.add_argument("--language", required=True)
            command.add_argument("--batch-size", type=int, default=8)
        else:
            command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("import")
    command.add_argument("--request", type=Path, required=True)
    command.add_argument("--request-sha256", required=True)
    command.add_argument("--response", type=Path, required=True)
    command.add_argument("--context-id", required=True)
    command.add_argument("--supersedes", type=Path, help="Exact prior review to replace, preserving its history")
    command.add_argument("--output", type=Path, required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop("command")
    try:
        if operation == "next":
            result = prepare_next_session_review(**args)
        elif operation == "import":
            args["response"] = read_json(args["response"])
            imported = import_session_review(**args)
            result = {key: imported[key] for key in (
                "language", "request_sha256", "review_status", "provider_calls_executed",
                "production_eligible", "generation_status",
            )}
            result["reviewed_units"] = len(imported["decisions"])
            result["output"] = str(args["output"])
        else:
            report = write_session_progress(**args)
            result = {key: report[key] for key in (
                "total_review_units", "reviewed_units", "unreviewed_units", "provider_calls_executed",
                "review_status", "production_eligible", "generation_status",
            )}
            result["output"] = str(args["output"])
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Session review failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
