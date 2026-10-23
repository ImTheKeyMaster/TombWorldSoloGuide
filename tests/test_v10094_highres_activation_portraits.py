from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "Deathwatch"

OPERATIVES = (
    "sergeant",
    "aegis",
    "breacher",
    "blademaster",
    "marksman",
    "demolisher",
    "horde-slayer",
    "headtaker",
    "gunner",
    "bombard",
    "disruptor",
)


def activation_source():
    return APP


def test_release_is_v10094_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 94)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_activation_screen_uses_dedicated_high_resolution_asset_root():
    source = activation_source()
    assert "DEATHWATCH_PORTRAIT_ROOT='Assets/Images/TombUI/Deathwatch/'" in source
    assert "function deathwatchPortraitImage(id)" in source
    assert "deathwatchPortraitImage(activation.operativeId)" in source

def test_roster_rail_can_reuse_high_resolution_activation_assets():
    source = activation_source()
    assert "function deathwatchPortraitSvg(id,svgClass='')" in source
    assert 'experimental-roster-image' in source
    assert "return deathwatchPortraitSvg(id,svgClass)" in source

def test_activation_svg_processes_at_384_square_resolution():
    source = activation_source()
    assert 'viewBox="0 0 384 384"' in source
    assert 'width="384" height="384"' in source
    assert "experimentalActivationPortraitCutout" not in source

def test_all_high_resolution_activation_assets_exist_and_are_precached():
    for operative_id in OPERATIVES:
        filename = {"horde-slayer": "horder-slayer", "headtaker": "headtake"}.get(operative_id, operative_id)
        asset = ASSET_ROOT / f"Deathwatch_{filename}.png"
        assert asset.is_file(), operative_id
        assert asset.stat().st_size > 100000, operative_id
        assert f"./Assets/Images/TombUI/Deathwatch/Deathwatch_{filename}.png" in WORKER

def test_photoshop_style_filter_is_still_used_with_high_resolution_sources():
    source = activation_source()
    assert "function deathwatchPortraitSvg(id,svgClass='')" in source
    assert "grayKeyed" not in source
    assert "colorized" not in source
    assert "feColorMatrix" not in source
