"""Run after npm run build with Python Playwright and Chromium installed."""

import base64
import io
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

DIST = Path(__file__).resolve().parents[1] / "dist"
BASE = "/studio-api/productions/demo"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZQAAAABJRU5ErkJggg==")


def main():
    job = dict(id="demo", name="Offline", language="en", supportLanguage="pt", kind="frequency",
               status="completed", stage="export", updatedAt="", canDownload=True)
    notes = [dict(id=str(i), title=f"Word {i}", model="Words", revision="r1", fields=[
        dict(name="Definition", editable=True, text="initial", audio=["7"]),
        dict(name="Picture", imageField=True, hasImage=False, text="", audio=[]),
    ]) for i in range(1, 27)]
    note = notes[-1]
    audio = io.BytesIO()
    with wave.open(audio, "wb") as stream:
        stream.setparams((1, 1, 8000, 0, "NONE", ""))
        stream.writeframes(bytes([128]) * 800)

    def handle(route):
        url = urlsplit(route.request.url)
        path, query = url.path, parse_qs(url.query)
        if url.hostname != "127.0.0.1":
            raise AssertionError(f"Unexpected host {url.hostname}")
        if path == "/studio-api/productions/catalog":
            return route.fulfill(json={"en": ["frequency"]})
        if path == "/studio-api/productions":
            return route.fulfill(json=[job])
        if path == BASE + "/result":
            rows = [row for row in notes if query.get("q", [""])[0] in row["title"]]
            offset = int(query["offset"][0])
            return route.fulfill(json={"notes": rows[offset:offset + 25], "total": len(rows)})
        if path == BASE + "/result/26":
            payload = route.request.post_data_json
            if payload["fields"].get("Definition") == "unsaved":
                note["revision"] = "external"
            if payload["revision"] != note["revision"]:
                return route.fulfill(status=409, json={"detail": "Outra edição foi salva."})
            for field in note["fields"]:
                if field["name"] in payload["fields"]:
                    field["text"] = payload["fields"][field["name"]]
                    field["hasImage"] = False
            note["revision"] += "x"
            return route.fulfill(json=note)
        if path == BASE + "/result/26/image":
            if route.request.method == "PUT":
                assert query == {"field": ["Picture"], "revision": [note["revision"]]}
                assert route.request.post_data_buffer == PNG
                note["fields"][1]["hasImage"] = True
                note["revision"] += "x"
                return route.fulfill(json=note)
            return route.fulfill(body=PNG, content_type="image/png")
        if path == BASE + "/media/7":
            return route.fulfill(body=audio.getvalue(), content_type="audio/wav")
        if path == BASE + "/export":
            return route.continue_()
        if path == "/" or path.startswith("/assets/"):
            return route.fulfill(path=DIST / (path.strip("/") or "index.html"))
        raise AssertionError(f"Unexpected path {path}")

    class Download(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != BASE + "/export":
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", 'attachment; filename="offline.apkg"')
            self.end_headers()
            self.wfile.write(b"offline fixture")

    with HTTPServer(("127.0.0.1", 0), Download) as server, sync_playwright() as playwright:
        Thread(target=server.serve_forever, daemon=True).start()
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", handle)
        page.goto(f"http://127.0.0.1:{server.server_port}/#resultado/demo")
        page.get_by_role("button", name="Próxima").click()
        expect(page.get_by_role("heading", name="Word 26")).to_be_visible()
        page.get_by_role("button", name="Anterior").click()
        expect(page.get_by_role("heading", name="Word 1", exact=True)).to_be_visible()
        page.get_by_label("Buscar nas notas").fill("Word 26")
        page.get_by_role("button", name="Buscar", exact=True).click()
        expect(page.get_by_text("1 a 1 de 1")).to_be_visible()
        editor = page.get_by_label("Definition", exact=True)
        editor.fill("updated")
        page.get_by_role("button", name="Salvar texto").click()
        expect(editor).to_have_value("updated")
        assert note["fields"][0]["text"] == "updated"
        editor.fill("unsaved")
        page.get_by_role("button", name="Salvar texto").click()
        expect(page.get_by_role("alert")).to_have_text("Outra edição foi salva.")
        expect(editor).to_have_value("unsaved")
        page.get_by_role("button", name="Descartar alterações e recarregar nota").click()
        expect(editor).to_have_value("updated")
        page.locator("audio").evaluate("audio => audio.play()")
        page.get_by_label("Selecionar PNG").set_input_files({"name": "test.png", "mimeType": "image/png", "buffer": PNG})
        image = page.get_by_role("img", name="Imagem de Word 26")
        expect(image).to_be_visible()
        page.wait_for_function("document.querySelector('.review-field img')?.naturalWidth === 1")
        page.get_by_role("button", name="Remover imagem").click()
        expect(image).to_have_count(0)
        assert not note["fields"][1]["hasImage"]
        with page.expect_download() as download:
            page.get_by_role("link", name="Baixar deck").click()
        assert download.value.suggested_filename == "offline.apkg", (download.value.suggested_filename, download.value.failure())
        assert download.value.path().read_bytes() == b"offline fixture"
        assert not errors, errors
        browser.close()
        server.shutdown()
    print("Passed offline result UI: paging, search, edit, conflict, audio, PNG upload/removal and download.")


if __name__ == "__main__":
    main()

