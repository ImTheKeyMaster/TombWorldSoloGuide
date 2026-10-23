from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def activation_source():
    return APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function playerSequentialStage")
    ]


def portrait_css():
    return CSS.split(
        "v10.0.95: Preserve side-facing portrait edges and reach the Movement border.",
        1,
    )[1].split("/* v10.0.96:", 1)[0]


def test_release_surfaces_are_v10089_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 89)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_portrait_is_deathwatch_experimental_only():
    source = activation_source()
    assert "portraitMarkup:document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
    assert "deathwatchPortraitImage(activation.operativeId)" in source
    assert "portraitUrl" not in source
    assert "has-operative-portrait" in source
    assert "experimental-activation-portrait" in source

def test_activation_portrait_is_decorative_and_noninteractive():
    source = activation_source()
    assert 'class="experimental-activation-portrait" aria-hidden="true"' in source
    assert 'class="experimental-activation-portrait-svg"' in source
    assert 'focusable="false"' in source
    block = portrait_css()
    assert "pointer-events:none" in block


def test_portrait_uses_alpha_cutout_instead_of_css_blending():
    source = activation_source()
    block = portrait_css()
    assert 'class="experimental-activation-portrait-svg"' in source
    assert 'href="${escapeHtml(deathwatchPortraitImage(activation.operativeId))}"' in source
    assert "experimentalActivationPortraitCutout" not in source
    assert "feColorMatrix" not in source
    assert "mix-blend-mode" not in block
    assert "filter:grayscale" not in block
    assert "mask-image:linear-gradient" not in block

def test_portrait_has_its_own_header_column_and_does_not_cover_controls():
    block = portrait_css()
    shell = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait{', 1
    )[1].split("}", 1)[0]
    assert "grid-template-columns:minmax(0,1fr) minmax(145px,34%)" in shell
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    assert "grid-column:2" in portrait
    assert "grid-row:1 / span 2" in portrait
    rest = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>:not(h2):not(.activation-profile-strip):not(.experimental-activation-portrait){',
        1,
    )[1].split("}", 1)[0]
    assert "grid-column:1 / -1" in rest


def test_current_mode_activation_has_no_portrait_by_default():
    source = activation_source()
    assert "portraitMarkup=''" in source
    assert "portraitUrl" not in source
    assert "deathwatchPortraitImage(activation.operativeId)" in source
