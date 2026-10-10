from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def v97_css():
    return CSS.split(
        "v10.0.97: Responsive portrait framing without breaking Movement contact.",
        1,
    )[1].split(".fight-sequence", 1)[0]


def test_release_is_v10097_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 97)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_landscape_expands_left_clip_allowance_when_horizontal_room_exists():
    block = v97_css()
    assert "@media (orientation:landscape) and (min-width:600px)" in block
    landscape = block.split(
        "@media (orientation:landscape) and (min-width:600px){",
        1,
    )[1].split("}", 2)[0]
    assert "clip-path:inset(-96px -96px 0 -220px)" in landscape


def test_portrait_restores_weapon_to_movement_spacing():
    block = v97_css()
    portrait = block.split(
        "@media (orientation:portrait){",
        1,
    )[1].split("@media (orientation:portrait) and (min-width:521px)", 1)[0]
    assert "margin-top:8px" in portrait


def test_portrait_lowers_art_by_matching_amount_to_keep_movement_contact():
    block = v97_css()
    portrait = block.split(
        "@media (orientation:portrait){",
        1,
    )[1].split("@media (orientation:portrait) and (min-width:521px)", 1)[0]
    assert "transform:translate(18px,-18px)" in portrait
    wide_portrait = block.split(
        "@media (orientation:portrait) and (min-width:521px){",
        1,
    )[1]
    assert "transform:translate(24px,-24px)" in wide_portrait


def test_v96_right_edge_and_transparency_treatments_are_preserved():
    assert "v10.0.96: Flush Deathwatch activation portrait to the frame and Movement border." in CSS
    assert "transform:translate(24px,-38px)" in CSS
    assert 'result="tightKey"' in APP
    assert '<feComposite in="sharpened" in2="tightKey" operator="in" result="finalPortrait"' in APP


def test_change_remains_experimental_only():
    block = v97_css()
    assert 'html[data-ui="tomb"] .human-activation-shell.has-operative-portrait' in block
    assert 'html[data-ui="classic"] .human-activation-shell.has-operative-portrait' not in block
