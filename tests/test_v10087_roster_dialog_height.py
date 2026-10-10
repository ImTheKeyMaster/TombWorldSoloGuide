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


def test_detail_image_frame_has_fixed_desktop_height():
    block = roster_css()
    rule = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image{', 1
    )[1].split("}", 1)[0]
    assert "align-self:center" in rule
    assert "height:156px" in rule
    assert "min-height:156px" in rule

    image = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image img{', 1
    )[1].split("}", 1)[0]
    assert "height:100%" in image
    assert "max-height:none" in image


def test_detail_image_frame_has_fixed_phone_height():
    block = roster_css()
    mobile = block.split("@media(max-width:600px)", 1)[1].split(
        "@media(max-height:520px)", 1
    )[0]
    assert 'experimental-roster-detail-image{height:112px;min-height:112px}' in mobile
    assert 'experimental-roster-detail-image img{max-height:none}' in mobile


def test_detail_image_frame_has_fixed_compact_landscape_height():
    block = roster_css()
    landscape = block.split("@media(max-height:520px) and (orientation:landscape)", 1)[1]
    assert 'experimental-roster-detail-image{height:80px;min-height:80px}' in landscape
    assert 'experimental-roster-detail-image img{max-height:none}' in landscape


def test_fix_remains_experimental_only():
    assert 'html[data-ui="classic"] .experimental-roster-detail-image' not in CSS
    picker = APP[
        APP.index("function showPlayerActivation()")
        : APP.index("function playerActivationSummary")
    ]
    assert "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'" in picker
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in picker
