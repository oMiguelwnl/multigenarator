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
        "configured": {name: name in ("openrouter_api_key", "database_url") for name in (
            "openai_api_key", "openrouter_api_key", "deepl_api_key", "azure_speech_key", "database_url"
        )},
        "extra_keys": [],
    }

    def handle(route):
        path = urlsplit(route.request.url).path
        if path == "/studio-api/connections":
            return route.fulfill(json=config)
        if path == "/studio-api/keys/openrouter_api_key/reveal":
            return route.fulfill(json={"value": "fixture-secret"})
        if path == "/studio-api/keys/openrouter_api_key" and route.request.method == "POST":
            payload = route.request.post_data_json
            assert payload == {"label": "Reserva", "value": "backup-fixture"}
            config["extra_keys"] = [{"id": "fixture-id", "provider": "openrouter_api_key", "label": "Reserva", "active": False}]
            return route.fulfill(json=config)
        if path == "/studio-api/keys/openrouter_api_key/fixture-id/activate":
            config["extra_keys"][0]["active"] = True
            return route.fulfill(json=config)
        if path == "/studio-api/keys/openrouter_api_key/primary/activate":
            config["extra_keys"][0]["active"] = False
            return route.fulfill(json=config)
        if path == "/studio-api/keys/openrouter_api_key/fixture-id/reveal":
            return route.fulfill(json={"value": "backup-fixture"})
        if path == "/studio-api/check/openrouter":
            return route.fulfill(json={"message": "Conexão verificada, sem gerar conteúdo."})
        if path == "/studio-api/check/database":
            return route.fulfill(status=400, json={"detail": "Não foi possível conectar ao PostgreSQL."})
        if path == "/studio-api/models":
            return route.fulfill(json=[
                {"id": "budget/model", "name": "Budget Model"},
                {"id": "quality/model", "name": "Quality Model"},
            ])
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
        page.set_default_timeout(3000)
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
        generation = page.locator("fieldset", has=page.locator("legend", has_text="Geração dos cartões"))
        generation.get_by_role("button", name="Adicionar outra chave").click()
        generation.get_by_label("Nome da chave").fill("Reserva")
        generation.get_by_label("Nova chave").fill("backup-fixture")
        generation.get_by_role("button", name="Salvar chave").click()
        expect(generation.get_by_text("Reserva", exact=True)).to_be_visible()
        generation.get_by_role("button", name="Usar esta").click()
        expect(generation.get_by_text("Em uso")).to_be_visible()
        generation.get_by_role("button", name="Mostrar Reserva").click()
        expect(generation.get_by_text("backup-fixture")).to_be_visible()
        generation.get_by_role("button", name="Usar chave principal").click()
        expect(generation.get_by_text("Chave principal em uso.")).to_be_visible()
        generation.get_by_role("button", name="Verificar conexão").click()
        expect(page.get_by_role("dialog", name="Conexão verificada")).to_contain_text("OpenRouter")
        page.get_by_role("dialog").get_by_role("button", name="Fechar").click()
        page.locator("fieldset", has=page.locator("legend", has_text="Banco de dados")).get_by_role("button", name="Verificar conexão").click()
        expect(page.get_by_role("dialog", name="Falha na conexão")).to_contain_text("PostgreSQL")
        position = page.get_by_role("dialog").evaluate("e => { const r = e.getBoundingClientRect(); return { top: r.top, left: r.left, height: r.height, width: r.width, viewport: innerHeight, viewportWidth: innerWidth, scroll: scrollY }; }")
        assert position["scroll"] > 0, position
        assert abs(position["top"] + position["height"] / 2 - position["viewport"] / 2) < 40, position
        assert abs(position["left"] + position["width"] / 2 - position["viewportWidth"] / 2) < 2, position
        close_alignment = page.get_by_role("dialog").get_by_role("button", name="Fechar").evaluate("e => { const b = e.getBoundingClientRect(), i = e.querySelector('svg')?.getBoundingClientRect(); return i && Math.abs((b.left + b.right - i.left - i.right) / 2) < 2 && Math.abs((b.top + b.bottom - i.top - i.bottom) / 2) < 2; }")
        assert close_alignment
        page.get_by_role("dialog").get_by_role("button", name="Fechar").click()
        page.get_by_role("button", name="Escolher modelo").click()
        picker = page.get_by_role("dialog", name="Modelos disponíveis")
        expect(picker.get_by_text("Budget Model")).to_be_visible()
        expect(picker.get_by_text("Quality Model")).to_be_visible()
        picker.get_by_placeholder("Buscar modelo").fill("quality")
        expect(picker.get_by_text("Budget Model")).to_have_count(0)
        picker.get_by_role("button", name="Quality Model (quality/model)").click()
        expect(page.get_by_label("Modelo", exact=True)).to_have_value("quality/model")
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
    print("Passed offline Chromium: multiple keys, centered dialogs, model picker, and menus.")


if __name__ == "__main__":
    main()
