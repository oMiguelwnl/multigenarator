import csv
import io
import json
import sqlite3
from contextlib import closing
from uuid import uuid4
from zipfile import ZipFile

import genanki
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from multilang.studio.results import create_results_router


@pytest.fixture
def studio(tmp_path, request):
    job = uuid4()
    deck = genanki.Deck(1678901234, "Approved export")
    sound = tmp_path / "sample.mp3"
    sound.write_bytes(b"ID3-sample")
    image = tmp_path / "cat.png"
    image.write_bytes(b"stored media")
    models = [
        (["Word", "Definition", "Example Sentence", "Audio", "Image", "Extra"],
         ["猫", "original", 'café, 한글\t"نعم"\r\n次\r語\nкрай', "[sound:sample.mp3]", '<img src="cat.png">', ""]),
        (["JamoOrBlock", "Reading"], ["한", "hán"]),
    ]
    for index, (fields, values) in enumerate(models[:getattr(request, "param", 1)]):
        model = genanki.Model(1234567890 + index, f"Modelo {index}",
                              fields=[{"name": field} for field in fields],
                              templates=[{"name": "Front", "qfmt": "{{" + fields[0] + "}}", "afmt": "answer"}])
        deck.add_note(genanki.Note(model, values))
        if index == 0:
            deck.add_note(genanki.Note(model, ["猫二", "déjà", "", "", "", ""]))
    package = tmp_path / "original.apkg"
    genanki.Package(deck, media_files=[str(sound), str(image)]).write_to_file(package)
    root = tmp_path / "reviews"
    app = FastAPI()
    app.include_router(create_results_router(lambda _: package, review_root=root))
    with TestClient(app) as client:
        yield client, f"/studio-api/productions/{job}", root / str(job), package


def approve(client, base):
    token = client.get(base + "/result").json()["approval"]["revision"]
    response = client.post(base + "/approvals", json={"revision": token})
    assert response.is_success, response.text
    return response.json()["latest"]["snapshotSha256"]


def edit(client, base, value):
    note = next(n for n in client.get(base + "/result").json()["notes"] if n["model"] == "Modelo 0")
    response = client.patch(f"{base}/result/{note['id']}", json={
        "revision": note["revision"], "fields": {"Definition": value},
    })
    assert response.is_success, response.text


def table(data, fmt):
    return list(csv.reader(io.StringIO(data.decode("utf-8"), newline=""), delimiter="," if fmt == "csv" else "\t",
                           strict=True))


@pytest.mark.parametrize("fmt", ["csv", "tsv"])
@pytest.mark.parametrize("studio", [1, 2], indirect=True, ids=["single-model", "mixed-models"])
def test_export_matches_approved_fields_and_survives_reapproval(studio, fmt):
    client, base, directory, package = studio
    edit(client, base, 'edição, "猫" & 한글')
    digest = approve(client, base)
    url = f"{base}/approvals/{digest}/export/{fmt}"
    response = client.get(url)
    assert response.status_code == 200
    assert digest in response.headers["content-disposition"]
    assert directory.name in response.headers["content-disposition"]
    snapshot, = directory.glob("approvals/*/snapshot.apkg")
    with ZipFile(snapshot) as apkg, closing(sqlite3.connect(":memory:")) as db:
        db.deserialize(apkg.read("collection.anki2"))
        models = json.loads(db.execute("select models from col").fetchone()[0])
        expected = {}
        for mid, fields in db.execute("select mid, flds from notes order by id"):
            model = models[str(mid)]
            expected.setdefault(str(mid), [[f["name"] for f in model["flds"]]]).append(fields.split("\x1f"))
    assert "edição," in expected["1234567890"][1][1]
    if len(expected) == 1:
        assert table(response.content, fmt) == expected["1234567890"]
    else:
        with ZipFile(io.BytesIO(response.content)) as bundle:
            manifest = json.loads(bundle.read("manifest.json"))
            assert manifest["snapshotSha256"] == digest and manifest["productionId"] == directory.name
            assert {str(m["id"]) for m in manifest["models"]} == set(expected)
            for item in manifest["models"]:
                mid = str(item["id"])
                assert item["name"] == models[mid]["name"] and item["file"].endswith("." + fmt)
                assert table(bundle.read(item["file"]), fmt) == expected[mid]
    edit(client, base, "posterior")
    assert client.get(url).content == response.content
    newer = approve(client, base)
    assert newer != digest
    assert client.get(f"{base}/approvals/{newer}/export/{fmt}").content != response.content
    package.unlink()
    (directory / "collection.anki2").unlink()
    assert client.get(url).content == response.content


def test_export_requires_approved_intact_snapshot_for_this_production(studio):
    client, base, directory, _ = studio
    def download(hash_value):
        return client.get(f"{base}/approvals/{hash_value}/export/tsv")

    assert download("0" * 64).status_code == 404
    digest = approve(client, base)
    assert client.get(f"/studio-api/productions/{uuid4()}/approvals/{digest}/export/csv").status_code == 404
    snapshot, = directory.glob("approvals/*/snapshot.apkg")
    snapshot.write_bytes(snapshot.read_bytes() + b"changed")
    assert download(digest).status_code == 409
    snapshot.unlink()
    assert download(digest).status_code == 409


def test_export_requires_complete_approval_receipt(studio):
    client, base, directory, _ = studio
    digest = approve(client, base)
    receipt, = directory.glob("approvals/*/receipt.json")
    record = json.loads(receipt.read_bytes())
    del record["operator"]
    receipt.write_text(json.dumps(record), encoding="utf-8")
    assert client.get(f"{base}/approvals/{digest}/export/csv").status_code == 409
