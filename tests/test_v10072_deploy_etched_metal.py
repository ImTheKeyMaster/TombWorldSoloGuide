from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10072_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 72)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_etched_surface_hook_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-etched-card':''" in render_setup
    assert render_setup.count("deploy-etched-card") == 1
    assert "deploy-corner" not in render_setup


def test_etched_surface_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-etched-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-etched-card' not in CSS
    before = CSS.split(f"{scope}::before{{", 1)[1].split("}", 1)[0]
    after = CSS.split(f"{scope}::after{{", 1)[1].split("}", 1)[0]
    assert "pointer-events:none" in before
    assert "pointer-events:none" in after
    assert "z-index:0" in before
    assert "z-index:0" in after
    assert f"{scope}>*" in CSS


def test_surface_uses_machining_scratches_fractures_and_restrained_power_trace():
    block = CSS.split("experimental-only etched-metal surface", 1)[1]
    assert "repeating-linear-gradient(90deg" in block
    assert "repeating-linear-gradient(176deg" in block
    assert "rgba(161,184,179,.16)" in block
    assert "rgba(103,195,255,.24)" in block
    assert "drop-shadow(0 0 4px rgba(103,195,255,.12))" in block
    assert ".btn" not in block
    assert ".check-row" not in block
    assert ".wizard-actions" not in block


def test_armored_corner_experiment_is_fully_removed():
    assert "deploy-armored-card" not in APP
    assert "deploy-corner" not in APP
    assert "deploy-armored-card" not in CSS
    assert "deploy-corner" not in CSS
