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


def test_v100106_mask_and_runtime_zoom_are_superseded_by_supplied_cutouts():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "-1.42" not in source
    assert 'tableValues="0 0 0 .10 .45 .80 1 1 1"' not in source
    assert "experimentalNecronPortraitFrame" not in APP
    assert "return portraitImageMarkup(" in source


def test_single_direct_renderer_still_feeds_all_experimental_necron_portraits():
    roster = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "experimentalNecronPortraitSvg(npo,filterId,svgClass)" in roster
    assert "experimentalNecronRosterTint-" in roster
    assert "experimentalNecronRosterDetailTint" in roster
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronWizardTint'" in solo
