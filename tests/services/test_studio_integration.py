import io
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import genanki
from fastapi.testclient import TestClient

from multilang.studio.productions import ProductionService
from multilang.studio.server import create_studio_app


def test_studio_import_review_and_download_across_restart(tmp_path, monkeypatch):
    job = uuid4()
    production = uuid4()
    origin = "http://127.0.0.1:8765"
    base = f"/studio-api/productions/{production}"
    commands = []

    def offline_cli(self, args, observe):
        commands.append(args[0])
        if args[0] == "generate":
            observe(f"job_id={job}")
            return
        assert args[0] == "export"
        folder = Path(args[args.index("--output-dir") + 1])
        model = genanki.Model(1234567890, "Review", fields=[
            {"name": "Word"}, {"name": "Definition"},
        ], templates=[{"name": "Card", "qfmt": "{{Word}}", "afmt": "{{Definition}}"}])
        deck = genanki.Deck(1234567891, "Fixture")
        deck.add_note(genanki.Note(model, ["one", "first"]))
        genanki.Package(deck).write_to_file(folder / f"{job}.apkg")
        observe("card_count=1")
        observe(f"artifact_path={folder / f'{job}.apkg'}")

    monkeypatch.setattr(ProductionService, "_cli", offline_cli)
    dist = tmp_path / "frontend/dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("studio")

    def client():
        app = create_studio_app(root=tmp_path, token="local")
        return TestClient(app, base_url=origin, headers={"Origin": origin})

    def authenticate(browser):
        assert browser.post("/studio-api/session", json={"token": "local"}).status_code == 200

    source = "one\n" * 10_000
    with client() as browser:
        assert browser.get("/").text == "studio"
        assert browser.get(base + "/result").status_code == 401
        authenticate(browser)
        assert "word-list" in browser.get("/studio-api/productions/catalog").json()["en"]
        preview = browser.post("/studio-api/sources/preview", content=source.encode(),
                               params={"kind": "word-list", "language": "en", "extension": "txt"},
                               headers={"Content-Type": "application/octet-stream"})
        assert preview.json()["candidate_count"] == 1
        response = browser.post("/studio-api/productions", json={
            "id": str(production), "name": "Fixture", "language": "en", "kind": "word-list",
            "supportLanguage": "pt", "sourceText": source, "sourceExtension": "txt",
        })
        assert response.status_code == 202

    with client() as browser:
        authenticate(browser)
        assert commands == ["generate", "export"]
        assert browser.get(base).json()["status"] == "completed"
        note = browser.get(base + "/result").json()["notes"][0]
        edit = {"revision": note["revision"], "fields": {"Definition": "updated"}}
        assert browser.patch(base + "/result/" + note["id"], json=edit).status_code == 200
        assert browser.get(base + "/result", params={"q": "updated"}).json()["total"] == 1
        with ZipFile(io.BytesIO(browser.get(base + "/export").content)) as package:
            assert "collection.anki2" in package.namelist()
