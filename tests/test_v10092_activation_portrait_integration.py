from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def portrait_css():
    return CSS.split(
        "v10.0.92: Brighter, sharper Experimental Deathwatch activation portrait with integrated vertical reach.",
        1,
    )[1].split(".fight-sequence", 1)[0]


def activation_source():
    return APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function renderHumanPlayerActionPicker")
    ]


def test_release_is_v10092_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 92)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_portrait_filter_lifts_detail_and_adds_light_sharpening():
    source = activation_source()
    assert 'result="lifted"' in source
    assert '<feFuncR type="gamma" amplitude="1.10" exponent=".78" offset=".01"' in source
    assert '<feFuncG type="gamma" amplitude="1.24" exponent=".70" offset=".015"' in source
    assert '<feConvolveMatrix in="lifted"' in source
    assert 'kernelMatrix="0 -.08 0 -.08 1.32 -.08 0 -.08 0"' in source
    assert 'preserveAlpha="true"' in source


def test_portrait_preserves_more_dark_detail_than_v10091():
    source = activation_source()
    assert '1.063 3.576 .361 0 -.28' in source
    assert '<feFuncA type="linear" slope="1.08" intercept="-.01"' in source


def test_portrait_can_reach_movement_panel_without_black_box_clipping():
    block = portrait_css()
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    art = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait .experimental-activation-portrait-svg{',
        1,
    )[1].split("}", 1)[0]
    assert "min-height:208px" in portrait
    assert "overflow:visible" in portrait
    assert "background:transparent" in portrait
    assert "top:-14px" in art
    assert "right:-18%" in art
    assert "width:176%" in art


def test_change_remains_experimental_and_deathwatch_only():
    source = APP[
        APP.index("function renderHumanPlayerActionPicker")
        : APP.index("function playerSequentialStage")
    ]
    assert "document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
