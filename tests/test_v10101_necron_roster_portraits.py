from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")

ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "NecronActivation"
ASSETS = (
    "canoptek-macrocyte-accelerator.webp",
    "canoptek-macrocyte-reanimator.webp",
    "canoptek-macrocyte-warrior-1.webp",
    "canoptek-macrocyte-warrior-2.webp",
    "canoptek-macrocyte-warrior-3.webp",
    "canoptek-scarab-swarm.webp",
    "canoptek-tomb-crawler-1.webp",
    "canoptek-tomb-crawler-2.webp",
    "geomancer.webp",
    "necron-warrior-gauss-flayer.webp",
    "necron-warrior-gauss-reaper.webp",
)


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_is_v100101_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 101)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_supplied_necron_portraits_are_present_and_precached():
    for filename in ASSETS:
        asset = ASSET_ROOT / filename
        assert asset.is_file(), filename
        assert asset.stat().st_size > 5000, filename
        assert f"./Assets/Images/TombUI/NecronActivation/{filename}" in WORKER


def test_portrait_mapping_matches_supported_tomb_world_npo_types():
    source = section("const EXPERIMENTAL_NECRON_IMAGE_ROOT", "function showExperimentalDeathwatchRosterRail")
    assert "npo.type==='Canoptek Scarab Swarm'" in source
    assert "npo.type==='Necron Warrior'" in source
    assert "npo.weaponId==='gauss-reaper'" in source
    assert "npo.type==='Canoptek Tomb Crawler'" in source
    assert "Number(npo.displayNumber)===2?2:1" in source
    assert "npo.type==='Geomancer'" in source
    assert "npo.type==='Canoptek Macrocyte Accelerator'" in source
    assert "npo.type==='Canoptek Macrocyte Reanimator'" in source
    assert "npo.type==='Canoptek Macrocyte Warrior'" in source
    assert "Math.max(1,Math.min(3,Number(npo.displayNumber)||1))" in source


def test_necron_portraits_use_supplied_precolored_transparent_assets_without_runtime_filter():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "portraitImageMarkup(" in source
    assert "experimental-necron-framed-svg" in source
    for old_filter_piece in (
        "<filter",
        "feColorMatrix",
        "backgroundKey",
        "subjectMask",
        "tableValues=",
        "feConvolveMatrix",
    ):
        assert old_filter_piece not in source


def test_experimental_necron_picker_uses_roster_rail_and_starts_unselected():
    source = section("function experimentalNecronRosterMarkup", "function experimentalDeathwatchRosterMarkup")
    assert 'class="experimental-roster-item"' in source
    assert 'class="experimental-roster-image"' in source
    assert 'class="experimental-roster-name"' in source
    assert 'class="experimental-roster-detail"' in source
    assert 'class="experimental-roster-stats placeholder"' in source
    assert "const railOverflowClass=ordered.length>5?' is-overflowing':''" in source
    assert 'class="experimental-roster-rail experimental-necron-roster-rail${railOverflowClass}"' in source
    assert 'tabindex="-1" data-dialog-focus' in source
    assert "let selectedId='';" in source
    assert 'id="confirmExperimentalNecronSelection" disabled' in source
    assert "button.classList.toggle('selected',selected)" in source
    assert source.count("data-roster-npo]',root)") >= 3
    assert "Begin Activation" in source


def test_necron_picker_preserves_solo_threat_principle_and_classic_select():
    source = section("function showNpoSelection()", "function remainingPlayerOperatives")
    assert "const candidates=readyNpos()" in source
    assert "sortedNposForDisplay(candidates)" in source
    assert "document.documentElement.dataset.ui==='tomb'" in source
    assert "showExperimentalNecronRosterRail(candidates)" in source
    assert source.index("showExperimentalNecronRosterRail(candidates)") < source.index("if(isPvpMode())")
    assert "Threat Principle" in source
    assert "has an ability, or is a threat, to Shoot or Fight" in source
    assert "is not in cover" in source
    assert "is closest to" in source
    assert "determine one at random" in source
    assert '<select id="officialNpoSelection" data-dialog-focus>' in source


def test_necron_rail_scrolls_when_many_ready_operatives_are_present():
    assert 'html[data-ui="tomb"] .experimental-roster-rail.experimental-necron-roster-rail.is-overflowing{' in CSS
    assert "overflow-x:auto" in CSS
    assert "scroll-snap-type:x proximity" in CSS
    assert 'html[data-ui="tomb"] .experimental-necron-roster-rail.is-overflowing .experimental-roster-item{' in CSS
    assert "flex:0 0 clamp(112px,18vw,142px)" in CSS


def test_necron_portrait_is_used_in_both_activation_experiences():
    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    assert "portraitMarkup:document.documentElement.dataset.ui==='tomb'?experimentalNecronPortraitSvg(n,'experimentalNecronHumanActivationTint','experimental-activation-portrait-svg'):''" in human

    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronWizardTint','experimental-necron-wizard-svg')" in solo
    assert 'class="experimental-necron-activation-header has-operative-portrait"' in solo
    assert 'class="experimental-necron-activation-portrait"' in solo

    assert 'html[data-ui="tomb"] .experimental-necron-activation-header.has-operative-portrait{' in CSS
    assert 'html[data-ui="tomb"] .experimental-necron-wizard-svg{' in CSS
    shell = section("function renderHumanActivationShell", "function renderHumanPlayerActionPicker")
    assert "portraitUrl='',portraitMarkup=''" in shell
    assert "const resolvedPortraitMarkup=portraitMarkup||(portraitUrl?" in shell


def test_current_ui_remains_without_new_necron_portraits():
    assert 'html[data-ui="classic"] .experimental-necron-roster-rail' not in CSS
    assert 'html[data-ui="classic"] .experimental-necron-activation-header' not in CSS
    assert "NPO portraits are intentionally not displayed in Current UI." in APP
