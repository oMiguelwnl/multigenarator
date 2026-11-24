"""Exercise provider, database and production menus in Chromium with offline data."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


DIST = Path(__file__).resolve().parents[1] / "dist"


def main():
    config = {
        "transport": "openrouter", "model": "test/model", "azure_region": "brazilsouth",
        "api_max_output_tokens": 2048,
        "configured": {name: name == "openrouter_api_key" for name in (
            "openai_api_key", "openrouter_api_key", "deepl_api_key", "azure_speech_key", "database_url"
        )},
    }

    def handle(route):
        path = urlsplit(route.request.url).path
        if path == "/studio-api/connections":
            return route.fulfill(json=config)
        if path == "/studio-api/keys/openrouter_api_key/reveal":
            return route.fulfill(json={"value": "fixture-secret"})
        if path == "/studio-api/productions/catalog":
            return route.fulfill(json={"en": ["frequency"]})
        if path == "/studio-api/productions":
            return route.fulfill(json=[])
        if path == "/" or path.startswith("/assets/"):
            return route.fulfill(path=DIST / (path.strip("/") or "index.html"))
        return route.fulfill(status=404, json={"detail": "offline fixture"})

    class Server(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_error(404)

    with HTTPServer(("127.0.0.1", 0), Server) as server, sync_playwright() as playwright:
        Thread(target=server.serve_forever, daemon=True).start()
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", handle)
        page.goto(f"http://127.0.0.1:{server.server_port}/#conexoes")
        expect(page.get_by_text("Banco de dados · PostgreSQL")).to_be_visible()
        key = page.get_by_label("Chave do OpenRouter oculta")
        expect(key).to_have_value("••••••••••••")
        page.get_by_role("button", name="Mostrar Chave do OpenRouter").click()
        expect(page.get_by_label("Chave do OpenRouter visível")).to_have_value("fixture-secret")
        page.get_by_role("button", name="Ocultar Chave do OpenRouter").click()
        expect(key).to_have_value("••••••••••••")
        page.locator(".select-trigger").first.click()
        chosen = page.locator(".select-option", has_text="OpenRouter")
        expect(chosen).to_be_visible()
        colors = chosen.evaluate("e => { const s = getComputedStyle(e); return [s.color, s.backgroundColor]; }")
        assert colors[0] != colors[1], colors
        page.locator(".select-option", has_text="OpenAI").click()
        expect(page.locator(".select-trigger").first).to_contain_text("OpenAI")
        page.locator(".sidebar").get_by_text("Produções").click()
        page.locator(".page-heading .button.primary").click()
        page.locator(".configuration .select-trigger").nth(2).click()
        expect(page.locator(".select-option", has_text="Lista personalizada")).to_be_visible()
        page.locator(".select-option", has_text="Lista personalizada").click()
        expect(page.locator(".configuration .select-trigger").nth(2)).to_contain_text("Lista personalizada")
        assert not errors, errors
        browser.close()
        server.shutdown()
    print("Passed offline Chromium: database field, masked reveal, provider and material menus.")


if __name__ == "__main__":
    main()
