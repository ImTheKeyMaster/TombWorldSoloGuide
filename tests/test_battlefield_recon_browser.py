"""Isolated browser smoke test for real photo input and feature gating."""
from pathlib import Path
import struct
import zlib
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def fixture_png():
    w, h = 240, 320
    rows = bytearray()
    for y in range(h):
        rows.append(0)
        for x in range(w):
            v = 220 if (x-65)**2+(y-105)**2 < 8**2 or (x-175)**2+(y-205)**2 < 8**2 else 38
            rows.extend((v, v, v))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(rows))+chunk(b"IEND",b"")

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (390, 1024):
        page = browser.new_page(viewport={"width":width,"height":844})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content('<html data-experimental="off"><body><div data-recon-kind="move" data-recon-actor="Necron Warrior" data-recon-action="Reposition"></div><button id="normal">Movement Complete</button></body></html>')
        page.add_style_tag(path=str(ROOT/"styles.css"))
        page.add_style_tag(path=str(ROOT/"battlefield-recon.css"))
        page.add_script_tag(path=str(ROOT/"battlefield-recon.js"))
        assert page.locator(".recon-panel").count() == 0
        page.evaluate("document.documentElement.dataset.experimental='on'")
        page.locator(".recon-panel summary").click()
        page.locator("input[aria-label='Choose battlefield photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":fixture_png()})
        page.wait_for_function("!document.querySelector('.recon-workspace').hidden && !document.querySelector('[data-recon=scan]').disabled")
        canvas = page.locator("canvas")
        bounds = canvas.bounding_box()
        assert bounds["width"] <= width
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        canvas.click(position={"x":bounds["width"]*.27,"y":bounds["height"]*.33})
        assert "Tap the destination" in page.locator(".recon-status").inner_text()
        canvas.click(position={"x":bounds["width"]*.73,"y":bounds["height"]*.64})
        assert "Marked" in page.locator(".recon-status").inner_text()
        page.get_by_text("Clear marks",exact=True).click()
        assert "Tap the acting NPO" in page.locator(".recon-status").inner_text()
        page.locator("input[aria-label='Choose battlefield photo']").set_input_files({"name":"bad.png","mimeType":"image/png","buffer":b"invalid"})
        page.wait_for_function("document.querySelector('.recon-status').textContent.includes('Could not read')")
        page.locator(".recon-panel summary").click()
        page.wait_for_function("document.querySelector('.recon-workspace').hidden")
        page.evaluate("document.documentElement.dataset.experimental='off'")
        page.wait_for_function("!document.querySelector('.recon-panel')")
        assert page.locator("#normal").is_enabled()
        assert not errors, errors
        page.close()
    browser.close()
print("Battlefield Recon browser checks passed at 390px and 1024px.")
