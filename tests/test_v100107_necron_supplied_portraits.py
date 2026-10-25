from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
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


def test_release_is_v100107_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 107)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_all_supplied_portrait_assets_are_webp_and_precached():
    for filename in ASSETS:
        data = (ASSET_ROOT / filename).read_bytes()
        assert len(data) > 5000, filename
        assert data[:4] == b"RIFF", filename
        assert data[8:12] == b"WEBP", filename
        assert f"./Assets/Images/TombUI/NecronActivation/{filename}" in WORKER


def test_operatives_keep_the_expected_portrait_associations():
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


def test_supplied_images_are_rendered_directly_without_recoloring_or_keying():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert "return portraitImageMarkup(" in source
    assert "experimental-necron-framed-svg" in source
    assert "APP_VERSION" in source
    for removed_runtime_treatment in (
        "experimentalNecronGreenPortraitSvg",
        "experimentalNecronPortraitFrame",
        "<filter",
        "feColorMatrix",
        "feComponentTransfer",
        "feConvolveMatrix",
        "backgroundKey",
        "subjectMask",
        "tableValues=",
    ):
        assert removed_runtime_treatment not in source
    assert "experimentalNecronGreenPortraitSvg" not in APP
    assert "experimentalNecronPortraitFrame" not in APP


def test_direct_renderer_is_used_in_every_experimental_necron_portrait_context():
    roster = section("function experimentalNecronPortraitMarkup", "function showExperimentalDeathwatchRosterRail")
    human = section("function renderHumanNpoActionPicker", "function selectHumanNpoAction")
    solo = section("function renderNpoActivationHeader", "function renderNpoGuideFooter")

    assert "experimentalNecronPortraitSvg(npo,filterId,svgClass)" in roster
    assert "experimentalNecronRosterTint-" in roster
    assert "experimentalNecronRosterDetailTint" in roster
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronHumanActivationTint'" in human
    assert "experimentalNecronPortraitSvg(n,'experimentalNecronWizardTint'" in solo


def test_current_ui_still_does_not_show_experimental_necron_portraits():
    assert "NPO portraits are intentionally not displayed in Current UI." in APP
