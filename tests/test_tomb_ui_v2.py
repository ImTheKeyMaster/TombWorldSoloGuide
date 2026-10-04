from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "tomb-ui-v2.css").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def picker_source():
    return APP.split("const TOMB_V2_ASSET_ROOT", 1)[1].split("function showPlayerActivation()", 1)[0]


def css_rule(selector):
    return CSS.split(selector + "{", 1)[1].split("}", 1)[0]


def test_v2_css_is_versioned_and_available_offline():
    assert f'href="tomb-ui-v2.css?v={CURRENT_APP_VERSION}"' in INDEX
    assert "./tomb-ui-v2.css" in WORKER
    assert "./Assets/Images/TombUI/v2/portrait-sprite.webp" in WORKER


def test_picker_uses_layout_first_markup_and_live_controls():
    picker = picker_source()
    assert 'class="tomb-v2-card"' in picker
    assert 'class="tomb-card-skin"' in picker
    assert 'class="tomb-v2-card-content"' in picker
    assert 'class="tomb-v2-portrait-zone"' in picker
    assert '<img class="tomb-v2-portrait portrait-${portrait}"' in picker
    assert 'class="tomb-v2-radio"' in picker
    assert 'class="tomb-v2-button primary"' in picker
    assert 'class="tomb-v2-button secondary"' in picker
    assert "beginPlayerActivation(selectedId)" in picker


def test_operative_cards_do_not_use_removed_frame_architecture():
    picker = picker_source()
    card_css = CSS.split('html[data-ui="tomb"] .tomb-v2-card{', 1)[1].split(
        'html[data-ui="tomb"] .tomb-v2-preview{', 1
    )[0]
    for removed in ("tomb-nine-slice", "tomb-frame-background", "tomb-frame-edges",
                    "tomb-frame-foreground", "tomb-card-frame-parts", "border-image", "mask:"):
        assert removed not in picker
        assert removed not in card_css


def test_cards_are_responsive_css_grid_components_with_stable_ratio():
    card = css_rule('html[data-ui="tomb"] .tomb-v2-card')
    content = css_rule('html[data-ui="tomb"] .tomb-v2-card-content')
    grid = css_rule('html[data-ui="tomb"] .tomb-v2-operative-grid')
    assert "display:grid" in card
    assert "aspect-ratio:2.7/1" in card
    assert "display:grid" in content
    assert "grid-template-columns:" in content
    assert "grid-auto-rows:auto" in grid
    assert "align-content:start" in grid


def test_portrait_viewport_clips_content_and_supports_archetypes():
    viewport = css_rule('html[data-ui="tomb"] .tomb-v2-portrait-zone')
    portrait = css_rule('html[data-ui="tomb"] .tomb-v2-portrait')
    assert "overflow:hidden" in viewport
    assert "height:100%" in viewport
    assert "object-fit:cover" in portrait
    for archetype in ("leader", "rifleman", "melee", "heavy"):
        assert f".portrait-{archetype}" in CSS


def test_preview_is_content_driven_three_column_grid():
    preview = css_rule('html[data-ui="tomb"] .tomb-v2-preview')
    assert "display:grid" in preview
    assert "grid-template-columns:" in preview
    assert "minmax(0,1fr)" in preview
    assert "height:auto" in preview
    assert "min-height:" in preview
    assert "class=\"tomb-v2-preview-icon\"" in picker_source()
    assert "class=\"tomb-v2-preview-ornament\"" in picker_source()


def test_portrait_and_landscape_column_counts_are_css_driven():
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in CSS
    landscape = CSS.split("@media(orientation:landscape) and (max-height:500px)", 1)[1]
    assert "grid-template-columns:repeat(4,minmax(0,1fr))" in landscape
    portrait = CSS.split("@media(orientation:portrait)", 1)[1]
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in portrait


def test_orientation_changes_never_write_visual_dimensions_in_javascript():
    picker = picker_source()
    for forbidden in ("orientationchange", "resize", ".style.height", ".style.width",
                      "gridTemplateRows", "gridAutoRows", "setProperty"):
        assert forbidden not in picker


def test_classic_picker_and_save_schema_remain_unchanged():
    classic = APP.split("function showPlayerActivation()", 1)[1].split("function playerActivationSummary", 1)[0]
    assert "document.documentElement.dataset.ui==='tomb'" in classic
    assert '<select id="humanPlayerSelection"' in classic
    assert "beginPlayerActivation($('#humanPlayerSelection').value)" in classic
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
