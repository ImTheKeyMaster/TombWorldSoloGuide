from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def roster_css():
    return CSS.split(
        "Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1
    )[1]


def test_release_surfaces_are_v10087_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 87)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_detail_panel_reserves_desktop_portrait_footprint():
    block = roster_css()
    detail = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail{', 1
    )[1].split("}", 1)[0]
    assert "min-height:206px" in detail

    frame = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image{', 1
    )[1].split("}", 1)[0]
    assert "align-self:stretch" in frame
    assert "min-height:156px" in frame
    assert "height:156px" not in frame

    image = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image img{', 1
    )[1].split("}", 1)[0]
    assert "height:100%" in image
    assert "max-height:180px" in image


def test_detail_panel_reserves_phone_portrait_footprint():
    block = roster_css()
    mobile = block.split("@media(max-width:600px)", 1)[1].split(
        "@media(max-height:520px)", 1
    )[0]
    assert "min-height:142px" in mobile
    assert 'experimental-roster-detail-image{min-height:112px}' in mobile
    assert 'experimental-roster-detail-image img{max-height:122px}' in mobile


def test_detail_panel_reserves_compact_landscape_portrait_footprint():
    block = roster_css()
    landscape = block.split("@media(max-height:520px) and (orientation:landscape)", 1)[1]
    assert "min-height:104px" in landscape
    assert 'experimental-roster-detail-image{min-height:80px}' in landscape
    assert 'experimental-roster-detail-image img{max-height:88px}' in landscape


def test_fix_remains_experimental_only():
    assert 'html[data-ui="classic"] .experimental-roster-detail-image' not in CSS
    picker = APP[
        APP.index("function showPlayerActivation()")
        : APP.index("function playerActivationSummary")
    ]
    assert "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'" in picker
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in picker
