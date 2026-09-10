"""Repro: play the 1Y dataset and confirm playback survives the 15s auto-refresh.

Usage: python tests/repro_playback.py  (expects the app on :4071)
"""
import time
import playwright.sync_api as _  # noqa

with __import__("playwright.sync_api", fromlist=["sync_playwright"]).sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://localhost:4071", wait_until="networkidle")

    page.click('button[data-days="365"]')
    page.wait_for_function("document.getElementById('tl-date-end').textContent !== '—'", timeout=20000)
    print("1Y span:", page.inner_text("#tl-date-start"), "->", page.inner_text("#tl-date-end"))

    page.click("#tl-play")
    t0 = time.time()
    for want in (5, 14, 16, 20, 30):
        time.sleep(max(0, want - (time.time() - t0)))
        d = page.inner_text("#tl-date")
        playing = page.evaluate("!!document.querySelector('#tl-play-icon path[d^=\"M7 5\"]')")
        print(f"t={want:2d}s  date={d:<16} playing={playing}")
    b.close()
