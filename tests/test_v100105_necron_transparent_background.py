from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_is_v100105_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 105)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_transparency_now_comes_from_supplied_assets_not_runtime_keying():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "portraitImageMarkup(" in source
    assert "backgroundKey" not in source
    assert "subjectMask" not in source
    assert "feColorMatrix" not in source
    assert "feComponentTransfer" not in source


def test_precentered_cutouts_render_neutrally():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "experimental-necron-framed-svg" in source
    assert "experimentalNecronPortraitFrame" not in APP
