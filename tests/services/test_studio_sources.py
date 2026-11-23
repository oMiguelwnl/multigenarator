import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from multilang.studio.sources import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def preview(client, content, **params):
    query = {"language": "en", "extension": "txt", "kind": "word-list", **params}
    return client.post(
        "/studio-api/sources/preview",
        params=query,
        content=content,
        headers={"Content-Type": "application/octet-stream"},
    )


def test_list_uses_cli_normalization_order_and_warnings(client):
    response = preview(client, 'Cat;dog\ncat\n\n"take care"'.encode())
    assert response.status_code == 200
    result = response.json()
    assert result["items"] == ["Cat", "dog", "take care"]
    assert result["candidate_count"] == 3
    assert result["duplicates"] == 1
    assert result["ignored"] == 1


def test_kindle_html_uses_selected_input_mode(client):
    data = b'<div class="noteText">take care</div><div class="noteText">the sky</div>'
    params = {"kind": "highlights", "extension": "html"}
    text = preview(client, data, **params).json()
    assert text["highlight_count"] == 2
    assert text["excerpts"] == ["take care", "the sky"]
    assert set(text["items"]) == {"take", "care", "sky"}
    vocab = preview(client, data, mode="vocabulary", **params).json()
    assert vocab["items"] == ["take care", "the sky"]


def test_large_preview_counts_all_candidates_but_limits_examples(client):
    data = "\n".join(f"word{i}" for i in range(153)).encode()
    result = preview(client, data).json()
    assert result["candidate_count"] == 153
    assert 0 < len(result["items"]) < 153


def test_preview_rejects_files_over_the_same_limit_as_the_attachment(client):
    assert preview(client, b"x" * 5_000_001).status_code == 413


def test_kindle_txt_preview_omits_book_metadata(client):
    data = b"Book title\n- Your Highlight on Location 123\n\ntake care\n==========\n"
    response = preview(client, data, kind="highlights", mode="vocabulary")
    assert response.json()["excerpts"] == response.json()["items"] == ["take care"]


@pytest.mark.parametrize(("data", "params"), [
    (b"\xff", {}), (b"bad\x00file", {}), (b"  ", {}),
    (b"sun", {"extension": "html"}),
    (b"<p>private text</p>", {"kind": "highlights", "extension": "html"}),
    (b"the", {"kind": "highlights"}),
    (b"private text", {"kind": "highlights", "language": "ko", "mode": "vocabulary"}),
])
def test_rejects_unusable_input_without_echoing_private_content(client, data, params):
    response = preview(client, data, **params)
    assert response.status_code == 422
    assert "private" not in response.text


def test_korean_highlights_return_counts_only(client, monkeypatch):
    from types import SimpleNamespace

    from multilang.studio import sources

    monkeypatch.setattr(sources, "_korean_resolver", lambda: object())
    monkeypatch.setattr(sources, "extract_highlight_candidates", lambda *args, **kwargs:
        SimpleNamespace(candidates=[SimpleNamespace(display_form="private")], errors=[],
                        duplicate_count=0, rejected_token_count=0))
    response = preview(client, b"private excerpt", kind="highlights", language="ko")
    assert response.status_code == 200
    assert response.json()["items"] == response.json()["excerpts"] == []
    assert response.json()["candidate_count"] == 1
    assert "private" not in response.text

