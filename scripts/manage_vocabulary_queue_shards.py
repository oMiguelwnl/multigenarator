"""Prepare exclusive native queue copies or reconcile completed decisions offline."""

import argparse
import hashlib
import json
from pathlib import Path

from multilang.services.vocabulary_queue_shards import _json, merge_shard, prepare_shards


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    prepare = modes.add_parser("prepare")
    for name in ("plan", "parent-binding", "groups", "output"):
        prepare.add_argument("--" + name, type=Path, required=True)
    for name in ("plan-sha256", "parent-binding-sha256"):
        prepare.add_argument("--" + name, required=True)
    merge = modes.add_parser("merge")
    for name in ("manifest", "report"):
        merge.add_argument("--" + name, type=Path, required=True)
    for name in ("manifest-sha256", "group"):
        merge.add_argument("--" + name, required=True)
    args = vars(parser.parse_args(argv))
    mode = args.pop("mode")
    if mode == "prepare":
        args["groups"] = _json(args["groups"])
        result = prepare_shards(**args)
        manifest = args["output"] / "manifest.json"
        print(
            json.dumps(
                {
                    "manifest": str(manifest),
                    "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                    "groups": {
                        name: {
                            "work": row["work"],
                            "parent_binding": row["parent_binding"],
                            "parent_binding_sha256": row["parent_binding_sha256"],
                            "sessions": len(row["session_ids"]),
                        }
                        for name, row in result["groups"].items()
                    },
                },
                indent=2,
            )
        )
    else:
        result = merge_shard(**args)
        print(
            json.dumps(
                {
                    "report": str(args["report"]),
                    "group": result["group"],
                    "sessions": len(result["sessions"]),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
