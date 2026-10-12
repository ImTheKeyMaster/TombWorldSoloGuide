"""Validate the coffin-themed iPhone, desktop, and Android PWA artwork."""
import json
import struct
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))

ICONS = {
    "icon-180.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
    "icon-1024.png": 1024,
    "icon-maskable-192.png": 192,
    "icon-maskable-512.png": 512,
}

def test_all_png_dimensions():
    for name, size in ICONS.items():
        data = (ROOT / "Assets" / name).read_bytes()
        assert data[:8] == bytes.fromhex("89504e470d0a1a0a"), name
        assert struct.unpack(">II", data[16:24]) == (size, size), name

def test_manifest_has_regular_and_maskable_icons():
    actual = {(icon["src"], icon["purpose"]) for icon in MANIFEST["icons"]}
    expected = {
        ("Assets/icon-192.png", "any"),
        ("Assets/icon-512.png", "any"),
        ("Assets/icon-maskable-192.png", "maskable"),
        ("Assets/icon-maskable-512.png", "maskable"),
    }
    assert actual == expected

def test_references_use_new_art_everywhere():
    assert 'href="Assets/icon-192.png" type="image/png"' in HTML
    assert 'href="Assets/favicon.ico" type="image/x-icon"' in HTML
    assert f'Assets/icon-180.png?v={CURRENT_APP_VERSION}' in HTML
    assert f'Assets/icon-192.png?v={CURRENT_APP_VERSION}' in HTML
    assert "Assets/icon-192.png" in APP
    for source in (HTML, APP, SW):
        assert "Assets/icon.svg" not in source

def test_offline_assets_and_version():
    precache = SW.split("const PRECACHE_ASSETS = [", 1)[1].split("];", 1)[0]
    for file in (*ICONS, "favicon.ico"):
        assert f"./Assets/{file}" in precache
    assert (ROOT / "Assets/favicon.ico").read_bytes()[:4] == bytes.fromhex("00000100")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'V{CURRENT_APP_VERSION}' in HTML
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
