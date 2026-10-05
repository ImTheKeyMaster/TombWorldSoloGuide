from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v3.css").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def rule(selector):
    return CSS.split(selector + "{", 1)[1].split("}", 1)[0]


def test_v3_skin_is_loaded_after_v2_and_versioned():
    v2 = f'tomb-ui-v2.css?v={CURRENT_APP_VERSION}'
    v3 = f'tomb-ui-v3.css?v={CURRENT_APP_VERSION}'
    assert v2 in INDEX
    assert v3 in INDEX
    assert INDEX.index(v2) < INDEX.index(v3)


def test_runtime_uses_v3_portrait_sprite():
    picker = APP.split("const TOMB_V2_ASSET_ROOT", 1)[1].split("function showPlayerActivation()", 1)[0]
    assert "Assets/Images/TombUI/v3/" in picker
    assert "portraits.webp" in picker
    assert "portrait-sprite.webp" not in picker


def test_v3_card_skin_preserves_reference_aspect_ratio():
    card = rule('html[data-ui="tomb"] .tomb-v2-card')
    assert "aspect-ratio:480/180" in card
    assert 'card-ready.svg' in card
    selected = rule('html[data-ui="tomb"] .tomb-v2-card.selected')
    assert 'card-selected.svg' in selected


def test_v3_selected_card_has_layered_glow_without_geometry_change():
    selected = rule('html[data-ui="tomb"] .tomb-v2-card.selected')
    assert selected.count("0 0") >= 3
    assert "width:" not in selected
    assert "height:" not in selected
    assert "aspect-ratio:" not in selected


def test_v3_selection_control_uses_art_assets():
    off = rule('html[data-ui="tomb"] .tomb-v2-radio')
    on = rule('html[data-ui="tomb"] .tomb-v2-card.selected .tomb-v2-radio')
    assert "select-unselected.svg" in off
    assert "select-selected.svg" in on


def test_v3_buttons_use_fixed_endcaps_and_stretchable_centers():
    primary = rule('html[data-ui="tomb"] .tomb-v2-button.primary')
    secondary = rule('html[data-ui="tomb"] .tomb-v2-button.secondary')
    for name in ("button-confirm-left.svg", "button-confirm-center.svg", "button-confirm-right.svg"):
        assert name in primary
    for name in ("button-cancel-left.svg", "button-cancel-center.svg", "button-cancel-right.svg"):
        assert name in secondary
    assert "calc(100% -" in primary
    assert "calc(100% -" in secondary


def test_v3_uses_separate_portrait_and_landscape_outer_frames():
    assert "screen-frame-portrait.svg" in CSS
    landscape = CSS.split("@media(orientation:landscape) and (max-height:500px)", 1)[1]
    assert "screen-frame-landscape.svg" in landscape
    assert "aspect-ratio:430/932" in CSS
    assert "aspect-ratio:1170/556" in landscape


def test_v3_action_preview_uses_art_shell_and_live_content_layout():
    preview = rule('html[data-ui="tomb"] .tomb-v2-preview')
    assert "action-preview.svg" in preview
    assert "grid-template-columns:" in preview
    assert "minmax(0,1fr)" in preview


def test_v3_assets_are_precached_for_offline_play():
    for asset in (
        "./tomb-ui-v3.css",
        "./Assets/Images/TombUI/v3/portraits.webp",
        "./Assets/Images/TombUI/v3/screen-frame-portrait.svg",
        "./Assets/Images/TombUI/v3/screen-frame-landscape.svg",
        "./Assets/Images/TombUI/v3/card-ready.svg",
        "./Assets/Images/TombUI/v3/card-selected.svg",
        "./Assets/Images/TombUI/v3/action-preview.svg",
        "./Assets/Images/TombUI/v3/button-confirm-left.svg",
        "./Assets/Images/TombUI/v3/button-confirm-center.svg",
        "./Assets/Images/TombUI/v3/button-confirm-right.svg",
        "./Assets/Images/TombUI/v3/button-cancel-left.svg",
        "./Assets/Images/TombUI/v3/button-cancel-center.svg",
        "./Assets/Images/TombUI/v3/button-cancel-right.svg",
    ):
        assert asset in WORKER


def test_classic_ui_and_save_schema_are_unchanged():
    classic = APP.split("function showPlayerActivation()", 1)[1].split("function playerActivationSummary", 1)[0]
    assert "document.documentElement.dataset.ui==='tomb'" in classic
    assert '<select id="humanPlayerSelection"' in classic
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
