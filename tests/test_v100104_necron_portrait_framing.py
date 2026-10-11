from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_is_v100104_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 104)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_necron_portraits_use_centered_source_framing_instead_of_css_zoom():
    source = section("function experimentalNecronPortraitFrame", "function experimentalNecronPortraitMarkup")
    assert "if(npo.type==='Canoptek Scarab Swarm')return {x:-32,y:-140,size:450};" in source
    assert "if(npo.type==='Necron Warrior')return {x:-30,y:-62,size:430};" in source
    assert "return {x:-8,y:-8,size:400};" in source
    assert 'x="${frame.x}" y="${frame.y}" width="${frame.size}" height="${frame.size}"' in source
    assert "experimental-necron-framed-svg" in source

    assert "brightness(1.62)" not in CSS
    assert "transform:scale(1.34)" not in CSS


def test_necron_filter_uses_the_exact_deathwatch_green_pipeline():
    deathwatch = section("function experimentalDeathwatchGreenPortraitSvg", "const EXPERIMENTAL_NECRON_IMAGE_ROOT")
    necron = section("function experimentalNecronGreenPortraitSvg", "function experimentalNecronPortraitMarkup")

    for shared in (
        'values=".2126 .7152 .0722 0 0 .2126 .7152 .0722 0 0 .2126 .7152 .0722 0 0 1.063 3.576 .361 0 -.28" result="grayKeyed"',
        'in="grayKeyed" result="tightKey"',
        'tableValues="0 0 0 0 .2 .65 .9 1 1"',
        'in="grayKeyed" result="colorized"',
        'tableValues="0 .0963 .1925 .2888 .385 .5388 .6925 .8463 1"',
        'tableValues="0 .1537 .3075 .4612 .615 .7112 .8075 .9037 1"',
        'tableValues="0 .1106 .2213 .3319 .4425 .5819 .7213 .8606 1"',
        'kernelMatrix="0 -.05 0 -.05 1.20 -.05 0 -.05 0"',
    ):
        assert shared in deathwatch
        assert shared in necron


def test_framing_clips_in_roster_and_activation_views():
    block = CSS.split(
        "v10.0.104: Necron portraits use intrinsic SVG crop/framing and the exact Deathwatch green treatment.",
        1,
    )[1].split(
        "v10.0.101: Experimental Necron Roster Rail reuses the Deathwatch rail",
        1,
    )[0]
    assert ".experimental-necron-framed-svg{" in block
    assert "overflow:hidden" in block
    assert ".experimental-necron-roster-picker .experimental-roster-tinted-svg{" in block
    assert "transform:none" in block
    assert "filter:none" in block
    assert ".experimental-roster-image{" not in block
    assert ".experimental-roster-item{" not in block


def test_same_framed_helper_feeds_roster_detail_and_activation_portraits():
    source = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    assert "experimentalNecronGreenPortraitSvg(npo,filterId,svgClass)" in source
    assert "experimentalNecronPortraitMarkup(npo,`experimentalNecronRosterTint-" in source
    assert "experimentalNecronPortraitMarkup(npo,'experimentalNecronRosterDetailTint'" in source

    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronGreenPortraitSvg(n,'experimentalNecronWizardTint'" in solo
