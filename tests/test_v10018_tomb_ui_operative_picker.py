from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v2.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_surfaces_are_synchronized():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 20)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f"V{CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")


def test_tomb_picker_is_feature_flagged_and_classic_picker_remains():
    selection = section("function showPlayerActivation()", "function playerActivationSummary")
    assert "document.documentElement.dataset.ui==='tomb'" in selection
    assert "showTombPlayerOperativeSelection(candidates)" in selection
    assert '<select id="humanPlayerSelection"' in selection
    assert "beginPlayerActivation($('#humanPlayerSelection').value)" in selection


def test_tomb_v2_picker_is_part_of_app_iife_runtime():
    picker = section("const TOMB_V2_ASSET_ROOT", "function showPlayerActivation()")
    for asset in (
        "Assets/Images/TombUI/v2/",
        "card-ready.svg",
        "card-selected.svg",
        "portrait-sprite.webp",
        "Assets/Images/TombUI/action-preview.webp",
        "Assets/Images/TombUI/button-primary.webp",
        "Assets/Images/TombUI/button-secondary.webp",
    ):
        assert asset in picker
    assert 'class="tomb-v2-shell"' in picker
    assert 'class="tomb-v2-operative-grid"' in picker
    assert 'role="radiogroup"' in picker
    assert 'role="radio"' in picker
    assert "aria-checked" in picker


def test_tomb_v2_selection_enumerates_every_card_and_preserves_activation_path():
    picker = section("const TOMB_V2_ASSET_ROOT", "function showPlayerActivation()")
    collection = "$$('[data-tomb-player-operative]',modal)"
    assert picker.count(collection) == 2
    assert "selectedId=button.dataset.tombPlayerOperative" in picker
    assert "card.dataset.tombPlayerOperative===selectedId" in picker
    assert "card.classList.toggle('selected',selected)" in picker
    assert "card.setAttribute('aria-checked',String(selected))" in picker
    assert "frame.src=selected?TOMB_V2_SELECTED_FRAME:TOMB_V2_READY_FRAME" in picker
    assert "status.textContent=selected?'SELECTED':'READY'" in picker
    assert "confirm.disabled=false" in picker
    assert "beginPlayerActivation(selectedId)" in picker


def test_tomb_v2_does_not_render_legacy_monogram_wound_dial_cards():
    picker = section("const TOMB_V2_ASSET_ROOT", "function showPlayerActivation()")
    for legacy in (
        "tomb-operative-card-content",
        "tomb-operative-portrait-slot",
        "tomb-operative-wounds",
        "operative-ready.webp",
        "operative-selected.webp",
    ):
        assert legacy not in picker


def test_tomb_v2_styles_are_scoped_to_experimental_ui():
    assert 'html[data-ui="tomb"] .tomb-v2-shell' in CSS
    assert 'html[data-ui="tomb"] .tomb-v2-card' in CSS
    assert 'html[data-ui="tomb"] .tomb-v2-operative-grid' in CSS
    assert 'html[data-ui="tomb"] .tomb-v2-radio' in CSS


def test_tomb_v2_compact_portrait_and_landscape_layouts():
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in CSS
    landscape = CSS.split("@media(orientation:landscape) and (max-height:500px)", 1)[1]
    assert "grid-template-columns:repeat(4,minmax(0,1fr))" in landscape
    portrait = CSS.split("@media(orientation:portrait)", 1)[1]
    assert "grid-template-columns:repeat(2,minmax(0,1fr))!important" in portrait
    assert "gap:8px!important" in portrait


def test_tomb_v2_assets_are_precached_for_pwa_use():
    assert "./tomb-ui-v2.css" in WORKER
    for asset in (
        "./Assets/Images/TombUI/v2/portrait-sprite.webp",
        "./Assets/Images/TombUI/v2/card-ready.svg",
        "./Assets/Images/TombUI/v2/card-selected.svg",
    ):
        assert asset in WORKER


def test_save_schema_is_unchanged():
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
