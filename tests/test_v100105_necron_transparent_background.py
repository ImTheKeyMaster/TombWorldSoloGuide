from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_is_v100105_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 105)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_colorization_matches_requested_photoshop_h135_s23_l0_lookup():
    source = section("function experimentalNecronGreenPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert 'tableValues="0 .0963 .1925 .2888 .385 .5388 .6925 .8463 1"' in source
    assert 'tableValues="0 .1537 .3075 .4612 .615 .7112 .8075 .9037 1"' in source
    assert 'tableValues="0 .1106 .2213 .3319 .4425 .5819 .7213 .8606 1"' in source


def test_background_removal_is_separate_from_grayscale_colorization():
    source = section("function experimentalNecronGreenPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert 'result="portraitGray"' in source
    assert 'values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.063 3.576 .361 0 -1.42" result="backgroundKey"' in source
    assert 'in="backgroundKey" result="subjectMask"' in source
    assert 'tableValues="0 0 0 .10 .45 .80 1 1 1"' in source
    assert 'in="portraitGray" result="colorized"' in source
    assert 'in2="subjectMask" operator="in" result="finalPortrait"' in source
    assert '1.063 3.576 .361 0 -.28" result="grayKeyed"' not in source


def test_gauss_flayer_recenters_after_background_is_removed():
    source = section("function experimentalNecronPortraitFrame", "function experimentalNecronGreenPortraitSvg")
    assert "if(npo.type==='Necron Warrior'){" in source
    assert "npo.weaponId==='gauss-reaper'" in source
    assert "? {x:-60,y:-90,size:500}" in source
    assert ": {x:0,y:-100,size:500}" in source


def test_transparent_cutout_helper_is_shared_by_all_experimental_necron_portraits():
    roster = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")

    assert "experimentalNecronGreenPortraitSvg(npo,filterId,svgClass)" in roster
    assert "experimentalNecronPortraitMarkup(npo," in roster
    assert "experimentalNecronRosterTint-" in roster
    assert "experimentalNecronPortraitMarkup(npo,'experimentalNecronRosterDetailTint'" in roster
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronWizardTint'" in solo
