"""Private crash-only worker for Korean foundation pointer replacement tests."""

from __future__ import annotations

from importlib import import_module
import os
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    project_root = Path(sys.argv[1]).resolve(strict=True)
    expected_receipt_sha256 = sys.argv[2]
    authorization_sha256 = sys.argv[3]
    api = import_module("multilang.services.korean_foundation_snapshot")
    api._PROJECT_ROOT = project_root
    api._FIXED_PATHS = api._KoreanFoundationSnapshotPaths.from_project_root(
        project_root
    )

    def terminate_before_pointer_replace(
        _temporary_path: Path,
        _pointer_path: Path,
    ) -> None:
        os._exit(91)

    api._replace_active_pointer = terminate_before_pointer_replace
    api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=expected_receipt_sha256,
        authorization_sha256=authorization_sha256,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
