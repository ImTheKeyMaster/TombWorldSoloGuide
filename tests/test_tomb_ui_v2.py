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


def test_tomb_picker_uses_v3_frame_as_non_obscuring_background_detail():
    picker = picker_source()
    frame = css_rule('html[data-ui="tomb"] .tomb-v3-screen-frame')
    modal = css_rule('html[data-ui="tomb"] .tomb-operative-picker-modal')
    shell = css_rule('html[data-ui="tomb"] .tomb-v2-shell')
    content_layer = css_rule('html[data-ui="tomb"] .tomb-v2-shell>:not(.tomb-v3-screen-frame)')
    portrait_svg = (ROOT / "Assets/Images/TombUI/v3/screen-frame-portrait.svg").read_text(encoding="utf-8")
    landscape_svg = (ROOT / "Assets/Images/TombUI/v3/screen-frame-landscape.svg").read_text(encoding="utf-8")
    assert 'class="tomb-v3-screen-frame"' in picker
    assert "position:absolute" in frame
    assert "inset:0" in frame
    assert "pointer-events:none" in frame
    assert "z-index:0" in frame
    assert "transform:scaleX(1.12)" in frame
    assert "screen-frame-portrait.svg" in frame
    assert "z-index:1" in content_layer
    assert "border:0" in modal
    assert "background:transparent" in modal
    assert "box-shadow:none" in modal
    assert "padding:14px" in shell
    assert "min-height:0" in shell
    assert "overflow:hidden" in shell
    assert 'preserveAspectRatio="none"' in portrait_svg
    assert 'preserveAspectRatio="none"' in landscape_svg
    landscape = CSS.split("@media(orientation:landscape) and (max-height:500px)", 1)[1]
    assert "screen-frame-landscape.svg" in landscape
    assert "transform:none" in landscape
    assert 'padding:8px 10px calc(8px + env(safe-area-inset-bottom))' in landscape


def test_tomb_confirm_has_no_chevron_and_classic_picker_is_untouched():
    picker = picker_source()
    tomb_confirm = picker.split('id="confirmTombPlayerSelection"', 1)[1].split("</button>", 1)[0]
    confirm_skin = (ROOT / "Assets/Images/TombUI/v3/button-confirm-full.svg").read_text(encoding="utf-8")
    assert "»" not in tomb_confirm
    assert "M447 42l16 18-16 18" not in confirm_skin
    classic = APP.split("function showPlayerActivation()", 1)[1].split("function playerActivationSummary", 1)[0]
    assert '<select id="humanPlayerSelection"' in classic
    assert 'id="confirmHumanPlayerSelection"' in classic


def test_v2_css_is_versioned_and_available_offline():
    assert f'href="tomb-ui-v2.css?v={CURRENT_APP_VERSION}"' in INDEX
    assert "./tomb-ui-v2.css" in WORKER
    assert "./Assets/Images/TombUI/v3/portrait-leader.webp" in WORKER
    assert "./Assets/Images/TombUI/v3/portrait-rifleman.webp" in WORKER
    assert "./Assets/Images/TombUI/v3/portrait-melee.webp" in WORKER
    assert "./Assets/Images/TombUI/v3/portrait-heavy.webp" in WORKER
    assert "./Assets/Images/TombUI/v3/screen-frame-portrait.svg" in WORKER
    assert "./Assets/Images/TombUI/v3/screen-frame-landscape.svg" in WORKER


def test_physical_portraits_preserve_aspect_ratio_by_orientation():
    portrait_marker = '@media (orientation:portrait){\n html[data-ui="tomb"] img.tomb-v2-portrait{'
    portrait_override = CSS.split(portrait_marker, 1)[1].split("}", 1)[0]
    assert "width:auto!important;height:100%!important" in portrait_override
    landscape_marker = '@media (orientation:landscape) and (max-height:600px){\n html[data-ui="tomb"] img.tomb-v2-portrait{'
    compact_landscape = CSS.split(landscape_marker, 1)[1].split("}", 1)[0]
    assert "width:100%!important;height:auto!important" in compact_landscape


def test_release_version_surfaces_follow_current_app_version():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") >= 12


