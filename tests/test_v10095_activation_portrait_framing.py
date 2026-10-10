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


def test_release_is_v10095_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 95)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_portrait_side_overflow_is_visible_but_bottom_stays_clipped():
    block = portrait_css()
    portrait = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait{',
        1,
    )[1].split("}", 1)[0]
    assert "overflow:visible" in portrait
    assert "clip-path:inset(-96px -96px 0 -96px)" in portrait
    assert "min-height:208px" in portrait


def test_portrait_is_lowered_to_meet_movement_border():
    block = portrait_css()
    art = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.experimental-activation-portrait .experimental-activation-portrait-svg{',
        1,
    )[1].split("}", 1)[0]
    assert "top:4px" in art
    assert "right:-10%" in art
    assert "width:176%" in art


def test_mobile_portraits_keep_the_same_side_safe_behavior():
    block = portrait_css()
    assert "top:2px" in block
    assert "right:-12%" in block
    assert "right:-14%" in block


def test_text_stays_above_horizontal_portrait_overflow():
    block = portrait_css()
    heading = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>h2{',
        1,
    )[1].split("}", 1)[0]
    profile = block.split(
        'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait>.activation-profile-strip{',
        1,
    )[1].split("}", 1)[0]
    assert "position:relative" in heading
    assert "z-index:1" in heading
    assert "position:relative" in profile
    assert "z-index:1" in profile


def test_change_remains_experimental_only():
    block = portrait_css()
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in block
    assert 'html[data-ui="classic"] .human-activation-shell.has-operative-portrait' not in block
