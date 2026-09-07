from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")


def section(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


HUD = section(APP, "function missionHudHtml()", "const missionProgressRenderers")
PORTRAIT_HUD = section(
    STYLES,
    "/* v2.2.5: aligned portrait HUD labels",
    "/* v2.2.8: read-only Player defense profile",
)
DYNAMIC_HUD = section(
    STYLES,
    "/* v9.2." "55: dynamically shared HUD label and value rows */",
    "/* v2.2.8: read-only Player defense profile",
)


def test_release_and_shared_dynamic_two_row_grid():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 55)
    assert ".hud{grid-template-rows:auto auto;column-gap:1px;row-gap:0}" in DYNAMIC_HUD
    assert "grid-row:span 2" in DYNAMIC_HUD
    assert "grid-template-rows:subgrid" in DYNAMIC_HUD
    assert "min-height" not in PORTRAIT_HUD


def test_all_six_semantic_label_value_pairs_participate_in_shared_rows():
    assert HUD.count('class="hud-cell"') == 4
    assert 'class="hud-cell hud-threat"' in HUD
    assert 'class="hud-cell mission-hud"' in HUD
    assert HUD.count("<small>") >= 6
    assert HUD.count("<strong>") >= 6
    assert "playerSideLabel()" in HUD
    assert "DeathKorps" not in DYNAMIC_HUD
    assert "DeathWatch" not in DYNAMIC_HUD


def test_threat_and_mission_buttons_keep_accessibility_and_interactions():
    assert 'id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"' in HUD
    assert 'id="missionHud" type="button" aria-label="Mission Details, ${escapeHtml(name)}, ${escapeHtml(status)}"' in HUD
    assert ".hud .hud-cell:focus-visible" in STYLES
    assert "$('#threatHudToggle')?.addEventListener('click'" in APP
    assert "$('#missionHud')?.addEventListener('click',showMissionDetails)" in APP


def test_portrait_breaks_wrap_naturally_without_fixed_three_line_reservation():
    assert ".portrait-break{display:inline}" in PORTRAIT_HUD
    assert ".hud small{line-height:1.1}" in PORTRAIT_HUD
    assert "height:" not in DYNAMIC_HUD
    assert "min-height:" not in DYNAMIC_HUD
