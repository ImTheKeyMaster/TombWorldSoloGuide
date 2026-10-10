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
        "v10.0.89: Experimental Deathwatch activation portrait.", 1
    )[1]


def test_release_surfaces_are_v10089_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 89)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_portrait_is_deathwatch_experimental_only():
    source = activation_source()
    assert "portraitUrl:document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
    assert "?experimentalDeathwatchRosterImage(activation.operativeId):''" in source
    assert "portraitUrl=''" in source
    assert "has-operative-portrait" in source
    assert "experimental-activation-portrait" in source


def test_activation_portrait_is_decorative_and_noninteractive():
    source = activation_source()
    assert 'class="experimental-activation-portrait" aria-hidden="true"' in source
    assert 'alt=""' in source
    block = portrait_css()
    assert "pointer-events:none" in block


def test_green_scale_hud_treatment_is_scoped_to_experimental_ui():
    block = portrait_css()
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in block
    assert 'html[data-ui="classic"] .human-activation-shell.has-operative-portrait' not in block
    assert "filter:grayscale(1) sepia(1) saturate(2.35) hue-rotate(72deg)" in block
    assert "mix-blend-mode:screen" in block
    assert "mask-image:linear-gradient(to bottom" in block


def test_portrait_has_its_own_header_column_and_does_not_cover_controls():
    block = portrait_css()
    shell = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait{', 1
    )[1].split("}", 1)[0]
    assert "grid-template-columns:minmax(0,1fr) minmax(145px,34%)" in shell
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{', 1
    )[1].split("}", 1)[0]
    assert "grid-column:2" in portrait
    assert "grid-row:1 / span 2" in portrait
    rest = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>:not(h2):not(.activation-profile-strip):not(.experimental-activation-portrait){', 1
    )[1].split("}", 1)[0]
    assert "grid-column:1 / -1" in rest


def test_current_mode_activation_has_no_portrait_by_default():
    source = activation_source()
    assert "portraitUrl=''" in source
