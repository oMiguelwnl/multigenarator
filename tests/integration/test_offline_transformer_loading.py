"""Exercise the real optional loader using a tiny, locally constructed model."""

import hashlib
import socket

import pytest


def test_verified_local_transformer_loads_through_stanza_cache_without_network(tmp_path, monkeypatch):
    pytest.importorskip("stanza")
    transformers = pytest.importorskip("transformers")
    from stanza.models.common.foundation_cache import FoundationCache

    from multilang.services.transformer_artifacts import _base, local_foundation_cache

    repo = "dbmdz/bert-base-turkish-128k-cased"
    revision = "a" * 40
    directory = tmp_path / _base(repo, revision)
    directory.mkdir(parents=True)
    vocabulary = directory / "vocab.txt"
    vocabulary.write_text("[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\nmerhaba\n", encoding="utf-8")
    tokenizer = transformers.BertTokenizerFast(vocab_file=str(vocabulary))
    tokenizer.save_pretrained(directory)
    model = transformers.BertModel(transformers.BertConfig(
        vocab_size=6, hidden_size=8, num_hidden_layers=1, num_attention_heads=2,
        intermediate_size=16, max_position_embeddings=32,
    ))
    model.save_pretrained(directory, safe_serialization=True)
    files = {
        str(path.relative_to(tmp_path)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.iterdir()
    }
    manifest = {
        "model_language": "tr", "processors": {"pos": "imst_bert"}, "files": files,
        "external_dependencies": [{"repo_id": repo, "revision": revision, "files": files}],
    }

    def deny_network(*args, **kwargs):
        raise AssertionError("local transformer attempted network access")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    cache = FoundationCache(local_foundation_cache(manifest, tmp_path))
    loaded_model, loaded_tokenizer = cache.load_bert(repo)
    assert loaded_tokenizer("merhaba")["input_ids"] == [2, 5, 3]
    assert loaded_model(**loaded_tokenizer("merhaba", return_tensors="pt")).last_hidden_state.shape == (
        1, 3, 8
    )
    with pytest.raises(ValueError, match="unverified transformer"):
        cache.load_bert("unverified/model")
