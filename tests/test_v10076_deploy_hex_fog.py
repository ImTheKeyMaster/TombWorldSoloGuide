from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10076_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 76)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_hex_fog_hook_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-hex-fog-card':''" in render_setup
    assert render_setup.count("deploy-hex-fog-card") == 1


def test_hex_fog_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-hex-fog-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-hex-fog-card' not in CSS
    before = CSS.split(f"{scope}::before{{", 1)[1].split("}", 1)[0]
    after = CSS.split(f"{scope}::after{{", 1)[1].split("}", 1)[0]
    assert "pointer-events:none" in before
    assert "pointer-events:none" in after
    assert "z-index:0" in before
    assert "z-index:0" in after
    assert f"{scope}>*" in CSS


def test_hex_field_is_css_generated_and_fades_toward_content():
    block = CSS.split("experimental-only broken hex field + atmospheric fog", 1)[1]
    assert "repeating-linear-gradient(30deg" in block
    assert "repeating-linear-gradient(150deg" in block
    assert "repeating-linear-gradient(90deg" in block
    assert "-webkit-mask-image:radial-gradient" in block
    assert "mask-image:radial-gradient" in block
    assert "background-size:36px 62px" in block
    assert "background-size:30px 52px" in block


def test_fog_is_css_generated_and_responsive():
    block = CSS.split("experimental-only broken hex field + atmospheric fog", 1)[1]
    assert block.count("radial-gradient(ellipse") >= 9
    assert "@media(max-width:600px)" in block
    assert "@media(max-width:380px)" in block
    assert "filter:saturate(.72)" in block
    assert "url(" not in block


def test_rejected_previous_deploy_experiments_remain_absent():
    rejected = (
        "deploy-stamps-card",
        "deploy-telemetry-card",
        "deploy-etched-card",
        "deploy-armored-card",
        "deploy-corner",
    )
    for token in rejected:
        assert token not in APP
        assert token not in CSS
