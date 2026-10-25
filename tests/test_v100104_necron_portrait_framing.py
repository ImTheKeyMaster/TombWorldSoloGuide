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


def test_supplied_assets_are_preframed_so_runtime_frame_math_is_gone():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "experimentalNecronPortraitFrame" not in APP
    assert "return portraitImageMarkup(" in source
    assert "object-fit:contain" in CSS
    assert "experimental-necron-framed-svg" in source


def test_framing_clips_safely_in_all_experimental_views():
    assert ".experimental-necron-framed-svg{" in CSS
    assert "object-position:center center" in CSS
    assert ".experimental-necron-roster-picker .experimental-roster-tinted-svg{" in CSS
    assert "transform:none" in CSS
    assert "filter:none" in CSS


def test_same_direct_renderer_feeds_roster_detail_and_activation_portraits():
    source = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    assert "experimentalNecronPortraitSvg(npo,filterId,svgClass)" in source
    assert "experimentalNecronRosterTint-" in source
    assert "experimentalNecronRosterDetailTint" in source

    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronWizardTint'" in solo
