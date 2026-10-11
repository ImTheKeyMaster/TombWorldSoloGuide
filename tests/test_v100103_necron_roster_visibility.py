from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_is_v100103_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 103)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_v100103_visibility_hack_is_not_left_active_after_framing_fix():
    assert "v10.0.103: Make Experimental Necron Roster Rail portraits larger and easier to read." not in CSS
    assert "filter:brightness(1.62) contrast(1.08)" not in CSS
    assert "filter:brightness(1.50) contrast(1.07)" not in CSS
    assert "transform:scale(1.34)" not in CSS
    assert "transform:scale(1.42)" not in CSS
    assert "transform:scale(1.38)" not in CSS
