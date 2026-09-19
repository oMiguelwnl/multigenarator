"""Development data must be acquired under its own pinned source provenance."""

import hashlib
import json

import httpx
import pytest


@pytest.mark.parametrize(
    ("language", "repository", "filename"),
    [
        ("de", "UD_German-GSD", "de_gsd-ud-dev.conllu"),
        ("tr", "UD_Turkish-IMST", "tr_imst-ud-dev.conllu"),
    ],
)
def test_development_acquisition_uses_separate_pinned_split(
    tmp_path, language, repository, filename
):
    from multilang.services.vocabulary_acquisition import acquire_source
    from multilang.services.vocabulary_preparation import source_catalog

    data = b"# sent_id = development\n"
    urls = []

    def download(request):
        urls.append(str(request.url))
        return httpx.Response(200, stream=httpx.ByteStream(data))

    with httpx.Client(transport=httpx.MockTransport(download)) as client:
        receipt = acquire_source(language, "corpus-dev", tmp_path, client=client)
    expected = (
        f"https://raw.githubusercontent.com/UniversalDependencies/{repository}/r2.16/{filename}"
    )
    assert urls == [expected]
    assert receipt["source_url"] == expected
    assert receipt["kind"] == "corpus-dev"
    assert receipt["sha256"] == hashlib.sha256(data).hexdigest()
    assert (tmp_path / receipt["file"]).read_bytes() == data
    assert json.loads(next(tmp_path.glob("*.receipt.json")).read_text()) == receipt
    assert receipt["redistribution_approved"] is False
    assert receipt["linguistic_review_approved"] is False
    corpus = source_catalog(language)["corpus"]
    assert expected not in corpus["train_urls"] + corpus["test_urls"]


def test_missing_development_split_is_rejected_before_network_or_files(tmp_path, monkeypatch):
    from multilang.services import vocabulary_acquisition as module

    monkeypatch.setattr(
        module,
        "source_catalog",
        lambda _: {"corpus": {"test_urls": ["https://example.com/test.conllu"]}},
    )
    with pytest.raises(ValueError, match="no catalogued development corpus"):
        module.acquire_source("en", "corpus-dev", tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("index", [-1, 1])
def test_development_acquisition_checks_catalog_index(tmp_path, index):
    from multilang.services.vocabulary_acquisition import acquire_source

    with pytest.raises(ValueError, match="index"):
        acquire_source("de", "corpus-dev", tmp_path / "absent", index=index)
    assert not (tmp_path / "absent").exists()
