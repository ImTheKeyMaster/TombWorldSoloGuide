from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def necron_wizard_css():
    return CSS.split(
        "v10.0.102: Keep Necron wizard portraits fully inside the activation header.",
        1,
    )[1].split(".fight-sequence", 1)[0]


def test_release_is_v100102_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 102)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_necron_wizard_portrait_is_constrained_to_header_height():
    block = necron_wizard_css()
    svg = block.split(
        'html[data-ui="tomb"] .experimental-necron-wizard-svg{',
        1,
    )[1].split("}", 1)[0]
    assert "bottom:0" in svg
    assert "height:100%" in svg
    assert "max-height:100%" in svg
    assert "height:auto" not in svg


def test_necron_wizard_keeps_existing_horizontal_scale_and_right_alignment():
    block = necron_wizard_css()
    svg = block.split(
        'html[data-ui="tomb"] .experimental-necron-wizard-svg{',
        1,
    )[1].split("}", 1)[0]
    assert "right:-18px" in svg
    assert "width:152%" in svg


def test_mobile_scaling_overrides_are_preserved():
    block = necron_wizard_css()
    assert "right:-12px" in block
    assert "width:162%" in block
    assert "width:168%" in block


def test_change_remains_experimental_only():
    block = necron_wizard_css()
    assert 'html[data-ui="tomb"] .experimental-necron-wizard-svg' in block
    assert 'html[data-ui="classic"] .experimental-necron-wizard-svg' not in block
