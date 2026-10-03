"""Run the prepared session queue through the local Codex ChatGPT login."""

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_session_queue import run_queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--session-id", dest="session_ids", action="append")
    parser.add_argument("--exclude-language", dest="exclude_languages", action="append",
                        help="Reserve this language for another session; repeat for multiple languages")
    args = vars(parser.parse_args())
    try:
        result = run_queue(**args)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Queue could not run: {error}\n")
    print(json.dumps({key: value for key, value in result.items() if key not in {"sessions", "session_ids"}},
                     ensure_ascii=False, indent=2))
    return 0 if result["status"] == "first_pass_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
