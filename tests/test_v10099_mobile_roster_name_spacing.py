from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def roster_source():
    return APP[
        APP.index("function showExperimentalDeathwatchRosterRail")
        : APP.index("function showPlayerActivation()")
    ]


def test_release_is_v10099_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 99)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_roster_detects_single_line_names_after_render():
    source = roster_source()
    assert "const updateRosterNameDensity=()=>{" in source
    assert "button.classList.remove('single-line-name')" in source
    assert "const lineHeight=parseFloat(getComputedStyle(name).lineHeight)||0" in source
    assert "name.scrollHeight<=lineHeight*1.35" in source
    assert "button.classList.add('single-line-name')" in source
    assert "requestAnimationFrame(updateRosterNameDensity)" in source


def test_small_screens_reclaim_only_single_line_name_space():
    mobile = CSS.split("@media(max-width:600px){", 1)[1].split("@media(max-height:520px)", 1)[0]
    assert ".experimental-roster-item{min-height:96px;padding:4px 2px 29px}" in mobile
    assert ".experimental-roster-item.single-line-name{padding-bottom:18px}" in mobile
    assert ".experimental-roster-item.single-line-name .experimental-roster-image{height:min(75px,calc((100vw - 90px)/5 + 11px))}" in mobile


def test_wrapped_names_keep_existing_two_line_reserve():
    mobile = CSS.split("@media(max-width:600px){", 1)[1].split("@media(max-height:520px)", 1)[0]
    assert ".experimental-roster-item{min-height:96px;padding:4px 2px 29px}" in mobile
    assert ".experimental-roster-name{font-size:.62rem;letter-spacing:0}" in mobile
    assert "-webkit-line-clamp:2" in CSS


def test_desktop_roster_sizing_is_unchanged():
    base = CSS.split("Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1)[1].split("@media(max-width:600px)", 1)[0]
    assert "min-height:104px" in base
    assert "padding:5px 4px 18px" in base
    assert "height:clamp(64px,11vw,96px)" in base


def test_change_remains_experimental_only():
    assert 'html[data-ui="tomb"] .experimental-roster-item.single-line-name' in CSS
    assert 'html[data-ui="classic"] .experimental-roster-item.single-line-name' not in CSS
