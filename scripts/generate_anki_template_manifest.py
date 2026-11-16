from __future__ import annotations

import json
from pathlib import Path

from multilang.services.anki_template_preview import build_anki_template_preview_manifest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "frontend" / "apps" / "admin" / "src" / "anki-template-manifest.json"


def main() -> None:
    manifest = build_anki_template_preview_manifest()
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
