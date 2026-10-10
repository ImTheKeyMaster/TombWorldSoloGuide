from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_release_is_v10091_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 91)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_art_uses_svg_luminance_key_for_true_rendered_alpha():
    source = APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function renderHumanPlayerActionPicker")
    ]
    assert '<svg class="experimental-activation-portrait-svg"' in source
    assert '<filter id="experimentalActivationPortraitCutout"' in source
    assert '<feColorMatrix type="matrix"' in source
    assert '<feFuncA type="linear" slope="1.08" intercept="-.01"' in source
    assert '<image href="${escapeHtml(portraitUrl)}"' in source


def test_no_muddy_css_post_processing_remains_on_activation_portrait():
    block = CSS.split(
        "v10.0.93: Photoshop-matched colorize and hard clip at the Movement boundary.",
        1,
    )[1].split(".fight-sequence", 1)[0]
    assert "mix-blend-mode" not in block
    assert "filter:grayscale" not in block
    assert "filter:sepia" not in block
    assert "opacity:" not in block
    assert "mask-image" not in block
    assert "background:transparent" in block
