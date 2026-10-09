from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_surfaces_are_v10082_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 82)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_shared_setup_hex_helper_uses_approved_geometry_counts():
    helper = APP[APP.index("function setupHexArt()") : APP.index("function renderTeamSelection()")]
    assert "setup-hex-art setup-hex-art-upper" in helper
    assert "setup-hex-art setup-hex-art-lower" in helper
    assert "'<i></i>'.repeat(25)" in helper
    assert "'<i></i>'.repeat(20)" in helper
    assert 'aria-hidden="true"' in helper


def test_honeycomb_is_applied_to_all_new_game_setup_render_paths():
    render_team = APP[APP.index("function renderTeamSelection()") : APP.index("const setupStepDefinitions")]
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    render_mode = APP[APP.index("function renderGameModeSelection()") : APP.index("function missionSetupChecks")]
    assert 'class="wizard-card setup-true-hex-card"' in render_team
    assert "${setupHexArt()}" in render_team
    assert render_setup.count('class="wizard-card setup-true-hex-card"') == 3
    assert render_setup.count("${setupHexArt()}") == 3
    assert 'class="wizard-card setup-true-hex-card"' in render_mode
    assert "${setupHexArt()}" in render_mode
    assert "deployHexArt" not in render_setup
    assert "stepId==='deploy'?' deploy-true-hex-card':''" not in render_setup


def test_normal_setup_steps_all_share_one_decorated_card_renderer():
    steps = APP[APP.index("function activeSetupSteps()") : APP.index("function currentSetupStepId()")]
    assert "const steps=['mission','killzone']" in steps
    assert "if(hasMultiplePlayerTeams())steps.push('team')" in steps
    assert "steps.push('playerRoster','options','deploy','ready')" in steps
    render_setup = APP[APP.index("function renderSetup()") : APP.index("function renderGameModeSelection()")]
    assert '<section class="wizard-card setup-true-hex-card"' in render_setup
    assert "${setupContent(stepId)}" in render_setup


def test_true_hex_art_is_experimental_only_and_noninteractive():
    scope = 'html[data-ui="tomb"] .setup-true-hex-card'
    assert scope in CSS
    assert 'html[data-ui="classic"] .setup-true-hex-card' not in CSS
    assert ".setup-hex-art{display:none}" in CSS
    art = CSS.split(f'{scope}>.setup-hex-art{{', 1)[1].split("}", 1)[0]
    assert "display:grid" in art
    assert "position:absolute" in art
    assert "pointer-events:none" in art
    assert "z-index:0" in art
    assert f"{scope}>*:not(.setup-hex-art):not(.wizard-actions)" in CSS


def test_each_cell_remains_an_actual_six_sided_hexagon():
    block = CSS.split("experimental-only true honeycomb hex clusters across New Game Setup", 1)[1]
    assert "clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%)" in block
    assert "--hex-w:42px" in block
    assert "--hex-h:48.5px" in block
    assert "--hex-step:36.4px" in block
    assert "grid-template-columns:repeat(5,var(--hex-w))" in block
    assert "grid-auto-rows:var(--hex-step)" in block
    assert "translateX(calc(var(--hex-w) / 2))" in block


def test_clusters_keep_approved_mirrored_green_placement():
    block = CSS.split("experimental-only true honeycomb hex clusters across New Game Setup", 1)[1]
    upper = block.split(".setup-hex-art-upper{", 1)[1].split("}", 1)[0]
    lower = block.split(".setup-hex-art-lower{", 1)[1].split("}", 1)[0]
    assert "right:-54px" in upper
    assert "top:0" in upper
    assert "ellipse at 100% 42%" in upper
    assert "left:-72px" in lower
    assert "bottom:-26px" in lower
    assert "ellipse at 0 100%" in lower
    assert "color:rgba(118,245,168,.26)" in block
    assert "rgba(118,245,168,.38)" in block
    assert "filter:drop-shadow(0 0 4px rgba(118,245,168,.07))" in block


def test_setup_actions_keep_existing_mobile_and_desktop_layering():
    block = CSS.split("experimental-only true honeycomb hex clusters across New Game Setup", 1)[1]
    assert ".setup-true-hex-card>*:not(.setup-hex-art):not(.wizard-actions)" in block
    assert ".wizard-shell>.wizard-card>.wizard-actions{position:fixed" in CSS
    assert "@media(min-width:601px)" in block
    desktop = block.split("@media(min-width:601px)", 1)[1]
    assert ".setup-true-hex-card>.wizard-actions" in desktop
    assert "position:relative" in desktop
    assert "z-index:1" in desktop


def test_phone_layout_keeps_approved_responsive_hexes():
    block = CSS.split("experimental-only true honeycomb hex clusters across New Game Setup", 1)[1]
    assert "@media(max-width:600px)" in block
    assert "@media(max-width:380px)" in block
    assert "--hex-w:30px" in block
    assert "--hex-h:34.6px" in block
    assert "--hex-step:26px" in block
    assert "right:-66px;opacity:.42" in block
    assert "left:-74px;opacity:.32" in block


def test_deploy_only_hex_class_names_are_removed():
    for token in ("deploy-true-hex-card", "deploy-hex-art-left", "deploy-hex-art-right"):
        assert token not in APP
        assert token not in CSS
