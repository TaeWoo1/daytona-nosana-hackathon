"""Runs INSIDE the Daytona sandbox: real Chromium render via Playwright.

usage: python3 render.py <path> <clicks_json> <screenshot_path>
Opens http://localhost:8000<path>, replays the click history (list of texts) in order, then prints
page.inner_text("body") (what a browser shows) and saves a full-page screenshot.
Each call is a fresh browser (stateless); state is reproduced by replaying clicks.
"""
import json
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

path = urllib.parse.urlparse(sys.argv[1]).path or "/"
if not path.startswith("/"):
    path = "/" + path
clicks = json.loads(sys.argv[2])
shot = sys.argv[3]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1100, "height": 800})
    notes = []
    try:
        r = pg.goto("http://localhost:8000" + path, timeout=15000)
        if r and r.status >= 400:
            notes.append(f"HTTP {r.status} for {path}")
        for i, t in enumerate(clicks):
            try:
                pg.get_by_text(t).first.click(timeout=3000)
                pg.wait_for_timeout(300)
                if i == len(clicks) - 1:
                    notes.append(f"clicked: {t!r}")
            except Exception as e:  # noqa: BLE001
                if i == len(clicks) - 1:
                    notes.append(f"click failed for {t!r}: {type(e).__name__}")
        text = pg.inner_text("body")
        pg.screenshot(path=shot, full_page=True)
    except Exception as e:  # noqa: BLE001
        text = f"ERROR: could not open {path}: {type(e).__name__}: {e}"
    b.close()

print("\n".join(notes + [text]))
