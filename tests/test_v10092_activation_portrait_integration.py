from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def portrait_css():
    return CSS.split(
        "v10.0.95: Preserve side-facing portrait edges and reach the Movement border.",
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


def test_portrait_filter_matches_photoshop_colorize_and_keeps_light_sharpening():
    source = activation_source()
    assert "deathwatchPortraitImage(activation.operativeId)" in source
    assert "colorized" not in source
    assert "grayKeyed" not in source
    assert "feConvolveMatrix" not in source
    assert "experimentalActivationPortraitCutout" not in source

def test_portrait_preserves_background_alpha_key():
    source = activation_source()
    assert "experimentalActivationPortraitCutout" not in source
    assert "<image href=" in source
    assert "preserveAspectRatio=" in source

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
    assert "clip-path:inset(-96px -96px 0 -96px)" in portrait
    assert "background:transparent" in portrait
    assert "top:4px" in art
    assert "right:-10%" in art
    assert "width:176%" in art


def test_change_remains_experimental_and_deathwatch_only():
    source = APP[
        APP.index("function renderHumanPlayerActionPicker")
        : APP.index("function playerSequentialStage")
    ]
    assert "document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
