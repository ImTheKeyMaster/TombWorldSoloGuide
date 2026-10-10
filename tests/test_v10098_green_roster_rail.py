from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def roster_source():
    return APP[
        APP.index("const EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT")
        : APP.index("function showPlayerActivation()")
    ]


def test_release_is_v10098_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 98)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_roster_rail_uses_green_high_resolution_portrait_helper():
    source = roster_source()
    assert "function experimentalDeathwatchGreenPortraitSvg(id,filterId,svgClass='')" in source
    assert "experimentalDeathwatchActivationImage(id)" in source
    assert "experimentalDeathwatchGreenPortraitSvg(id," in source
    assert "experimentalRosterTint-${index}" in source
    assert "'experimental-roster-tinted-svg')" in source


def test_roster_green_filter_matches_activation_portrait_treatment():
    source = roster_source()
    assert 'result="grayKeyed"' in source
    assert 'result="tightKey"' in source
    assert 'result="colorized"' in source
    assert 'tableValues="0 .0963 .1925 .2888 .385 .5388 .6925 .8463 1"' in source
    assert 'tableValues="0 .1537 .3075 .4612 .615 .7112 .8075 .9037 1"' in source
    assert 'tableValues="0 .1106 .2213 .3319 .4425 .5819 .7213 .8606 1"' in source
    assert '<feComposite in="sharpened" in2="tightKey" operator="in" result="finalPortrait"' in source


def test_selected_roster_detail_uses_same_green_portrait_helper():
    source = roster_source()
    assert 'id="experimentalRosterDetailImage"' in source
    assert "detailImage.innerHTML=experimentalDeathwatchGreenPortraitSvg(selectedId,'experimentalRosterDetailTint','experimental-roster-tinted-svg')" in source
    assert "detailImage.classList.remove('placeholder')" in source


def test_roster_css_supports_inline_svg_in_rail_and_detail_panel():
    assert 'html[data-ui="tomb"] .experimental-roster-image svg{' in CSS
    assert 'html[data-ui="tomb"] .experimental-roster-detail-image svg{' in CSS
    assert 'html[data-ui="tomb"] .experimental-roster-tinted-svg{' in CSS


def test_change_remains_experimental_deathwatch_only():
    source = APP[
        APP.index("function showPlayerActivation()")
        : APP.index("function playerActivationSummary")
    ]
    assert "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'" in source
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in source
    assert 'html[data-ui="classic"] .experimental-roster' not in CSS
