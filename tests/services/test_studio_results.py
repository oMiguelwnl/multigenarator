import base64
import io
import json
import sqlite3
from uuid import UUID
from zipfile import ZipFile

import genanki
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from multilang.domain.exporting import (
    FREQUENCY_EXPORT_CARD_FIELD_NAMES,
    JAPANESE_EXPORT_CARD_FIELD_NAMES,
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
)
from multilang.studio.results import create_results_router

JOB = UUID("02dc94a6-6242-4710-b3d2-cbff8914ec35")
BASE = f"/studio-api/productions/{JOB}"


@pytest.fixture
def review(tmp_path, request):
    clip = tmp_path / "sample.mp3"
    clip.write_bytes(b"ID3\x04sample")
    names, overrides = getattr(request, "param", (
        ["Word", "Definition", "Example Sentence", "sentence_audio", "Image"], {},
    ))
    values = {"Word": "one", "Definition": "first", "Example Sentence": "An example.",
              "sentence_audio": "[sound:sample.mp3]", **overrides}
    model = genanki.Model(1234567890, "Sample", fields=[{"name": name} for name in names],
                          templates=[{"name": "Card", "qfmt": "{{" + names[0] + "}}",
                                      "afmt": "{{" + names[1] + "}}"}])
    deck = genanki.Deck(1678901234, "Sample")
    note = genanki.Note(model, [values.get(name, "") for name in names], guid="stableguid")
    deck.add_note(note)
    package = tmp_path / "original.apkg"
    genanki.Package(deck, media_files=[str(clip)]).write_to_file(package)
    app = FastAPI()
    app.include_router(create_results_router(lambda job: package, review_root=tmp_path / "reviews"))
    with TestClient(app) as client:
        yield client, package


def test_edit_review_and_export_preserve_original_and_identity(review):
    client, original = review
    initial = original.read_bytes()
    result = client.get(f"{BASE}/result").json()
    assert result["total"] == 1
    note = result["notes"][0]
    assert client.get(f"{BASE}/media/0").content == b"ID3\x04sample"
    edit = {"revision": note["revision"], "fields": {"Definition": "a & b"}}
    route = f"{BASE}/result/{note['id']}"
    assert client.patch(route, json=edit).status_code == 200
    assert client.patch(route, json=edit).status_code == 409
    assert client.get(f"{BASE}/result", params={"q": "a & b"}).json()["total"] == 1
    with ZipFile(io.BytesIO(client.get(f"{BASE}/export").content)) as archive:
        assert json.loads(archive.read("media")) == {"0": "sample.mp3"}
        assert archive.read("0") == b"ID3\x04sample"
        with sqlite3.connect(":memory:") as db:
            db.deserialize(archive.read("collection.anki2"))
            guid, fields = db.execute("select guid, flds from notes").fetchone()
            assert guid == "stableguid"
            assert fields.split("\x1f") == ["one", "a &amp; b", "An example.", "[sound:sample.mp3]", ""]
    assert original.read_bytes() == initial


def test_edit_sentence_drops_stale_audio_and_rejects_structural_fields(review):
    client, _ = review
    note = client.get(f"{BASE}/result").json()["notes"][0]
    route = f"{BASE}/result/{note['id']}"
    for name, value in [("Word", "two"), ("Definition", "[sound:forged.mp3]")]:
        assert client.patch(route, json={"revision": note["revision"], "fields": {name: value}}).status_code == 422
    updated = client.patch(route, json={"revision": note["revision"], "fields": {"Example Sentence": "Changed."}})
    assert updated.status_code == 200
    assert not any(f["audio"] for f in updated.json()["fields"])


@pytest.mark.parametrize("review,sentence", [
    ((JAPANESE_EXPORT_CARD_FIELD_NAMES, {"Sentence": "猫です。", "Sentence Furigana": "猫[ねこ]です。"}), "Sentence"),
    ((MANDARIN_EXPORT_CARD_FIELD_NAMES, {"Example Sentence": "<ruby>猫<rt>māo</rt></ruby>"}), "Example Sentence"),
    ((FREQUENCY_EXPORT_CARD_FIELD_NAMES, {
        "Example Sentence": '<span class="semantic-cloze-target">cat</span>',
    }), "Example Sentence"),
], indirect=["review"])
def test_review_protects_sentences_with_dependent_readings_or_cloze(review, sentence):
    client, _ = review
    note = client.get(f"{BASE}/result").json()["notes"][0]
    fields = {field["name"]: field for field in note["fields"]}
    assert not fields[sentence]["editable"]
    response = client.patch(f"{BASE}/result/{note['id']}", json={
        "revision": note["revision"], "fields": {sentence: "Replacement"},
    })
    assert response.status_code == 422
    assert client.get(f"{BASE}/result").json()["notes"][0] == note


@pytest.mark.parametrize("review", [(
    FREQUENCY_EXPORT_CARD_FIELD_NAMES, {"word": "one", "word_audio": "[sound:sample.mp3]"},
)], indirect=True)
def test_only_changed_sentence_loses_its_clip_in_export(review):
    client, _ = review
    note = client.get(f"{BASE}/result").json()["notes"][0]
    route = f"{BASE}/result/{note['id']}"
    for sentence in (" An example. ", "New example."):
        response = client.patch(route, json={
            "revision": note["revision"], "fields": {"Example Sentence": sentence},
        })
        assert response.is_success
        if sentence.strip() == "An example.":
            assert response.json() == note
    with ZipFile(io.BytesIO(client.get(f"{BASE}/export").content)) as archive:
        with sqlite3.connect(":memory:") as db:
            db.deserialize(archive.read("collection.anki2"))
            fields, = db.execute("select flds from notes").fetchone()
            values = dict(zip(FREQUENCY_EXPORT_CARD_FIELD_NAMES, fields.split("\x1f"), strict=True))
            assert values["Example Sentence"] == "New example."
            assert values["sentence_audio"] == ""
            assert values["word_audio"] == "[sound:sample.mp3]"


def test_png_roundtrip_removal_and_stale_revision(review):
    client, original = review
    initial = original.read_bytes()
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=")
    note = client.get(f"{BASE}/result").json()["notes"][0]
    route = f"{BASE}/result/{note['id']}"
    params = {"field": "Image", "revision": note["revision"]}
    headers = {"Content-Type": "image/png"}
    damaged = png[:40] + bytes([png[40] ^ 1]) + png[41:]
    assert client.put(route + "/image", params=params, headers=headers, content=damaged).status_code == 422
    response = client.put(route + "/image", params=params, headers=headers, content=png)
    assert response.status_code == 200
    assert client.get(route + "/image", params={"field": "Image"}).content == png
    with ZipFile(io.BytesIO(client.get(f"{BASE}/export").content)) as archive:
        members = json.loads(archive.read("media"))
        assert archive.read("1") == png
        with sqlite3.connect(":memory:") as db:
            db.deserialize(archive.read("collection.anki2"))
            fields, = db.execute("select flds from notes").fetchone()
            assert fields.split("\x1f")[-1] == f'<img src="{members["1"]}">'
    assert client.patch(route, json={"revision": response.json()["revision"], "fields": {"Image": ""}}).is_success
    assert client.get(route + "/image", params={"field": "Image"}).status_code == 404
    assert client.put(route + "/image", params=params, headers=headers, content=png).status_code == 409
    with ZipFile(io.BytesIO(client.get(f"{BASE}/export").content)) as archive:
        assert list(json.loads(archive.read("media")).values()) == ["sample.mp3"]
    assert original.read_bytes() == initial

