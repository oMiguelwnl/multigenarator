"""Run or supervise a versioned review policy on the parent's exact native inventory."""

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_review_policy_queue import (
    run_policy_queue,
    supervise_policy_queue,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "supervise"))
    for name in ("plan", "output", "parent-queue", "policy"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("plan-sha256", "policy-sha256", "parent-binding-sha256", "implementation-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--workers", type=int, default=3)
    args = vars(parser.parse_args(argv))
    mode = args.pop("mode")
    try:
        result = (run_policy_queue if mode == "run" else supervise_policy_queue)(**args)
    except (ValueError, OSError, KeyError, TypeError):
        parser.exit(2, "Policy queue failed validation; inspect bound local artifacts.\n")
    allowed = ("status", "completed_sessions", "selected_sessions", "restarts", "generation_status",
               "requested_model", "reasoning_effort", "production_eligible")
    print(json.dumps({key: result[key] for key in allowed if key in result}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "first_pass_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
