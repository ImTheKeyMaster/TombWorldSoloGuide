from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_is_v100106_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 106)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_necron_background_key_is_more_aggressive_than_v100105():
    source = section("function experimentalNecronGreenPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert '1.063 3.576 .361 0 -1.42" result="backgroundKey"' in source
    assert 'tableValues="0 0 0 .10 .45 .80 1 1 1"' in source
    assert '1.063 3.576 .361 0 -1.25" result="backgroundKey"' not in source
    assert 'tableValues="0 0 .45 .85 1 1 1 1 1"' not in source


def test_photoshop_equivalent_green_colorization_is_unchanged():
    source = section("function experimentalNecronGreenPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert 'tableValues="0 .0963 .1925 .2888 .385 .5388 .6925 .8463 1"' in source
    assert 'tableValues="0 .1537 .3075 .4612 .615 .7112 .8075 .9037 1"' in source
    assert 'tableValues="0 .1106 .2213 .3319 .4425 .5819 .7213 .8606 1"' in source
    assert 'in="portraitGray" result="colorized"' in source


def test_model_family_frames_are_larger_for_identification():
    source = section("function experimentalNecronPortraitFrame", "function experimentalNecronGreenPortraitSvg")
    assert "if(npo.type==='Canoptek Scarab Swarm')return {x:-34,y:-151,size:452};" in source
    assert "? {x:-60,y:-90,size:500}" in source
    assert ": {x:0,y:-100,size:500}" in source
    assert "if(npo.type==='Canoptek Tomb Crawler')return {x:-40,y:-32,size:460};" in source
    assert "if(npo.type==='Geomancer')return {x:-35,y:-30,size:455};" in source
    assert "if(npo.type==='Canoptek Macrocyte Accelerator')return {x:-43,y:-34,size:470};" in source
    assert "if(npo.type==='Canoptek Macrocyte Reanimator')return {x:-43,y:-34,size:470};" in source
    assert "if(npo.type==='Canoptek Macrocyte Warrior')return {x:-43,y:-30,size:470};" in source


def test_single_helper_still_feeds_all_experimental_necron_portraits():
    roster = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "experimentalNecronGreenPortraitSvg(npo,filterId,svgClass)" in roster
    assert "experimentalNecronRosterTint-" in roster
    assert "experimentalNecronRosterDetailTint" in roster
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronWizardTint'" in solo
