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


def test_release_is_v100108_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 108)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_all_supplied_necron_portraits_are_present_and_precached():
    for filename in ASSETS:
        data = (ASSET_ROOT / filename).read_bytes()
        assert len(data) > 20000, filename
        assert data[:4] == b"RIFF", filename
        assert data[8:12] == b"WEBP", filename
        assert f"./Assets/Images/TombUI/NecronActivation/{filename}" in WORKER


def test_existing_necron_mapping_remains_complete():
    source = section("const EXPERIMENTAL_NECRON_IMAGE_ROOT", "function showExperimentalDeathwatchRosterRail")
    assert "npo.type==='Canoptek Scarab Swarm'" in source
    assert "npo.type==='Necron Warrior'" in source
    assert "npo.weaponId==='gauss-reaper'" in source
    assert "npo.type==='Canoptek Tomb Crawler'" in source
    assert "npo.type==='Geomancer'" in source
    assert "npo.type==='Canoptek Macrocyte Accelerator'" in source
    assert "npo.type==='Canoptek Macrocyte Reanimator'" in source
    assert "npo.type==='Canoptek Macrocyte Warrior'" in source


def test_supplied_portraits_are_rendered_directly_without_runtime_recoloring():
    source = section("function experimentalNecronPortraitSvg", "function experimentalNecronPortraitMarkup")
    assert '<image href="' in source
    assert 'preserveAspectRatio="xMidYMid meet"' in source
    for runtime_treatment in (
        "feColorMatrix",
        "feComponentTransfer",
        "feConvolveMatrix",
        "backgroundKey",
        "subjectMask",
        "tableValues=",
    ):
        assert runtime_treatment not in source
