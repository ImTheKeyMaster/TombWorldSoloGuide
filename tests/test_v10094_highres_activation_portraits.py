from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "DeathwatchActivation"

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
    assert "EXPERIMENTAL_DEATHWATCH_ACTIVATION_IMAGE_ROOT='Assets/Images/TombUI/DeathwatchActivation/'" in source
    assert "function experimentalDeathwatchActivationImage(id)" in source
    assert "?experimentalDeathwatchActivationImage(activation.operativeId):''" in source


def test_roster_rail_can_reuse_high_resolution_activation_assets():
    source = activation_source()
    assert "function experimentalDeathwatchActivationImage(id)" in source
    assert "function experimentalDeathwatchGreenPortraitSvg(id,filterId,svgClass='')" in source
    assert 'experimental-roster-image' in source
    assert "experimentalDeathwatchActivationImage(id)" in source


def test_activation_svg_processes_at_384_square_resolution():
    source = activation_source()
    assert 'viewBox="0 0 384 384"' in source
    assert 'width="384" height="384"' in source
    assert 'filter="url(#experimentalActivationPortraitCutout)"' in source


def test_all_high_resolution_activation_assets_exist_and_are_precached():
    for operative_id in OPERATIVES:
        asset = ASSET_ROOT / f"{operative_id}.webp"
        assert asset.is_file(), operative_id
        assert asset.stat().st_size > 18000, operative_id
        worker_path = f"./Assets/Images/TombUI/DeathwatchActivation/{operative_id}.webp"
        assert worker_path in WORKER


def test_photoshop_style_filter_is_still_used_with_high_resolution_sources():
    source = activation_source()
    assert 'result="grayKeyed"' in source
    assert 'result="colorized"' in source
    assert 'tableValues="0 .0963 .1925 .2888 .385 .5388 .6925 .8463 1"' in source
    assert 'tableValues="0 .1537 .3075 .4612 .615 .7112 .8075 .9037 1"' in source
    assert 'tableValues="0 .1106 .2213 .3319 .4425 .5819 .7213 .8606 1"' in source
