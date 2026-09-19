"""Deliver exact media beside Korean CSV/TSV artifacts."""

from hashlib import sha256
from pathlib import Path


def copy_korean_tabular_media(media_index: dict[str, Path], output_dir: Path) -> None:
    destination = output_dir / "collection.media"
    if destination.is_symlink():
        raise ValueError("Korean export media destination is unsafe")
    if len(media_index) > 10_000:
        raise ValueError("Korean export media limit exceeded")
    pending = []
    total_bytes = 0
    for tag, source in media_index.items():
        basename = tag.removeprefix("[sound:").removesuffix("]")
        if (tag != f"[sound:{basename}]" or Path(basename).name != basename
                or not basename or any(not (char.isalnum() or char in "._- ") for char in basename)
                or source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= 20_000_000):
            raise ValueError("Korean export media reference is unsafe")
        data = source.read_bytes()
        total_bytes += len(data)
        if len(data) > 20_000_000 or total_bytes > 500_000_000:
            raise ValueError("Korean export media limit exceeded")
        digest = sha256(data).digest()
        target = destination / basename
        if target.is_symlink():
            raise ValueError("Korean export media destination is unsafe")
        if target.exists() and (not target.is_file() or target.stat().st_size != len(data)
                or sha256(target.read_bytes()).digest() != digest):
            raise ValueError("Korean export media destination conflicts with existing bytes")
        pending.append((target, source, len(data), digest))
    destination.mkdir(parents=True, exist_ok=True)
    for target, source, size, digest in pending:
        if destination.is_symlink() or target.is_symlink() or source.is_symlink() or source.stat().st_size != size:
            raise ValueError("Korean export media changed during delivery")
        data = source.read_bytes()
        if sha256(data).digest() != digest:
            raise ValueError("Korean export media changed during delivery")
        if target.exists() and (not target.is_file() or target.stat().st_size != size
                or sha256(target.read_bytes()).digest() != digest):
            raise ValueError("Korean export media destination conflicts with existing bytes")
        if not target.exists():
            with target.open("xb") as output:
                output.write(data)
