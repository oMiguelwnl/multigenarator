"""Persist local delivery evidence and recheck it before reporting readiness."""

from hashlib import file_digest
from pathlib import Path

from multilang.repositories.transactions import lock_job_for_update, repository_transaction


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 600_000_000:
        raise ValueError("invalid grammar delivery artifact")
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def record_grammar_delivery(session, job, prepared, output_path: Path, *, bootstrap_cards=()) -> None:
    """Only called after the reviewed assembler and exporter both succeed."""
    receipt = {
        "version": 1,
        "bundle_sha256": prepared.bundle_sha256,
        "output_path": str(output_path.resolve()),
        "output_sha256": _digest(output_path),
        "media": {_digest(path): str(path.resolve()) for path in prepared.media_index.values()},
        "bootstrap_cards": [card.model_dump(mode="json") for card in bootstrap_cards],
        "delivered_media": ({str((output_path.parent / "collection.media" / path.name).resolve()): _digest(path)
            for path in prepared.media_index.values()} if output_path.suffix.lower() in {".csv", ".tsv"} else {}),
    }
    with repository_transaction(session):
        job = lock_job_for_update(session, job.id)
        job.resume_state = {**job.resume_state, "korean_grammar_delivery": receipt}


def current_grammar_delivery_items(job, bundle) -> set[str]:
    """A prior export is insufficient when media or the active foundation changed."""
    from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
    from multilang.services.korean_grammar_export import assemble_korean_grammar_export_rows

    receipt = job.resume_state.get("korean_grammar_delivery")
    if not isinstance(receipt, dict) or receipt.get("version") != 1:
        return set()
    try:
        if receipt["bundle_sha256"] != bundle.bundle_sha256:
            return set()
        if _digest(Path(receipt["output_path"])) != receipt["output_sha256"]:
            return set()
        delivered = receipt.get("delivered_media", {})
        if not isinstance(delivered, dict) or len(delivered) > 10_000:
            return set()
        if Path(receipt["output_path"]).suffix.lower() in {".csv", ".tsv"} and not delivered:
            return set()
        if any(_digest(Path(path)) != expected for path, expected in delivered.items()):
            return set()
        media = receipt["media"]
        if not isinstance(media, dict) or len(media) > 10_000:
            return set()
        bootstrap = receipt.get("bootstrap_cards", [])
        if not isinstance(bootstrap, list) or len(bootstrap) > 256:
            return set()
        prepared = assemble_korean_grammar_export_rows(
            bundle=bundle, job_id=job.id, media_paths={digest: Path(path) for digest, path in media.items()},
            bootstrap_cards=tuple(KoreanGrammarBootstrapCard.model_validate(card) for card in bootstrap),
        )
        return {row.identity.item_key for row in prepared.rows}
    except (KeyError, TypeError, ValueError, OSError):
        return set()
