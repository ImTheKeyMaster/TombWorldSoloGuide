from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def necron_visibility_css():
    return CSS.split(
        "v10.0.103: Make Experimental Necron Roster Rail portraits larger and easier to read.",
        1,
    )[1].split(
        "v10.0.101: Experimental Necron Roster Rail reuses the Deathwatch rail",
        1,
    )[0]


def test_release_is_v100103_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 103)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_necron_rail_portraits_are_larger_than_shared_roster_defaults():
    block = necron_visibility_css()
    assert ".experimental-necron-roster-picker .experimental-roster-image{" in block
    assert "height:clamp(78px,13vw,108px)" in block
    assert ".experimental-necron-roster-picker .experimental-roster-item{" in block
    assert "min-height:118px" in block


def test_necron_rail_art_is_zoomed_and_brightened():
    block = necron_visibility_css()
    assert "transform:scale(1.34)" in block
    assert "transform-origin:50% 62%" in block
    assert "filter:brightness(1.62) contrast(1.08)" in block


def test_selected_necron_detail_portrait_is_also_brighter_and_larger():
    block = necron_visibility_css()
    assert ".experimental-necron-roster-picker .experimental-roster-detail-image .experimental-roster-tinted-svg{" in block
    assert "transform:scale(1.16)" in block
    assert "filter:brightness(1.50) contrast(1.07)" in block


def test_phone_and_short_landscape_keep_visibility_improvements():
    block = necron_visibility_css()
    assert "@media(max-width:600px)" in block
    assert "height:min(76px,calc((100vw - 76px)/4.5))" in block
    assert "transform:scale(1.42)" in block
    assert "@media(max-height:520px) and (orientation:landscape)" in block
    assert "height:62px" in block
    assert "transform:scale(1.38)" in block


def test_deathwatch_roster_is_not_targeted_by_new_rules():
    block = necron_visibility_css()
    assert ".experimental-necron-roster-picker" in block
    assert ".experimental-deathwatch-roster-picker" not in block
