from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v2.css").read_text(encoding="utf-8")


def picker_source():
    return APP.split("const TOMB_V2_ASSET_ROOT", 1)[1].split("function showPlayerActivation()", 1)[0]


def test_v2_css_is_versioned_and_override_script_is_gone():
    assert 'href="tomb-ui-v2.css"' in INDEX
    assert 'src="tomb-ui-v2.js"' not in INDEX
    assert "tomb-ui-v2.js" not in WORKER


def test_v2_assets_are_available_offline():
    assert "./tomb-ui-v2.css" in WORKER
    for asset in (
        "./Assets/Images/TombUI/v2/portrait-sprite.webp",
        "./Assets/Images/TombUI/v2/card-ready.svg",
        "./Assets/Images/TombUI/v2/card-selected.svg",
        "./Assets/Images/TombUI/v2/card-valid.svg",
        "./Assets/Images/TombUI/v2/card-disabled.svg",
        "./Assets/Images/TombUI/v2/card-danger.svg",
    ):
        assert asset in WORKER


def test_v2_picker_is_integrated_into_app_runtime():
    picker = picker_source()
    assert "portrait-sprite.webp" in picker
    assert "card-ready.svg" in picker
    assert "card-selected.svg" in picker
    assert 'class="tomb-v2-shell"' in picker
    assert 'class="tomb-v2-operative-grid"' in picker
    assert "$$('[data-tomb-player-operative]',modal)" in picker
    assert "beginPlayerActivation(selectedId)" in picker
    assert "aria-checked" in picker
    assert "SELECTED" in picker


def test_v2_picker_no_longer_renders_legacy_full_width_card_markup():
    picker = picker_source()
    assert "tomb-operative-card-content" not in picker
    assert "tomb-operative-monogram" not in picker
    assert "tomb-operative-wounds" not in picker
    assert "operative-ready.webp" not in picker
    assert "operative-selected.webp" not in picker


def test_v2_portrait_layout_is_compact_two_column():
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in CSS
    assert ".tomb-v2-portrait" in CSS
    assert "background-size:400% 200%" in CSS


def test_v2_landscape_has_explicit_four_column_layout_and_portrait_reset():
    assert "@media(orientation:landscape) and (max-height:500px)" in CSS
    assert "grid-template-columns:repeat(4,minmax(0,1fr))" in CSS
    assert "@media(orientation:portrait)" in CSS
    assert "height:auto!important" in CSS
    assert "gap:8px!important" in CSS
