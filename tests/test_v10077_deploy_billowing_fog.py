from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10077_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 77)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_billowing_fog_hook_is_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-billowing-fog-card':''" in render_setup
    assert render_setup.count("deploy-billowing-fog-card") == 1


def test_billowing_fog_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-billowing-fog-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-billowing-fog-card' not in CSS
    before = CSS.split(f"{scope}::before{{", 1)[1].split("}", 1)[0]
    after = CSS.split(f"{scope}::after{{", 1)[1].split("}", 1)[0]
    assert "pointer-events:none" in before
    assert "pointer-events:none" in after
    assert "z-index:0" in before
    assert "z-index:0" in after
    assert f"{scope}>*" in CSS


def test_fog_is_built_from_many_overlapping_cloud_lobes():
    block = CSS.split("experimental-only layered billowing fog", 1)[1]
    assert block.count("radial-gradient(ellipse ") >= 13
    assert "filter:blur(15px)" in block
    assert "filter:blur(24px)" in block
    assert "deployFogDriftA" in block
    assert "deployFogDriftB" in block
    assert "repeating-linear-gradient" not in block
    assert "deploy-hex-fog-card" not in block
    assert "url(" not in block


def test_fog_moves_as_two_independent_banks_and_respects_reduced_motion():
    block = CSS.split("experimental-only layered billowing fog", 1)[1]
    assert "@keyframes deployFogDriftA" in block
    assert "@keyframes deployFogDriftB" in block
    assert "18s ease-in-out infinite alternate" in block
    assert "26s ease-in-out infinite alternate" in block
    assert "@media(prefers-reduced-motion:reduce)" in block
    reduced = block.split("@media(prefers-reduced-motion:reduce)", 1)[1]
    assert "animation:none" in reduced
    assert "transform:none" in reduced


def test_fog_scales_back_on_small_phones():
    block = CSS.split("experimental-only layered billowing fog", 1)[1]
    assert "@media(max-width:600px)" in block
    assert "@media(max-width:380px)" in block
    assert "opacity:.44" in block
    assert "opacity:.32" in block
    assert "opacity:.36" in block
    assert "opacity:.24" in block


def test_rejected_hex_and_prior_visual_experiments_are_absent():
    rejected = (
        "deploy-hex-fog-card",
        "repeating-linear-gradient(30deg",
        "deploy-stamps-card",
        "deploy-telemetry-card",
        "deploy-etched-card",
        "deploy-armored-card",
        "deploy-corner",
    )
    for token in rejected:
        assert token not in APP
        if token != "repeating-linear-gradient(30deg":
            assert token not in CSS
