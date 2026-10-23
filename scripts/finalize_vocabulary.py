"""Consolidate explicitly pinned lexical snapshots; does not generate decks."""

import argparse
import hashlib
import json
from pathlib import Path

from multilang.services.vocabulary_finalization import _read, publish_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = _read(args.inputs, args.inputs_sha256)
    inputs = json.loads(raw)
    result = publish_inventory(inputs=inputs, output=args.output)
    print(
        json.dumps(
            dict(
                languages=len(result["languages"]),
                output=str(args.output),
                manifest_sha256=hashlib.sha256(
                    (args.output / "manifest.json").read_bytes()
                ).hexdigest(),
                generation_status=result["generation_status"],
            )
        )
    )


if __name__ == "__main__":
    main()
