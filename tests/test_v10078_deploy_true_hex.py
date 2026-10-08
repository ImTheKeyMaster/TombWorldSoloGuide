from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10078_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 78)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_true_hex_hook_and_decoration_are_deploy_only():
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert "stepId==='deploy'?' deploy-true-hex-card':''" in render_setup
    assert "deployHexArt=stepId==='deploy'?" in render_setup
    assert "'<i></i>'.repeat(25)" in render_setup
    assert "'<i></i>'.repeat(20)" in render_setup
    assert 'aria-hidden="true"' in render_setup


def test_true_hex_art_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .deploy-true-hex-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .deploy-true-hex-card' not in CSS
    assert ".deploy-hex-art{display:none}" in CSS
    art = CSS.split(f'{scope}>.deploy-hex-art{{', 1)[1].split("}", 1)[0]
    assert "display:grid" in art
    assert "position:absolute" in art
    assert "pointer-events:none" in art
    assert "z-index:0" in art
    assert f"{scope}>*:not(.deploy-hex-art)" in CSS


def test_each_cell_is_an_actual_six_sided_hexagon():
    block = CSS.split("experimental-only true honeycomb hex clusters", 1)[1]
    assert "clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)" in block
    assert "--hex-w:42px" in block
    assert "--hex-h:48.5px" in block
    assert "--hex-step:36.4px" in block
    assert "grid-template-columns:repeat(5,var(--hex-w))" in block
    assert "grid-auto-rows:var(--hex-step)" in block
    assert "translateX(calc(var(--hex-w) / 2))" in block


def test_hex_clusters_are_broken_faded_and_edge_anchored():
    block = CSS.split("experimental-only true honeycomb hex clusters", 1)[1]
    assert ".deploy-hex-art-left" in block
    assert ".deploy-hex-art-right" in block
    assert "left:-54px" in block
    assert "right:-72px" in block
    assert "-webkit-mask-image:radial-gradient" in block
    assert "mask-image:radial-gradient" in block
    assert "opacity:.14" in block
    assert "rgba(103,195,255,.62)" in block


def test_phone_layout_shrinks_hexes_without_consuming_content_space():
    block = CSS.split("experimental-only true honeycomb hex clusters", 1)[1]
    assert "@media(max-width:600px)" in block
    assert "@media(max-width:380px)" in block
    assert "--hex-w:30px" in block
    assert "--hex-h:34.6px" in block
    assert "--hex-step:26px" in block
    assert "position:absolute" in block


def test_fog_and_previous_rejected_visual_experiments_are_absent():
    rejected = (
        "deploy-billowing-fog-card",
        "deployFogDriftA",
        "deployFogDriftB",
        "deploy-stamps-card",
        "deploy-telemetry-card",
        "deploy-etched-card",
        "deploy-armored-card",
        "deploy-corner",
    )
    for token in rejected:
        assert token not in APP
        assert token not in CSS
