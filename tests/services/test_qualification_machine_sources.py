"""Additional review evidence must bind exact local UTF-8 bytes and character spans."""

import hashlib
import importlib

import pytest


def api():
    return importlib.import_module("multilang.services.qualification_machine_sources")


def reference(tmp_path, text="Conjugação: nós vimos.", **updates):
    path = tmp_path / "source.txt"
    path.write_bytes(text.encode())
    values = dict(
        path=path,
        file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_id="local-grammar",
        record_id="page-1",
        language="pt",
        start=12,
        end=len(text),
    )
    values.update(updates)
    return api().VerifiedReviewExcerpt(**values)


def test_verified_excerpt_uses_unicode_character_offsets_and_file_digest(tmp_path):
    value = reference(tmp_path)
    source = api().load_verified_review_excerpt(value, language="pt")
    assert source.excerpt == "nós vimos."
    assert source.source_sha256 == value.file_sha256
    assert source.record_id == "page-1"


def test_changed_source_bytes_fail_before_review(tmp_path):
    value = reference(tmp_path)
    value.path.write_text("another document")
    with pytest.raises(ValueError, match="checksum"):
        api().load_verified_review_excerpt(value, language="pt")


def test_excerpt_declared_language_must_match_review(tmp_path):
    value = reference(tmp_path)
    with pytest.raises(ValueError, match="language"):
        api().load_verified_review_excerpt(value, language="en")


@pytest.mark.parametrize("start,end", [(0, 1000), (10, 5), (3, 3)])
def test_excerpt_rejects_invalid_source_spans(tmp_path, start, end):
    with pytest.raises(ValueError):
        value = reference(tmp_path, start=start, end=end)
        api().load_verified_review_excerpt(value, language="pt")


@pytest.mark.parametrize("data", [b"\xff", "a\u0301".encode()])
def test_excerpt_rejects_invalid_utf8_and_non_nfc(tmp_path, data):
    value = reference(tmp_path, start=0, end=1)
    value.path.write_bytes(data)
    value = value.model_copy(
        update={
            "file_sha256": hashlib.sha256(data).hexdigest(),
            "end": len(data.decode("utf-8", errors="replace")),
        }
    )
    with pytest.raises(ValueError):
        api().load_verified_review_excerpt(value, language="pt")


def test_excerpt_rejects_symlink_source(tmp_path):
    value = reference(tmp_path)
    link = tmp_path / "link.txt"
    link.symlink_to(value.path)
    with pytest.raises(ValueError, match="symlink"):
        api().load_verified_review_excerpt(value.model_copy(update={"path": link}), language="pt")


def test_excerpt_bounds_file_and_excerpt_sizes(tmp_path):
    with pytest.raises(ValueError):
        value = reference(tmp_path, "a" * 64001, start=0, end=64001)
        api().load_verified_review_excerpt(value, language="pt")
    value = reference(tmp_path, "a" * (16 * 1024**2 + 1), start=0, end=1)
    with pytest.raises(ValueError, match="bounded|limit|size"):
        api().load_verified_review_excerpt(value, language="pt")
