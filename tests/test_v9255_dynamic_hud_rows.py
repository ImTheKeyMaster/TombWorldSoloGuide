import json
import re
from pathlib import Path

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
HUD_GRID = re.search(r"\.hud\{grid-template-rows:([^}]*)\}", STYLES).group(1)
HUD_CELL_GRID = re.search(r"\.hud>\.hud-cell\{([^}]*)\}", STYLES).group(1)


def test_two_line_maximum_uses_content_sized_shared_rows():
    assert HUD_GRID.startswith("auto auto;")
    assert "grid-row:span 2" in HUD_CELL_GRID
    assert "grid-template-rows:subgrid" in HUD_CELL_GRID
    assert "min-height" not in PORTRAIT_HUD


def test_three_line_maximum_keeps_all_six_label_value_pairs_in_shared_rows():
    assert HUD.count('class="hud-cell"') == 4
    assert 'class="hud-cell hud-threat"' in HUD
    assert 'class="hud-cell mission-hud"' in HUD
    assert HUD.count("<small>") == HUD.count("</small>")
    assert HUD.count("<strong>") == HUD.count("</strong>")
    assert "playerSideLabel()" in HUD


def test_dynamic_shrink_has_no_fixed_label_or_value_track_height():
    assert HUD_GRID.split(";", 1)[0] == "auto auto"
    assert not re.search(r"(?:min-)?height", HUD_GRID + HUD_CELL_GRID)


def test_threat_and_mission_buttons_keep_accessibility_and_interactions():
    assert 'id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"' in HUD
    assert 'id="missionHud" type="button" aria-label="Mission Details, ${escapeHtml(name)}, ${escapeHtml(status)}"' in HUD
    assert ".hud .hud-cell:focus-visible" in STYLES
    assert "$('#threatHudToggle')?.addEventListener('click'" in APP
    assert "$('#missionHud')?.addEventListener('click',showMissionDetails)" in APP


def test_portrait_breaks_wrap_naturally_without_fixed_three_line_reservation():
    assert ".portrait-break{display:inline}" in PORTRAIT_HUD
    assert ".hud small{line-height:1.1}" in PORTRAIT_HUD
    assert "min-height" not in PORTRAIT_HUD


def test_deathwatch_and_death_korps_keep_contextual_names_without_team_css():
    team_names = {
        json.loads((ROOT / path).read_text(encoding="utf-8"))["teamName"]
        for path in (
            "Player_Operatives/DeathWatch.json",
            "Player_Operatives/DeathKorps.json",
        )
    }
    assert team_names == {"Deathwatch", "Death Korps"}
    assert "playerSideLabel()" in HUD
    assert all(name.lower() not in STYLES.lower() for name in team_names)
