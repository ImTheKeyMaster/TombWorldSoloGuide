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


def test_activation_art_uses_prepared_native_alpha_cutouts():
    source = APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function playerSequentialStage")
    ]
    assert "deathwatchPortraitSvg(activation.operativeId,'experimental-activation-portrait-svg')" in source
    assert 'function portraitImageMarkup(' in APP
    assert 'src="${escapeHtml(src)}"' in APP
    assert '<svg class="experimental-activation-portrait-svg"' not in source
    assert "experimentalActivationPortraitCutout" not in source
    assert "<feColorMatrix" not in source
    assert "const resolvedPortraitMarkup=portraitMarkup;" in source

def test_no_muddy_css_post_processing_remains_on_activation_portrait():
    block = CSS.split(
        "v10.0.95: Preserve side-facing portrait edges and reach the Movement border.",
        1,
    )[1].split(".fight-sequence", 1)[0]
    assert "mix-blend-mode" not in block
    assert "filter:grayscale" not in block
    assert "filter:sepia" not in block
    assert "opacity:" not in block
    assert "mask-image" not in block
    assert "background:transparent" in block