def test_hud_uses_dedicated_icons_and_live_apl_meter():
    picker = picker_source()
    assert "tombV2HudIcon('threat')" in picker
    assert "tombV2HudIcon('tp')" in picker
    assert "tombV2HudIcon('apl')" in picker
    assert 'class="tomb-v2-hud-label"' in picker
    assert 'class="tomb-v2-hud-value"' in picker
    assert 'id="tombV2AplDots"' in picker
    assert "effectiveApl(candidates[0],Number(firstDefinition?.apl||3))" in picker
    assert "selectedApl=effectiveApl(selectedId,Number(definition.apl||3))" in picker
    assert "aplDots.innerHTML=tombV2AplDots(selectedApl)" in picker
    assert "modal.querySelectorAll(\'[data-tomb-player-operative]\').forEach" in picker
    assert "grid-template-columns:1.1fr 1.1fr .86fr" in CSS
    assert "max-width:12px" in CSS
    assert "(max-width:740px)" in CSS
    assert "grid-template-columns:16px minmax(0,1fr) 18px" in CSS


def test_picker_uses_layout_first_markup_and_live_controls():
    picker = picker_source()
    assert 'class="tomb-v2-card"' in picker
    assert 'class="tomb-card-skin"' in picker
    assert 'class="tomb-v2-card-content"' in picker
    assert 'class="tomb-v2-portrait-zone"' in picker
    assert '<img class="tomb-v2-portrait"' in picker
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


def test_buttons_remain_layout_driven_instead_of_stretched_images():
    picker = picker_source()
    button = css_rule('html[data-ui="tomb"] .tomb-v2-button')
    assert '<button class="tomb-v2-button primary"' in picker
    assert '<button class="tomb-v2-button secondary"' in picker
    assert 'tomb-v2-button-skin' not in picker
    assert "display:flex" in button
    assert "background-size:100% 100%" in button
    assert "clip-path:none" in button
    assert "object-fit:fill" not in button
    assert "<img" not in picker.split('class="tomb-v2-actions"', 1)[1]

def test_portrait_viewport_clips_content_and_supports_archetypes():
    viewport = css_rule('html[data-ui="tomb"] .tomb-v2-portrait-zone')
    portrait = css_rule('html[data-ui="tomb"] .tomb-v2-portrait')
    assert "overflow:hidden" in viewport
    assert "height:100%" in viewport
    assert "width:400%" in portrait
    assert "height:auto" in portrait
    assert "max-height:none" in portrait
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


def test_landscape_picker_scrolls_on_outer_modal_for_ios():
    landscape = CSS.split("@media(orientation:landscape) and (max-height:500px)", 1)[1].split("@media(orientation:portrait)", 1)[0]
    modal = landscape.split('html[data-ui="tomb"] .tomb-operative-picker-modal{', 1)[1].split("}", 1)[0]
    inner = landscape.split('html[data-ui="tomb"] .tomb-operative-picker-modal .modal-inner{', 1)[1].split("}", 1)[0]
    assert "overflow-y:auto!important" in modal
    assert "overflow-x:hidden!important" in modal
    assert "-webkit-overflow-scrolling:touch" in modal
    assert "touch-action:pan-y" in modal
    assert "max-height:calc(100dvh - 10px)!important" in modal
    assert "max-height:none!important" in inner
    assert "overflow:visible!important" in inner
    assert "overflow:auto" not in inner


def test_frame_safe_areas_keep_content_inside_portrait_and_landscape_rails():
    release_css = CSS.split("/* v10.0.65: keep all Tomb picker content inside the decorative frame opening. */", 1)[1]
    portrait = release_css.split("@media (orientation:portrait){", 1)[1].split("@media (orientation:landscape)", 1)[0]
    landscape = release_css.split("@media (orientation:landscape) and (max-height:600px){", 1)[1]
    assert "padding-top:38px" in portrait
    assert "padding-right:18px" in portrait
    assert "padding-left:18px" in portrait
    assert "padding-top:clamp(34px,8dvh,46px)" in landscape
    assert "padding-right:clamp(46px,5vw,64px)" in landscape
    assert "padding-bottom:clamp(36px,8dvh,48px)" in landscape
    assert "padding-left:clamp(46px,5vw,64px)" in landscape
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in CSS
    narrow = release_css.split("@media (orientation:landscape) and (max-height:600px) and (max-width:740px){", 1)[1]
    assert "padding-right:34px" in narrow
    assert "padding-left:34px" in narrow
    assert "flex-wrap:nowrap" in narrow
    assert "gap:8px" in narrow
    assert "flex:1 1 0" in narrow
    assert "min-width:120px" in narrow


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
    assert 'class="btn ghost" data-close>Close Guide</button>' in classic


