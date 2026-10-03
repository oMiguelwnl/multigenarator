"""Save all vocabulary selections as immutable files and in configured PostgreSQL.

No generation runtime or provider clients are constructed. Export does not read
credentials. Persist/verify read only database configuration through Settings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multilang.services.vocabulary_selection_snapshot import (
    bundle_selection_snapshot,
    export_selection_snapshot,
    migrate_selection_schema,
    persist_selection_snapshot,
    verify_database_snapshot,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    export = commands.add_parser("export")
    export.add_argument("--plan", type=Path, required=True)
    export.add_argument("--plan-sha256", required=True)
    export.add_argument("--work", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--nordic-version", type=Path)
    bundle = commands.add_parser("bundle")
    bundle.add_argument("--snapshot", type=Path, required=True)
    bundle.add_argument("--archive", type=Path, required=True)
    bundle.add_argument("--receipt", type=Path, required=True)
    for name in ("persist", "verify"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--snapshot", type=Path, required=True)
        cmd.add_argument("--receipt", type=Path, required=True)
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    if operation == "export":
        import sys

        result = export_selection_snapshot(
            **args, progress=lambda text: print(text, file=sys.stderr, flush=True)
        )
        print(
            json.dumps(
                {k: result[k] for k in ("snapshot_id", "total_records", "languages")},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    receipt = args["receipt"]
    if receipt.exists():
        parser.error("receipt destination already exists")
    if operation == "bundle":
        result = bundle_selection_snapshot(args["snapshot"], args["archive"])
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import SQLAlchemyError

    from multilang.settings import Settings

    settings = Settings()
    url = make_url(settings.database_url)
    engine = create_engine(
        settings.database_url,
        connect_args={"connect_timeout": 10} if url.get_backend_name() == "postgresql" else {},
    )
    try:
        if operation == "persist":
            migrate_selection_schema(engine)
            imported = persist_selection_snapshot(engine, args["snapshot"])
        else:
            imported = None
        verification = verify_database_snapshot(engine, args["snapshot"])
        result = {
            "import": imported,
            "verification": verification,
            "database_backend": url.get_backend_name(),
            "database_name": url.database,
            "tables": ["vocabulary_selection_snapshots", "vocabulary_selection_units"],
            "generation_executed": False,
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except SQLAlchemyError as exc:
        parser.exit(
            2,
            f"Database operation failed ({type(exc).__name__}); no credentials or payloads logged.\n",
        )
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
