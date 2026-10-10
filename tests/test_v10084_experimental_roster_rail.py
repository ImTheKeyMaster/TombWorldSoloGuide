from pathlib import Path
import json

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
DEATHWATCH = json.loads((ROOT / "Player_Operatives" / "DeathWatch.json").read_text(encoding="utf-8"))
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "DeathwatchRoster"
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


def activation_picker_source():
    return APP[APP.index("function showPlayerActivation()") : APP.index("function playerActivationSummary")]


def test_release_surfaces_are_v10084_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 84)
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER


def test_roster_rail_is_strictly_experimental_and_deathwatch_only():
    picker = activation_picker_source()
    gate = "document.documentElement.dataset.ui==='tomb'&&selectedPlayerTeamName().toLowerCase()==='deathwatch'"
    assert gate in picker
    assert "showExperimentalDeathwatchRosterRail(candidates);" in picker
    assert picker.index("showExperimentalDeathwatchRosterRail(candidates);") < picker.index('id="humanPlayerSelection"')
    assert "if(candidates.length===1){beginPlayerActivation(candidates[0]);return;}" in picker


def test_current_mode_dropdown_path_is_preserved():
    picker = activation_picker_source()
    assert '<select id="humanPlayerSelection" data-dialog-focus>' in picker
    assert '<option value="">Select a Ready operative</option>' in picker
    assert "$('#humanPlayerSelection').onchange=()=>{$('#confirmHumanPlayerSelection').disabled=!$('#humanPlayerSelection').value;};" in picker
    assert "$('#confirmHumanPlayerSelection').onclick=()=>beginPlayerActivation($('#humanPlayerSelection').value);" in picker


def test_roster_rail_uses_integrated_radio_style_selection_and_keyboard_navigation():
    rail = APP[APP.index("function showExperimentalDeathwatchRosterRail") : APP.index("function showPlayerActivation")]
    assert 'role="radiogroup"' in rail
    assert 'role="radio"' in rail
    assert 'aria-checked="false"' in rail
    assert "$$('[data-roster-operative]',modal).forEach" in rail
    assert "['ArrowLeft','ArrowRight','Home','End']" in rail
    assert "button.setAttribute('aria-checked',String(selected));" in rail
    assert "confirm.disabled=false;" in rail


def test_roster_assets_are_individual_complete_and_precached():
    definition_ids = {item["id"] for item in DEATHWATCH["operatives"]}
    assert definition_ids == set(OPERATIVES)
    for operative_id in OPERATIVES:
        asset = ASSET_ROOT / f"{operative_id}.svg"
        assert asset.is_file(), operative_id
        svg = asset.read_text(encoding="utf-8")
        assert 'viewBox="0 0 160 160"' in svg, operative_id
        assert "M15 149h130" in svg, operative_id
        worker_path = f"./Assets/Images/TombUI/DeathwatchRoster/{operative_id}.svg"
        assert worker_path in WORKER
    assert "DeathwatchRoster/" in APP
    assert "sprite" not in APP[APP.index("const EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT") : APP.index("function showPlayerActivation")].lower()


def test_roster_rail_stays_one_row_and_fits_the_max_deathwatch_roster():
    assert DEATHWATCH["rosterSize"] == 5
    block = CSS.split("Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1)[1]
    assert 'html[data-ui="tomb"] .experimental-roster-rail{' in block
    rail = block.split('html[data-ui="tomb"] .experimental-roster-rail{', 1)[1].split("}", 1)[0]
    assert "display:flex" in rail
    assert "overflow:hidden" in rail
    item = block.split('html[data-ui="tomb"] .experimental-roster-item{', 1)[1].split("}", 1)[0]
    assert "flex:1 1 0" in item
    assert "min-width:0" in item


def test_new_roster_styles_are_experimental_only():
    marker = "/* v10.0.84: Experimental Deathwatch Roster Rail. Current UI is intentionally untouched. */"
    assert marker in CSS
    block = CSS.split(marker, 1)[1]
    assert 'html[data-ui="tomb"] .experimental-roster-picker' in block
    assert 'html[data-ui="tomb"] .experimental-roster-detail' in block
    assert 'html[data-ui="classic"] .experimental-roster' not in CSS


def test_experimental_panel_copy_mentions_roster_rail():
    assert "Experimental Tomb UI" in INDEX
    assert "Deathwatch Roster Rail" in INDEX


def test_mobile_roster_labels_remain_readable_and_can_wrap():
    block = CSS.split("Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1)[1]
    assert "font-size:clamp(.6rem,1.55vw,.7rem)" in block
    assert "white-space:normal" in block
    assert "-webkit-line-clamp:2" in block
    mobile = block.split("@media(max-width:600px)", 1)[1].split("@media(max-height:520px)", 1)[0]
    assert "font-size:.62rem" in mobile
    assert "padding:4px 2px 29px" in mobile
