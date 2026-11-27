"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=__import__("os").environ.get("CHROMIUM_PATH"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.wait_for_function("document.querySelector('#metadata').textContent.includes('retrieved')")
                page.locator('#earlier').click()
                assert 'Murrayville' in page.locator('#cards').inner_text()
                page.locator('#later').click()
                assert 'Murrayville' not in page.locator('#cards').inner_text()
                page.locator('#dart').click()
                assert 'Ochterloney' in page.locator('#cards').inner_text()
                page.locator('#all').click()
                assert page.locator('#cards article').count() == 12
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                base = f"http://127.0.0.1:{server.server_port}/example-tool/"
                page.goto(base + "records/names/langley-prairie/")
                page.get_by_role("link", name="Match an envelope dated 1911-05-15").click()
                page.wait_for_selector("#cards article")
                assert "Murrayville" in page.locator("#cards").inner_text()
                page.locator("#cards a", has_text="related records").click()
                assert page.url.endswith("/records/offices/station-innes/")
                page.get_by_role("link", name="Open this office in the postmark finder").click()
                page.wait_for_selector("#selected-office:visible")
                assert page.locator("#cards article").count() == 1
                static = browser.new_context(java_script_enabled=False, viewport={"width":390,"height":844})
                view = static.new_page()
                view.goto(base)
                view.get_by_role("link", name="browse postal histories").click()
                view.get_by_role("link", name="Willoughby", exact=True).click()
                assert "1927-12-15" in view.locator("main").inner_text()
                assert view.get_by_text("Previous recorded opening", exact=False).count() == 1
                assert view.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                static.close()
                assert not errors, errors
                browser.close()
            print("Browser checks passed: project subpath, filters, records and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
