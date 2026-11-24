"""Exercise the local deck sales journey with installed Python Playwright and Chrome."""

import argparse
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "frontend/apps/web"
WIDTHS = (1440, 1024, 820, 768, 390, 320)


def check_links(page):
    for href in page.locator("a").evaluate_all("links => links.map(link => link.href)"):
        parsed = urlsplit(href)
        assert parsed.scheme == "file", href
        destination = Path(url2pathname(parsed.path)).resolve()
        assert destination.is_relative_to(WEB) and destination.is_file(), href
        if destination == Path(url2pathname(urlsplit(page.url).path)).resolve() and parsed.fragment:
            assert page.locator(f'[id="{unquote(parsed.fragment)}"]').count() == 1, href


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots", action="store_true")
    args = parser.parse_args()
    output = ROOT / "output/previews/loja-publica/edicao"
    reports = ROOT / "output/reports/deck-product-page"
    reports.mkdir(parents=True, exist_ok=True)
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            for width in WIDTHS:
                page = browser.new_page(
                    viewport={"width": width, "height": 900 if width > 760 else 844},
                    reduced_motion="reduce",
                )
                page.set_default_timeout(3000)
                errors, network, failed = [], [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("requestfailed", lambda request: failed.append(request.url))
                page.on("request", lambda request: network.append(request.url)
                        if request.url.startswith(("http:", "https:")) else None)
                page.goto((WEB / "index.html").as_uri())
                check_links(page)
                page.get_by_role("link", name="Comprar", exact=True).click()
                assert urlsplit(page.url).path.endswith("/decks/ingles-frequencia/index.html")
                expect(page.locator("h1")).to_contain_text("ingl\u00eas")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
                check_links(page)
                for section in ("sobre", "missao", "caracteristicas", "demo", "avaliacoes", "duvidas", "adquirir"):
                    expect(page.locator(f"#{section}")).to_be_visible()
                section_order = page.locator("main > section[id]").evaluate_all(
                    "sections => sections.map(section => section.id)"
                )
                assert section_order == [
                    "sobre", "demo", "caracteristicas", "avaliacoes", "adquirir", "entrega", "duvidas"
                ], section_order
                positions = [page.locator(f"#{section}").bounding_box()["y"] for section in section_order]
                assert positions == sorted(positions), (width, positions)
                expect(page.locator(".product-hero #incluido")).to_be_visible()
                expect(page.locator(".product-hero .hero-offer button")).to_be_disabled()
                expect(page.locator("#sobre #missao")).to_be_visible()
                if width > 760:
                    offer = page.locator(".hero-offer button").bounding_box()
                    assert offer["y"] + offer["height"] <= page.viewport_size["height"], width
                    pitch = page.locator(".product-hero .pitch").bounding_box()
                    sidebar = page.locator(".product-offer").bounding_box()
                    assert sidebar["x"] >= pitch["x"] + pitch["width"], width
                page.keyboard.press("Tab")
                expect(page.locator(".skip")).to_be_focused()
                page.keyboard.press("Enter")
                page.get_by_role("link", name="Experimentar o deck", exact=True).click()
                expect(page.locator("#demo")).to_be_focused()
                demo = page.locator("#demo-flip")
                demo.locator("summary").press("Enter")
                expect(demo).to_have_attribute("open", "")
                expect(demo.locator(".demo-answer")).to_contain_text("Reunir pessoas")
                demo.locator("summary").press("Enter")
                expect(demo).not_to_have_attribute("open", "")
                expect(page.locator("#avaliacoes")).to_contain_text("Ainda sem avalia\u00e7\u00f5es")
                expect(page.locator("#adquirir button")).to_be_disabled()
                for details in page.locator(".faq details").all():
                    details.locator("summary").click()
                    expect(details).to_have_attribute("open", "")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
                    details.locator("summary").click()
                for control in page.locator("a, button, summary").all():
                    assert control.bounding_box()["height"] >= 44, (width, "small control")
                expect(page.locator("script, form, input")).to_have_count(0)
                if args.screenshots and width in (1440, 390):
                    output.mkdir(parents=True, exist_ok=True)
                    page.goto((WEB / "decks/ingles-frequencia/index.html").as_uri())
                    page.screenshot(path=str(output / f"ingles-{width}.png"), full_page=width == 390)
                    if width == 1440:
                        page.screenshot(path=str(reports / "desktop-full.png"), full_page=True)
                        page.locator("#demo").screenshot(path=str(output / "demo-1440.png"))
                        page.locator("#missao").screenshot(path=str(reports / "mission-1440.png"))
                        page.locator("#adquirir").screenshot(path=str(reports / "purchase-1440.png"))
                    else:
                        page.screenshot(path=str(reports / "mobile-top.png"))
                page.get_by_role("link", name="Todos os decks", exact=True).click()
                assert Path(url2pathname(urlsplit(page.url).path)) == WEB / "index.html"
                assert not errors and not network and not failed, (errors, network, failed)
                if args.screenshots and width in (1440, 390):
                    page.goto((WEB / "index.html").as_uri())
                    page.screenshot(
                        path=str(output.parent / f"loja-{width}.png"), full_page=width == 390
                    )
                rows.append({"width": width, "journey": "pass", "keyboard": "pass", "overflow": False})
                page.close()
        finally:
            browser.close()
    (reports / "checks.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"PASS: deck sales journey at {len(rows)} widths, no providers or payment calls.")


if __name__ == "__main__":
    main()
