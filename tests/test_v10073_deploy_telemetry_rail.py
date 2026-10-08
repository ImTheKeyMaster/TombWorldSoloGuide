from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10073_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 73)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_telemetry_rail_hook_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-telemetry-card':''" in render_setup
    assert render_setup.count("deploy-telemetry-card") == 1


def test_telemetry_rail_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-telemetry-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-telemetry-card' not in CSS
    before = CSS.split(f"{scope}::before{{", 1)[1].split("}", 1)[0]
    after = CSS.split(f"{scope}::after{{", 1)[1].split("}", 1)[0]
    assert "pointer-events:none" in before
    assert "pointer-events:none" in after
    assert "z-index:0" in before
    assert "z-index:0" in after
    assert f"{scope}>*" in CSS


def test_telemetry_rail_has_ticks_numbers_and_restrained_cyan_indicators():
    block = CSS.split("experimental-only deployment telemetry rail", 1)[1]
    assert "repeating-linear-gradient(to bottom" in block
    assert 'content:"01\\A 02\\A 03\\A 04"' in block
    assert "#67c3ff" in block
    assert "width:14px" in block
    assert "ui-monospace" in block
    assert ".btn" not in block
    assert ".check-row" not in block
    assert ".wizard-actions" not in block


def test_etched_surface_experiment_is_fully_removed():
    assert "deploy-etched-card" not in APP
    assert "deploy-etched-card" not in CSS
    assert "experimental-only etched-metal surface" not in CSS
