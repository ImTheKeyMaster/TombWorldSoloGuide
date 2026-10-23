from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def portrait_source():
    return APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function renderHumanPlayerActionPicker")
    ]


def portrait_css():
    return CSS.split(
        "v10.0.95: Preserve side-facing portrait edges and reach the Movement border.",
        1,
    )[1].split(".fight-sequence", 1)[0]


def test_release_is_v10093_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 93)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_portrait_grayscales_before_colorization():
    source = portrait_source()
    assert "deathwatchPortraitImage(activation.operativeId)" in APP
    assert "grayKeyed" not in source
    assert ".2126 .7152 .0722" not in source

def test_colorization_matches_hue_135_saturation_23_lightness_zero_curve():
    source = portrait_source()
    assert "<feFuncR" not in source
    assert "<feFuncG" not in source
    assert "<feFuncB" not in source

def test_background_is_keyed_out_and_portrait_stays_crisp():
    source = portrait_source()
    assert "feConvolveMatrix" not in source
    assert "tightKey" not in source
    assert "const resolvedPortraitMarkup=portraitMarkup;" in source

def test_portrait_is_clipped_at_movement_boundary():
    block = portrait_css()
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    assert "min-height:208px" in portrait
    assert "overflow:visible" in portrait
    assert "clip-path:inset(-96px -96px 0 -96px)" in portrait
    assert "background:transparent" in portrait


def test_change_remains_experimental_and_deathwatch_only():
    source = APP[
        APP.index("function renderHumanPlayerActionPicker")
        : APP.index("function playerSequentialStage")
    ]
    assert "document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
