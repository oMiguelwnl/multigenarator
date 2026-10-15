"""Observe an existing vocabulary queue and retry explicit account capacity errors.

No queue configuration changes are accepted: work, repository, session selection,
language exclusions, model, reasoning and concurrency come from its binding.
Create queue-output/STOP or send SIGINT/SIGTERM to stop. Unknown errors block.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_queue_supervisor import supervise_queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True, help="Existing bound queue output")
    parser.add_argument(
        "--supervision", type=Path, required=True, help="Supervisor state and retry history"
    )
    parser.add_argument("--cooldown-seconds", type=float, default=1800)
    parser.add_argument("--poll-seconds", type=float, default=5)
    try:
        result = supervise_queue(**vars(parser.parse_args(argv)))
    except (ValueError, OSError) as error:
        parser.exit(2, f"Queue supervision could not start: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "first_pass_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
