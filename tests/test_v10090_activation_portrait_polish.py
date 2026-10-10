from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def portrait_css():
    return CSS.split(
        "v10.0.91: Experimental Deathwatch activation portrait with luminance-keyed alpha.",
        1,
    )[1]


def activation_source():
    return APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function playerSequentialStage")
    ]


def test_release_surfaces_are_v10090_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 90)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_portrait_retains_mockup_scale_and_position():
    block = portrait_css()
    art = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait .experimental-activation-portrait-svg{',
        1,
    )[1].split("}", 1)[0]
    assert "position:absolute" in art
    assert "top:-18px" in art
    assert "right:-20%" in art
    assert "width:170%" in art
    assert "height:auto" in art


def test_black_source_background_is_converted_to_alpha():
    source = activation_source()
    block = portrait_css()
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    assert "background:transparent" in portrait
    assert 'result="keyed"' in source
    assert 'slope="1.15"' in source
    assert 'intercept="-.03"' in source
    assert 'mix-blend-mode:lighten' not in block
    assert 'contrast(1.65)' not in block
    assert 'grayscale(1)' not in block


def test_portrait_polish_remains_experimental_only():
    block = portrait_css()
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in block
    assert 'html[data-ui="classic"] .human-activation-shell.has-operative-portrait' not in block
