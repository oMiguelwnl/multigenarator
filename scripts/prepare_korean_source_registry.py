"""Prepare every local NIKL source row and candidate alias without generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.korean_source_registry import build_korean_source_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-manifest-sha256", required=True)
    parser.add_argument("--supplement", type=Path, required=True)
    parser.add_argument("--supplement-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    try:
        result = build_korean_source_registry(**vars(parser.parse_args(argv)))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Korean source registry failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
