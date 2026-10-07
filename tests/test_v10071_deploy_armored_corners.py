from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10071_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 71)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_deploy_corner_markup_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-armored-card':''" in render_setup
    assert render_setup.count("deploy-armored-card") == 1
    assert render_setup.count("deploy-corner-") == 4
    assert 'aria-hidden="true"' in render_setup


def test_armored_corners_are_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-armored-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-armored-card' not in CSS
    corner = CSS.split(f'{scope}>.deploy-corner{{', 1)[1].split("}", 1)[0]
    assert "position:absolute" in corner
    assert "pointer-events:none" in corner
    assert "z-index:2" in corner
    assert "clip-path:polygon" in corner


def test_corner_details_include_rivets_glow_and_wear_without_restyling_controls():
    block = CSS.split("experimental-only armored corner details", 1)[1]
    assert "box-shadow:12px 0 0 #60747a" in block
    assert "#67c3ff" in block
    assert "rgba(151,178,183,.24)" in block
    assert ".btn" not in block
    assert ".check-row" not in block
    assert ".wizard-actions" not in block


def test_watermark_is_fully_removed_from_live_surfaces():
    assert "deploy-watermark-card" not in APP
    assert "deploy-watermark.svg" not in CSS
    assert "deploy-watermark.svg" not in WORKER
