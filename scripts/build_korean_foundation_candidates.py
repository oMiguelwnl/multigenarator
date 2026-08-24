"""Build and validate fixed Korean foundation curation drafts."""

from __future__ import annotations

import argparse


_BATCH_IDS = (
    "hangul-h0-h3",
    "hangul-h4-h7",
    "hangul-h8-h10",
    "pronunciation-p0-p4",
    "pronunciation-p5-p9",
    "pronunciation-p10-p13",
)
_FAMILIES = ("hangul", "pronunciation")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or validate fixed Korean foundation curation drafts."
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("project-batch", "validate-batch"):
        command = commands.add_parser(operation)
        command.add_argument("batch_id", choices=_BATCH_IDS)
    family = commands.add_parser("assemble-family")
    family.add_argument("family", choices=_FAMILIES)
    commands.add_parser("assemble")
    commands.add_parser("validate-drafts")
    return parser


def main() -> None:
    args = _parser().parse_args()
    from multilang.services import korean_foundation_ai_curation as service

    if args.operation == "project-batch":
        result = service.write_korean_foundation_batch_projection(args.batch_id)
    elif args.operation == "validate-batch":
        result = service.validate_korean_foundation_batch_draft(args.batch_id)
    elif args.operation == "assemble-family":
        result = service.write_korean_foundation_family_draft(args.family)
    elif args.operation == "assemble":
        result = service.write_korean_foundation_draft_manifest()
    else:
        result = service.validate_korean_foundation_drafts()
    print(result.content_hash)


if __name__ == "__main__":
    main()
