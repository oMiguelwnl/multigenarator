"""Run a pinned local vocabulary coverage campaign without provider access."""

import argparse
import json
import sys
from pathlib import Path

from multilang.services.vocabulary_coverage_campaign import run_campaign


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_campaign(
        args.config,
        args.config_sha256,
        args.output,
        progress=lambda message: print(message, file=sys.stderr, flush=True),
    )
    print(
        json.dumps(
            {
                "snapshot_id": result["snapshot_id"],
                "languages": len(result["languages"]),
                "corpora": len(result["results"]),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