def test_picker_uses_v3_portrait_sprite_without_v3_layout_skin():
    picker = picker_source()
    assert "Assets/Images/TombUI/v3/portrait-" in picker
    assert "tomb-ui-v3.css" not in INDEX
    portrait = css_rule('html[data-ui="tomb"] .tomb-v2-portrait')
    assert "width:400%" in portrait
    assert "height:auto" in portrait
    assert "max-height:none" in portrait


def test_selected_state_uses_layered_glow_without_geometry_change():
    selected = css_rule('html[data-ui="tomb"] .tomb-v2-card.selected')
    assert selected.count("0 0") >= 4
    assert "width:" not in selected
    assert "height:" not in selected
    assert "aspect-ratio:" not in selected


def test_final_card_frame_hierarchy_keeps_selected_border_brightest():
    release_css = CSS.split("/* v10.0.63: selected-card hierarchy and continuous HUD pill frames */", 1)[1]
    base = release_css.split('html[data-ui="tomb"] .tomb-v2-card{', 1)[1].split("}", 1)[0]
    selected = release_css.split('html[data-ui="tomb"] .tomb-v2-card.selected{', 1)[1].split("}", 1)[0]
    assert "--accent:#416f7c" in base
    assert "--accent:#65e4ff" in selected
    assert "background:var(--accent)" in selected
    assert selected.count("0 0") >= 4


def test_hud_pills_use_one_contiguous_chamfered_outline():
    release_css = CSS.split("/* v10.0.63: selected-card hierarchy and continuous HUD pill frames */", 1)[1]
    cell = release_css.split('html[data-ui="tomb"] .tomb-v2-hud-cell{', 1)[1].split("}", 1)[0]
    inner = release_css.split('html[data-ui="tomb"] .tomb-v2-hud-cell::after{', 1)[1].split("}", 1)[0]
    top_fragment = release_css.split('html[data-ui="tomb"] .tomb-v2-hud-cell::before{', 1)[1].split("}", 1)[0]
    assert "border:0" in cell
    assert "background:#4c8996" in cell
    assert "content:none" in top_fragment
    assert "inset:1px" in inner
    assert "clip-path:polygon(" in inner


def test_v3_buttons_use_single_seamless_vector_skins():
    picker = picker_source()
    primary = css_rule('html[data-ui="tomb"] .tomb-v2-button.primary')
    secondary = css_rule('html[data-ui="tomb"] .tomb-v2-button.secondary')
    base = css_rule('html[data-ui="tomb"] .tomb-v2-button')
    assert 'tomb-v2-button-skin' not in picker
    assert "button-confirm-full.svg" in primary
    assert "button-cancel-full.svg" in secondary
    assert "button-confirm-left.svg" not in primary
    assert "button-cancel-left.svg" not in secondary
    assert "background-size:100% 100%" in base


def test_v3_button_assets_are_precached():
    service_worker = (ROOT / "service-worker.js").read_text()
    assert "button-confirm-full.svg" in service_worker
    assert "button-cancel-full.svg" in service_worker
    for retired_piece in (
        "button-confirm-left.svg",
        "button-confirm-center.svg",
        "button-confirm-right.svg",
        "button-cancel-left.svg",
        "button-cancel-center.svg",
        "button-cancel-right.svg",
    ):
        assert retired_piece not in service_worker


def test_v3_button_focus_indicator_remains_accessible():
    focus = css_rule('html[data-ui="tomb"] .tomb-v2-button:focus-visible')
    assert "outline:2px solid #8ee7ff" in focus
    assert "outline-offset:3px" in focus
