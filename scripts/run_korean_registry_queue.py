"""Run the isolated Korean campaign serially through the ChatGPT account."""

import argparse
import json
from pathlib import Path

from multilang.services.korean_registry_queue import run_registry_queue


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "work", "output", "repository"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    args = vars(parser.parse_args(argv))
    try:
        result = run_registry_queue(**args)
    except (ValueError, OSError, KeyError, TypeError):
        parser.error("isolated queue validation failed; no source content displayed")
    keys = {
        "status",
        "reason",
        "counts_observed",
        "requested_model",
        "reasoning_effort",
        "workers",
        "attempts_started",
        "generation_status",
        "production_eligible",
    }
    summary = {k: v for k, v in result.items() if k in keys}
    if result.get("counts_observed") and result.get("snapshot"):
        summary.update(
            {
                k: result["snapshot"][k]
                for k in (
                    "total_units",
                    "reviewed_units",
                    "unreviewed_units",
                    "uncertain_units",
                    "include_proposals",
                    "exclude_proposals",
                )
            }
        )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "first_pass_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
