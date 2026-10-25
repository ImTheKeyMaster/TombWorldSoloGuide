from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def v96_css():
    return CSS.split(
        "v10.0.96: Flush Deathwatch activation portrait to the frame and Movement border.",
        1,
    )[1].split(".fight-sequence", 1)[0]


def activation_source():
    return APP[
        APP.index("function renderHumanActivationShell")
        : APP.index("function playerSequentialStage")
    ]


def test_release_is_v10096_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 96)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_portrait_is_shifted_flush_to_desktop_and_mobile_right_edges():
    block = v96_css()
    assert "transform:translate(24px,-38px)" in block
    assert "right:-12%" in block
    assert "transform:translate(18px,-32px)" in block
    assert "right:-13%" in block
    assert "transform:translate(18px,-26px)" in block
    assert "right:-15%" in block


def test_movement_frame_is_pulled_up_to_portrait_boundary():
    block = v96_css()
    group = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.activation-groups{',
        1,
    )[1].split("}", 1)[0]
    assert "margin-top:-6px" in group
    assert "position:relative" in group
    assert "z-index:1" in group


def test_low_opacity_background_is_hard_clamped_after_sharpening():
    source = activation_source()
    assert "tightKey" not in source
    assert "sharpened" not in source
    assert "<feComposite" not in source
    assert "const resolvedPortraitMarkup=portraitMarkup;" in source

def test_existing_photoshop_colorization_and_high_res_source_remain_intact():
    source = activation_source()
    assert "deathwatchPortraitSvg(activation.operativeId,'experimental-activation-portrait-svg')" in source
    assert "deathwatchPortraitImage(activation.operativeId)" in source
    assert "grayKeyed" not in source
    assert "colorized" not in source

def test_change_remains_experimental_deathwatch_only():
    source = APP[
        APP.index("function renderHumanPlayerActionPicker")
        : APP.index("function playerSequentialStage")
    ]
    assert "document.documentElement.dataset.ui==='tomb'" in source
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
