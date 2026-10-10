from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def portrait_polish_css():
    return CSS.split(
        "v10.0.90: Match the Experimental activation portrait to the high-contrast mockup.",
        1,
    )[1]


def test_release_surfaces_are_v10090_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 90)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_portrait_uses_mockup_scale_and_position():
    block = portrait_polish_css()
    image = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait img{',
        1,
    )[1].split("}", 1)[0]
    assert "position:absolute" in image
    assert "top:-18px" in image
    assert "right:-20%" in image
    assert "width:170%" in image
    assert "height:auto" in image
    assert "opacity:.96" in image


def test_activation_portrait_background_visually_drops_out():
    block = portrait_polish_css()
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    image = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait img{',
        1,
    )[1].split("}", 1)[0]
    assert "background:transparent" in portrait
    assert "-webkit-mask-image:none" in portrait
    assert "mask-image:none" in portrait
    assert "background:transparent" in image
    assert "mix-blend-mode:lighten" in image
    assert "contrast(1.65)" in image
    assert "grayscale(1)" in image


def test_portrait_polish_remains_experimental_only():
    block = portrait_polish_css()
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in block
    assert 'html[data-ui="classic"] .human-activation-shell.has-operative-portrait' not in block
