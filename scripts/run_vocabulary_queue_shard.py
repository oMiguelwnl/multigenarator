"""Execute a hash-bound isolated vocabulary review queue and consolidate it."""

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_queue_shard_execution import execute_shard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("manifest", "policy"):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("manifest-sha256", "group", "policy-sha256", "implementation-sha256"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--workers", type=int, default=3)
    try:
        result = execute_shard(**vars(parser.parse_args()))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Shard execution stopped: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "consolidated" else 2


if __name__ == "__main__":
    raise SystemExit(main())
