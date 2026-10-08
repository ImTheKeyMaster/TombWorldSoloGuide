from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10074_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 74)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_inspection_markings_hook_is_deploy_only_and_decorative_text_is_hidden():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-stamps-card':''" in render_setup
    assert render_setup.count("deploy-stamps-card") == 1
    assert render_setup.count('aria-hidden="true"') >= 2
    assert '<span class="deploy-stamp-authorized" aria-hidden="true">DEPLOYMENT AUTHORIZED</span>' in render_setup
    assert '<span class="deploy-field-code" aria-hidden="true">SECTOR 07 · GRID K-19 · INSPECT 442</span>' in render_setup


def test_inspection_markings_are_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-stamps-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-stamps-card' not in CSS
    authorized = CSS.split(f"{scope}>.deploy-stamp-authorized{{", 1)[1].split("}", 1)[0]
    field_code = CSS.split(f"{scope}>.deploy-field-code{{", 1)[1].split("}", 1)[0]
    assert "pointer-events:none" in authorized
    assert "pointer-events:none" in field_code
    assert "z-index:0" in authorized
    assert "z-index:0" in field_code
    assert f"{scope}>*" in CSS


def test_markings_use_original_stencil_inventory_and_hazard_details():
    block = CSS.split("experimental-only inspection stamps and field markings", 1)[1]
    assert "deploy-stamp-authorized" in block
    assert "deploy-field-code" in block
    assert 'content:"DEPLOYMENT AUTHORIZED"' not in block
    assert 'content:"SECTOR 07' not in block
    assert "repeating-linear-gradient(90deg" in block
    assert "repeating-linear-gradient(135deg" in block
    assert "ui-monospace" in block
    assert "rgba(103,195,255,.13)" in block
    assert ".btn" not in block
    assert ".check-row" not in block
    assert ".wizard-actions" not in block


def test_previous_visual_experiments_are_fully_removed():
    assert "deploy-telemetry-card" not in APP
    assert "deploy-telemetry-card" not in CSS
    assert "experimental-only deployment telemetry rail" not in CSS
    assert "deploy-etched-card" not in APP
    assert "deploy-etched-card" not in CSS
    assert "experimental-only etched-metal surface" not in CSS
