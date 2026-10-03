from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
JS = (ROOT / "tomb-ui-v2.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v2.css").read_text(encoding="utf-8")


def test_v2_assets_are_loaded_only_as_new_unique_files():
    assert 'href="tomb-ui-v2.css"' in INDEX
    assert 'src="tomb-ui-v2.js"' in INDEX
    assert 'tomb-ui-v2.css?v=' not in INDEX
    assert 'tomb-ui-v2.js?v=' not in INDEX


def test_v2_assets_are_available_offline():
    for asset in (
        "./tomb-ui-v2.css",
        "./tomb-ui-v2.js",
        "./Assets/Images/TombUI/v2/portrait-sprite.webp",
        "./Assets/Images/TombUI/v2/card-ready.svg",
        "./Assets/Images/TombUI/v2/card-selected.svg",
        "./Assets/Images/TombUI/v2/card-valid.svg",
        "./Assets/Images/TombUI/v2/card-disabled.svg",
        "./Assets/Images/TombUI/v2/card-danger.svg",
    ):
        assert asset in WORKER


def test_v2_picker_uses_real_graphic_assets_and_live_selection_state():
    assert "portrait-sprite.webp" in JS
    assert "card-ready.svg" in JS
    assert "card-selected.svg" in JS
    assert "$$('[data-tomb-player-operative]',modal)" in JS
    assert "beginPlayerActivation(selectedId)" in JS
    assert "aria-checked" in JS
    assert "SELECTED" in JS


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
